import json


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"


def test_auth_flow(client):
    # Register
    reg_res = client.post(
        "/api/auth/register",
        json={"email": "alice@scaler.ai", "password": "supersecret123", "name": "Alice"},
    )
    assert reg_res.status_code == 201
    assert "access_token" in reg_res.get_json()

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "alice@scaler.ai", "password": "supersecret123"},
    )
    assert login_res.status_code == 200
    token = login_res.get_json()["access_token"]

    # Me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.get_json()["user"]["email"] == "alice@scaler.ai"


def test_form_crud_and_duplication(client, auth_headers):
    # Create Form
    create_res = client.post(
        "/api/forms",
        json={
            "title": "Product Research Form",
            "description": "Understanding user needs",
            "theme_settings": {
                "font_family": "Inter",
                "text_color": "#111827",
                "button_color": "#4F46E5",
            },
        },
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    form_data = create_res.get_json()["form"]
    form_id = form_data["id"]
    assert form_data["title"] == "Product Research Form"
    assert len(form_data["questions"]) == 3  # Starter questions: welcome, mc, thank_you

    # Update Form
    put_res = client.put(
        f"/api/forms/{form_id}",
        json={"title": "Updated Form Title", "status": "draft"},
        headers=auth_headers,
    )
    assert put_res.status_code == 200
    assert put_res.get_json()["form"]["title"] == "Updated Form Title"

    # Duplicate Form
    dup_res = client.post(f"/api/forms/{form_id}/duplicate", headers=auth_headers)
    assert dup_res.status_code == 201
    dup_form = dup_res.get_json()["form"]
    assert dup_form["title"] == "Updated Form Title (Copy)"
    assert dup_form["id"] != form_id
    assert len(dup_form["questions"]) == len(form_data["questions"])

    # Publish Form
    pub_res = client.post(f"/api/forms/{form_id}/publish", headers=auth_headers)
    assert pub_res.status_code == 200
    assert pub_res.get_json()["status"] == "published"


def test_question_types_and_reordering(client, auth_headers):
    # Create empty form without starters
    create_res = client.post(
        "/api/forms",
        json={"title": "Custom Test Form", "include_starter": False},
        headers=auth_headers,
    )
    form_id = create_res.get_json()["form"]["id"]

    # 1. Add Dropdown question
    q1_res = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "dropdown",
            "title": "Select Country",
            "required": True,
            "properties": {
                "choices": [{"id": "c1", "label": "USA"}, {"id": "c2", "label": "India"}],
            },
            "media": {
                "media_type": "image",
                "media_url": "https://example.com/map.jpg",
                "desktop_orientation": "left_split_1_3",
                "mobile_orientation": "top",
            },
        },
        headers=auth_headers,
    )
    assert q1_res.status_code == 201
    q1_id = q1_res.get_json()["question"]["id"]

    # 2. Add Contact question
    q2_res = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "contact",
            "title": "Contact Card",
            "properties": {
                "fields": {
                    "first_name": {"enabled": True, "required": True},
                    "email": {"enabled": True, "required": True, "regex": "^[^@]+@[^@]+\\.[^@]+$"},
                    "phone_number": {"enabled": True, "required": False},
                }
            },
        },
        headers=auth_headers,
    )
    assert q2_res.status_code == 201
    q2_id = q2_res.get_json()["question"]["id"]

    # 3. Add Rating question
    q3_res = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "rating",
            "title": "Rate our service",
            "required": True,
            "properties": {
                "icon": "thumbs_up",
                "max_rating": 5,
            },
        },
        headers=auth_headers,
    )
    assert q3_res.status_code == 201
    q3_id = q3_res.get_json()["question"]["id"]

    # Reorder questions: put q3 first, then q1, then q2
    reorder_res = client.put(
        f"/api/forms/{form_id}/questions/reorder",
        json={"question_ids": [q3_id, q1_id, q2_id]},
        headers=auth_headers,
    )
    assert reorder_res.status_code == 200
    reordered = reorder_res.get_json()["questions"]
    assert reordered[0]["id"] == q3_id
    assert reordered[1]["id"] == q1_id
    assert reordered[2]["id"] == q2_id


