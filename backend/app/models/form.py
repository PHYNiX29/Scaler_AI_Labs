import uuid
from datetime import datetime, timezone
import secrets
from app.extensions import db


def generate_slug():
    return secrets.token_urlsafe(8)


class Form(db.Model):
    __tablename__ = "forms"

    id = db.Column(db.String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(255), nullable=False, default="Untitled Form")
    description = db.Column(db.Text, nullable=True, default="")
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True, default=generate_slug)
    status = db.Column(db.String(20), nullable=False, default="draft")  # draft | published
    views_count = db.Column(db.Integer, default=0)
    submissions_count = db.Column(db.Integer, default=0)

    # Global theme / typography / aesthetic customization
    theme_settings = db.Column(
        db.JSON,
        nullable=False,
        default=lambda: {
            "font_family": "Inter",
            "text_color": "#262627",
            "background_color": "#FFFFFF",
            "button_color": "#0445AF",
            "button_text_color": "#FFFFFF",
            "is_bold": False,
            "is_italic": False,
            "progress_bar": "percentage",
        },
    )

    # General form settings
    settings = db.Column(
        db.JSON,
        nullable=False,
        default=lambda: {
            "show_progress_bar": True,
            "show_question_numbers": True,
            "letters_on_answers": True,
        },
    )

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    questions = db.relationship(
        "Question",
        backref="form",
        lazy="select",
        order_by="Question.order_index",
        cascade="all, delete-orphan",
    )
    responses = db.relationship(
        "Response",
        backref="form",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_questions=True):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "slug": self.slug,
            "status": self.status,
            "views_count": self.views_count,
            "submissions_count": self.submissions_count,
            "theme_settings": self.theme_settings or {},
            "settings": self.settings or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "questions_count": len(self.questions) if self.questions else 0,
        }
        if include_questions:
            data["questions"] = [q.to_dict() for q in sorted(self.questions, key=lambda q: q.order_index)]
        return data

    def to_public_dict(self):
        """Format for public respondents - excludes private creator metadata"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "slug": self.slug,
            "status": self.status,
            "theme_settings": self.theme_settings or {},
            "settings": self.settings or {},
            "submissions_count": self.submissions_count,
            "questions": [q.to_dict() for q in sorted(self.questions, key=lambda q: q.order_index)],
        }
