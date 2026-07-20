def test_rfes_require_auth(client, make_case):
    case = make_case()
    res = client.post(f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"})
    assert res.status_code == 401


def test_create_rfe_for_missing_case_returns_404(client, auth_headers):
    res = client.post(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000/rfes",
        json={"received_date": "2026-01-01"},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_create_rfe_advances_case_status_and_notifies(client, auth_headers, make_case):
    case = make_case()
    assert case["status"] == "intake"

    create = client.post(
        f"/api/v1/cases/{case['id']}/rfes",
        json={"received_date": "2026-01-01", "response_due_date": "2026-02-01", "notes": "income evidence"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    rfe = create.json()
    assert rfe["status"] == "open"
    assert rfe["evidence_count"] == 0
    assert rfe["case_number"] == case["case_number"]

    updated_case = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers).json()
    assert updated_case["status"] == "rfe"

    notifications = client.get("/api/v1/notifications", headers=auth_headers).json()
    assert any(n["type"] == "rfe_received" for n in notifications)


def test_create_rfe_does_not_override_a_later_status(client, auth_headers, make_case):
    case = make_case()
    client.patch(f"/api/v1/cases/{case['id']}", json={"status": "approved"}, headers=auth_headers)

    client.post(f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers)

    updated_case = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers).json()
    assert updated_case["status"] == "approved"


def test_resolving_the_last_open_rfe_moves_case_back_to_filed(client, auth_headers, make_case):
    case = make_case()
    rfe = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers
    ).json()
    assert client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers).json()["status"] == "rfe"

    respond = client.patch(f"/api/v1/rfes/{rfe['id']}", json={"status": "responded"}, headers=auth_headers)
    assert respond.status_code == 200

    updated_case = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers).json()
    assert updated_case["status"] == "filed"


def test_resolving_one_of_two_open_rfes_keeps_case_in_rfe_status(client, auth_headers, make_case):
    case = make_case()
    first = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-15"}, headers=auth_headers)

    client.patch(f"/api/v1/rfes/{first['id']}", json={"status": "closed"}, headers=auth_headers)

    updated_case = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers).json()
    assert updated_case["status"] == "rfe"


def test_resolving_rfe_does_not_override_a_status_moved_on_manually(client, auth_headers, make_case):
    case = make_case()
    rfe = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers
    ).json()
    # Preparer manually moved the case forward while the RFE was still open.
    client.patch(f"/api/v1/cases/{case['id']}", json={"status": "approved"}, headers=auth_headers)

    client.patch(f"/api/v1/rfes/{rfe['id']}", json={"status": "responded"}, headers=auth_headers)

    updated_case = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers).json()
    assert updated_case["status"] == "approved"


def test_rfe_evidence_checklist_flow(client, auth_headers, make_case):
    case = make_case()
    rfe = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers
    ).json()

    item = client.post(
        f"/api/v1/rfes/{rfe['id']}/evidence",
        json={"description": "Certified marriage certificate"},
        headers=auth_headers,
    )
    assert item.status_code == 201
    item_id = item.json()["id"]
    assert item.json()["status"] == "pending"

    detail = client.get(f"/api/v1/rfes/{rfe['id']}", headers=auth_headers).json()
    assert len(detail["evidence_items"]) == 1

    updated = client.patch(
        f"/api/v1/rfes/{rfe['id']}/evidence/{item_id}", json={"status": "gathered"}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "gathered"

    listed = client.get(f"/api/v1/cases/{case['id']}/rfes", headers=auth_headers).json()
    assert listed[0]["evidence_gathered_count"] == 1
    assert listed[0]["evidence_count"] == 1

    deleted = client.delete(f"/api/v1/rfes/{rfe['id']}/evidence/{item_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_deleting_case_cascades_to_rfes_and_evidence(client, auth_headers, make_case):
    case = make_case()
    rfe = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers
    ).json()
    client.post(f"/api/v1/rfes/{rfe['id']}/evidence", json={"description": "Passport copy"}, headers=auth_headers)

    deleted = client.delete(f"/api/v1/cases/{case['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/rfes/{rfe['id']}", headers=auth_headers)
    assert missing.status_code == 404


def test_ai_status_route_not_shadowed_by_rfe_id_route(client, auth_headers):
    # Regression test: /rfes/ai-status was previously registered *after*
    # /rfes/{rfe_id}, so FastAPI matched "ai-status" as a rfe_id path param
    # first and returned 422 instead of ever reaching this route.
    res = client.get("/api/v1/rfes/ai-status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"configured": False}


def test_suggest_evidence_without_api_key_returns_503(client, auth_headers, make_case):
    case = make_case()
    rfe = client.post(
        f"/api/v1/cases/{case['id']}/rfes",
        json={"received_date": "2026-01-01", "raw_text": "Please submit proof of income."},
        headers=auth_headers,
    ).json()

    res = client.post(f"/api/v1/rfes/{rfe['id']}/suggest", json={}, headers=auth_headers)
    assert res.status_code == 503
