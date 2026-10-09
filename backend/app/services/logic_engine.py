from typing import Any, Dict, List, Optional

SCREENS = ("welcome", "thank_you")


def _choice_id(question: Any, answer: Any) -> Optional[str]:
    """Maps an answer to the choice id that branching rules are keyed on."""
    if question.question_type == "yes_no":
        return "yes" if str(answer).lower() in ("yes", "true") else "no"
    if question.question_type in ("multiple_choice", "dropdown"):
        for choice in (question.properties or {}).get("choices", []):
            if choice.get("label") == answer:
                return choice.get("id")
    return None  # multi-select lists and free-text types never branch


def evaluate_next_step(question: Any, answer: Any, all_questions: List[Any]) -> Dict[str, Any]:
    """
    Decides where a respondent goes after answering `question`.
    A matching rule in question.logic_jumps wins; otherwise the next question in order.
    Returns {"next_question_id": str | None, "is_end": bool}; when is_end is true the
    id (if any) is the ending screen to show.
    """
    ordered = sorted(all_questions, key=lambda q: q.order_index)
    by_id = {q.id: q for q in ordered}

    target = None
    choice_id = _choice_id(question, answer)
    for rule in question.logic_jumps or []:
        if choice_id is not None and rule.get("choice_id") == choice_id:
            target = by_id.get(rule.get("target_question_id"))  # a deleted target falls back to sequential
            break

    if target is None:
        # Next real question in order; after the last one, the first ending screen (if the form has one)
        later = [q for q in ordered[ordered.index(question) + 1:] if q.question_type not in SCREENS]
        endings = [q for q in ordered if q.question_type == "thank_you"]
        target = later[0] if later else (endings[0] if endings else None)

    return {
        "next_question_id": target.id if target else None,
        "is_end": target is None or target.question_type == "thank_you",
    }


def walk_path(all_questions: List[Any], answers: Dict[str, Any]) -> List[Any]:
    """The questions a respondent with these answers actually sees, in order."""
    ordered = sorted(all_questions, key=lambda q: q.order_index)
    by_id = {q.id: q for q in ordered}
    current = next((q for q in ordered if q.question_type not in SCREENS), None)

    path = []
    while current is not None and current not in path:  # `not in path` stops a rule that jumps backwards looping forever
        path.append(current)
        step = evaluate_next_step(current, answers.get(current.id), ordered)
        current = None if step["is_end"] else by_id[step["next_question_id"]]
    return path
