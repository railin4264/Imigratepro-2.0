import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.models.case import Case
from app.schemas.gap_analysis import GapAnalysisResponse, GapItemRead
from app.schemas.requirements import FormRequirementsRead, RequirementCategoryRead
from app.seed_data.uscis_requirements import USCIS_REQUIREMENTS_BY_FORM_CODE
from app.services.gap_analysis import analyze_case

router = APIRouter(tags=["gap-analysis"])


def _reference_checklist(case: Case) -> list[FormRequirementsRead]:
    codes = sorted({gf.template.code for gf in case.generated_forms})
    checklist = []
    for code in codes:
        entry = USCIS_REQUIREMENTS_BY_FORM_CODE.get(code)
        if not entry:
            continue
        checklist.append(
            FormRequirementsRead(
                form_code=code,
                source_url=entry.source_url,
                source_label=entry.source_label,
                verified_on=entry.verified_on,
                categories=[RequirementCategoryRead(title=c.title, items=c.items) for c in entry.categories],
            )
        )
    return checklist


@router.get("/cases/{case_id}/gap-analysis", response_model=GapAnalysisResponse)
def get_case_gap_analysis(case_id: uuid.UUID, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    gaps = analyze_case(case)
    return GapAnalysisResponse(
        case_id=case.id,
        checked_at=datetime.now(timezone.utc),
        gaps=[GapItemRead(severity=g.severity, code=g.code, message=g.message, client_id=g.client_id) for g in gaps],
        reference_checklist=_reference_checklist(case),
    )
