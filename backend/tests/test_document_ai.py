"""extract_document_data() has no text-interpolation injection surface (the
prompt template is a static string; the untrusted input is the image/PDF
bytes themselves, a different class of risk than text injection) -- this
just confirms it goes through the shared reliability client."""

import json
from types import SimpleNamespace

import pytest

from app.services import document_ai


class _FakeMessages:
    def __init__(self, capture: dict):
        self._capture = capture

    def create(self, **kwargs):
        self._capture["kwargs"] = kwargs
        payload = json.dumps(
            {
                "document_type": "passport",
                "first_name": "Ana",
                "last_name": "Perez",
                "date_of_birth": "1990-01-01",
                "country_of_birth": "Mexico",
                "nationality": "Mexican",
                "passport_number": "X1234567",
                "a_number": "",
                "expiration_date": "2030-01-01",
                "confidence_notes": "",
            }
        )
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=payload)])


class _FakeClient:
    def __init__(self, capture: dict):
        self.messages = _FakeMessages(capture)


@pytest.fixture
def capture(monkeypatch):
    monkeypatch.setattr(document_ai.settings, "ANTHROPIC_API_KEY", "test-key")
    box: dict = {}
    monkeypatch.setattr(document_ai, "build_client", lambda: _FakeClient(box))
    return box


def test_extract_document_data_uses_the_shared_reliability_client(capture):
    document_ai.extract_document_data(b"fake-pdf-bytes", "application/pdf")
    assert "kwargs" in capture


def test_extract_document_data_returns_parsed_fields(capture):
    result = document_ai.extract_document_data(b"fake-pdf-bytes", "application/pdf")
    assert result["first_name"] == "Ana"
