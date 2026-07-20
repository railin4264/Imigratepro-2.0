import uuid
import pytest
from pathlib import Path
from app.models.e_signature import ESignature
from app.models.form import GeneratedForm
from app.seed_forms import seed as seed_forms


@pytest.fixture
def seeded_forms():
    seed_forms()


def test_esign_flow_and_tamper_detection(client, db_session, auth_headers, seeded_forms, make_case):
    # 1. Create a case
    case = make_case()
    case_id = case["id"]

    # 2. Generate a form (which creates a PDF on disk)
    res_gen = client.post(
        f"/api/v1/cases/{case_id}/forms",
        json={"form_code": "I-130"},
        headers=auth_headers,
    )
    assert res_gen.status_code == 201, res_gen.text
    form_data = res_gen.json()
    form_id = form_data["id"]
    
    # Retrieve form object from the db to get the output PDF path
    form_obj = db_session.get(GeneratedForm, uuid.UUID(form_id))
    assert form_obj is not None
    output_pdf_path = form_obj.output_pdf_path
    
    assert output_pdf_path is not None
    assert Path(output_pdf_path).exists()

    # 3. Sign the form via POST /api/v1/e-signatures
    payload = {
        "form_id": form_id,
        "signer_type": "client",
        "signer_name": "Jose Garcia",
        "signer_email": "jose@example.com",
        "signature_method": "typed",
        "signature_value": "Jose Garcia",
        "consent_text": "I agree to the terms of this electronic signature.",
    }
    
    res_sign = client.post(
        "/api/v1/e-signatures",
        json=payload,
        headers=auth_headers,
    )
    assert res_sign.status_code == 201, res_sign.text
    sig_data = res_sign.json()
    sig_id = sig_data["id"]
    
    assert sig_data["form_id"] == form_id
    assert sig_data["signer_name"] == "Jose Garcia"
    assert sig_data["signature_value"] == "Jose Garcia"
    assert sig_data["consent_text"] == "I agree to the terms of this electronic signature."
    assert sig_data["document_hash"] is not None

    # 4. Verify signature is present via GET /api/v1/e-signatures
    res_list = client.get(
        f"/api/v1/e-signatures?form_id={form_id}",
        headers=auth_headers,
    )
    assert res_list.status_code == 200
    signatures = res_list.json()
    assert len(signatures) == 1
    assert signatures[0]["id"] == sig_id

    # 5. Verify verification endpoint status (should be changed=False)
    res_verify = client.get(
        f"/api/v1/e-signatures/{sig_id}",
        headers=auth_headers,
    )
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["changed"] is False
    assert verify_data["signature"]["id"] == sig_id

    # 6. Verify download endpoint (GET /api/v1/e-signatures/{id}?download=true)
    res_dl = client.get(
        f"/api/v1/e-signatures/{sig_id}?download=true",
        headers=auth_headers,
    )
    assert res_dl.status_code == 200
    assert res_dl.content[:4] == b"%PDF"

    # 7. Modify the PDF on disk to trigger tamper detection (changed=True)
    with open(output_pdf_path, "ab") as f:
        f.write(b"\n%tampered_content")

    # 8. Verify tamper detection flags changed=True
    res_verify_tampered = client.get(
        f"/api/v1/e-signatures/{sig_id}",
        headers=auth_headers,
    )
    assert res_verify_tampered.status_code == 200
    verify_tampered_data = res_verify_tampered.json()
    assert verify_tampered_data["changed"] is True
