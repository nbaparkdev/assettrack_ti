
# app/services/email_service.py
import traceback
import smtplib
import asyncio
from email.message import EmailMessage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.models.email_log import EmailLog
from app.crud.system_settings import system_settings


def _send_smtp_email(host, port, user, password, tls, sender, recipient, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    server = smtplib.SMTP(host, int(port), timeout=15)
    if tls:
        server.starttls()

    server.login(user, password)
    server.send_message(msg)
    server.quit()


async def _save_email_log(session_factory: async_sessionmaker, recipient: str, subject: str, body: str, status: str, error_message: str):
    """Salva o log de e-mail em uma sessão própria e independente, sem interferir na sessão principal."""
    try:
        async with session_factory() as log_db:
            log = EmailLog(
                recipient=recipient,
                subject=subject,
                body=body,
                status=status,
                error_message=error_message
            )
            log_db.add(log)
            await log_db.commit()
    except Exception as e:
        print(f"[EMAIL LOG] Erro ao salvar log: {e}")


class EmailService:
    async def send_notification(
        self,
        email_to: str,
        subject: str,
        message: str,
        db: AsyncSession = None
    ) -> bool:
        status = "SUCCESS"
        error_message = None

        if not db:
            print("[EMAIL] Nenhuma sessão DB fornecida, e-mail não enviado.")
            return False

        try:
            # Lê as configurações SMTP do banco de dados
            smtp_host = await system_settings.get_setting(db, "smtp_host", "")
            smtp_port = await system_settings.get_setting(db, "smtp_port", "587")
            smtp_user = await system_settings.get_setting(db, "smtp_user", "")
            smtp_pass = await system_settings.get_setting(db, "smtp_password", "")
            smtp_tls_str = await system_settings.get_setting(db, "smtp_tls", "true")
            smtp_from = await system_settings.get_setting(db, "smtp_from", smtp_user)

            smtp_tls = smtp_tls_str.lower() == "true"

            if not smtp_host or not smtp_user or not smtp_pass:
                raise Exception("Configurações SMTP incompletas no sistema.")

            # Executa o envio em thread separada (não bloqueia o event loop)
            await asyncio.to_thread(
                _send_smtp_email,
                smtp_host, smtp_port, smtp_user, smtp_pass,
                smtp_tls, smtp_from, email_to, subject, message
            )

        except Exception as e:
            status = "ERROR"
            error_message = str(e)
            print(f"[EMAIL] Erro no envio para {email_to}: {e}")
            traceback.print_exc()

        # Salva o log em sessão própria para não corromper a sessão do chamador
        try:
            # Obtém a session factory a partir da engine da sessão atual
            from app.database import SessionLocal
            await _save_email_log(
                session_factory=SessionLocal,
                recipient=email_to,
                subject=subject,
                body=message,
                status=status,
                error_message=error_message
            )
        except Exception as e:
            print(f"[EMAIL LOG] Falha ao registrar log: {e}")

        return status == "SUCCESS"
