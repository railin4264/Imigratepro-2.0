from pathlib import Path

from pypdf import PdfReader, PdfWriter


def fill_pdf_form(template_path: Path, output_path: Path, field_values: dict[str, str]) -> None:
    """Fill an AcroForm PDF's text/choice fields and write the result to output_path.

    USCIS forms ship with owner-password encryption that only restricts editing
    permissions (empty user password), so they open normally but must be
    decrypted with '' before pypdf will touch their form fields.

    Every USCIS form in this catalog is an Adobe XFA *hybrid* PDF: alongside the
    plain AcroForm fields pypdf fills below, the file also embeds an XFA XML
    packet that Adobe Acrobat/Reader uses *instead of* the AcroForm layer
    whenever it's present -- and pypdf has no XFA support, so that packet
    still holds the original blank template after filling. Left in place, the
    exact same output PDF looks correctly filled in a browser or Preview
    (which just render the AcroForm) but reverts to blank in Adobe Reader,
    which is what USCIS itself tells filers to use. Deleting /XFA from the
    written AcroForm forces every viewer, Adobe included, to fall back to the
    AcroForm layer -- the one pypdf actually filled.
    """

    reader = PdfReader(str(template_path))
    if reader.is_encrypted:
        reader.decrypt("")

    writer = PdfWriter()
    writer.append(reader)

    non_empty_values = {k: v for k, v in field_values.items() if v}
    for page in writer.pages:
        writer.update_page_form_field_values(page, non_empty_values, auto_regenerate=False)

    acro_form = writer._root_object.get("/AcroForm")
    if acro_form:
        writer.set_need_appearances_writer(True)
        acro_form_obj = acro_form.get_object()
        if "/XFA" in acro_form_obj:
            del acro_form_obj["/XFA"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
