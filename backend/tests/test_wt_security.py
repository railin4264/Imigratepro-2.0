import pytest
import uuid
from datetime import datetime, timezone, timedelta
from io import BytesIO
from app.models.auth_token import DeniedToken, RefreshToken
from app.models.audit_log import AICallAudit
from app.models.case import ParticipantRole, CaseParticipant
from app.models.client import Client
from app.models.document import Document
from app.services import document_ai, form_review_ai, rfe_ai
from app.core.security import decode_access_token

@pytest.fixture
def seeded_forms():
    from app.seed_forms import seed as seed_forms
    seed_forms()

def test_form_token_document_scoping(client, auth_headers, make_case, seeded_forms, db_session):
    # 1. Create a case
    case_data = make_case()
    case_id = uuid.UUID(case_data["id"])
    
    # Create two clients
    client_b = Client(first_name="Beneficiary", last_name="Client", email="b@test.local")
    client_s = Client(first_name="Sponsor", last_name="Client", email="s@test.local")
    db_session.add_all([client_b, client_s])
    db_session.commit()
    
    # Associate them with the case
    part_b = CaseParticipant(case_id=case_id, client_id=client_b.id, role=ParticipantRole.BENEFICIARY)
    part_s = CaseParticipant(case_id=case_id, client_id=client_s.id, role=ParticipantRole.SPONSOR)
    db_session.add_all([part_b, part_s])
    db_session.commit()
    
    # Generate G-28 form (only beneficiary role is relevant for G-28 autofill maps)
    generated = client.post(
        f"/api/v1/cases/{case_id}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    token = generated["access_token"]
    
    # Upload one document for beneficiary, one for sponsor
    doc_b = Document(case_id=case_id, client_id=client_b.id, original_filename="b_doc.pdf", storage_path="b_path")
    doc_s = Document(case_id=case_id, client_id=client_s.id, original_filename="s_doc.pdf", storage_path="s_path")
    db_session.add_all([doc_b, doc_s])
    db_session.commit()
    
    # List documents using form token
    res = client.get(f"/api/v1/public/forms/{token}/documents")
    assert res.status_code == 200
    docs = res.json()
    
    # Form token must only see beneficiary document, not sponsor document
    assert len(docs) == 1
    assert docs[0]["original_filename"] == "b_doc.pdf"

    # Upload document using form token with role="sponsor" (disallowed for G-28)
    # The backend must override the disallowed role with a fallback (beneficiary) to not break the wizard
    # We pass file as a tuple for multipart upload
    files = {"file": ("uploaded.pdf", BytesIO(b"fake PDF content"), "application/pdf")}
    data = {"role": "sponsor"}
    res_upload = client.post(f"/api/v1/public/forms/{token}/documents", files=files, data=data)
    assert res_upload.status_code == 201
    uploaded_doc = res_upload.json()
    assert uploaded_doc["client_id"] == str(client_b.id)  # Overridden to beneficiary!


def test_access_token_revocation(client, admin_user, auth_headers, db_session):
    auth_val = auth_headers["Authorization"]
    token = auth_val.split(" ")[1]
    
    # Verify token is initially valid
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    
    # Revoke via explicit endpoint /auth/revoke
    res_revoke = client.post("/api/v1/auth/revoke", json={"token": token}, headers=auth_headers)
    assert res_revoke.status_code == 204
    
    # Token must now be rejected
    res_denied = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res_denied.status_code == 401


def test_logout_revokes_access_token(client, admin_user, auth_headers, db_session):
    auth_val = auth_headers["Authorization"]
    token = auth_val.split(" ")[1]
    
    # Logout
    res_logout = client.post("/api/v1/auth/logout", json={"refresh_token": "dummy"}, headers=auth_headers)
    assert res_logout.status_code == 204
    
    # Verify token is revoked
    res_me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res_me.status_code == 401


def test_ai_call_audit_log_from_services(monkeypatch, db_session):
    # Mock Anthropic client for document_ai
    class FakeUsage:
        input_tokens = 150
        output_tokens = 50
    class FakeMessage:
        stop_reason = "end_turn"
        content = [type("Block", (object,), {"type": "text", "text": '{"first_name": "Ana", "document_type": "passport", "last_name": "Perez", "date_of_birth": "1990-01-01", "country_of_birth": "Mexico", "nationality": "Mexican", "passport_number": "X1234567", "a_number": "", "expiration_date": "2030-01-01", "confidence_notes": ""}'})]
        usage = FakeUsage()
    class FakeMessages:
        def create(self, **kwargs):
            return FakeMessage()
    class FakeClient:
        messages = FakeMessages()
        
    monkeypatch.setattr(document_ai.settings, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(document_ai, "build_client", lambda: FakeClient())
    
    # Clear existing audits
    db_session.query(AICallAudit).delete()
    db_session.commit()
    
    # Call document_ai service
    document_ai.extract_document_data(b"pdf-bytes", "application/pdf")
    
    # Verify audit log was created
    audit = db_session.query(AICallAudit).first()
    assert audit is not None
    assert audit.model == document_ai.MODEL
    assert audit.input_tokens == 150
    assert audit.output_tokens == 50
    # Estimated cost = 150 * 15.0 / 1e6 + 50 * 75.0 / 1e6 = 0.00225 + 0.00375 = 0.006
    assert abs(audit.estimated_cost - 0.006) < 1e-9
    assert audit.prompt_hash != ""


def test_denied_token_cleanup(db_session):
    from app.services.token_cleanup import cleanup_expired_tokens
    
    # Create two denied tokens: one expired (cutoff is 7 days ago, so let's set it to 10 days ago), one fresh
    now = datetime.now(timezone.utc)
    expired = DeniedToken(jti="expired_jti", expires_at=now - timedelta(days=10))
    fresh = DeniedToken(jti="fresh_jti", expires_at=now + timedelta(days=1))
    db_session.add_all([expired, fresh])
    db_session.commit()
    
    # Run cleanup
    res = cleanup_expired_tokens(db_session)
    assert res["denied_tokens_deleted"] == 1
    
    # Verify expired is deleted, fresh remains
    assert db_session.query(DeniedToken).filter(DeniedToken.jti == "expired_jti").first() is None
    assert db_session.query(DeniedToken).filter(DeniedToken.jti == "fresh_jti").first() is not None

