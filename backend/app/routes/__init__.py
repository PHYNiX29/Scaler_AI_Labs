from app.routes.auth_routes import auth_bp
from app.routes.form_routes import form_bp
from app.routes.public_routes import public_bp
from app.routes.response_routes import response_bp
from app.routes.upload_routes import upload_bp

__all__ = ["auth_bp", "form_bp", "public_bp", "response_bp", "upload_bp"]
