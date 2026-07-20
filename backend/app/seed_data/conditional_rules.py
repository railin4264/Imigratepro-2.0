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

I_131_CONDITIONS = {
    # "2.A. Have you EVER before been issued a Reentry Permit or Refugee Travel
    # Document? (If you answered 'Yes,' provide the information in Item
    # Numbers 2.b. - 2.c. ...)"
    "form1[0].P7[0].P4_Line2b_DateIssued[0]": [
        {"field": "form1[0].P7[0].P4_Line2a_YesNo[0]", "equals": "/Y"},
    ],
    "form1[0].P7[0].P4_Line2c_Disposition[0]": [
        {"field": "form1[0].P7[0].P4_Line2a_YesNo[0]", "equals": "/Y"},
    ],
    # "3.A. Have you EVER been issued an Advance Parole Document? (If you
    # answered 'Yes,' please provide the information in Item Numbers 3.b. -
    # 3.c. ...)"
    "form1[0].P7[0].P4_Line3b_DateIssued[0]": [
        {"field": "form1[0].P7[0].P4_Line3a_YesNo[0]", "equals": "/Y"},
    ],
    "form1[0].P7[0].P4_Line3c_Disposition[0]": [
        {"field": "form1[0].P7[0].P4_Line3a_YesNo[0]", "equals": "/Y"},
    ],
    # "6.a. Are you currently outside the United States? ... 6.b./6.c. If you
    # answered 'Yes,' ..."
    "form1[0].#subform[9].P6_Line6b_CityOrTown[0]": [
        {"field": "form1[0].#subform[9].P6_Line6a_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[9].P6_Line6c_Country[0]": [
        {"field": "form1[0].#subform[9].P6_Line6a_YesNo[1]", "equals": "/Y"},
    ],
    # "If you checked the apartment, suite or floor box, enter the number
    # here" -- the near-universal address-unit-number pattern, repeated
    # per address block on this form.
    "form1[0].P5[0].Part2_Line3_AptSteFlrNumber[0]": [
        {"field": "form1[0].P5[0].Part2_Line3_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].P5[0].Part2_Line3_Unit[1]", "equals": "/ APT "},
        {"field": "form1[0].P5[0].Part2_Line3_Unit[2]", "equals": "/ FLR "},
    ],
    "form1[0].P5[0].Part2_Line4_AptSteFlrNumber[0]": [
        {"field": "form1[0].P5[0].Part2_Line4_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].P5[0].Part2_Line4_Unit[1]", "equals": "/ APT "},
        {"field": "form1[0].P5[0].Part2_Line4_Unit[2]", "equals": "/ FLR "},
    ],
    "form1[0].P6[0].P2_Line24_AptSteFlrNumber[0]": [
        {"field": "form1[0].P6[0].P2_Line24_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].P6[0].P2_Line24_Unit[1]", "equals": "/ APT "},
        {"field": "form1[0].P6[0].P2_Line24_Unit[2]", "equals": "/ FLR "},
    ],
    "form1[0].P6[0].P2_Line25_AptSteFlrNumber[0]": [
        {"field": "form1[0].P6[0].P2_Line25_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].P6[0].P2_Line25_Unit[1]", "equals": "/ APT "},
        {"field": "form1[0].P6[0].P2_Line25_Unit[2]", "equals": "/ FLR "},
    ],
    "form1[0].#subform[8].P4_Line9a_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[8].P4_Line9a_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[8].P4_Line9a_Unit[1]", "equals": "/ APT "},
        {"field": "form1[0].#subform[8].P4_Line9a_Unit[2]", "equals": "/ FLR "},
    ],
}

