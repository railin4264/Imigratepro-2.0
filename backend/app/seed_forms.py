"""Upsert the built-in FormTemplate rows (I-130, I-765, G-28), loading each
form's full field inventory from app/seed_data/field_inventories/*.json
(produced by scripts/extract_form_fields.py).

Run with: ./.venv/Scripts/python.exe -m app.seed_forms
"""

import json
from pathlib import Path

from app.core.database import SessionLocal
from app.models.form import FormTemplate
from app.seed_data.conditional_rules import CONDITIONS_BY_FORM_CODE
from app.seed_data.form_field_maps import FORM_TEMPLATES

INVENTORY_DIR = Path(__file__).resolve().parent / "seed_data" / "field_inventories"


def seed() -> None:
    db = SessionLocal()
    try:
        for entry in FORM_TEMPLATES:
            template = db.query(FormTemplate).filter_by(code=entry["code"]).one_or_none()
            if template is None:
                template = FormTemplate(code=entry["code"])
                db.add(template)

            inventory = json.loads((INVENTORY_DIR / entry["inventory_file"]).read_text())
            conditions = CONDITIONS_BY_FORM_CODE.get(entry["code"], {})
            for field in inventory:
                if field["name"] in conditions:
                    field["show_if"] = conditions[field["name"]]

            template.name = entry["name"]
            template.edition_date = entry["edition_date"]
            template.pdf_template_path = entry["pdf_template_path"]
            template.field_schema = inventory
            template.autofill_map = entry["autofill_map"]
        db.commit()
        print(f"Seeded {len(FORM_TEMPLATES)} form templates.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
