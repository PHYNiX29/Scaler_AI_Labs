import uuid
from datetime import datetime, timezone
from app.extensions import db


class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    form_id = db.Column(
        db.String(36), db.ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True
    )

    def __init__(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4().hex
        super().__init__(**kwargs)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    user_agent = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="in_progress")  # in_progress | completed
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_at = db.Column(db.DateTime, nullable=True)
    time_taken_seconds = db.Column(db.Integer, nullable=True, default=0)

    answers = db.relationship(
        "Answer",
        backref="response",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_answers=True):
        data = {
            "id": self.id,
            "form_id": self.form_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "time_taken_seconds": self.time_taken_seconds,
        }
        if include_answers:
            data["answers"] = {ans.question_id: ans.value for ans in self.answers}
            data["answers_detailed"] = [ans.to_dict() for ans in self.answers]
        return data
