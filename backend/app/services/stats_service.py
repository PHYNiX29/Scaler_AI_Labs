from typing import Dict, Any, List
from collections import Counter
from app.models.form import Form
from app.models.response import Response
from app.models.answer import Answer


def calculate_form_stats(form: Form) -> Dict[str, Any]:
    """
    Computes summary metrics and per-question analytics for a form.
    """
    responses: List[Response] = form.responses
    total_responses = len(responses)
    completed_responses = [r for r in responses if r.status == "completed"]
    completed_count = len(completed_responses)

    completion_rate = (
        round((completed_count / total_responses) * 100, 1) if total_responses > 0 else 0.0
    )

    times = [r.time_taken_seconds for r in completed_responses if r.time_taken_seconds and r.time_taken_seconds > 0]
    avg_time_seconds = round(sum(times) / len(times)) if times else 0

    # Build answer mapping by question_id
    answers_by_qid: Dict[str, List[Any]] = {}
    for r in responses:
        for ans in r.answers:
            if ans.question_id not in answers_by_qid:
                answers_by_qid[ans.question_id] = []
            if ans.value is not None:
                answers_by_qid[ans.question_id].append(ans.value)

    # Per-question analytics
    question_stats = []
    for q in sorted(form.questions, key=lambda x: x.order_index):
        if q.question_type in ("welcome", "thank_you"):
            continue

        raw_answers = answers_by_qid.get(q.id, [])
        answered_count = len(raw_answers)
        props = q.properties or {}

        q_stat: Dict[str, Any] = {
            "question_id": q.id,
            "title": q.title,
            "question_type": q.question_type,
            "order_index": q.order_index,
            "total_answers": answered_count,
            "dropoff_rate": round(
                ((total_responses - answered_count) / total_responses * 100), 1
            )
            if total_responses > 0
            else 0.0,
        }

        # Analyze by type
        if q.question_type in ("multiple_choice", "dropdown"):
            choices = props.get("choices", [])
            choice_labels = [
                c["label"] if isinstance(c, dict) and "label" in c else str(c) for c in choices
            ]
            if props.get("allow_none"):
                choice_labels.append("None of the above")

            counter = Counter()
            for val in raw_answers:
                if isinstance(val, list):
                    for item in val:
                        counter[str(item)] += 1
                elif isinstance(val, dict) and "other" in val:
                    counter[f"Other: {val['other']}"] += 1
                else:
                    counter[str(val)] += 1

            breakdown = []
            for label in choice_labels:
                count = counter.get(label, 0)
                pct = round((count / answered_count) * 100, 1) if answered_count > 0 else 0.0
                breakdown.append({"choice": label, "count": count, "percentage": pct})

            # Include any custom 'Other' entries
            for key, count in counter.items():
                if key not in choice_labels:
                    pct = round((count / answered_count) * 100, 1) if answered_count > 0 else 0.0
                    breakdown.append({"choice": key, "count": count, "percentage": pct})

            q_stat["breakdown"] = breakdown

        elif q.question_type == "yes_no":
            yes_count = 0
            no_count = 0
            for val in raw_answers:
                v_str = str(val).lower()
                if v_str in ("yes", "true", "1"):
                    yes_count += 1
                elif v_str in ("no", "false", "0"):
                    no_count += 1

            q_stat["breakdown"] = [
                {
                    "choice": "Yes",
                    "count": yes_count,
                    "percentage": round((yes_count / answered_count) * 100, 1) if answered_count > 0 else 0.0,
                },
                {
                    "choice": "No",
                    "count": no_count,
                    "percentage": round((no_count / answered_count) * 100, 1) if answered_count > 0 else 0.0,
                },
            ]

        elif q.question_type == "rating":
            max_rating = int(props.get("max_rating", 5))
            numeric_vals = []
            for val in raw_answers:
                try:
                    numeric_vals.append(int(val))
                except (ValueError, TypeError):
                    pass

            avg_rating = (
                round(sum(numeric_vals) / len(numeric_vals), 2) if numeric_vals else 0.0
            )
            rating_counter = Counter(numeric_vals)
            breakdown = []
            for star in range(1, max_rating + 1):
                count = rating_counter.get(star, 0)
                pct = round((count / len(numeric_vals)) * 100, 1) if numeric_vals else 0.0
                breakdown.append({"rating": star, "count": count, "percentage": pct})

            q_stat["avg_rating"] = avg_rating
            q_stat["max_rating"] = max_rating
            q_stat["breakdown"] = breakdown

        elif q.question_type == "contact":
            subfield_counts = Counter()
            for val in raw_answers:
                if isinstance(val, dict):
                    for subfield, subval in val.items():
                        if subval and str(subval).strip():
                            subfield_counts[subfield] += 1
            q_stat["field_counts"] = dict(subfield_counts)
            q_stat["recent_entries"] = raw_answers[-10:] if raw_answers else []

        else:
            # Text, email, number
            q_stat["recent_entries"] = [str(x) for x in raw_answers[-10:]]

        question_stats.append(q_stat)

    return {
        "form_id": form.id,
        "form_title": form.title,
        "views_count": form.views_count,
        "total_responses": total_responses,
        "completed_count": completed_count,
        "completion_rate": completion_rate,
        "avg_time_seconds": avg_time_seconds,
        "questions": question_stats,
    }
