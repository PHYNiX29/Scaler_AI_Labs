def make_form(client, **body):
    return client.post("/api/forms", json={"title": "Test form", "include_starter": False, **body}).json()["form"]


def add_question(client, form_id, **body):
    res = client.post(f"/api/forms/{form_id}/questions", json=body)
    assert res.status_code == 201, res.text
    return res.json()["question"]


def test_health_check(client):
    assert client.get("/api/health").json() == {"status": "healthy"}


def test_form_crud_duplicate_and_publish(client):
    form = make_form(client, title="Product research", include_starter=True)
    assert [q["question_type"] for q in form["questions"]] == ["welcome", "multiple_choice", "thank_you"]
    assert form["status"] == "draft"

    renamed = client.put(f"/api/forms/{form['id']}", json={"title": "Renamed"}).json()["form"]
    assert renamed["title"] == "Renamed"
    assert client.put(f"/api/forms/{form['id']}", json={"title": ""}).status_code == 422

    copy = client.post(f"/api/forms/{form['id']}/duplicate").json()["form"]
    assert copy["title"] == "Renamed (Copy)"
    assert copy["id"] != form["id"] and copy["slug"] != form["slug"]
    assert len(copy["questions"]) == 3

    assert client.post(f"/api/forms/{form['id']}/publish", json={}).json()["status"] == "published"
    assert client.post(f"/api/forms/{form['id']}/publish", json={}).json()["status"] == "draft"

    listed = client.get("/api/forms").json()["forms"]
    assert {f["id"] for f in listed} == {form["id"], copy["id"]}

    assert client.delete(f"/api/forms/{form['id']}").status_code == 200
    assert client.get(f"/api/forms/{form['id']}").status_code == 404


def test_duplicate_repoints_branching_at_the_copied_questions(client):
    form = make_form(client)
    target = add_question(client, form["id"], question_type="short_text", title="Why?")
    add_question(
        client, form["id"], question_type="yes_no", title="Happy?",
        logic_jumps=[{"choice_id": "no", "target_question_id": target["id"]}],
    )
    copy = client.post(f"/api/forms/{form['id']}/duplicate").json()["form"]
    copied_target, copied_yes_no = copy["questions"]
    assert copied_yes_no["logic_jumps"] == [{"choice_id": "no", "target_question_id": copied_target["id"]}]


def test_question_add_update_reorder_delete(client):
    form = make_form(client)
    q1 = add_question(client, form["id"], question_type="dropdown", title="Country",
                      properties={"choices": [{"id": "c1", "label": "India"}]})
    q2 = add_question(client, form["id"], question_type="rating", title="Rate us")
    q3 = add_question(client, form["id"], question_type="email", title="Email")
    assert q1["media"]["desktop_orientation"] == "float_right"  # model default applied
    assert client.post(f"/api/forms/{form['id']}/questions", json={"question_type": "bogus"}).status_code == 422

    updated = client.put(f"/api/forms/{form['id']}/questions/{q2['id']}", json={"required": True, "description": "1-5"})
    assert updated.json()["question"]["required"] is True
    assert updated.json()["question"]["title"] == "Rate us"  # untouched fields survive a partial update

    reordered = client.put(f"/api/forms/{form['id']}/questions/reorder", json={"question_ids": [q3["id"], q1["id"], q2["id"]]})
    assert [q["id"] for q in reordered.json()["questions"]] == [q3["id"], q1["id"], q2["id"]]
    assert client.put(f"/api/forms/{form['id']}/questions/reorder", json={"question_ids": [q1["id"]]}).status_code == 422

    assert client.delete(f"/api/forms/{form['id']}/questions/{q1['id']}").status_code == 200
    remaining = client.get(f"/api/forms/{form['id']}").json()["form"]["questions"]
    assert [(q["id"], q["order_index"]) for q in remaining] == [(q3["id"], 0), (q2["id"], 1)]


def test_draft_forms_are_not_publicly_visible(client):
    form = make_form(client)
    assert client.get(f"/api/public/forms/{form['slug']}").status_code == 404
    assert client.get(f"/api/public/forms/{form['slug']}?preview=true").status_code == 404
    assert client.post(f"/api/public/forms/{form['slug']}/submit", json={"answers": {}}).status_code == 404


