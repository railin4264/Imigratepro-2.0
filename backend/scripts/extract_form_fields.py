"""One-off tool: extract the complete field inventory (name, type, official
USCIS tooltip label, page, checkbox/choice options) from a fillable PDF, and
write it out as JSON. Run once per form whenever a new template is added or
a form edition changes.

Usage: ./.venv/Scripts/python.exe scripts/extract_form_fields.py i-130.pdf
"""

import json
import sys
from pathlib import Path

from pypdf import PdfReader

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def full_field_name(annotation_obj) -> str:
    name = annotation_obj.get("/T")
    parent = annotation_obj.get("/Parent")
    full = name
    while parent is not None:
        pobj = parent.get_object()
        pt = pobj.get("/T")
        if pt:
            full = f"{pt}.{full}" if full else pt
        parent = pobj.get("/Parent")
    return full


def extract(pdf_path: Path) -> list[dict]:
    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        reader.decrypt("")

    fields = reader.get_fields() or {}
    name_to_page: dict[str, int] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots")
        if not annots:
            continue
        for a in annots:
            obj = a.get_object()
            name = full_field_name(obj)
            if name and name not in name_to_page:
                name_to_page[name] = page_number

    inventory = []
    for name, field in fields.items():
        ft = field.get("/FT")
        if ft is None or "PDF417BarCode" in name:
            continue

        entry = {
            "name": name,
            "type": {"/Tx": "text", "/Btn": "checkbox", "/Ch": "choice"}.get(ft, ft),
            "label": field.get("/TU") or name.split(".")[-1],
            "page": name_to_page.get(name),
        }

        if ft == "/Btn":
            states = [s for s in (field.get("/_States_") or []) if s != "/Off"]
            entry["on_value"] = states[0] if states else "/1"
        elif ft == "/Ch":
            entry["options"] = [opt[0] if isinstance(opt, list) else opt for opt in (field.get("/_States_") or [])]

        inventory.append(entry)

    inventory.sort(key=lambda e: (e["page"] or 0,))
    return inventory


if __name__ == "__main__":
    filename = sys.argv[1]
    pdf_path = BACKEND_ROOT / "form_templates" / filename
    out_path = BACKEND_ROOT / "app" / "seed_data" / "field_inventories" / f"{pdf_path.stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    inventory = extract(pdf_path)
    out_path.write_text(json.dumps(inventory, indent=2))
    print(f"{filename}: {len(inventory)} fields -> {out_path}")