I_485_CONDITIONS = {
    # "Have you ever used any other date of birth? ... If you answered 'Yes,'
    # provide all other dates of birth."
    "form1[0].#subform[0].Pt1Line3A_OtherDOB[0]": [
        {"field": "form1[0].#subform[0].Pt1Line3_YN[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[0].Pt1Line3B_OtherDOB[0]": [
        {"field": "form1[0].#subform[0].Pt1Line3_YN[0]", "equals": "/Y"},
    ],
    # "5. Have you ever used, or been assigned, any other A-Number? ... If
    # you answered 'Yes,' Provide the A-Numbers."
    "form1[0].#subform[1].Pt1Line5A_ANumber[0]": [
        {"field": "form1[0].#subform[1].Pt1Line5_YN[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line5B_ANumber[0]": [
        {"field": "form1[0].#subform[1].Pt1Line5_YN[0]", "equals": "/Y"},
    ],
    # "18. Is this your current mailing address? ... If you answered 'No,'
    # provide your current mailing address."
    "form1[0].#subform[2].Pt1Line18_CurrentStreetNumberName[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentInCareOfName[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentUnit[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentUnit[1]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentUnit[2]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentAptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentCityOrTown[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentState[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentZipCode[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_YN[1]", "equals": "/N"},
    ],
    # "1. Have you EVER been a member of ... any organization ...? If you
    # answered 'Yes' to Item Number 1., complete Item Numbers 2. - 9."
    "form1[0].#subform[12].Pt9Line2_Organization1[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line3_CityTownOfBirth[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line3_State[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line3_Country[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line4_FamilyName[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line4_Involvement[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line5_DateFrom[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line5_DateTo[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[12].Pt9Line6_Organization2[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line7_CityTownOfBirth[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line7_State[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line7_Country[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line8_FamilyName[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line8_Involvement[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line9_DateFrom[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[13].Pt9Line9_DateTo[0]": [
        {"field": "form1[0].#subform[12].Pt8Line1_YesNo[1]", "equals": "/Y"},
    ],
    # "If you checked the apartment, suite or floor box, enter the number here."
    "form1[0].#subform[2].Pt1Line18US_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18US_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[2].Pt1Line18US_Unit[1]", "equals": "/ FLR "},
        {"field": "form1[0].#subform[2].Pt1Line18US_Unit[2]", "equals": "/ APT "},
    ],
    "form1[0].#subform[2].Pt1Line18_CurrentAptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[2].Pt1Line18_CurrentUnit[0]", "equals": "/ APT "},
        {"field": "form1[0].#subform[2].Pt1Line18_CurrentUnit[1]", "equals": "/ STE "},
        {"field": "form1[0].#subform[2].Pt1Line18_CurrentUnit[2]", "equals": "/ FLR "},
    ],
    "form1[0].#subform[3].Pt1Line18_PriorAddress_Number[0]": [
        {"field": "form1[0].#subform[3].Pt1Line18_PriorAddress_Unit[0]", "equals": "/APT"},
        {"field": "form1[0].#subform[3].Pt1Line18_PriorAddress_Unit[1]", "equals": "/STE"},
        {"field": "form1[0].#subform[3].Pt1Line18_PriorAddress_Unit[2]", "equals": "/FLR"},
    ],
    "form1[0].#subform[3].Pt1Line18_RecentNumber[0]": [
        {"field": "form1[0].#subform[3].Pt1Line18_RecentUnit[0]", "equals": "/APT"},
        {"field": "form1[0].#subform[3].Pt1Line18_RecentUnit[1]", "equals": "/STE"},
        {"field": "form1[0].#subform[3].Pt1Line18_RecentUnit[2]", "equals": "/FLR"},
    ],
    "form1[0].#subform[8].P4Line7_Number[0]": [
        {"field": "form1[0].#subform[8].P4Line7_Unit[0]", "equals": "/APT"},
        {"field": "form1[0].#subform[8].P4Line7_Unit[1]", "equals": "/STE"},
        {"field": "form1[0].#subform[8].P4Line7_Unit[2]", "equals": "/FLR"},
    ],
    "form1[0].#subform[8].P4Line8_Number[0]": [
        {"field": "form1[0].#subform[8].P4Line8_Unit[0]", "equals": "/APT"},
        {"field": "form1[0].#subform[8].P4Line8_Unit[1]", "equals": "/STE"},
        {"field": "form1[0].#subform[8].P4Line8_Unit[2]", "equals": "/FLR"},
    ],
    "form1[0].#subform[9].P6Line8_Number[0]": [
        {"field": "form1[0].#subform[9].P6Line8_Unit[0]", "equals": "/APT"},
        {"field": "form1[0].#subform[9].P6Line8_Unit[1]", "equals": "/STE"},
        {"field": "form1[0].#subform[9].P6Line8_Unit[2]", "equals": "/FLR"},
    ],
}

