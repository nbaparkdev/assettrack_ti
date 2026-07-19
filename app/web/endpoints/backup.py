import io
import os
import json
import zipfile
from collections import defaultdict, deque
from datetime import datetime
from app.core.datetime_utils import now_sp
from typing import Annotated, Optional

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import StreamingResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect as sa_inspect
from app.database import get_db, engine
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _topological_sort(inspector, table_names: list[str]) -> list[str]:
    """Sort tables so that parent tables (referenced by FKs) come before child tables.

    Handles circular FK dependencies (users <-> departamentos) by treating
    nullable FKs as non-blocking for the sort.
    """
    # Build parent->child graph: parent -> [children that reference it]
    children = defaultdict(list)
    for table_name in table_names:
        for fk in inspector.get_foreign_keys(table_name):
            parent = fk["referred_table"]
            children[parent].append(table_name)

    # Compute in-degree: how many parent tables each table depends on
    in_degree = {t: 0 for t in table_names}
    for child, fks in [(t, inspector.get_foreign_keys(t)) for t in table_names]:
        for fk in fks:
            parent = fk["referred_table"]
            in_degree[child] += 1

    # Kahn's algorithm
    queue = deque([t for t in table_names if in_degree[t] == 0])
    result = []

    while queue:
        table = queue.popleft()
        result.append(table)
        for child in children.get(table, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Handle circular dependencies (tables remaining in the cycle)
    remaining = [t for t in table_names if t not in result]
    for table in remaining:
        in_degree[table] = 0  # force-add
    queue = deque([t for t in remaining if in_degree[t] == 0])
    while queue:
        table = queue.popleft()
        if table not in result:
            result.append(table)
        for child in children.get(table, []):
            if child in remaining and child not in result:
                queue.append(child)
    # Append any still-missing tables
    for table in table_names:
        if table not in result:
            result.append(table)

    return result


async def check_admin(user: Annotated[User, Depends(get_active_user_web)]):
    if user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Acesso negado")
    return user


@router.get("/admin/backup", response_class=HTMLResponse)
async def backup_page(
    request: Request,
    success: Optional[str] = None,
    error: Optional[str] = None,
    user: Annotated[User, Depends(check_admin)] = None,
):
    return templates.TemplateResponse("admin/backup.html", {
        "request": request,
        "user": user,
        "success": success,
        "error": error,
        "title": "Backup do Sistema",
    })


@router.post("/admin/backup/export")
async def export_backup(
    request: Request,
    user: Annotated[User, Depends(check_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        def dump_sync(sync_conn):
            inspector = sa_inspect(sync_conn.get_bind())
            all_tables = inspector.get_table_names()
            # Sort topologically: parent tables before child tables (INSERTs won't violate FKs)
            ordered_tables = _topological_sort(inspector, all_tables)
            lines = [
                f"-- AssetTrack TI Backup",
                f"-- Gerado por: {user.nome}",
                f"-- Data: {now_sp().isoformat()}",
                "",
            ]
            for table_name in ordered_tables:
                columns = inspector.get_columns(table_name)
                col_names = [c["name"] for c in columns]
                if not col_names:
                    continue
                rows = sync_conn.execute(
                    text(f'SELECT * FROM "{table_name}"')
                ).fetchall()
                if not rows:
                    continue
                lines.append(f"\n-- Table: {table_name}")
                col_list = ", ".join(f'"{c}"' for c in col_names)
                # Batch rows in groups of 500 for faster import
                batch = []
                for row in rows:
                    vals = []
                    for v in row:
                        if v is None:
                            vals.append("NULL")
                        elif isinstance(v, (int, float)):
                            vals.append(str(v))
                        elif isinstance(v, bool):
                            vals.append("TRUE" if v else "FALSE")
                        elif isinstance(v, datetime):
                            vals.append(f"'{v.isoformat()}'")
                        elif isinstance(v, bytes):
                            vals.append(f"'\\x{v.hex()}'")
                        elif isinstance(v, (dict, list)):
                            json_str = json.dumps(v, ensure_ascii=False)
                            escaped = json_str.replace("'", "''")
                            vals.append(f"'{escaped}'")
                        elif isinstance(v, str):
                            if (v.startswith("[") and v.endswith("]")) or (v.startswith("{") and v.endswith("}")):
                                try:
                                    json.loads(v)
                                except json.JSONDecodeError:
                                    try:
                                        import ast
                                        parsed = ast.literal_eval(v)
                                        v = json.dumps(parsed, ensure_ascii=False)
                                    except Exception:
                                        pass
                            escaped = v.replace("'", "''")
                            vals.append(f"'{escaped}'")
                        else:
                            escaped = str(v).replace("'", "''")
                            vals.append(f"'{escaped}'")
                    batch.append(f"({', '.join(vals)})")
                    if len(batch) >= 500:
                        lines.append(
                            f"INSERT INTO \"{table_name}\" ({col_list}) VALUES\n  {', '.join(batch)};"
                        )
                        batch = []
                if batch:
                    lines.append(
                        f"INSERT INTO \"{table_name}\" ({col_list}) VALUES\n  {', '.join(batch)};"
                    )
            return "\n".join(lines)

        sql_dump = await db.run_sync(dump_sync)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("database.sql", sql_dump)

            uploads_dir = "static/uploads"
            if os.path.exists(uploads_dir):
                for root, dirs, files in os.walk(uploads_dir):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        arcname = os.path.join(
                            "uploads",
                            os.path.relpath(filepath, uploads_dir),
                        )
                        zf.write(filepath, arcname)

        buf.seek(0)
        timestamp = now_sp().strftime("%Y%m%d_%H%M%S")
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="backup_assettrack_{timestamp}.zip"'
            },
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/backup?error=Erro+ao+exportar:+{str(e)}",
            status_code=303,
        )


@router.post("/admin/backup/import")
async def import_backup(
    request: Request,
    backup_file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(check_admin)],
):
    if not backup_file.filename or not backup_file.filename.endswith(".zip"):
        return RedirectResponse(
            url="/admin/backup?error=Arquivo+invalido.+Envie+um+.zip",
            status_code=303,
        )

    try:
        contents = await backup_file.read()
        buf = io.BytesIO(contents)

        with zipfile.ZipFile(buf, "r") as zf:
            # Restore database from SQL
            if "database.sql" in zf.namelist():
                sql_content = zf.read("database.sql").decode("utf-8")

                async with engine.connect() as raw_conn:
                    await raw_conn.run_sync(lambda conn: _import_sql(conn, sql_content))

            # Restore uploaded files
            for name in zf.namelist():
                if name.startswith("uploads/") and not name.endswith("/"):
                    target = os.path.join("static", name)
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with open(target, "wb") as f:
                        f.write(zf.read(name))

        return RedirectResponse(
            url="/admin/backup?success=Backup+restaurado+com+sucesso!",
            status_code=303,
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/backup?error=Erro+ao+importar:+{str(e)}",
            status_code=303,
        )


def _import_sql(conn, sql_content: str):
    """Delete all data and import SQL dump in a single transaction.

    Uses DELETE (ROW EXCLUSIVE lock) instead of TRUNCATE (ACCESS EXCLUSIVE)
    to avoid lock conflicts with other sessions that hold ACCESS SHARE locks
    from SELECT queries (e.g. the user session from cookie auth).
    """
    with conn.begin():
        inspector = sa_inspect(conn)
        tables = inspector.get_table_names()

        # Break circular FK (users <-> departamentos) by nullifying nullable FKs
        for stmt in [
            'UPDATE "users" SET departamento_id = NULL',
            'UPDATE "departamentos" SET responsavel_id = NULL',
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # Delete in reverse topological order (children before parents),
        # so FK constraints aren't violated when deleting parent rows.
        ordered = _topological_sort(inspector, tables)
        for table_name in reversed(ordered):
            try:
                conn.execute(text(f'DELETE FROM "{table_name}"'))
            except Exception:
                pass

        # Parse statements: accumulate lines until semicolon, skip comment-only lines
        stmt_lines = []
        for line in sql_content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            stmt_lines.append(line)
            if stripped.endswith(";"):
                stmt = "\n".join(stmt_lines).rstrip(";").strip()
                if stmt:
                    conn.execute(text(stmt))
                stmt_lines = []
