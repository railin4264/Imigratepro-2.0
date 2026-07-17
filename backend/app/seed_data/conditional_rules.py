# Conditional visibility rules for the electronic form editor: a field is
# only shown once one of its `show_if` conditions is satisfied by the current
# answers. This is UI-only -- it does not affect what gets written to the PDF
# beyond what the editor lets the user see and fill in.
#
# Every rule here is verified directly against the official USCIS tooltip
# text for the *gate* field (e.g. "2. If you are filing this petition for
# your child or parent, select the box that describes your relationship"),
# not guessed from field naming alone. Fields with no explicit "if you
# answered X" / "if applicable" language in their own label are left
# unconditional rather than assumed.

I_130_CONDITIONS = {
    # "2. If you are filing this petition for your child or parent, select..."
    "form1[0].#subform[0].Pt1Line2_InWedlock[0]": [
        {"field": "form1[0].#subform[0].Pt1Line1_Child[0]", "equals": "/Y"},
        {"field": "form1[0].#subform[0].Pt1Line1_Parent[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[0].Pt1Line2_AdoptedChild[0]": [
        {"field": "form1[0].#subform[0].Pt1Line1_Child[0]", "equals": "/Y"},
        {"field": "form1[0].#subform[0].Pt1Line1_Parent[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[0].Pt1Line2_Stepchild[0]": [
        {"field": "form1[0].#subform[0].Pt1Line1_Child[0]", "equals": "/Y"},
        {"field": "form1[0].#subform[0].Pt1Line1_Parent[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[0].Pt1Line2_OutOfWedlock[0]": [
        {"field": "form1[0].#subform[0].Pt1Line1_Child[0]", "equals": "/Y"},
        {"field": "form1[0].#subform[0].Pt1Line1_Parent[0]", "equals": "/Y"},
    ],
    # "3. If the beneficiary is your brother/sister, are you related by adoption?"
    "form1[0].#subform[0].Pt1Line3_Yes[0]": [
        {"field": "form1[0].#subform[0].Pt1Line1_Siblings[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[0].Pt1Line3_No[0]": [
        {"field": "form1[0].#subform[0].Pt1Line1_Siblings[0]", "equals": "/Y"},
    ],
    # "11. Is your current mailing address the same as your physical address?"
    # -> physical address (Line 12) only needed if the answer is No.
    "form1[0].#subform[1].Pt2Line12_StreetNumberName[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_Unit[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_Unit[1]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_Unit[2]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_CityOrTown[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_State[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_ZipCode[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_Province[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_Country[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
    "form1[0].#subform[1].Pt2Line12_PostalCode[0]": [
        {"field": "form1[0].#subform[1].Pt2Line11_No[0]", "equals": "/N"},
    ],
}

I_765_CONDITIONS = {
    # "6. Is your current mailing address the same as your physical address?"
    # Part2Line5_Checkbox[0] = No -> physical address (Line 7) needed.
    "form1[0].Page2[0].Pt2Line7_StreetNumberName[0]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_Unit[0]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_Unit[1]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_Unit[2]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_AptSteFlrNumber[0]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_CityOrTown[0]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_State[0]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
    "form1[0].Page2[0].Pt2Line7_ZipCode[0]": [
        {"field": "form1[0].Page2[0].Part2Line5_Checkbox[0]", "equals": "/N"},
    ],
}

CONDITIONS_BY_FORM_CODE = {
    "I-130": I_130_CONDITIONS,
    "I-765": I_765_CONDITIONS,
    "G-28": {},
}
