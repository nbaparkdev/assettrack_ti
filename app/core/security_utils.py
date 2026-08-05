import os
import uuid
from typing import Set, Optional
from fastapi import HTTPException, UploadFile, status

ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_DOCUMENT_EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv", ".zip", ".xml"
}
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

def validate_uploaded_file(
    file: UploadFile,
    allowed_extensions: Set[str] = ALLOWED_IMAGE_EXTENSIONS,
) -> str:
    """
    Validates file upload extensions and cleans filenames to prevent path traversal
    and execution of arbitrary/malicious file types (XSS, RCE).
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido ou não fornecido."
        )

    filename = os.path.basename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if not ext or ext not in allowed_extensions:
        allowed_str = ", ".join(sorted(allowed_extensions))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo '{ext}' não permitido. Extensões aceitas: {allowed_str}"
        )

    return ext

def generate_safe_filename(ext: str, prefix: str = "upload") -> str:
    """Generates a secure UUID-based filename."""
    clean_ext = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
    return f"{prefix}_{uuid.uuid4().hex[:12]}{clean_ext}"
