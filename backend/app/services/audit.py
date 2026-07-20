import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_action(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Record a destructive/financial action for the compliance trail.
    Callers are expected to commit as part of their existing transaction --
    this only adds the row (same pattern as app.services.notifications.notify)."""

    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
    )


def log_ai_call(
    db: Session,
    model: str,
    prompt: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Log an AI call to the audit database, hashing the prompt to protect PII,
    and calculating the estimated cost based on token counts. Never logs raw prompt or PII."""
    import hashlib
    from app.models.audit_log import AICallAudit

    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    # Calculate estimated cost for claude-opus-4-8 (or default to Opus rates)
    # Claude 3 Opus pricing: $15.00 / 1M input, $75.00 / 1M output
    cost_per_input = 15.0 / 1_000_000
    cost_per_output = 75.0 / 1_000_000
    estimated_cost = (input_tokens * cost_per_input) + (output_tokens * cost_per_output)

    audit = AICallAudit(
        prompt_hash=prompt_hash,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
    )
    db.add(audit)

