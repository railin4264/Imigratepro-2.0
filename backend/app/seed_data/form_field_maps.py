# Autofill mappings from official USCIS AcroForm field names to our internal
# data paths (resolved by app.services.form_data.resolve_source against the
# context built by build_case_context).
#
# These cover the core biographic/address/contact fields -- name, DOB, country
# of birth, A-Number, mailing address, sex, marital status, SSN, phone/email --
# verified against the field names and page layout of each downloaded PDF (see
# backend/form_templates/). Every other
# field on the form is still part of the electronic form (see field_schema,
# loaded from app/seed_data/field_inventories/*.json, which lists all ~438-97
# fields with their official USCIS label) -- it's just not pre-filled
# automatically, and is left for the attorney/paralegal to complete in the
# form editor before generating the final PDF.

I_130_AUTOFILL = [
    {"pdf_field": "form1[0].#subform[0].Pt2Line4a_FamilyName[0]", "source": "petitioner.last_name"},
    {"pdf_field": "form1[0].#subform[0].Pt2Line4b_GivenName[0]", "source": "petitioner.first_name"},
    {"pdf_field": "form1[0].#subform[0].Pt2Line4c_MiddleName[0]", "source": "petitioner.middle_name"},
    {"pdf_field": "form1[0].#subform[0].#area[4].Pt2Line1_AlienNumber[0]", "source": "petitioner.a_number"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line7_CountryofBirth[0]", "source": "petitioner.country_of_birth"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line8_DateofBirth[0]", "source": "petitioner.date_of_birth"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line10_StreetNumberName[0]", "source": "petitioner.address_line"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line10_CityOrTown[0]", "source": "petitioner.city"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line10_State[0]", "source": "petitioner.state"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line10_ZipCode[0]", "source": "petitioner.zip_code"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line10_Country[0]", "source": "petitioner.country"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line4a_FamilyName[0]", "source": "beneficiary.last_name"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line4b_GivenName[0]", "source": "beneficiary.first_name"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line4c_MiddleName[0]", "source": "beneficiary.middle_name"},
    {"pdf_field": "form1[0].#subform[4].#area[6].Pt4Line1_AlienNumber[0]", "source": "beneficiary.a_number"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line8_CountryOfBirth[0]", "source": "beneficiary.country_of_birth"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line9_DateOfBirth[0]", "source": "beneficiary.date_of_birth"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line11_StreetNumberName[0]", "source": "beneficiary.address_line"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line11_CityOrTown[0]", "source": "beneficiary.city"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line11_State[0]", "source": "beneficiary.state"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line11_ZipCode[0]", "source": "beneficiary.zip_code"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line11_Country[0]", "source": "beneficiary.country"},
    # Petitioner -- sex, marital status (Part 2), SSN, and contact info (Part 6)
    {"pdf_field": "form1[0].#subform[1].Pt2Line9_Male[0]", "source": "petitioner.sex", "match_value": "male", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line9_Female[0]", "source": "petitioner.sex", "match_value": "female", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line17_Single[0]", "source": "petitioner.marital_status", "match_value": "single", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line17_Married[0]", "source": "petitioner.marital_status", "match_value": "married", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line17_Divorced[0]", "source": "petitioner.marital_status", "match_value": "divorced", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line17_Widowed[0]", "source": "petitioner.marital_status", "match_value": "widowed", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line17_Separated[0]", "source": "petitioner.marital_status", "match_value": "separated", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[1].Pt2Line17_Annulled[0]", "source": "petitioner.marital_status", "match_value": "annulled", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[0].Pt2Line11_SSN[0]", "source": "petitioner.ssn"},
    {"pdf_field": "form1[0].#subform[8].Pt6Line3_DaytimePhoneNumber[0]", "source": "petitioner.phone"},
    {"pdf_field": "form1[0].#subform[8].Pt6Line4_MobileNumber[0]", "source": "petitioner.mobile_phone"},
    {"pdf_field": "form1[0].#subform[8].Pt6Line5_Email[0]", "source": "petitioner.email"},
    # Beneficiary -- sex, marital status (Part 4), SSN, contact info
    {"pdf_field": "form1[0].#subform[4].Pt4Line9_Male[0]", "source": "beneficiary.sex", "match_value": "male", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line9_Female[0]", "source": "beneficiary.sex", "match_value": "female", "set_value": "/Y"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line18_MaritalStatus[3]", "source": "beneficiary.marital_status", "match_value": "single", "set_value": "/SNM"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line18_MaritalStatus[4]", "source": "beneficiary.marital_status", "match_value": "married", "set_value": "/M"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line18_MaritalStatus[5]", "source": "beneficiary.marital_status", "match_value": "divorced", "set_value": "/D"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line18_MaritalStatus[0]", "source": "beneficiary.marital_status", "match_value": "widowed", "set_value": "/W"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line18_MaritalStatus[2]", "source": "beneficiary.marital_status", "match_value": "separated", "set_value": "/S"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line18_MaritalStatus[1]", "source": "beneficiary.marital_status", "match_value": "annulled", "set_value": "/A"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line3_SSN[0]", "source": "beneficiary.ssn"},
    {"pdf_field": "form1[0].#subform[4].Pt4Line14_DaytimePhoneNumber[0]", "source": "beneficiary.phone"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line15_MobilePhoneNumber[0]", "source": "beneficiary.mobile_phone"},
    {"pdf_field": "form1[0].#subform[5].Pt4Line16_EmailAddress[0]", "source": "beneficiary.email"},
]

I_765_AUTOFILL = [
    {"pdf_field": "form1[0].Page1[0].Line1a_FamilyName[0]", "source": "beneficiary.last_name"},
    {"pdf_field": "form1[0].Page1[0].Line1b_GivenName[0]", "source": "beneficiary.first_name"},
    {"pdf_field": "form1[0].Page1[0].Line1c_MiddleName[0]", "source": "beneficiary.middle_name"},
    {"pdf_field": "form1[0].Page2[0].Line7_AlienNumber[0]", "source": "beneficiary.a_number"},
    {"pdf_field": "form1[0].Page3[0].Line19_DOB[0]", "source": "beneficiary.date_of_birth"},
    {"pdf_field": "form1[0].Page3[0].Line18c_CountryOfBirth[0]", "source": "beneficiary.country_of_birth"},
    {"pdf_field": "form1[0].Page2[0].Line4b_StreetNumberName[0]", "source": "beneficiary.address_line"},
    {"pdf_field": "form1[0].Page2[0].Pt2Line5_CityOrTown[0]", "source": "beneficiary.city"},
    {"pdf_field": "form1[0].Page2[0].Pt2Line5_State[0]", "source": "beneficiary.state"},
    {"pdf_field": "form1[0].Page2[0].Pt2Line5_ZipCode[0]", "source": "beneficiary.zip_code"},
    {"pdf_field": "form1[0].Page2[0].Line12b_SSN[0]", "source": "beneficiary.ssn"},
    {"pdf_field": "form1[0].Page4[0].Pt3Line3_DaytimePhoneNumber1[0]", "source": "beneficiary.phone"},
    {"pdf_field": "form1[0].Page4[0].Pt3Line4_MobileNumber1[0]", "source": "beneficiary.mobile_phone"},
    {"pdf_field": "form1[0].Page4[0].Pt3Line5_Email[0]", "source": "beneficiary.email"},
]

G_28_AUTOFILL = [
    {"pdf_field": "form1[0].#subform[0].Pt1Line2a_FamilyName[0]", "source": "attorney.last_name"},
    {"pdf_field": "form1[0].#subform[0].Pt1Line2b_GivenName[0]", "source": "attorney.first_name"},
    {"pdf_field": "form1[0].#subform[0].Pt2Line1b_BarNumber[0]", "source": "attorney.bar_number"},
    {"pdf_field": "form1[0].#subform[0].Pt2Line1d_NameofFirmOrOrganization[0]", "source": "attorney.firm_name"},
    {"pdf_field": "form1[0].#subform[0].Line3a_StreetNumber[0]", "source": "attorney.address_line"},
    {"pdf_field": "form1[0].#subform[0].Line3c_CityOrTown[0]", "source": "attorney.city"},
    {"pdf_field": "form1[0].#subform[0].Line3e_ZipCode[0]", "source": "attorney.zip_code"},
    {"pdf_field": "form1[0].#subform[0].Line4_DaytimeTelephoneNumber[0]", "source": "attorney.phone"},
    {"pdf_field": "form1[0].#subform[0].Line6_EMail[0]", "source": "attorney.email"},
    {"pdf_field": "form1[0].#subform[0].Line7_MobileTelephoneNumber[0]", "source": "attorney.mobile_phone"},
    {"pdf_field": "form1[0].#subform[1].Pt3Line5a_FamilyName[0]", "source": "beneficiary.last_name"},
    {"pdf_field": "form1[0].#subform[1].Pt3Line5b_GivenName[0]", "source": "beneficiary.first_name"},
    {"pdf_field": "form1[0].#subform[1].Pt3Line5c_MiddleName[0]", "source": "beneficiary.middle_name"},
    {"pdf_field": "form1[0].#subform[1].Pt3Line9_ANumber[0]", "source": "beneficiary.a_number"},
]

FORM_TEMPLATES = [
    {
        "code": "I-130",
        "name": "Petition for Alien Relative",
        "edition_date": "04/01/24",
        "pdf_template_path": "i-130.pdf",
        "inventory_file": "i-130.json",
        "autofill_map": I_130_AUTOFILL,
    },
    {
        "code": "I-765",
        "name": "Application for Employment Authorization",
        "edition_date": "08/21/25",
        "pdf_template_path": "i-765.pdf",
        "inventory_file": "i-765.json",
        "autofill_map": I_765_AUTOFILL,
    },
    {
        "code": "G-28",
        "name": "Notice of Entry of Appearance as Attorney or Accredited Representative",
        "edition_date": "09/17/18",
        "pdf_template_path": "g-28.pdf",
        "inventory_file": "g-28.json",
        "autofill_map": G_28_AUTOFILL,
    },
]
