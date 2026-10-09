from app.models.question import Question
from app.services.validator import validate_answer
from app.services.logic_engine import evaluate_next_step, walk_path


def make_questions():
    mc = Question(
        id="mc", order_index=1, question_type="multiple_choice", title="Framework",
        properties={"choices": [{"id": "c1", "label": "React"}, {"id": "c2", "label": "Vue"}]},
        logic_jumps=[{"choice_id": "c2", "target_question_id": "vue"}, {"choice_id": "c1", "target_question_id": "end_b"}],
    )
    return [
        Question(id="welcome", order_index=0, question_type="welcome", logic_jumps=[]),
        mc,
        Question(id="react", order_index=2, question_type="short_text", required=True, logic_jumps=[]),
        Question(id="vue", order_index=3, question_type="short_text", logic_jumps=[]),
        Question(id="end_a", order_index=4, question_type="thank_you", logic_jumps=[]),
        Question(id="end_b", order_index=5, question_type="thank_you", logic_jumps=[]),
    ]


def test_branching_rules_and_sequential_fallback():
    questions = make_questions()
    mc, react, vue = questions[1], questions[2], questions[3]

    # A rule jumps to its target question
    assert evaluate_next_step(mc, "Vue", questions) == {"next_question_id": "vue", "is_end": False}
    # A rule can target a specific ending
    assert evaluate_next_step(mc, "React", questions) == {"next_question_id": "end_b", "is_end": True}
    # No matching rule (unknown answer, or a multi-select list): next question in order
    assert evaluate_next_step(mc, "Svelte", questions)["next_question_id"] == "react"
    assert evaluate_next_step(mc, ["React", "Vue"], questions)["next_question_id"] == "react"
    # After the last question: the first ending
    assert evaluate_next_step(vue, "x", questions) == {"next_question_id": "end_a", "is_end": True}
    # A rule whose target was deleted falls back to sequential
    mc.logic_jumps = [{"choice_id": "c2", "target_question_id": "gone"}]
    assert evaluate_next_step(mc, "Vue", questions)["next_question_id"] == "react"
    # No endings at all
    assert evaluate_next_step(vue, "x", [mc, react, vue]) == {"next_question_id": None, "is_end": True}


def test_walk_path_follows_answers_and_survives_loops():
    questions = make_questions()
    assert [q.id for q in walk_path(questions, {"mc": "Vue"})] == ["mc", "vue"]
    assert [q.id for q in walk_path(questions, {"mc": "React"})] == ["mc"]
    assert [q.id for q in walk_path(questions, {})] == ["mc", "react", "vue"]

    yes_no = Question(id="yn", order_index=6, question_type="yes_no",
                      logic_jumps=[{"choice_id": "yes", "target_question_id": "mc"}])
    looped = [q for q in questions if q.question_type != "thank_you"] + [yes_no]
    assert [q.id for q in walk_path(looped, {"yn": "Yes"})] == ["mc", "react", "vue", "yn"]


def test_contact_page_subfield_validation():
    """Verifies contact page subfield toggles, regex validation, and required flags."""
    contact_q = Question(
        id="q_contact",
        question_type="contact",
        title="Contact Card",
        required=True,
        properties={
            "fields": {
                "first_name": {"enabled": True, "required": True},
                "last_name": {"enabled": True, "required": False},
                "email": {"enabled": True, "required": True, "regex": "^[^@]+@[^@]+\\.[^@]+$"},
                "phone_number": {"enabled": True, "required": False, "regex": "^\\+?[0-9]{10,15}$"},
                "company": {"enabled": False, "required": False},
            }
        },
    )

    # Missing required first_name
    valid, err = validate_answer(contact_q, {"email": "test@test.com"})
    assert valid is False
    assert "First Name is required" in err

    # Invalid email regex
    valid, err = validate_answer(contact_q, {"first_name": "John", "email": "invalid-email"})
    assert valid is False
    assert "valid email" in err or "does not match" in err

    # Invalid phone regex
    valid, err = validate_answer(
        contact_q, {"first_name": "John", "email": "john@test.com", "phone_number": "abc"}
    )
    assert valid is False
    assert "Phone Number does not match" in err

    # Fully valid contact submission
    valid, err = validate_answer(
        contact_q,
        {"first_name": "John", "email": "john@test.com", "phone_number": "+12345678901"},
    )
    assert valid is True
    assert err is None


def test_rating_page_max_bounds():
    """Verifies rating page restricts answers to 0..max_rating (e.g. 3 or 5)."""
    q_rating_3 = Question(
        id="q_r3",
        question_type="rating",
        title="Quick 3 star rating",
        required=True,
        properties={"max_rating": 3, "icon": "thumbs_up"},
    )

    # Valid values: 0, 1, 2, 3
    assert validate_answer(q_rating_3, 0)[0] is True
    assert validate_answer(q_rating_3, 3)[0] is True

    # Invalid values: 4 or 5 should fail because max is 3
    valid, err = validate_answer(q_rating_3, 4)
    assert valid is False
    assert "between 0 and 3" in err

    # Rating with max 5
    q_rating_5 = Question(
        id="q_r5",
        question_type="rating",
        title="5 star rating",
        required=True,
        properties={"max_rating": 5, "icon": "star"},
    )
    assert validate_answer(q_rating_5, 5)[0] is True
    valid5, err5 = validate_answer(q_rating_5, 6)
    assert valid5 is False
    assert "between 0 and 5" in err5
