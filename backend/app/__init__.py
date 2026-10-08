import os
from flask import Flask, jsonify
from app.config import config
from app.extensions import db, jwt, cors, limiter, migrate
from app.routes.auth_routes import auth_bp
from app.routes.form_routes import form_bp
from app.routes.public_routes import public_bp
from app.routes.response_routes import response_bp
from app.routes.upload_routes import upload_bp


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config["default"]))

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    limiter.init_app(app)
    migrate.init_app(app, db)

    # Ensure uploads folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(form_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(response_bp)
    app.register_blueprint(upload_bp)

    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "Typeform Clone Backend"}), 200

    # Custom Error Handlers
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded. Please wait before trying again.",
                    "description": str(e.description),
                }
            ),
            429,
        )

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    # Initialize database tables
    with app.app_context():
        db.create_all()

    return app
