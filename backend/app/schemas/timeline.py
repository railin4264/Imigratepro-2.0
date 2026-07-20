from pydantic import BaseModel


class TimelineStepRead(BaseModel):
    key: str
    status: str


class CaseTimelineResponse(BaseModel):
    case_number: str
    steps: list[TimelineStepRead]
