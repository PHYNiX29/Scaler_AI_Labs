import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename

upload_bp = Blueprint("uploads", __name__)


def allowed_file(filename):
    allowed_exts = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts


@upload_bp.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported"}), 400

    original_ext = file.filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{original_ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    media_type = "video" if original_ext in ("mp4", "webm") else "image"
    file_url = f"/uploads/{unique_filename}"

    return (
        jsonify(
            {
                "message": "File uploaded successfully",
                "filename": unique_filename,
                "url": file_url,
                "media_type": media_type,
            }
        ),
        201,
    )


@upload_bp.route("/uploads/<filename>", methods=["GET"])
def get_uploaded_file(filename):
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_dir, secure_filename(filename))