I_589_CONDITIONS = {
    # Part B -- each numbered Yes/No question has its own "If Yes, Explain"
    # narrative field right after it.
    "form1[0].#subform[7].PBL2_TextField[0]": [
        {"field": "form1[0].#subform[7].ckboxyn2[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[7].PBL3A_TextField[0]": [
        {"field": "form1[0].#subform[7].ckboxyn3a[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[7].PBL3B_TextField[0]": [
        {"field": "form1[0].#subform[7].ckboxyn3b[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[7].PB4_TextField[0]": [
        {"field": "form1[0].#subform[7].ckboxyn4[0]", "equals": "/Y"},
    ],
    # Part C, same pattern.
    "form1[0].#subform[8].PCL1_TextField[0]": [
        {"field": "form1[0].#subform[8].ckboxync1[0]", "equals": "/Y"},
    ],
    # "2.A. and 2.B. If Yes, to either or both questions ..." -- either gate works.
    "form1[0].#subform[8].PCL2B_TextField[0]": [
        {"field": "form1[0].#subform[8].ckboxync2a[0]", "equals": "/Y"},
        {"field": "form1[0].#subform[8].ckboxync2b[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[8].PCL3_TextField[0]": [
        {"field": "form1[0].#subform[8].ckboxync3[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[9].PCL4_TextField[0]": [
        {"field": "form1[0].#subform[9].PCckboxyn4[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[9].PCL5_TextField[0]": [
        {"field": "form1[0].#subform[9].ckboxync5[0]", "equals": "/Y"},
    ],
    "form1[0].#subform[9].PCL6_TextField[0]": [
        {"field": "form1[0].#subform[9].ckboxync6[0]", "equals": "/Y"},
    ],
}

I_751_CONDITIONS = {
    # "16. Is your physical address different than your mailing address? ...
    # If you answered 'Yes' to Item Number 16., provide your physical
    # address below."
    "form1[0].#subform[1].Pt1Line17_InCareofName[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_StreetNumberName[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_Unit[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_Unit[1]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_Unit[2]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_CityOrTown[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_State[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Pt1Line17_ZipCode[0]": [
        {"field": "form1[0].#subform[1].Line16_Checkbox[1]", "equals": "/Y"},
    ],
}

I_864_CONDITIONS = {
    # "3. Is your current mailing address the same as your physical address?
    # ... If you answered 'No' to Item Number 3., provide your physical
    # address in Item Number 4."
    "form1[0].#subform[1].P4_Line4a_StreetNumberName[0]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4b_Unit[0]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4b_Unit[1]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4b_Unit[2]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4c_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4d_CityOrTown[0]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4e_State[0]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
    "form1[0].#subform[1].P4_Line4f_ZipCode[0]": [
        {"field": "form1[0].#subform[1].P1_Line3_Checkbox[1]", "equals": "/N"},
    ],
}

I_90_CONDITIONS = {
    # "1. Are you requesting an accommodation because of your disabilities
    # and/or impairments? ... Select Yes."
    "form1[0].#subform[2].P4_checkbox1a[0]": [
        {"field": "form1[0].#subform[2].P4_checkbox1[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[3].P4_checkbox1b[0]": [
        {"field": "form1[0].#subform[2].P4_checkbox1[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[3].P4_checkbox1c[0]": [
        {"field": "form1[0].#subform[2].P4_checkbox1[1]", "equals": "/Y"},
    ],
}

N_336_CONDITIONS = {
    # "If you checked the apartment, suite or floor box, enter the number here."
    "form1[0].#subform[0].Pt1Line5_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[0].Pt1Line5_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[0].Pt1Line5_Unit[1]", "equals": "/ FLR "},
        {"field": "form1[0].#subform[0].Pt1Line5_Unit[2]", "equals": "/ APT "},
    ],
    "form1[0].#subform[1].Pt1Line6_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[1].Pt1Line6_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[1].Pt1Line6_Unit[1]", "equals": "/ FLR "},
        {"field": "form1[0].#subform[1].Pt1Line6_Unit[2]", "equals": "/ APT "},
    ],
    "form1[0].#subform[4].Pt6Line3_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[4].Pt6Line3_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[4].Pt6Line3_Unit[1]", "equals": "/ FLR "},
        {"field": "form1[0].#subform[4].Pt6Line3_Unit[2]", "equals": "/ APT "},
    ],
    "form1[0].#subform[5].Pt7Line3_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[5].Pt7Line3_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[5].Pt7Line3_Unit[1]", "equals": "/ FLR "},
        {"field": "form1[0].#subform[5].Pt7Line3_Unit[2]", "equals": "/ APT "},
    ],
}

N_565_CONDITIONS = {
    "form1[0].#subform[1].P2Line3_AptSteFlrNumber[0]": [
        {"field": "form1[0].#subform[1].P2Line3_Unit[0]", "equals": "/ STE "},
        {"field": "form1[0].#subform[1].P2Line3_Unit[1]", "equals": "/ APT "},
        {"field": "form1[0].#subform[1].P2Line3_Unit[2]", "equals": "/ FLR "},
    ],
}

N_400_CONDITIONS = {
    # "3. Would you like to legally change your name? If you answered
    # 'Yes,' type or print the new name you would like to use."
    "form1[0].#subform[1].Part2Line3_FamilyName[0]": [
        {"field": "form1[0].#subform[1].P2_Line34_NameChange[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Part2Line4a_GivenName[0]": [
        {"field": "form1[0].#subform[1].P2_Line34_NameChange[1]", "equals": "/Y"},
    ],
    "form1[0].#subform[1].Part2Line4a_MiddleName[0]": [
        {"field": "form1[0].#subform[1].P2_Line34_NameChange[1]", "equals": "/Y"},
    ],
}

N_470_CONDITIONS = {
    # "2. If you answered 'Yes' to Item Number 1., will those family members
    # reside with you outside the United States? ... If you answered 'Yes,'
    # provide the information below for each ... family member."
    "form1[0].#subform[2].Line1a_FamilyName[0]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1b_GivenName[0]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1c_MiddleName[0]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line19g_AlienNumber[0]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1a_FamilyName[1]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1b_GivenName[1]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1c_MiddleName[1]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line19g_AlienNumber[1]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1a_FamilyName[2]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1b_GivenName[2]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line1c_MiddleName[2]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
    "form1[0].#subform[2].Line19g_AlienNumber[2]": [{"field": "form1[0].#subform[2].Pt5Line2_Yes[2]", "equals": "/Y"}],
}

N_600_CONDITIONS = {
    # "20. Were you adopted? If you answered 'Yes' to Item Number 20.,
    # complete Item Numbers 20.A. - 20.E."
    "form1[0].#subform[6].Pt2Line17A_City[0]": [{"field": "form1[0].#subform[6].P2_Line17_Adopted[1]", "equals": "/Y"}],
    "form1[0].#subform[6].Pt2Line17A_State[0]": [{"field": "form1[0].#subform[6].P2_Line17_Adopted[1]", "equals": "/Y"}],
    "form1[0].#subform[6].Pt2Line17A_Country[0]": [{"field": "form1[0].#subform[6].P2_Line17_Adopted[1]", "equals": "/Y"}],
    "form1[0].#subform[6].Pt2Line17B_AdoptionDate[0]": [{"field": "form1[0].#subform[6].P2_Line17_Adopted[1]", "equals": "/Y"}],
    "form1[0].#subform[6].Pt2Line17C_LegalCustodyDate[0]": [{"field": "form1[0].#subform[6].P2_Line17_Adopted[1]", "equals": "/Y"}],
    "form1[0].#subform[6].Pt2Line17D_PhysicalCustody[0]": [{"field": "form1[0].#subform[6].P2_Line17_Adopted[1]", "equals": "/Y"}],
}

CONDITIONS_BY_FORM_CODE = {
    "I-130": I_130_CONDITIONS,
    "I-765": I_765_CONDITIONS,
    "G-28": {},
    "I-131": I_131_CONDITIONS,
    "I-485": I_485_CONDITIONS,
    "I-589": I_589_CONDITIONS,
    "I-751": I_751_CONDITIONS,
    "I-864": I_864_CONDITIONS,
    "I-90": I_90_CONDITIONS,
    "N-336": N_336_CONDITIONS,
    "N-565": N_565_CONDITIONS,
    "N-400": N_400_CONDITIONS,
    "N-470": N_470_CONDITIONS,
    "N-600": N_600_CONDITIONS,
    # Family/naturalization forms -- no show_if rules curated yet (deliberately
    # {}, same as G-28, not an oversight; see this dict's entry above and the
    # module docstring for what "no rules" means here).
    "I-129F": {},
    "I-360": {},
    "N-300": {},
    "N-426": {},
    "N-644": {},
    "N-648": {},
    "I-601": {},
    "I-601A": {},
    "I-612": {},
    "AR-11": {},
    "EOIR-29": {},
    "G-1041": {},
    "G-1041A": {},
    "G-1055": {},
    "G-1145": {},
    "G-1256": {},
    "G-1450": {},
    "G-1566": {},
    "G-1650": {},
    "G-1651": {},
    "G-28I": {},
    "G-325A": {},
    "G-325R": {},
    "G-845": {},
    "G-884": {},
    "I-102": {},
    "I-129": {},
    "I-129S": {},
    "I-131A": {},
    "I-134": {},
    "I-140": {},
    "I-140G": {},
    "I-191": {},
    "I-192": {},
    "I-193": {},
    "I-212": {},
    "I-290B": {},
    "I-356": {},
    "I-361": {},
    "I-363": {},
    "I-407": {},
    "I-508": {},
    "I-526": {},
    "I-526E": {},
    "I-539": {},
    "I-566": {},
    "I-600": {},
    "I-600A": {},
    "I-602": {},
    "I-687": {},
    "I-690": {},
    "I-693": {},
    "I-694": {},
    "I-698": {},
    "I-730": {},
    "I-765V": {},
    "I-800": {},
    "I-800A": {},
    "I-817": {},
    "I-821": {},
    "I-821D": {},
    "I-824": {},
    "I-829": {},
    "I-864A": {},
    "I-865": {},
    "I-881": {},
    "I-9": {},
    "I-905": {},
    "I-907": {},
    "I-910": {},
    "I-912": {},
    "I-914": {},
    "I-918": {},
    "I-929": {},
    "I-941": {},
    "I-945": {},
    "I-956": {},
    "I-956F": {},
    "I-956G": {},
    "I-956H": {},
    "I-956K": {},
}
