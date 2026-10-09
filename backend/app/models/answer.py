import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from app.database import Base


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    response_id = Column(
        String(36), ForeignKey("responses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id = Column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type = Column(String(50), nullable=True)
    value = Column(JSON, nullable=True)  # Can be string, list of strings, dict (for contact), int/float
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "response_id": self.response_id,
            "question_id": self.question_id,
            "question_type": self.question_type,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
