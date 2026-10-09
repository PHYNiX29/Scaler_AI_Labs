import uuid
from datetime import datetime, timezone
import secrets
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_slug():
    return secrets.token_urlsafe(8)


class Form(Base):
    __tablename__ = "forms"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False, default="Untitled Form")
    description = Column(Text, nullable=True, default="")
    slug = Column(String(100), unique=True, nullable=False, index=True, default=generate_slug)
    status = Column(String(20), nullable=False, default="draft")  # draft | published
    views_count = Column(Integer, default=0)
    submissions_count = Column(Integer, default=0)

    # Global theme / typography / aesthetic customization
    theme_settings = Column(
        JSON,
        nullable=False,
        default=lambda: {
            "font_family": "Inter",
            "text_color": "#262627",
            "background_color": "#FAFAFA",
            "button_color": "#262627",
            "button_text_color": "#FFFFFF",
        },
    )

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    questions = relationship(
        "Question",
        backref="form",
        lazy="select",
        order_by="Question.order_index",
        cascade="all, delete-orphan",
    )
    responses = relationship(
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
            "submissions_count": self.submissions_count,
            "questions": [q.to_dict() for q in sorted(self.questions, key=lambda q: q.order_index)],
        }
