from pypdf import PdfReader

from app.core.config import settings
from app.services.pdf_filler import fill_pdf_form

# G-28 is the smallest template in the catalog -- fast to read/write repeatedly.
_TEMPLATE = settings.FORM_TEMPLATES_DIR / "g-28.pdf"


def test_template_is_an_xfa_hybrid_form():
    # Sanity check the premise of the regression test below: if USCIS ever
    # ships a plain-AcroForm G-28 (no XFA), the fix this file guards becomes
    # a no-op for this file and the test should be pointed at one that still
    # reproduces the bug.
    reader = PdfReader(str(_TEMPLATE))
    acro_form = reader.trailer["/Root"].get("/AcroForm")
    assert acro_form is not None
    assert acro_form.get_object().get("/XFA") is not None


def test_fill_pdf_form_strips_xfa_so_adobe_reader_shows_the_acroform_values(tmp_path):
    # Every USCIS template is an XFA hybrid: Adobe Acrobat/Reader renders the
    # XFA packet instead of the AcroForm whenever it's present, and pypdf
    # can't update XFA -- so a filled PDF that still carries the original
    # (blank) XFA packet looks correctly filled in a browser but reverts to
    # blank in Adobe Reader, the tool USCIS itself tells filers to use.
    reader = PdfReader(str(_TEMPLATE))
    # get_fields() includes non-leaf group nodes (e.g. "form1[0]") that have
    # no /V to set -- pick an actual fillable text field.
    field_name = next(name for name, field in reader.get_fields().items() if field.get("/FT") == "/Tx")

    output_path = tmp_path / "filled.pdf"
    fill_pdf_form(_TEMPLATE, output_path, {field_name: "Test Value"})

    result = PdfReader(str(output_path))
    acro_form = result.trailer["/Root"].get("/AcroForm")
    assert acro_form is not None, "AcroForm must survive -- this is the layer that's actually filled"
    assert acro_form.get_object().get("/XFA") is None, "stale XFA packet must be removed"

    filled_fields = result.get_fields()
    assert filled_fields[field_name].get("/V") == "Test Value"
