import csv
import io
import json
import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response as HttpResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Form, Response
from app.routes.form_routes import get_owned_form
from app.services.stats_service import calculate_form_stats

router = APIRouter(prefix="/api/forms/{form_id}", tags=["responses"])


def get_owned_response(response_id: str, form: Form = Depends(get_owned_form), db: Session = Depends(get_db)) -> Response:
    response = db.query(Response).filter_by(id=response_id, form_id=form.id).first()
    if not response:
        raise HTTPException(404, "Response not found")
    return response


@router.get("/responses")
def list_responses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[Literal["in_progress", "completed"]] = None,
    form: Form = Depends(get_owned_form),
    db: Session = Depends(get_db),
):
    query = db.query(Response).filter_by(form_id=form.id)
    if status:
        query = query.filter_by(status=status)
    total = query.count()
    rows = query.order_by(Response.started_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "pages": -(-total // per_page),  # ceiling division
        "current_page": page,
        "per_page": per_page,
        "responses": [r.to_dict() for r in rows],
    }


@router.get("/responses/{response_id}")
def get_response(response: Response = Depends(get_owned_response), form: Form = Depends(get_owned_form)):
    """One submission in full, with answers listed in form order alongside their question titles."""
    values = {a.question_id: a.value for a in response.answers}
    data = response.to_dict()
    data["answers_breakdown"] = [
        {"question_id": q.id, "question_title": q.title, "question_type": q.question_type, "value": values[q.id]}
        for q in form.questions
        if q.id in values
    ]
    return {"response": data}


@router.delete("/responses/{response_id}")
def delete_response(
    response: Response = Depends(get_owned_response), form: Form = Depends(get_owned_form), db: Session = Depends(get_db)
):
    if response.status == "completed" and form.submissions_count > 0:
        form.submissions_count -= 1
    db.delete(response)
    db.commit()
    return {"message": "Response deleted"}


@router.get("/stats")
def get_stats(form: Form = Depends(get_owned_form)):
    return {"stats": calculate_form_stats(form)}


def _csv_cell(value) -> str:
    if value is None:
        return ""
    text = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
    # Respondent text starting with = + - @ would run as a formula when the file is opened in Excel
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@router.get("/export/csv")
def export_csv(form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    questions = [q for q in form.questions if q.question_type not in ("welcome", "thank_you")]
    responses = (
        db.query(Response).filter_by(form_id=form.id, status="completed").order_by(Response.submitted_at.desc()).all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Response ID", "Submitted at (UTC)", "Time taken (sec)"] + [_csv_cell(q.title) for q in questions])
    for r in responses:
        values = {a.question_id: a.value for a in r.answers}
        writer.writerow(
            [r.id, r.submitted_at.isoformat() if r.submitted_at else "", r.time_taken_seconds or 0]
            + [_csv_cell(values.get(q.id)) for q in questions]
        )

    filename = re.sub(r"\W+", "_", form.title).strip("_").lower() or "form"
    return HttpResponse(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}_responses.csv"'},
    )
