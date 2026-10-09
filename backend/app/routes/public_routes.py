"""Respondent-facing endpoints. No authentication: anyone with the link can fill a published form."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Answer, Form, Response
from app.schemas import StartBody, SubmitBody, ValidateStepBody
from app.services.logic_engine import evaluate_next_step, walk_path
from app.services.validator import validate_answer

router = APIRouter(prefix="/api/public/forms", tags=["public"])


def get_published_form(slug: str, db: Session = Depends(get_db)) -> Form:
    form = db.query(Form).filter_by(slug=slug, status="published").first()
    if not form:
        # Drafts answer exactly like missing forms so unpublished content never leaks
        raise HTTPException(404, "This form does not exist or is not published")
    return form


@router.get("/{slug}")
def get_public_form(form: Form = Depends(get_published_form), db: Session = Depends(get_db)):
    form.views_count += 1
    db.commit()
    return {"form": form.to_public_dict()}


@router.post("/{slug}/start", status_code=201)
def start_session(
    body: StartBody, request: Request, form: Form = Depends(get_published_form), db: Session = Depends(get_db)
):
    """Records an in-progress response so abandoned fills count towards the completion rate."""
    response = Response(
        form_id=form.id,
        session_id=body.session_id or uuid.uuid4().hex,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(response)
    db.commit()
    return {"session_id": response.session_id, "response_id": response.id}


@router.post("/{slug}/validate-step")
def validate_step(body: ValidateStepBody, form: Form = Depends(get_published_form)):
    """Validates one answer and applies branching to say which question comes next."""
    question = next((q for q in form.questions if q.id == body.question_id), None)
    if not question:
        raise HTTPException(404, "Question not found")

    is_valid, error = validate_answer(question, body.answer)
    if not is_valid:
        return {"valid": False, "error": error}
    return {"valid": True, **evaluate_next_step(question, body.answer, form.questions)}


@router.post("/{slug}/submit", status_code=201)
def submit_response(
    body: SubmitBody, request: Request, form: Form = Depends(get_published_form), db: Session = Depends(get_db)
):
    # Never trust the client's route through the form: re-walk the branching from the answers and
    # validate only the questions on that path. Questions skipped by a jump may be required but unanswered.
    path = walk_path(form.questions, body.answers)
    errors = {}
    for question in path:
        is_valid, error = validate_answer(question, body.answers.get(question.id))
        if not is_valid:
            errors[question.id] = error
    if errors:
        raise HTTPException(422, {"message": "Some answers are invalid", "field_errors": errors})

    response = None
    if body.session_id:
        response = db.query(Response).filter_by(form_id=form.id, session_id=body.session_id, status="in_progress").first()
    now = datetime.now(timezone.utc)
    if not response:
        response = Response(
            form_id=form.id,
            session_id=body.session_id or uuid.uuid4().hex,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500],
            started_at=now,
        )
        db.add(response)
        db.flush()

    response.status = "completed"
    response.submitted_at = now
    response.time_taken_seconds = body.time_taken_seconds
    for question in path:
        value = body.answers.get(question.id)
        if value not in (None, "", [], {}):
            db.add(Answer(response_id=response.id, question_id=question.id, question_type=question.question_type, value=value))

    form.submissions_count += 1
    db.commit()
    return {"message": "Response submitted", "response_id": response.id}
