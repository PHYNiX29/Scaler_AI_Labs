from typing import List, Dict, Any, Optional


def find_next_question_sequential(current_question: Any, all_questions: List[Any]) -> Optional[str]:
    """Finds the next question in sequential order by order_index."""
    sorted_q = sorted(all_questions, key=lambda q: q.order_index)
    found_current = False
    for q in sorted_q:
        if found_current:
            return q.id
        if q.id == current_question.id:
            found_current = True
    return None


def evaluate_next_step(
    current_question: Any,
    answer_value: Any,
    all_questions: List[Any],
) -> Dict[str, Any]:
    """
    Evaluates where the respondent should go next after answering current_question.
    Returns:
    {
        "next_question_id": str | None,
        "is_jump": bool,
        "is_end": bool
    }
    """
    q_type = current_question.question_type
    props = current_question.properties or {}
    jumps = current_question.logic_jumps or []

    # 1. Yes/No branching
    if q_type == "yes_no":
        branching = props.get("branching") or {}
        val_str = str(answer_value).lower() if answer_value is not None else ""
        is_yes = val_str in ("true", "yes", "1")
        is_no = val_str in ("false", "no", "0")

        target = None
        if is_yes and "yes" in branching and branching["yes"]:
            target = branching["yes"]
        elif is_no and "no" in branching and branching["no"]:
            target = branching["no"]

        if target:
            if target == "end" or target == "thank_you":
                return {"next_question_id": None, "is_jump": True, "is_end": True}
            return {"next_question_id": target, "is_jump": True, "is_end": False}

    # 2. Multiple Choice branching (Only allowed when allow_multiple is False)
    elif q_type == "multiple_choice":
        allow_multiple = props.get("allow_multiple", False)
        if not allow_multiple:
            # Check branching in properties or logic_jumps
            branching_rules = props.get("branching", []) or jumps
            answer_str = str(answer_value).strip() if answer_value is not None else ""

            for rule in branching_rules:
                rule_choice_id = rule.get("choice_id")
                rule_choice_label = rule.get("choice_label")
                target = rule.get("target_question_id") or rule.get("target")

                if not target:
                    continue

                if (rule_choice_id and rule_choice_id == answer_str) or (
                    rule_choice_label and rule_choice_label.lower() == answer_str.lower()
                ):
                    if target in ("end", "thank_you"):
                        return {"next_question_id": None, "is_jump": True, "is_end": True}
                    return {"next_question_id": target, "is_jump": True, "is_end": False}

    # 3. Generic logic jumps for any question type
    if jumps:
        for jump in jumps:
            condition = jump.get("condition", "always")
            val = jump.get("value")
            target = jump.get("target_question_id")

            if not target:
                continue

            match = False
            if condition == "always":
                match = True
            elif condition == "equals" and str(answer_value).lower() == str(val).lower():
                match = True
            elif condition == "not_equals" and str(answer_value).lower() != str(val).lower():
                match = True

            if match:
                if target in ("end", "thank_you"):
                    return {"next_question_id": None, "is_jump": True, "is_end": True}
                return {"next_question_id": target, "is_jump": True, "is_end": False}

    # 4. Default sequential flow
    next_id = find_next_question_sequential(current_question, all_questions)
    return {
        "next_question_id": next_id,
        "is_jump": False,
        "is_end": next_id is None,
    }
