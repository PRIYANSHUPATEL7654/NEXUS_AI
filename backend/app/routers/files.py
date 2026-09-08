from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..file_schemas import StoredFileResponse
from ..models import StoredFile, User
from ..security import get_current_active_user
from ..services.file_storage import (
    FileValidationError,
    delete_storage_file,
    resolve_storage_path,
    save_upload_file,
)


router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

ProcessingStatus = Literal[
    "uploaded",
    "extracting",
    "parsing",
    "awaiting_review",
    "completed",
    "failed",
]


def get_owned_file(
    file_id: int,
    user_id: int,
    db: Session
) -> StoredFile:
    stored_file = db.scalar(
        select(StoredFile).where(
            StoredFile.id == file_id,
            StoredFile.user_id == user_id
        )
    )

    if stored_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return stored_file


@router.post(
    "/upload",
    response_model=StoredFileResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: Annotated[
        UploadFile,
        File(description="NEXUS AI supported file")
    ],
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    try:
        saved_upload = await save_upload_file(
            file,
            current_user.id
        )
    except FileValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        ) from error
    finally:
        await file.close()

    existing_file = db.scalar(
        select(StoredFile).where(
            StoredFile.user_id == current_user.id,
            StoredFile.sha256_hash == saved_upload.sha256_hash
        )
    )

    if existing_file is not None:
        delete_storage_file(
            saved_upload.storage_path
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This file has already been uploaded. "
                f"Existing file ID: {existing_file.id}"
            )
        )

    stored_file = StoredFile(
        user_id=current_user.id,
        original_filename=saved_upload.original_filename,
        stored_filename=saved_upload.stored_filename,
        storage_path=saved_upload.storage_path,
        content_type=saved_upload.content_type,
        extension=saved_upload.extension,
        size_bytes=saved_upload.size_bytes,
        sha256_hash=saved_upload.sha256_hash,
        processing_status="uploaded"
    )

    db.add(stored_file)

    try:
        db.commit()
        db.refresh(stored_file)
    except IntegrityError as error:
        db.rollback()
        delete_storage_file(
            saved_upload.storage_path
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This file has already been uploaded"
        ) from error
    except Exception:
        db.rollback()
        delete_storage_file(
            saved_upload.storage_path
        )
        raise

    return stored_file


@router.get(
    "",
    response_model=list[StoredFileResponse]
)
def list_my_files(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    processing_status: ProcessingStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    statement = select(StoredFile).where(
        StoredFile.user_id == current_user.id
    )

    if processing_status is not None:
        statement = statement.where(
            StoredFile.processing_status == processing_status
        )

    statement = (
        statement
        .order_by(StoredFile.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/{file_id}",
    response_model=StoredFileResponse
)
def read_file_metadata(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    return get_owned_file(
        file_id,
        current_user.id,
        db
    )


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    stored_file = get_owned_file(
        file_id,
        current_user.id,
        db
    )

    file_path = resolve_storage_path(
        stored_file.storage_path
    )

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file content is missing"
        )

    return FileResponse(
        path=file_path,
        media_type=stored_file.content_type,
        filename=stored_file.original_filename
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_active_user
    )
):
    stored_file = get_owned_file(
        file_id,
        current_user.id,
        db
    )

    try:
        delete_storage_file(
            stored_file.storage_path
        )
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not remove the stored file"
        ) from error

    db.delete(stored_file)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
