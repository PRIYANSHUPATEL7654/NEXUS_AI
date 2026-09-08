import hashlib
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import UploadFile


load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parents[2]

configured_upload_directory = Path(
    os.getenv(
        "UPLOAD_DIRECTORY",
        "storage/uploads"
    )
)

if configured_upload_directory.is_absolute():
    UPLOAD_ROOT = configured_upload_directory.resolve()
else:
    UPLOAD_ROOT = (
        BACKEND_ROOT / configured_upload_directory
    ).resolve()

MAX_UPLOAD_SIZE_MB = int(
    os.getenv("MAX_UPLOAD_SIZE_MB", "10")
)

if MAX_UPLOAD_SIZE_MB <= 0:
    raise RuntimeError(
        "MAX_UPLOAD_SIZE_MB must be greater than zero"
    )

MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
CHUNK_SIZE_BYTES = 1024 * 1024

ALLOWED_FILE_TYPES: dict[str, set[str]] = {
    ".pdf": {
        "application/pdf",
        "application/octet-stream",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
        "application/octet-stream",
    },
    ".csv": {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    },
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
    ".txt": {
        "text/plain",
        "application/octet-stream",
    },
    ".md": {
        "text/markdown",
        "text/plain",
        "application/octet-stream",
    },
    ".png": {
        "image/png",
        "application/octet-stream",
    },
    ".jpg": {
        "image/jpeg",
        "application/octet-stream",
    },
    ".jpeg": {
        "image/jpeg",
        "application/octet-stream",
    },
}


class FileValidationError(ValueError):
    """Raised when an uploaded file is not acceptable."""


@dataclass(frozen=True)
class SavedUpload:
    original_filename: str
    stored_filename: str
    storage_path: str
    content_type: str
    extension: str
    size_bytes: int
    sha256_hash: str


def normalize_filename(filename: str | None) -> str:
    if not filename:
        raise FileValidationError(
            "The uploaded file must have a filename"
        )

    if "\x00" in filename:
        raise FileValidationError(
            "The filename contains an invalid character"
        )

    safe_filename = Path(
        filename.replace("\\", "/")
    ).name.strip()

    if not safe_filename:
        raise FileValidationError(
            "The uploaded file must have a valid filename"
        )

    if len(safe_filename) > 255:
        raise FileValidationError(
            "The filename must not exceed 255 characters"
        )

    return safe_filename


def validate_file_type(
    filename: str,
    content_type: str | None
) -> tuple[str, str]:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_FILE_TYPES:
        allowed_extensions = ", ".join(
            sorted(ALLOWED_FILE_TYPES)
        )
        raise FileValidationError(
            "Unsupported file extension. "
            f"Allowed extensions: {allowed_extensions}"
        )

    normalized_content_type = (
        content_type
        or "application/octet-stream"
    ).split(";", maxsplit=1)[0].strip().lower()

    if normalized_content_type not in ALLOWED_FILE_TYPES[extension]:
        raise FileValidationError(
            f"Content type {normalized_content_type!r} "
            f"does not match extension {extension!r}"
        )

    return extension, normalized_content_type


def validate_file_content(
    file_path: Path,
    extension: str
) -> None:
    with file_path.open("rb") as uploaded_file:
        header = uploaded_file.read(8192)

    if not header:
        raise FileValidationError(
            "Empty files are not allowed"
        )

    if extension == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise FileValidationError(
                "The file content is not a valid PDF"
            )
        return

    if extension == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise FileValidationError(
                "The file content is not a valid PNG image"
            )
        return

    if extension in {".jpg", ".jpeg"}:
        if not header.startswith(b"\xff\xd8\xff"):
            raise FileValidationError(
                "The file content is not a valid JPEG image"
            )
        return

    if extension in {".xlsx", ".docx"}:
        try:
            with zipfile.ZipFile(file_path) as archive:
                members = set(archive.namelist())
        except zipfile.BadZipFile as error:
            raise FileValidationError(
                f"The file content is not a valid {extension} file"
            ) from error

        required_member = (
            "xl/workbook.xml"
            if extension == ".xlsx"
            else "word/document.xml"
        )

        if required_member not in members:
            raise FileValidationError(
                f"The file content does not match {extension}"
            )
        return

    if extension in {".txt", ".csv", ".md"}:
        if b"\x00" in header:
            raise FileValidationError(
                "Text-based uploads cannot contain binary null bytes"
            )

        try:
            header.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise FileValidationError(
                "Text, CSV, and Markdown files must use UTF-8 encoding"
            ) from error


def storage_path_for_database(file_path: Path) -> str:
    try:
        return file_path.relative_to(
            BACKEND_ROOT
        ).as_posix()
    except ValueError:
        return str(file_path)


def resolve_storage_path(storage_path: str) -> Path:
    candidate = Path(storage_path)

    if not candidate.is_absolute():
        candidate = BACKEND_ROOT / candidate

    resolved_candidate = candidate.resolve()

    try:
        resolved_candidate.relative_to(UPLOAD_ROOT)
    except ValueError as error:
        raise RuntimeError(
            "Stored file path is outside the configured upload directory"
        ) from error

    return resolved_candidate


def delete_storage_file(storage_path: str) -> None:
    file_path = resolve_storage_path(storage_path)
    file_path.unlink(missing_ok=True)


async def save_upload_file(
    upload: UploadFile,
    user_id: int
) -> SavedUpload:
    original_filename = normalize_filename(
        upload.filename
    )
    extension, content_type = validate_file_type(
        original_filename,
        upload.content_type
    )

    user_directory = UPLOAD_ROOT / str(user_id)
    user_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    stored_filename = f"{uuid4().hex}{extension}"
    destination = user_directory / stored_filename

    sha256 = hashlib.sha256()
    size_bytes = 0

    try:
        with destination.open("xb") as output_file:
            while True:
                chunk = await upload.read(
                    CHUNK_SIZE_BYTES
                )

                if not chunk:
                    break

                size_bytes += len(chunk)

                if size_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise FileValidationError(
                        "File is too large. "
                        f"Maximum size is {MAX_UPLOAD_SIZE_MB} MB"
                    )

                sha256.update(chunk)
                output_file.write(chunk)

        validate_file_content(
            destination,
            extension
        )
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return SavedUpload(
        original_filename=original_filename,
        stored_filename=stored_filename,
        storage_path=storage_path_for_database(
            destination
        ),
        content_type=content_type,
        extension=extension,
        size_bytes=size_bytes,
        sha256_hash=sha256.hexdigest(),
    )
