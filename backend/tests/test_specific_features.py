import pytest
from app.models.question import Question
from app.services.validator import validate_answer
from app.services.logic_engine import evaluate_next_step


def test_welcome_page_stat_badges(client, auth_headers):
    """Verifies welcome screen supports either 'submissions' or 'time_to_complete', only one."""
    create_res = client.post(
        "/api/forms",
        json={"title": "Welcome Badge Test", "include_starter": False},
        headers=auth_headers,
    )
    form_id = create_res.get_json()["form"]["id"]

    # Welcome with time_to_complete
    q_res1 = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "welcome",
            "title": "Welcome 1",
            "properties": {
                "button_text": "Start Now",
                "stat_badge_type": "time_to_complete",
                "estimated_time_minutes": 3,
            },
        },
        headers=auth_headers,
    )
    assert q_res1.status_code == 201
    props1 = q_res1.get_json()["question"]["properties"]
    assert props1["stat_badge_type"] == "time_to_complete"
    assert props1["estimated_time_minutes"] == 3

    # Update to submissions badge
    q_id = q_res1.get_json()["question"]["id"]
    q_res2 = client.put(
        f"/api/forms/{form_id}/questions/{q_id}",
        json={
            "properties": {
                "button_text": "Let's Go",
                "stat_badge_type": "submissions",
            }
        },
        headers=auth_headers,
    )
    assert q_res2.status_code == 200
    props2 = q_res2.get_json()["question"]["properties"]
    assert props2["stat_badge_type"] == "submissions"


def test_media_desktop_and_mobile_orientations(client, auth_headers):
    """Verifies all 5 desktop orientations and 2 mobile orientations can be saved & retrieved."""
    desktop_orientations = [
        "left_split_1_3",
        "right_split_1_3",
        "left_box",
        "right_box",
        "background",
    ]
    mobile_orientations = ["top", "background"]

    create_res = client.post(
        "/api/forms",
        json={"title": "Media Orientation Test", "include_starter": False},
        headers=auth_headers,
    )
    form_id = create_res.get_json()["form"]["id"]

    for d_orient in desktop_orientations:
        for m_orient in mobile_orientations:
            q_res = client.post(
                f"/api/forms/{form_id}/questions",
                json={
                    "question_type": "dropdown",
                    "title": f"Media test {d_orient} {m_orient}",
                    "media": {
                        "media_type": "image",
                        "media_url": "https://example.com/asset.png",
                        "desktop_orientation": d_orient,
                        "mobile_orientation": m_orient,
                        "alt_text": "Hero graphic",
                    },
                    "styling": {
                        "text_color": "#4338CA",
                        "is_bold": True,
                        "is_italic": False,
                    },
                },
                headers=auth_headers,
            )
            assert q_res.status_code == 201
            media_data = q_res.get_json()["question"]["media"]
            assert media_data["desktop_orientation"] == d_orient
            assert media_data["mobile_orientation"] == m_orient
            styling = q_res.get_json()["question"]["styling"]
            assert styling["text_color"] == "#4338CA"
            assert styling["is_bold"] is True


def test_multiple_choice_branching_and_multiple_selection():
    """Verifies that multiple choice supports branching when single select, and disables branching when multi-select."""
    q_single = Question(
        id="q_mc_1",
        form_id="f1",
        order_index=1,
        question_type="multiple_choice",
        title="Favorite framework",
        required=True,
        properties={
            "choices": [{"id": "c1", "label": "React"}, {"id": "c2", "label": "Vue"}],
            "allow_multiple": False,
            "allow_other": True,
            "allow_none": True,
            "branching": [
                {"choice_id": "c1", "choice_label": "React", "target_question_id": "q_react_deep_dive"},
                {"choice_id": "c2", "choice_label": "Vue", "target_question_id": "q_vue_deep_dive"},
            ],
        },
    )

    all_q = [
        q_single,
        Question(id="q_react_deep_dive", order_index=2, question_type="short_text"),
        Question(id="q_vue_deep_dive", order_index=3, question_type="short_text"),
    ]

    # Test branching to React target
    eval_react = evaluate_next_step(q_single, "React", all_q)
    assert eval_react["is_jump"] is True
    assert eval_react["next_question_id"] == "q_react_deep_dive"

    # Test branching to Vue target
    eval_vue = evaluate_next_step(q_single, "Vue", all_q)
    assert eval_vue["is_jump"] is True
    assert eval_vue["next_question_id"] == "q_vue_deep_dive"

    # When allow_multiple is True, branching rules should NOT be triggered
    q_multi = Question(
        id="q_mc_multi",
        form_id="f1",
        order_index=1,
        question_type="multiple_choice",
        title="Languages used",
        properties={
            "choices": [{"id": "c1", "label": "Python"}, {"id": "c2", "label": "TypeScript"}],
            "allow_multiple": True,
            "branching": [
                {"choice_label": "Python", "target_question_id": "q_python_deep_dive"}
            ],
        },
    )
    all_multi_q = [
        q_multi,
        Question(id="q_next_seq", order_index=2, question_type="short_text"),
    ]
    eval_multi = evaluate_next_step(q_multi, ["Python", "TypeScript"], all_multi_q)
    assert eval_multi["is_jump"] is False
    assert eval_multi["next_question_id"] == "q_next_seq"


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
