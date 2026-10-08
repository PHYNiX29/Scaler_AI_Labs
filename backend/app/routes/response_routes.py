import csv
import io
import json
from flask import Blueprint, request, jsonify, Response as FlaskResponse
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.form import Form
from app.models.response import Response
from app.services.stats_service import calculate_form_stats

response_bp = Blueprint("responses", __name__, url_prefix="/api/forms/<form_id>")


@response_bp.route("/responses", methods=["GET"])
@jwt_required(optional=True)
def list_responses(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status = request.args.get("status")

    query = Response.query.filter_by(form_id=form_id)
    if status:
        query = query.filter_by(status=status)

    paginated = query.order_by(Response.started_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "total": paginated.total,
                "pages": paginated.pages,
                "current_page": paginated.page,
                "per_page": per_page,
                "responses": [r.to_dict() for r in paginated.items],
            }
        ),
        200,
    )


@response_bp.route("/responses/<response_id>", methods=["GET"])
@jwt_required(optional=True)
def get_single_response(form_id, response_id):
    response_rec = Response.query.filter_by(id=response_id, form_id=form_id).first()
    if not response_rec:
        return jsonify({"error": "Response not found"}), 404

    # Build question titles map
    q_map = {q.id: q.title for q in response_rec.form.questions}
    detailed_answers = []
    for ans in response_rec.answers:
        detailed_answers.append(
            {
                "question_id": ans.question_id,
                "question_title": q_map.get(ans.question_id, "Unknown Question"),
                "question_type": ans.question_type,
                "value": ans.value,
                "created_at": ans.created_at.isoformat() if ans.created_at else None,
            }
        )

    res_data = response_rec.to_dict()
    res_data["answers_breakdown"] = detailed_answers
    return jsonify({"response": res_data}), 200


@response_bp.route("/responses/<response_id>", methods=["DELETE"])
@jwt_required(optional=True)
def delete_response(form_id, response_id):
    response_rec = Response.query.filter_by(id=response_id, form_id=form_id).first()
    if not response_rec:
        return jsonify({"error": "Response not found"}), 404

    form = db.session.get(Form, form_id)
    if form and form.submissions_count > 0:
        form.submissions_count -= 1

    db.session.delete(response_rec)
    db.session.commit()
    return jsonify({"message": "Response deleted successfully"}), 200


@response_bp.route("/stats", methods=["GET"])
@jwt_required(optional=True)
def get_stats(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    stats = calculate_form_stats(form)
    return jsonify({"stats": stats}), 200


@response_bp.route("/export/csv", methods=["GET"])
@jwt_required(optional=True)
def export_csv(form_id):
    form = db.session.get(Form, form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404

    # Ordered questions (excluding welcome and thank_you)
    questions = [
        q
        for q in sorted(form.questions, key=lambda x: x.order_index)
        if q.question_type not in ("welcome", "thank_you")
    ]

    responses = (
        Response.query.filter_by(form_id=form_id, status="completed")
        .order_by(Response.submitted_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    headers = [
        "Response ID",
        "Submission Date (UTC)",
        "Time Taken (sec)",
        "IP Address",
    ]
    for q in questions:
        headers.append(q.title or f"Question {q.order_index}")
    writer.writerow(headers)

    # Data rows
    for r in responses:
        ans_dict = {a.question_id: a.value for a in r.answers}
        row = [
            r.id,
            r.submitted_at.isoformat() if r.submitted_at else "",
            r.time_taken_seconds or 0,
            r.ip_address or "",
        ]
        for q in questions:
            val = ans_dict.get(q.id, "")
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            row.append(str(val) if val is not None else "")
        writer.writerow(row)

    output.seek(0)
    filename = f"{form.title.replace(' ', '_').lower()}_responses.csv"
    return FlaskResponse(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
