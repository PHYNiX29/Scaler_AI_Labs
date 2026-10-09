import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES, UPLOAD_DIR

router = APIRouter(tags=["uploads"])


@router.post("/api/upload", status_code=201)
def upload_media(file: UploadFile):
    """Stores an image/video for a question. Files are served back from /uploads/<name>."""
    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(422, "File type not supported")

    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 10 MB")

    # The stored name is generated, never taken from the client, so it cannot escape UPLOAD_DIR
    filename = f"{uuid.uuid4().hex}.{extension}"
    (UPLOAD_DIR / filename).write_bytes(content)
    return {
        "filename": filename,
        "url": f"/uploads/{filename}",
        "media_type": "video" if extension in ("mp4", "webm") else "image",
    }
