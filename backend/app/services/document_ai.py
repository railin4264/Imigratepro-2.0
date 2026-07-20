"""Structured data extraction from identity documents (passport, birth/marriage
certificate, I-94) using Claude's vision input. Requires ANTHROPIC_API_KEY to be
set in backend/.env -- if it isn't, is_configured() is False and callers should
surface that instead of invoking extract_document_data (which raises)."""

import base64
import json

from app.core.config import settings
from app.services.ai_reliability import build_client

MODEL = "claude-opus-4-8"

_IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {
            "type": "string",
            "enum": [
                "passport",
                "birth_certificate",
                "marriage_certificate",
                "i94",
                "photo_id",
                "other",
            ],
        },
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "date_of_birth": {
            "type": "string",
            "description": "YYYY-MM-DD if it can be determined with confidence, else empty string",
        },
        "country_of_birth": {"type": "string"},
        "nationality": {"type": "string"},
        "passport_number": {"type": "string"},
        "a_number": {"type": "string", "description": "USCIS A-Number if present, digits only"},
        "expiration_date": {"type": "string", "description": "YYYY-MM-DD if present, else empty string"},
        "confidence_notes": {
            "type": "string",
            "description": "Any illegible fields, ambiguity, or reasons a value was left empty",
        },
    },
    "required": [
        "document_type",
        "first_name",
        "last_name",
        "date_of_birth",
        "country_of_birth",
        "nationality",
        "passport_number",
        "a_number",
        "expiration_date",
        "confidence_notes",
    ],
    "additionalProperties": False,
}

EXTRACTION_PROMPT = (
    "This is a scan or photo of an immigration-related identity document (passport, "
    "birth certificate, marriage certificate, I-94, or similar). Read it carefully and "
    "extract the fields in the schema. Use an empty string for any field that is not "
    "present or not legible -- do not guess at unclear characters, note the uncertainty "
    "in confidence_notes instead."
)


def is_configured() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def _content_block(file_bytes: bytes, content_type: str | None) -> dict:
    data = base64.standard_b64encode(file_bytes).decode("utf-8")
    if content_type == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}}
    media_type = content_type if content_type in _IMAGE_MEDIA_TYPES else "image/jpeg"
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


def extract_document_data(file_bytes: bytes, content_type: str | None) -> dict:
    """Send a document image/PDF to Claude and return fields matching EXTRACTION_SCHEMA.
    Raises RuntimeError if no API key is configured or the model declines -- callers
    should catch this and mark the Document as failed with the message."""

    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = build_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        output_config={"format": {"type": "json_schema", "schema": EXTRACTION_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": [
                    _content_block(file_bytes, content_type),
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined to process this document")

    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)
