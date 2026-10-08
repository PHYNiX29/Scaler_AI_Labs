import uuid
from datetime import datetime, timezone
from app.extensions import db


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    form_id = db.Column(
        db.String(36), db.ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index = db.Column(db.Integer, nullable=False, default=0, index=True)
    question_type = db.Column(db.String(50), nullable=False)
    # Types: welcome, dropdown, multiple_choice, contact, rating, yes_no, short_text, long_text, email, number, date, thank_you

    title = db.Column(db.String(500), nullable=False, default="")
    description = db.Column(db.Text, nullable=True, default="")
    required = db.Column(db.Boolean, default=False)

    # Question-specific properties (choices, fields, badges, icons, limits, etc.)
    properties = db.Column(db.JSON, nullable=False, default=dict)

    # Media attachments (image or video) with desktop & mobile orientations
    # desktop_orientation: "left_split_1_3" | "right_split_1_3" | "left_box" | "right_box" | "background"
    # mobile_orientation: "top" | "background"
    media = db.Column(
        db.JSON,
        nullable=False,
        default=lambda: {
            "media_type": None,  # "image" | "video" | None
            "media_url": None,
            "desktop_orientation": "right_split_1_3",
            "mobile_orientation": "top",
            "alt_text": "",
        },
    )

    # Logic jumps / branching configuration
    # Can contain direct target for next question or conditional branching rules
    logic_jumps = db.Column(db.JSON, nullable=False, default=list)

    # Per-question styling override (text color, bold, italic)
    styling = db.Column(
        db.JSON,
        nullable=False,
        default=lambda: {
            "text_color": None,
            "is_bold": False,
            "is_italic": False,
        },
    )

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
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
                "desktop_orientation": "right_split_1_3",
                "mobile_orientation": "top",
                "alt_text": "",
            },
            "logic_jumps": self.logic_jumps or [],
            "styling": self.styling or {"text_color": None, "is_bold": False, "is_italic": False},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
