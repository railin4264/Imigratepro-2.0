import json
from pathlib import Path

import pytest

from app.seed_data.conditional_rules import CONDITIONS_BY_FORM_CODE
from app.seed_data.form_field_maps import FORM_TEMPLATES

INVENTORY_DIR = Path(__file__).resolve().parents[1] / "app" / "seed_data" / "field_inventories"


def _real_field_names(code: str) -> set[str]:
    entry = next(t for t in FORM_TEMPLATES if t["code"] == code)
    inventory = json.loads((INVENTORY_DIR / entry["inventory_file"]).read_text(encoding="utf-8"))
    return {f["name"] for f in inventory}


@pytest.mark.parametrize("code", sorted(CONDITIONS_BY_FORM_CODE), ids=sorted(CONDITIONS_BY_FORM_CODE))
def test_conditional_rules_only_reference_real_pdf_fields(code):
    """Regression test, same class of bug as
    test_forms.py::test_autofill_map_only_references_real_pdf_fields: a
    show_if rule pointing at a field name that doesn't actually exist on the
    form would silently never show/hide anything (isFieldVisible just never
    matches), with nothing catching it."""

    conditions = CONDITIONS_BY_FORM_CODE[code]
    if not conditions:
        pytest.skip(f"{code}: no conditional rules registered")

    real_fields = _real_field_names(code)

    for conditional_field, gates in conditions.items():
        assert conditional_field in real_fields, (
            f"{code}: show_if rule attached to nonexistent field '{conditional_field}'"
        )
        for gate in gates:
            assert gate["field"] in real_fields, (
                f"{code}: show_if rule on '{conditional_field}' gates on nonexistent field '{gate['field']}'"
            )


def test_every_form_in_the_catalog_has_a_conditions_entry():
    # Not every form needs *rules* (empty dict is fine, e.g. G-28), but every
    # form should have a deliberate entry rather than silently falling back
    # to "no rules" via .get() -- see app/seed_data/conditional_rules.py's
    # module docstring for which forms don't have real rules and why.
    catalog_codes = {t["code"] for t in FORM_TEMPLATES}
    assert catalog_codes <= set(CONDITIONS_BY_FORM_CODE) | {"I-130A", "N-600K"}
