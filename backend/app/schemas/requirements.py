from pydantic import BaseModel


class RequirementCategoryRead(BaseModel):
    title: str
    items: list[str]


class FormRequirementsRead(BaseModel):
    form_code: str
    source_url: str
    source_label: str
    verified_on: str
    categories: list[RequirementCategoryRead]
