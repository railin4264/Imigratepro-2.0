from pathlib import Path

from pypdf import PdfReader, PdfWriter


def fill_pdf_form(template_path: Path, output_path: Path, field_values: dict[str, str]) -> None:
    """Fill an AcroForm PDF's text/choice fields and write the result to output_path.

    USCIS forms ship with owner-password encryption that only restricts editing
    permissions (empty user password), so they open normally but must be
    decrypted with '' before pypdf will touch their form fields.
    """

    reader = PdfReader(str(template_path))
    if reader.is_encrypted:
        reader.decrypt("")

    writer = PdfWriter()
    writer.append(reader)

    non_empty_values = {k: v for k, v in field_values.items() if v}
    for page in writer.pages:
        writer.update_page_form_field_values(page, non_empty_values, auto_regenerate=False)

    if writer._root_object.get("/AcroForm"):
        writer.set_need_appearances_writer(True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
