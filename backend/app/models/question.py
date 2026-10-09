import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    form_id = Column(
        String(36), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index = Column(Integer, nullable=False, default=0, index=True)
    question_type = Column(String(50), nullable=False)
    # Types: welcome, dropdown, multiple_choice, contact, rating, yes_no, short_text, long_text, email, number, date, thank_you

    title = Column(String(500), nullable=False, default="")
    description = Column(Text, nullable=True, default="")
    required = Column(Boolean, default=False)

    # Question-specific properties (choices, fields, badges, icons, limits, etc.)
    properties = Column(JSON, nullable=False, default=dict)

    # Media attachments (image or video) with desktop & mobile orientations
    # desktop_orientation: "split_left" | "split_right" | "float_left" | "float_right" | "wallpaper"
    # mobile_orientation: "stack" | "wallpaper"
    media = Column(
        JSON,
        nullable=False,
        default=lambda: {
            "media_type": None,  # "image" | "video" | None
            "media_url": None,
            "desktop_orientation": "float_right",
            "mobile_orientation": "stack",
            "alt_text": "",
        },
    )

    # Branching rules: [{"choice_id": <choice id | "yes" | "no">, "target_question_id": <question or ending id>}]
    # No matching rule means "continue to the next question in order".
    logic_jumps = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "form_id": self.form_id,
            "order_index": self.order_index,
            "question_type": self.question_type,
            "title": self.title,
            "description": self.description or "",
            "required": self.required,
            "properties": self.properties or {},
            "media": self.media
            or {
                "media_type": None,
                "media_url": None,
                "desktop_orientation": "float_right",
                "mobile_orientation": "stack",
                "alt_text": "",
            },
            "logic_jumps": self.logic_jumps or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
