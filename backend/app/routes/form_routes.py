import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.form import Form, generate_slug
from app.models.question import Question

form_bp = Blueprint("forms", __name__, url_prefix="/api/forms")


@form_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def get_forms():
    user_id = get_jwt_identity()
    query = Form.query
    if user_id:
        query = query.filter((Form.user_id == user_id) | (Form.user_id.is_(None)))
    forms = query.order_by(Form.updated_at.desc()).all()
    return jsonify({"forms": [f.to_dict(include_questions=False) for f in forms]}), 200


@form_bp.route("", methods=["POST"])
@jwt_required(optional=True)
def create_form():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    title = data.get("title", "My New Form").strip()
    description = data.get("description", "")
    theme_settings = data.get("theme_settings")
    settings = data.get("settings")

    form = Form(
        user_id=user_id,
        title=title or "My New Form",
        description=description,
        status="draft",
        slug=generate_slug(),
    )
    if theme_settings:
        form.theme_settings = theme_settings
    if settings:
        form.settings = settings

    db.session.add(form)
    db.session.flush()

    # Optional: populate with default starter template if requested
    include_starter = data.get("include_starter", True)
    if include_starter:
        # Default Welcome Page
        welcome_q = Question(
            form_id=form.id,
            order_index=0,
            question_type="welcome",
            title=f"Welcome to {form.title}",
            description="Please take a couple of minutes to fill out this form.",
            required=False,
            properties={
                "button_text": "Start",
                "stat_badge_type": "time_to_complete",  # "submissions" | "time_to_complete" | "none"
                "estimated_time_minutes": 2,
            },
            media={
                "media_type": None,
                "media_url": None,
                "desktop_orientation": "right_split_1_3",
                "mobile_orientation": "top",
                "alt_text": "",
            },
        )

        # Default Multiple Choice Page
        mc_q = Question(
            form_id=form.id,
            order_index=1,
            question_type="multiple_choice",
            title="How did you hear about us?",
            description="Select the option that best fits your experience.",
            required=True,
            properties={
                "choices": [
                    {"id": "c1", "label": "Social Media"},
                    {"id": "c2", "label": "Friend or Colleague"},
                    {"id": "c3", "label": "Search Engine (Google/Bing)"},
                ],
                "allow_multiple": False,
                "allow_other": True,
                "allow_none": False,
                "branching": [],
            },
            media={
                "media_type": None,
                "media_url": None,
                "desktop_orientation": "left_split_1_3",
                "mobile_orientation": "top",
                "alt_text": "",
            },
        )

        # Default Thank You Page
        thank_you_q = Question(
            form_id=form.id,
            order_index=2,
            question_type="thank_you",
            title="Thank you for your response!",
            description="We appreciate your valuable feedback.",
            required=False,
            properties={
                "button_text": "Submit Another Response",
                "button_url": "",
                "social_links": {
                    "twitter": "",
                    "linkedin": "",
                    "github": "",
                },
                "show_reload_button": True,
            },
            media={
                "media_type": None,
                "media_url": None,
                "desktop_orientation": "background",
                "mobile_orientation": "background",
                "alt_text": "",
            },
        )
        db.session.add_all([welcome_q, mc_q, thank_you_q])

    db.session.commit()
    return jsonify({"message": "Form created successfully", "form": form.to_dict()}), 201


