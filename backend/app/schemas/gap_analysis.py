import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.requirements import FormRequirementsRead


class GapItemRead(BaseModel):
    severity: str
    code: str
    message: str
    client_id: uuid.UUID | None = None


class GapAnalysisResponse(BaseModel):
    case_id: uuid.UUID
    checked_at: datetime
    gaps: list[GapItemRead]
    # USCIS's own published checklist for whichever forms are already
    # generated on this case -- reference only, not computed from case data
    # like `gaps` above (see app/seed_data/uscis_requirements.py).
    reference_checklist: list[FormRequirementsRead] = []
