import copy
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_current_user, get_db
from app.models import Form, Question, User
from app.schemas import FormCreate, FormUpdate, PublishBody, QuestionCreate, QuestionUpdate, ReorderBody

router = APIRouter(prefix="/api/forms", tags=["forms"])


def get_owned_form(form_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Form:
    form = db.query(Form).filter_by(id=form_id, user_id=user.id).first()
    if not form:
        raise HTTPException(404, "Form not found")
    return form


def get_owned_question(question_id: str, form: Form = Depends(get_owned_form)) -> Question:
    question = next((q for q in form.questions if q.id == question_id), None)
    if not question:
        raise HTTPException(404, "Question not found")
    return question


def starter_questions(form: Form) -> list[Question]:
    return [
        Question(
            form_id=form.id,
            order_index=0,
            question_type="welcome",
            title=form.title,
            properties={"button_text": "Start", "stat_badge_type": "time_to_complete", "estimated_time_minutes": 1},
        ),
        Question(
            form_id=form.id,
            order_index=1,
            question_type="multiple_choice",
            title="How did you hear about us?",
            properties={
                "choices": [
                    {"id": uuid.uuid4().hex[:8], "label": "Social media"},
                    {"id": uuid.uuid4().hex[:8], "label": "A friend or colleague"},
                    {"id": uuid.uuid4().hex[:8], "label": "Search engine"},
                ],
            },
        ),
        Question(
            form_id=form.id,
            order_index=2,
            question_type="thank_you",
            title="Thank you for your response!",
            properties={"button_text": "Create a typeform"},
        ),
    ]


# ---------------- Forms ----------------


@router.get("")
def list_forms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    forms = db.query(Form).filter_by(user_id=user.id).order_by(Form.updated_at.desc()).all()
    return {"forms": [f.to_dict(include_questions=False) for f in forms]}


@router.post("", status_code=201)
def create_form(body: FormCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    form = Form(user_id=user.id, title=body.title.strip() or "My new form", description=body.description)
    db.add(form)
    db.flush()
    if body.include_starter:
        db.add_all(starter_questions(form))
    db.commit()
    return {"form": form.to_dict()}


@router.get("/{form_id}")
def get_form(form: Form = Depends(get_owned_form)):
    return {"form": form.to_dict()}


@router.put("/{form_id}")
def update_form(body: FormUpdate, form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(form, field, value)
    db.commit()
    return {"form": form.to_dict()}


@router.delete("/{form_id}")
def delete_form(form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    db.delete(form)
    db.commit()
    return {"message": "Form deleted"}


@router.post("/{form_id}/duplicate", status_code=201)
def duplicate_form(form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    """Copies a form and its questions (not its responses) as a new draft."""
    new_form = Form(
        user_id=form.user_id,
        title=f"{form.title} (Copy)",
        description=form.description,
        theme_settings=copy.deepcopy(form.theme_settings),
    )
    db.add(new_form)
    db.flush()

    # Branching rules point at question ids, so they must be re-pointed at the copies
    id_map = {q.id: uuid.uuid4().hex for q in form.questions}
    for q in form.questions:
        db.add(
            Question(
                id=id_map[q.id],
                form_id=new_form.id,
                order_index=q.order_index,
                question_type=q.question_type,
                title=q.title,
                description=q.description,
                required=q.required,
                properties=copy.deepcopy(q.properties),
                media=copy.deepcopy(q.media),
                logic_jumps=[
                    {**rule, "target_question_id": id_map.get(rule.get("target_question_id"))}
                    for rule in q.logic_jumps or []
                ],
            )
        )
    db.commit()
    return {"form": new_form.to_dict()}


@router.post("/{form_id}/publish")
def set_publish_status(body: PublishBody, form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    form.status = body.status or ("draft" if form.status == "published" else "published")
    db.commit()
    return {"status": form.status, "slug": form.slug}


# ---------------- Questions ----------------


@router.post("/{form_id}/questions", status_code=201)
def add_question(body: QuestionCreate, form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    question = Question(
        form_id=form.id,
        order_index=max((q.order_index for q in form.questions), default=-1) + 1,
        **body.model_dump(exclude_none=True),
    )
    db.add(question)
    db.commit()
    return {"question": question.to_dict()}


# Declared before /{question_id} so "reorder" is not captured as a question id
@router.put("/{form_id}/questions/reorder")
def reorder_questions(body: ReorderBody, form: Form = Depends(get_owned_form), db: Session = Depends(get_db)):
    if sorted(body.question_ids) != sorted(q.id for q in form.questions):
        raise HTTPException(422, "question_ids must list every question of this form exactly once")
    position = {question_id: index for index, question_id in enumerate(body.question_ids)}
    for q in form.questions:
        q.order_index = position[q.id]
    db.commit()
    db.refresh(form)
    return {"questions": [q.to_dict() for q in form.questions]}


@router.put("/{form_id}/questions/{question_id}")
def update_question(body: QuestionUpdate, question: Question = Depends(get_owned_question), db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    db.commit()
    return {"question": question.to_dict()}


@router.delete("/{form_id}/questions/{question_id}")
def delete_question(
    question: Question = Depends(get_owned_question),
    form: Form = Depends(get_owned_form),
    db: Session = Depends(get_db),
):
    form.questions.remove(question)  # delete-orphan cascade removes the row
    for index, q in enumerate(form.questions):
        q.order_index = index
    db.commit()
    return {"message": "Question deleted"}
