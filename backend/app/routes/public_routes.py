import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.extensions import db, limiter
from app.models.form import Form
from app.models.question import Question
from app.models.response import Response
from app.models.answer import Answer
from app.services.validator import validate_answer
from app.services.logic_engine import evaluate_next_step

public_bp = Blueprint("public", __name__, url_prefix="/api/public")


@public_bp.route("/forms/<slug>", methods=["GET"])
@limiter.limit("120 per minute")
def get_public_form(slug):
    """
    Public endpoint to retrieve form details for filling.
    No authentication required.
    Increments view counter.
    """
    form = Form.query.filter_by(slug=slug).first()
    if not form:
        return jsonify({"error": "Form not found"}), 404

    is_preview = request.args.get("preview", "false").lower() == "true"
    if form.status != "published" and not is_preview:
        return (
            jsonify(
                {
                    "error": "This form is currently private or in draft mode.",
                    "status": form.status,
                }
            ),
            403,
        )

    # Increment view count if not in preview mode
    if not is_preview:
        form.views_count += 1
        db.session.commit()

    form_dict = form.to_public_dict()
    return jsonify({"form": form_dict}), 200


@public_bp.route("/forms/<slug>/start", methods=["POST"])
@limiter.limit("60 per minute")
def start_session(slug):
    """
    Initializes a respondent filling session to track partial fill & start timestamp.
    """
    form = Form.query.filter_by(slug=slug).first()
    if not form:
        return jsonify({"error": "Form not found"}), 404

    session_id = request.json.get("session_id") if request.is_json and request.json else None
    if not session_id:
        session_id = uuid.uuid4().hex

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")[:500]

    # Create in_progress response record
    response_rec = Response(
        form_id=form.id,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(response_rec)
    db.session.commit()

    return (
        jsonify(
            {
                "session_id": session_id,
                "response_id": response_rec.id,
                "started_at": response_rec.started_at.isoformat(),
            }
        ),
        201,
    )


@public_bp.route("/forms/<slug>/validate-step", methods=["POST"])
@limiter.limit("120 per minute")
def validate_step(slug):
    """
    Validates an individual question's answer in real-time as respondent advances.
    Evaluates branching logic to return the next question ID or end screen indicator.
    """
    form = Form.query.filter_by(slug=slug).first()
    if not form:
        return jsonify({"error": "Form not found"}), 404

    data = request.get_json() or {}
    question_id = data.get("question_id")
    answer_value = data.get("answer")

    question = Question.query.filter_by(id=question_id, form_id=form.id).first()
    if not question:
        return jsonify({"error": "Question not found"}), 404

    # Perform validation
    is_valid, err_msg = validate_answer(question, answer_value)
    if not is_valid:
        return jsonify({"valid": False, "error": err_msg}), 400

    # Calculate next step with logic engine
    all_questions = form.questions
    step_result = evaluate_next_step(question, answer_value, all_questions)

    return (
        jsonify(
            {
                "valid": True,
                "next_question_id": step_result["next_question_id"],
                "is_jump": step_result["is_jump"],
                "is_end": step_result["is_end"],
            }
        ),
        200,
    )


@public_bp.route("/forms/<slug>/submit", methods=["POST"])
@limiter.limit("20 per minute")  # Protect against spam / DDoS flooding
def submit_response(slug):
    """
    Finalizes the respondent submission, validates all answers, stores responses,
    and updates submission metrics.
    """
    form = Form.query.filter_by(slug=slug).first()
    if not form:
        return jsonify({"error": "Form not found"}), 404

    if form.status != "published":
        return jsonify({"error": "Cannot submit to an unpublished form"}), 400

    data = request.get_json() or {}
    session_id = data.get("session_id") or uuid.uuid4().hex
    raw_answers = data.get("answers", {})  # Dict of {question_id: value}
    time_taken = data.get("time_taken_seconds", 0)

    # Validate all required answers for the form
    questions_by_id = {q.id: q for q in form.questions}
    errors = {}

    for q_id, q in questions_by_id.items():
        if q.question_type in ("welcome", "thank_you"):
            continue
        val = raw_answers.get(q_id)
        is_valid, err_msg = validate_answer(q, val)
        if not is_valid:
            errors[q_id] = err_msg

    if errors:
        return (
            jsonify(
                {
                    "error": "Validation failed on some fields",
                    "field_errors": errors,
                }
            ),
            400,
        )

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")[:500]

    # Check if an existing in_progress response exists for this session
    response_rec = Response.query.filter_by(
        form_id=form.id, session_id=session_id
    ).first()

    now = datetime.now(timezone.utc)
    if not response_rec:
        response_rec = Response(
            form_id=form.id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            started_at=now,
        )
        db.session.add(response_rec)
        db.session.flush()

    response_rec.status = "completed"
    response_rec.submitted_at = now
    response_rec.time_taken_seconds = int(time_taken) if time_taken else 0

    # Save answers
    for q_id, val in raw_answers.items():
        if q_id not in questions_by_id:
            continue
        q = questions_by_id[q_id]
        answer_rec = Answer(
            response_id=response_rec.id,
            question_id=q_id,
            question_type=q.question_type,
            value=val,
        )
        db.session.add(answer_rec)

    form.submissions_count += 1
    db.session.commit()

    # Find thank you screen if any
    thank_you_screen = next(
        (q for q in form.questions if q.question_type == "thank_you"), None
    )

    return (
        jsonify(
            {
                "message": "Submission received successfully",
                "response_id": response_rec.id,
                "submitted_at": response_rec.submitted_at.isoformat(),
                "thank_you_screen": thank_you_screen.to_dict() if thank_you_screen else None,
            }
        ),
        201,
    )
