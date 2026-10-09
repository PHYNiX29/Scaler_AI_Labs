import re
from typing import Dict, Any, Tuple, Optional


EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$")


def validate_answer(question: Any, answer_value: Any) -> Tuple[bool, Optional[str]]:
    """
    Validates an answer against question rules and constraints.
    Returns (is_valid, error_message).
    """
    q_type = question.question_type
    props = question.properties or {}
    is_required = question.required

    # Check required condition
    is_empty = (
        answer_value is None
        or answer_value == ""
        or (isinstance(answer_value, (list, dict)) and len(answer_value) == 0)
    )

    if is_required and is_empty:
        return False, f"Question '{question.title or 'Field'}' is required."

    # If not required and answer is empty, it's valid
    if is_empty:
        return True, None

    # Question-specific validations
    if q_type in ("short_text", "long_text"):
        if not isinstance(answer_value, str):
            answer_value = str(answer_value)

        # Max character limit check
        max_length = props.get("max_length")
        if max_length and len(answer_value) > int(max_length):
            return False, f"Answer exceeds maximum length of {max_length} characters."

        # Regex check
        regex_pattern = props.get("regex")
        if regex_pattern:
            try:
                if not re.search(regex_pattern, answer_value):
                    return False, props.get("regex_error_message", "Answer does not match required format.")
            except re.error:
                pass  # Ignore invalid regex from creator

        return True, None

    elif q_type == "email":
        if not isinstance(answer_value, str) or not EMAIL_REGEX.match(answer_value.strip()):
            return False, "Please enter a valid email address."
        return True, None

    elif q_type == "number":
        try:
            num = float(answer_value)
            min_val = props.get("min")
            max_val = props.get("max")
            if min_val is not None and num < float(min_val):
                return False, f"Value must be at least {min_val}."
            if max_val is not None and num > float(max_val):
                return False, f"Value cannot exceed {max_val}."
            return True, None
        except (ValueError, TypeError):
            return False, "Please enter a valid number."

    elif q_type == "rating":
        max_rating = int(props.get("max_rating", 5))
        try:
            val = int(answer_value)
            if val < 0 or val > max_rating:
                return False, f"Rating must be between 0 and {max_rating}."
            return True, None
        except (ValueError, TypeError):
            return False, "Rating must be a valid number."

    elif q_type == "yes_no":
        if isinstance(answer_value, bool):
            return True, None
        if isinstance(answer_value, str) and answer_value.lower() in ("yes", "no", "true", "false"):
            return True, None
        return False, "Answer must be either Yes or No."

    elif q_type == "date":
        if not isinstance(answer_value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", answer_value.strip()):
            return False, "Please enter a valid date in YYYY-MM-DD format."
        return True, None

    elif q_type == "dropdown":
        choices = props.get("choices", [])
        choice_values = [
            c["label"] if isinstance(c, dict) and "label" in c else str(c) for c in choices
        ]
        if answer_value not in choice_values:
            return False, f"Selected option '{answer_value}' is not valid."
        return True, None

    elif q_type == "multiple_choice":
        choices = props.get("choices", [])
        allow_multiple = props.get("allow_multiple", False)
        allow_other = props.get("allow_other", False)
        allow_none = props.get("allow_none", False)

        choice_values = [
            c["label"] if isinstance(c, dict) and "label" in c else str(c) for c in choices
        ]
        if allow_none:
            choice_values.append("None of the above")

        if allow_multiple:
            if not isinstance(answer_value, list):
                return False, "Multiple choice selections must be provided as a list."
            for val in answer_value:
                # If it's an object with { other: text } or matches choices
                if isinstance(val, dict) and "other" in val and allow_other:
                    continue
                if val not in choice_values and not (allow_other and str(val).startswith("Other:")):
                    return False, f"Option '{val}' is not a valid choice."
        else:
            if isinstance(answer_value, dict) and "other" in answer_value and allow_other:
                return True, None
            if answer_value not in choice_values and not (
                allow_other and str(answer_value).startswith("Other:")
            ):
                return False, f"Option '{answer_value}' is not a valid choice."
        return True, None

    elif q_type == "contact":
        if not isinstance(answer_value, dict):
            return False, "Contact information must be an object with field values."

        fields_config = props.get("fields", {})
        default_fields = ["first_name", "last_name", "phone_number", "email", "company"]

        for f_name in default_fields:
            cfg = fields_config.get(f_name, {"enabled": True, "required": False})
            if not cfg.get("enabled", True):
                continue

            field_val = (answer_value.get(f_name) or "").strip()
            # Required check
            if cfg.get("required", False) and not field_val:
                label = f_name.replace("_", " ").title()
                return False, f"{label} is required."

            # Regex / Email format validation
            if field_val:
                custom_regex = cfg.get("regex")
                if custom_regex:
                    try:
                        if not re.search(custom_regex, field_val):
                            label = f_name.replace("_", " ").title()
                            return False, f"{label} does not match required format."
                    except re.error:
                        pass
                elif f_name == "email":
                    if not EMAIL_REGEX.match(field_val):
                        return False, "Please enter a valid email address."

        return True, None

    return True, None
