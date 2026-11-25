import pytest
from backend.app.core.config import settings


def test_health_check(client):
    """Verify /health returns 200, service name, and connected database."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "OfferCheck API"
    assert data["database"] == "connected"
    assert "timestamp" in data


def test_analyze_genuine_offer(client):
    """Test analyzing a verified campus recruitment email from Sudeepta Chauhan."""
    payload = {
        "sender": "sudeepta.chauhan@bennett.edu.in",
        "company": "Cisco",
        "text": (
            "Dear B.Tech CSE Students,\n\n"
            "The initial coding round for Cisco Summer Internship is scheduled on HackerRank. "
            "Bennett University and Cisco never charge any registration fee or training deposit. "
            "Please check the official portal at https://careers.cisco.com.\n\n"
            "Sudeepta Chauhan\nCareer Development Centre"
        )
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] < 25
    assert data["verdict"] == "low_risk"
    assert data["status"] == "completed"
    assert data["sender_domain"] == "bennett.edu.in"
    assert "what_to_do_next" in data
    assert len(data["what_to_do_next"]) > 0
    assert "id" in data


def test_analyze_scam_fee_override(client):
    """Test fake offer with upfront laptop security deposit triggers hard override (score >= 75)."""
    payload = {
        "sender": "recruitment@techsolutions-india.org",
        "company": "TechSolutions",
        "text": (
            "Congratulations! You are selected directly without any interview for the Web Dev Internship. "
            "Stipend is Rs. 45,000 per month. To confirm your slot, pay a refundable security deposit and laptop "
            "courier fee of Rs. 999 to hr@upi within 24 hours. Contact on Telegram: t.me/tech_interns. "
            "Send Aadhaar card and bank account details."
        )
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 75
    assert data["verdict"] == "likely_fake"
    assert any("FEE" in f["rule_id"] for f in data["findings"])
    assert any("INTERVIEW" in f["rule_id"] for f in data["findings"])


def test_analyze_blocklisted_domain(client):
    """Test domain marked as blocklisted forces score=100 and verdict=likely_fake."""
    payload = {
        "sender": "sudeepta.chauhan@bennett-careers.org",
        "company": "Bennett",
        "text": "Please confirm your internship slot immediately."
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 100
    assert data["verdict"] == "likely_fake"


def test_analyze_raw_eml_input(client):
    """Test analyzing email via raw_eml string containing headers and text."""
    eml_content = (
        "From: HR Manager <recruiter@techfake.net>\n"
        "To: student@bennett.edu.in\n"
        "Subject: Direct Selection Internship Offer\n"
        "Reply-To: scamdesk@gmail.com\n"
        "Received-SPF: fail\n"
        "\n"
        "You are directly selected without interview. Pay registration fee of Rs. 500 via UPI."
    )
    payload = {
        "sender": "recruiter@techfake.net",
        "raw_eml": eml_content
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] >= 55
    assert data["verdict"] == "likely_fake"
    assert any("REPLYTO" in f["rule_id"].upper() for f in data["findings"])


def test_analyze_empty_payload_fails(client):
    """Test submitting no text and no raw_eml returns 422 Unprocessable Entity."""
    payload = {
        "sender": "recruiter@example.com"
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 422


def test_get_report_by_id(client):
    """Test retrieving an existing report by ID."""
    # First analyze an offer
    payload = {
        "sender": "careers@google.com",
        "company": "Google",
        "text": "Invitation for Google STEP coding round on HackerRank. No fees charged."
    }
    create_res = client.post("/v1/analyze", json=payload)
    report_id = create_res.json()["id"]

    # Now retrieve it
    get_res = client.get(f"/v1/reports/{report_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == report_id
    assert data["sender_domain"] == "google.com"
    assert "findings" in data
    assert "what_to_do_next" in data


def test_get_nonexistent_report(client):
    """Test retrieving non-existent report returns 404 Not Found."""
    response = client.get("/v1/reports/non-existent-uuid-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_submit_report_feedback(client):
    """Test submitting user feedback ('scam') on an analyzed report."""
    # Analyze first
    payload = {
        "sender": "hr@fakejobs.com",
        "text": "Direct offer letter. Pay registration charges."
    }
    analyze_res = client.post("/v1/analyze", json=payload)
    report_id = analyze_res.json()["id"]

    # Post feedback
    fb_payload = {
        "label": "scam",
        "note": "They asked for UPI transfer after email reply."
    }
    fb_res = client.post(f"/v1/reports/{report_id}/feedback", json=fb_payload)
    assert fb_res.status_code == 201
    fb_data = fb_res.json()
    assert fb_data["report_id"] == report_id
    assert fb_data["label"] == "scam"
    assert fb_data["note"] == fb_payload["note"]


def test_submit_feedback_nonexistent_report(client):
    """Test submitting feedback on a non-existent report returns 404."""
    fb_payload = {"label": "real", "note": "Valid offer"}
    response = client.post("/v1/reports/missing-report-999/feedback", json=fb_payload)
    assert response.status_code == 404


def test_payload_size_cap_200kb(client):
    """Test that requests exceeding 200 KB are rejected with 413 Request Entity Too Large."""
    oversized_text = "A" * (205 * 1024)  # 205 KB
    payload = {
        "sender": "test@example.com",
        "text": oversized_text
    }
    response = client.post("/v1/analyze", json=payload)
    assert response.status_code == 413
    assert "limit" in response.json()["detail"].lower()
