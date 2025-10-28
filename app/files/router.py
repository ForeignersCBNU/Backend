from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from pathlib import Path
import uuid
from sqlalchemy import select

from app.deps import get_current_user
from app.db.session import SessionLocal
from app.db.models import UploadedFile, User
from app.files.parser import parse_and_store

router = APIRouter(prefix="/files", tags=["files"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED = {"pdf", "docx", "txt"}
MAX_UPLOAD_MB = 10

@router.post("/upload")
async def upload(
    bg: BackgroundTasks,                                 # non-default first
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    # basic validation
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
    data = await file.read()
    size_mb = len(data) / 1024 / 1024
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(status_code=413, detail="File too large")
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # store on disk
    name = f"{uuid.uuid4()}.{ext or 'bin'}"
    path = UPLOAD_DIR / name
    path.write_bytes(data)

    # DB record
    async with SessionLocal() as s:
        rec = UploadedFile(
            user_id=user.id,
            filename=file.filename,
            file_path=str(path),
            file_type=ext or "bin",
            ai_status="pending",
            summary=None,
        )
        s.add(rec)
        await s.commit()
        await s.refresh(rec)

    # background parse
    bg.add_task(parse_and_store, rec.id)

    return {
        "file_id": rec.id,
        "filename": rec.filename,
        "stored_as": rec.file_path,
        "ai_status": rec.ai_status,
    }

@router.get("/{file_id}/summary")
async def file_summary(file_id: str, user: User = Depends(get_current_user)):
    async with SessionLocal() as s:
        row = (
            await s.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        ).scalar_one_or_none()
        if not row or (row.user_id and row.user_id != user.id):
            raise HTTPException(status_code=404, detail="file not found")
        return {"file_id": row.id, "ai_status": row.ai_status, "summary": row.summary}