def test_respondent_flow_with_branching(client):
    form = make_form(client)
    fid, slug = form["id"], form["slug"]
    name = add_question(client, fid, question_type="short_text", title="Name", required=True, properties={"max_length": 10})
    happy = add_question(client, fid, question_type="yes_no", title="Happy?", required=True)
    why_not = add_question(client, fid, question_type="long_text", title="Why not?", required=True)
    email = add_question(client, fid, question_type="email", title="Email")
    ending = add_question(client, fid, question_type="thank_you", title="Bye")
    # Yes skips the required "Why not?" question
    client.put(f"/api/forms/{fid}/questions/{happy['id']}",
               json={"logic_jumps": [{"choice_id": "yes", "target_question_id": email["id"]}]})
    client.post(f"/api/forms/{fid}/publish", json={"status": "published"})

    assert len(client.get(f"/api/public/forms/{slug}").json()["form"]["questions"]) == 5
    session_id = client.post(f"/api/public/forms/{slug}/start", json={}).json()["session_id"]

    def step(question, answer):
        return client.post(f"/api/public/forms/{slug}/validate-step", json={"question_id": question["id"], "answer": answer}).json()

    assert step(name, "")["valid"] is False
    assert "maximum length" in step(name, "far too long a name")["error"]
    assert step(name, "Neo") == {"valid": True, "next_question_id": happy["id"], "is_end": False}
    assert step(happy, "Yes")["next_question_id"] == email["id"]
    assert step(happy, "No")["next_question_id"] == why_not["id"]
    assert step(email, "not-an-email")["valid"] is False
    assert step(email, "neo@matrix.io") == {"valid": True, "next_question_id": ending["id"], "is_end": True}

    # "No" path: the required follow-up is on the path, so leaving it out is rejected
    rejected = client.post(f"/api/public/forms/{slug}/submit", json={"answers": {name["id"]: "Neo", happy["id"]: "No"}})
    assert rejected.status_code == 422
    assert why_not["id"] in rejected.json()["detail"]["field_errors"]

    # "Yes" path: the required follow-up was skipped by the jump, so the submit succeeds
    accepted = client.post(
        f"/api/public/forms/{slug}/submit",
        json={"session_id": session_id, "answers": {name["id"]: "Neo", happy["id"]: "Yes"}, "time_taken_seconds": 30},
    )
    assert accepted.status_code == 201

    responses = client.get(f"/api/forms/{fid}/responses").json()
    assert responses["total"] == 1  # the in-progress session row was completed, not duplicated
    assert responses["responses"][0]["status"] == "completed"
    assert client.get(f"/api/forms/{fid}").json()["form"]["submissions_count"] == 1


def test_responses_stats_and_csv_export(client):
    form = make_form(client, title="Stats form")
    fid, slug = form["id"], form["slug"]
    rating = add_question(client, fid, question_type="rating", title="Satisfaction", required=True, properties={"max_rating": 5})
    comment = add_question(client, fid, question_type="short_text", title="Comment")
    client.post(f"/api/forms/{fid}/publish", json={})

    client.post(f"/api/public/forms/{slug}/start", json={})  # abandoned fill
    client.post(f"/api/public/forms/{slug}/submit", json={"answers": {rating["id"]: 5, comment["id"]: "=SUM(A1)"}, "time_taken_seconds": 40})
    client.post(f"/api/public/forms/{slug}/submit", json={"answers": {rating["id"]: 4}, "time_taken_seconds": 50})

    stats = client.get(f"/api/forms/{fid}/stats").json()["stats"]
    assert (stats["total_responses"], stats["completed_count"], stats["avg_time_seconds"]) == (3, 2, 45)
    assert stats["completion_rate"] == 66.7
    assert stats["questions"][0]["avg_rating"] == 4.5

    listed = client.get(f"/api/forms/{fid}/responses?status=completed").json()
    assert listed["total"] == 2
    detail = client.get(f"/api/forms/{fid}/responses/{listed['responses'][0]['id']}").json()["response"]
    assert detail["answers_breakdown"][0]["question_title"] == "Satisfaction"

    csv_res = client.get(f"/api/forms/{fid}/export/csv")
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "Satisfaction" in csv_res.text
    assert "'=SUM(A1)" in csv_res.text  # formula neutralised

    assert client.delete(f"/api/forms/{fid}/responses/{detail['id']}").status_code == 200
    assert client.get(f"/api/forms/{fid}").json()["form"]["submissions_count"] == 1


def test_upload_rejects_unsupported_types(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routes.upload_routes.UPLOAD_DIR", tmp_path)
    assert client.post("/api/upload", files={"file": ("evil.html", b"<script>", "text/html")}).status_code == 422
    ok = client.post("/api/upload", files={"file": ("photo.PNG", b"fake-png", "image/png")})
    assert ok.status_code == 201
    assert (tmp_path / ok.json()["filename"]).read_bytes() == b"fake-png"