@form_bp.route("/<form_id>", methods=["GET"])
@jwt_required(optional=True)
def get_form(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404
    return jsonify({"form": form.to_dict()}), 200


@form_bp.route("/<form_id>", methods=["PUT"])
@jwt_required(optional=True)
def update_form(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    data = request.get_json(silent=True) or {}
    if "title" in data:
        form.title = data["title"]
    if "description" in data:
        form.description = data["description"]
    if "status" in data:
        form.status = data["status"]
    if "theme_settings" in data:
        form.theme_settings = data["theme_settings"]
    if "settings" in data:
        form.settings = data["settings"]

    db.session.commit()
    return jsonify({"message": "Form updated successfully", "form": form.to_dict()}), 200


@form_bp.route("/<form_id>", methods=["DELETE"])
@jwt_required(optional=True)
def delete_form(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    db.session.delete(form)
    db.session.commit()
    return jsonify({"message": "Form deleted successfully"}), 200


@form_bp.route("/<form_id>/duplicate", methods=["POST"])
@jwt_required(optional=True)
def duplicate_form(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    user_id = get_jwt_identity() or form.user_id
    new_form = Form(
        user_id=user_id,
        title=f"{form.title} (Copy)",
        description=form.description,
        slug=generate_slug(),
        status="draft",
        theme_settings=dict(form.theme_settings or {}),
        settings=dict(form.settings or {}),
    )
    db.session.add(new_form)
    db.session.flush()

    # Map old question IDs to new question IDs for logic jumps
    id_map = {}
    new_questions = []
    for q in sorted(form.questions, key=lambda x: x.order_index):
        new_q_id = uuid.uuid4().hex
        id_map[q.id] = new_q_id
        new_q = Question(
            id=new_q_id,
            form_id=new_form.id,
            order_index=q.order_index,
            question_type=q.question_type,
            title=q.title,
            description=q.description,
            required=q.required,
            properties=dict(q.properties or {}),
            media=dict(q.media or {}),
            styling=dict(q.styling or {}),
            logic_jumps=list(q.logic_jumps or []),
        )
        new_questions.append(new_q)

    # Remap logic jumps and branching targets
    for nq in new_questions:
        if nq.logic_jumps:
            remapped_jumps = []
            for j in nq.logic_jumps:
                old_tgt = j.get("target_question_id")
                j_copy = dict(j)
                if old_tgt in id_map:
                    j_copy["target_question_id"] = id_map[old_tgt]
                remapped_jumps.append(j_copy)
            nq.logic_jumps = remapped_jumps

        # Remap branching in properties (yes_no, multiple_choice)
        if "branching" in nq.properties:
            b = nq.properties["branching"]
            if isinstance(b, dict):
                remapped_b = {}
                for k, v in b.items():
                    remapped_b[k] = id_map.get(v, v)
                nq.properties["branching"] = remapped_b
            elif isinstance(b, list):
                remapped_b = []
                for rule in b:
                    rc = dict(rule)
                    tgt = rc.get("target_question_id")
                    if tgt in id_map:
                        rc["target_question_id"] = id_map[tgt]
                    remapped_b.append(rc)
                nq.properties["branching"] = remapped_b

        db.session.add(nq)

    db.session.commit()
    return jsonify({"message": "Form duplicated successfully", "form": new_form.to_dict()}), 201


@form_bp.route("/<form_id>/publish", methods=["POST"])
@jwt_required(optional=True)
def toggle_publish(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    data = request.get_json(silent=True) or {}
    publish_status = data.get("status")
    if publish_status in ("published", "draft"):
        form.status = publish_status
    else:
        form.status = "published" if form.status == "draft" else "draft"

    db.session.commit()
    return (
        jsonify(
            {
                "message": f"Form is now {form.status}",
                "status": form.status,
                "slug": form.slug,
                "shareable_url": f"/to/{form.slug}",
            }
        ),
        200,
    )


# ---------------- Question Endpoints ----------------


@form_bp.route("/<form_id>/questions", methods=["POST"])
@jwt_required(optional=True)
def add_question(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    data = request.get_json(silent=True) or {}
    q_type = data.get("question_type", "short_text")
    title = data.get("title", f"New {q_type.replace('_', ' ').title()}")
    description = data.get("description", "")
    required = data.get("required", False)
    properties = data.get("properties", {})
    media = data.get("media", {
        "media_type": None,
        "media_url": None,
        "desktop_orientation": "right_split_1_3",
        "mobile_orientation": "top",
        "alt_text": "",
    })
    styling = data.get("styling", {"text_color": None, "is_bold": False, "is_italic": False})
    logic_jumps = data.get("logic_jumps", [])

    # Compute order_index
    max_order = max([q.order_index for q in form.questions], default=-1)
    insert_at = data.get("order_index")
    order_index = insert_at if insert_at is not None else max_order + 1

    question = Question(
        form_id=form.id,
        order_index=order_index,
        question_type=q_type,
        title=title,
        description=description,
        required=required,
        properties=properties,
        media=media,
        styling=styling,
        logic_jumps=logic_jumps,
    )
    db.session.add(question)
    db.session.commit()

    return jsonify({"message": "Question added", "question": question.to_dict()}), 201


@form_bp.route("/<form_id>/questions/<question_id>", methods=["PUT"])
@jwt_required(optional=True)
def update_question(form_id, question_id):
    question = Question.query.filter_by(id=question_id, form_id=form_id).first()
    if not question:
        return jsonify({"error": "Question not found"}), 404

    data = request.get_json() or {}
    if "title" in data:
        question.title = data["title"]
    if "description" in data:
        question.description = data["description"]
    if "question_type" in data:
        question.question_type = data["question_type"]
    if "required" in data:
        question.required = bool(data["required"])
    if "properties" in data:
        question.properties = data["properties"]
    if "media" in data:
        question.media = data["media"]
    if "styling" in data:
        question.styling = data["styling"]
    if "logic_jumps" in data:
        question.logic_jumps = data["logic_jumps"]
    if "order_index" in data:
        question.order_index = int(data["order_index"])

    db.session.commit()
    return jsonify({"message": "Question updated", "question": question.to_dict()}), 200


@form_bp.route("/<form_id>/questions/<question_id>", methods=["DELETE"])
@jwt_required(optional=True)
def delete_question(form_id, question_id):
    question = Question.query.filter_by(id=question_id, form_id=form_id).first()
    if not question:
        return jsonify({"error": "Question not found"}), 404

    db.session.delete(question)
    db.session.commit()

    # Re-normalize order indexes
    remaining_q = Question.query.filter_by(form_id=form_id).order_by(Question.order_index).all()
    for idx, q in enumerate(remaining_q):
        q.order_index = idx
    db.session.commit()

    return jsonify({"message": "Question deleted successfully"}), 200


@form_bp.route("/<form_id>/questions/reorder", methods=["PUT"])
@jwt_required(optional=True)
def reorder_questions(form_id):
    data = request.get_json() or {}
    question_ids = data.get("question_ids", [])

    if not isinstance(question_ids, list):
        return jsonify({"error": "question_ids must be a list of IDs"}), 400

    questions = Question.query.filter_by(form_id=form_id).all()
    q_map = {q.id: q for q in questions}

    for idx, q_id in enumerate(question_ids):
        if q_id in q_map:
            q_map[q_id].order_index = idx

    db.session.commit()
    updated_questions = (
        Question.query.filter_by(form_id=form_id).order_by(Question.order_index).all()
    )
    return (
        jsonify(
            {
                "message": "Questions reordered successfully",
                "questions": [q.to_dict() for q in updated_questions],
            }
        ),
        200,
    )
