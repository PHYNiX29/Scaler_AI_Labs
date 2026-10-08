import uuid
from datetime import datetime, timezone
from app.extensions import db


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    response_id = db.Column(
        db.String(36), db.ForeignKey("responses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id = db.Column(
        db.String(36), db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type = db.Column(db.String(50), nullable=True)
    value = db.Column(db.JSON, nullable=True)  # Can be string, list of strings, dict (for contact), int/float
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "response_id": self.response_id,
            "question_id": self.question_id,
            "question_type": self.question_type,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