def test_public_respondent_flow_and_validation(client, auth_headers):
    # Create and publish form with various question types
    create_res = client.post(
        "/api/forms",
        json={"title": "Public Survey Test", "include_starter": False},
        headers=auth_headers,
    )
    form = create_res.get_json()["form"]
    form_id = form["id"]
    slug = form["slug"]

    # Add text question with max_length
    q_text = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "short_text",
            "title": "Your Nickname",
            "required": True,
            "properties": {"max_length": 10},
        },
        headers=auth_headers,
    ).get_json()["question"]

    # Add Yes/No question with branching
    q_yn = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "yes_no",
            "title": "Are you a student?",
            "required": True,
            "properties": {"branching": {"yes": "target_page_1", "no": "end"}},
        },
        headers=auth_headers,
    ).get_json()["question"]

    # Publish form
    client.post(f"/api/forms/{form_id}/publish", headers=auth_headers)

    # 1. Respondent fetches public form (NO AUTH)
    pub_res = client.get(f"/api/public/forms/{slug}")
    assert pub_res.status_code == 200
    pub_data = pub_res.get_json()["form"]
    assert pub_data["title"] == "Public Survey Test"
    assert len(pub_data["questions"]) == 2

    # 2. Respondent step validation: exceeding max character length fails
    val_fail = client.post(
        f"/api/public/forms/{slug}/validate-step",
        json={"question_id": q_text["id"], "answer": "This string is much longer than 10 characters"},
    )
    assert val_fail.status_code == 400
    assert "exceeds maximum length" in val_fail.get_json()["error"]

    # Valid string succeeds
    val_ok = client.post(
        f"/api/public/forms/{slug}/validate-step",
        json={"question_id": q_text["id"], "answer": "Neo"},
    )
    assert val_ok.status_code == 200
    assert val_ok.get_json()["valid"] is True

    # 3. Branching check on Yes/No
    # Answer 'yes' -> next_question_id should be 'target_page_1'
    branch_yes = client.post(
        f"/api/public/forms/{slug}/validate-step",
        json={"question_id": q_yn["id"], "answer": "yes"},
    )
    assert branch_yes.status_code == 200
    assert branch_yes.get_json()["next_question_id"] == "target_page_1"

    # Answer 'no' -> target is 'end'
    branch_no = client.post(
        f"/api/public/forms/{slug}/validate-step",
        json={"question_id": q_yn["id"], "answer": "no"},
    )
    assert branch_no.status_code == 200
    assert branch_no.get_json()["is_end"] is True

    # 4. Final Submission
    sub_res = client.post(
        f"/api/public/forms/{slug}/submit",
        json={
            "answers": {
                q_text["id"]: "Neo",
                q_yn["id"]: "yes",
            },
            "time_taken_seconds": 35,
        },
    )
    assert sub_res.status_code == 201
    assert "response_id" in sub_res.get_json()


def test_responses_stats_and_csv_export(client, auth_headers):
    # Create, seed questions, submit a response, check stats & csv
    create_res = client.post(
        "/api/forms",
        json={"title": "Stats Form Test", "include_starter": False},
        headers=auth_headers,
    )
    form = create_res.get_json()["form"]
    form_id = form["id"]
    slug = form["slug"]

    # Rating question
    q_rating = client.post(
        f"/api/forms/{form_id}/questions",
        json={
            "question_type": "rating",
            "title": "Satisfaction",
            "required": True,
            "properties": {"max_rating": 5},
        },
        headers=auth_headers,
    ).get_json()["question"]

    client.post(f"/api/forms/{form_id}/publish", headers=auth_headers)

    # Submit 2 responses
    client.post(
        f"/api/public/forms/{slug}/submit",
        json={"answers": {q_rating["id"]: 5}, "time_taken_seconds": 40},
    )
    client.post(
        f"/api/public/forms/{slug}/submit",
        json={"answers": {q_rating["id"]: 4}, "time_taken_seconds": 50},
    )

    # Get stats
    stats_res = client.get(f"/api/forms/{form_id}/stats", headers=auth_headers)
    assert stats_res.status_code == 200
    stats = stats_res.get_json()["stats"]
    assert stats["total_responses"] == 2
    assert stats["completed_count"] == 2
    assert stats["avg_time_seconds"] == 45
    assert len(stats["questions"]) == 1
    assert stats["questions"][0]["avg_rating"] == 4.5

    # Export CSV
    csv_res = client.get(f"/api/forms/{form_id}/export/csv", headers=auth_headers)
    assert csv_res.status_code == 200
    assert csv_res.mimetype == "text/csv"
    csv_text = csv_res.data.decode("utf-8")
    assert "Satisfaction" in csv_text
    assert "Response ID" in csv_text
