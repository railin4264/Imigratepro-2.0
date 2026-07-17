// Reference Spanish translation for the recurring USCIS form vocabulary.
//
// USCIS forms must be filed in English -- this is NOT an official translation
// of the form, just a phrase-substitution aid to help a Spanish-speaking
// preparer or client understand what a field is asking for. It works by
// splitting each field's official label (the /TU tooltip we extracted from
// the PDF) into sentence-like segments and looking each one up here; segments
// we don't recognize (line numbers, letters, form-specific edge cases) are
// left in English rather than guessed at.
const PHRASES: Record<string, string> = {
  "Other fields": "Otros campos",
  // Part / section headers
  "Part 1.": "Parte 1.",
  "Part 2.": "Parte 2.",
  "Part 3.": "Parte 3.",
  "Part 4.": "Parte 4.",
  "Part 5.": "Parte 5.",
  "Part 6.": "Parte 6.",
  "Part 7.": "Parte 7.",
  "Part 8.": "Parte 8.",
  "Part 9.": "Parte 9.",
  "Information About You (Petitioner).": "Información sobre usted (peticionario).",
  "Information About You.": "Información sobre usted.",
  "Information About Beneficiary.": "Información sobre el beneficiario.",
  "Information About Your Parents.": "Información sobre sus padres.",
  "Information About Beneficiary's Family.": "Información sobre la familia del beneficiario.",
  "Information About Attorney or Accredited Representative.": "Información sobre el abogado o representante acreditado.",
  "Eligibility Information for Attorney or Accredited Representative.":
    "Información de elegibilidad del abogado o representante acreditado.",
  "Notice of Appearance as Attorney or Accredited Representative.":
    "Aviso de comparecencia como abogado o representante acreditado.",
  "Additional Information.": "Información adicional.",
  "Additional Information About Beneficiary.": "Información adicional sobre el beneficiario.",
  "Other Information.": "Otra información.",
  "Other Information About Beneficiary.": "Otra información sobre el beneficiario.",
  "Biographic Information.": "Información biográfica.",
  "Mailing Address.": "Dirección postal.",
  "Address History.": "Historial de direcciones.",
  "Employment History.": "Historial de empleo.",
  "Other Address and Contact Information.": "Otra dirección e información de contacto.",
  "Your Marital Information.": "Su información marital.",
  "Beneficiary's Marital Information.": "Información marital del beneficiario.",
  "Beneficiary's Employment Information.": "Información de empleo del beneficiario.",
  "Interpreter's Contact Information, Certification, and Signature.":
    "Información de contacto, certificación y firma del intérprete.",
  "Interpreter's Mailing Address.": "Dirección postal del intérprete.",
  "Preparer's Mailing Address.": "Dirección postal del preparador.",
  "Contact Information, Declaration, and Signature of the Person Preparing this Application, If Other Than the Applicant.":
    "Información de contacto, declaración y firma de la persona que preparó esta solicitud, si no es el solicitante.",
  "Contact Information, Declaration, and Signature of the Person Preparing this Petition, if Other Than the Petitioner.":
    "Información de contacto, declaración y firma de la persona que preparó esta petición, si no es el peticionario.",
  "Sex.": "Sexo.",
  "Select only one box.": "Seleccione solo una casilla.",
  "Select all applicable items.": "Seleccione todos los elementos que apliquen.",

  // Leaf instructions ("Enter ..." / "Select ...")
  "Enter as 2 digit month, 2 digit day and 4 digit year.":
    "Ingrese mes de 2 dígitos, día de 2 dígitos y año de 4 dígitos.",
  "Enter as 2-digit Month, 2-digit Day, and 4-digit Year.":
    "Ingrese mes de 2 dígitos, día de 2 dígitos y año de 4 dígitos.",
  "Enter the 2-digit Month, 2-digit Day and 4-digit Year.":
    "Ingrese mes de 2 dígitos, día de 2 dígitos y año de 4 dígitos.",
  "Enter Family Name (Last Name).": "Ingrese el apellido.",
  "Enter Given Name (First Name).": "Ingrese el primer nombre.",
  "Enter  Family Name, Last Name.": "Ingrese el apellido.",
  "Enter  Given Name, First Name.": "Ingrese el primer nombre.",
  "Enter Middle Name.": "Ingrese el segundo nombre.",
  "Enter City or Town.": "Ingrese la ciudad o pueblo.",
  "Enter Street Number and Name.": "Ingrese el número y nombre de la calle.",
  "Enter Province.": "Ingrese la provincia.",
  "Enter the Province.": "Ingrese la provincia.",
  "Enter Country.": "Ingrese el país.",
  "Enter the Country.": "Ingrese el país.",
  "Enter Apartment, Suite or Floor Number.": "Ingrese el número de apartamento, suite o piso.",
  "Enter Apartment, Suite or Floor number.": "Ingrese el número de apartamento, suite o piso.",
  "Enter Page Number.": "Ingrese el número de página.",
  "Enter Part Number.": "Ingrese el número de parte.",
  "Enter Item Number.": "Ingrese el número de artículo.",
  "Enter Postal Code.": "Ingrese el código postal.",
  "Enter the Postal Code.": "Ingrese el código postal.",
  "Enter Zip Code.": "Ingrese el código postal (ZIP).",
  "Enter ZIP Code.": "Ingrese el código postal (ZIP).",
  "Enter Additional Information.": "Ingrese información adicional.",
  "Enter additional information.": "Ingrese información adicional.",
  "Enter Date of Birth.": "Ingrese la fecha de nacimiento.",
  "Enter Country of Birth.": "Ingrese el país de nacimiento.",
  "Enter Relationship.": "Ingrese el parentesco.",
  "Enter Date of Signature.": "Ingrese la fecha de la firma.",
  "Select Male.": "Seleccione Masculino.",
  "Select Female.": "Seleccione Femenino.",
  "Enter Date From.": "Ingrese la fecha de inicio.",
  "Enter Date To.": "Ingrese la fecha de fin.",
  "Enter Date Marriage Ended.": "Ingrese la fecha en que terminó el matrimonio.",
  "Enter Date of Current Marriage (if currently married).": "Ingrese la fecha del matrimonio actual (si está casado/a).",
  "Enter Alien Registration Number (A.": "Ingrese el número de registro de extranjero (A-Number).",
  "Enter U S C I S Online Account Number, if any.": "Ingrese el número de cuenta en línea de USCIS, si tiene uno.",
  "Enter City / Town / Village of Birth.": "Ingrese la ciudad/pueblo/aldea de nacimiento.",
  "Enter City / Town / Village of Residence.": "Ingrese la ciudad/pueblo/aldea de residencia.",
  "Enter Country of Residence.": "Ingrese el país de residencia.",
  "Enter Class of Admission.": "Ingrese la clase de admisión.",
  "Enter Name of Employer / Company.": "Ingrese el nombre del empleador o empresa.",
  "Enter Your Occupation.": "Ingrese su ocupación.",
  "Enter Language.": "Ingrese el idioma.",
  "Enter Daytime Telephone Number.": "Ingrese el número de teléfono diurno.",
  "Enter Mobile Telephone Number, if any.": "Ingrese el número de celular, si tiene uno.",
  "Enter Email Address, if any.": "Ingrese el correo electrónico, si tiene uno.",
  "Enter Interpreter's Given Name (First Name).": "Ingrese el primer nombre del intérprete.",
  "Enter Interpreter's Family Name (Last Name).": "Ingrese el apellido del intérprete.",
  "Enter Interpreter's Daytime Telephone Number.": "Ingrese el número de teléfono diurno del intérprete.",
  "Enter Preparer's Given Name (First Name).": "Ingrese el primer nombre del preparador.",
  "Enter Preparer's Family Name (Last Name).": "Ingrese el apellido del preparador.",
  "Enter Preparer's Daytime Telephone Number.": "Ingrese el número de teléfono diurno del preparador.",
  "Enter Certificate Number.": "Ingrese el número de certificado.",
  "Enter Date of Issuance.": "Ingrese la fecha de emisión.",
  "Enter Place of Issuance.": "Ingrese el lugar de emisión.",
  "Enter Date of Admission.": "Ingrese la fecha de admisión.",
  "Enter In Care Of Name.": 'Ingrese el nombre "a cargo de" (c/o).',
  "Enter Volag Number, if any.": "Ingrese el número Volag, si tiene uno.",
  "Enter Attorney State Bar Number, if applicable.": "Ingrese el número de colegiado (bar number), si aplica.",
  "Select Apartment.": "Seleccione Apartamento.",
  "Select Suite.": "Seleccione Suite.",
  "Select Floor.": "Seleccione Piso.",
  "Select Designated Floor.": "Seleccione Piso designado.",
  "Select State from List of States.": "Seleccione el estado de la lista.",
  "Select state from list of states.": "Seleccione el estado de la lista.",
  "Select Married.": "Seleccione Casado/a.",
  "Select Divorced.": "Seleccione Divorciado/a.",
  "Select Widowed.": "Seleccione Viudo/a.",
  "Select Annulled.": "Seleccione Anulado.",
  "Select Separated.": "Seleccione Separado/a.",
  "Select Single, Never Married.": "Seleccione Soltero/a (nunca casado/a).",
  "Select Spouse.": "Seleccione Cónyuge.",
  "Select Brother / Sister.": "Seleccione Hermano/a.",
  "Select Parent.": "Seleccione Padre/Madre.",
  "Select Parents.": "Seleccione Padres.",
  "Select Child.": "Seleccione Hijo/a.",
  "Select Stepchild / Stepparent.": "Seleccione Hijastro/a o Padrastro/Madrastra.",
  "Select Lawful Permanent Resident.": "Seleccione Residente Permanente Legal.",
  "Select Birth in the United States.": "Seleccione Nacimiento en Estados Unidos.",
  "Select Naturalization.": "Seleccione Naturalización.",
  "Select Hispanic or Latino.": "Seleccione Hispano o Latino.",
  "Select Not Hispanic or Latino.": "Seleccione No Hispano o Latino.",
  "Select White.": "Seleccione Blanco.",
  "Select Black.": "Seleccione Negro.",
  "Select Brown.": "Seleccione Trigueño.",
  "Select Gray.": "Seleccione Canoso.",
  "Select Unknown / Other.": "Seleccione Desconocido / Otro.",
  "Enter Pounds.": "Ingrese libras.",
  "Enter 9 digit number.": "Ingrese un número de 9 dígitos.",
  "Enter 13 Characters.": "Ingrese 13 caracteres.",

  // More section / subsection headers
  "Additional Information About You (Petitioner).": "Información adicional sobre usted (peticionario).",
  "Employer 1.": "Empleador 1.",
  "Employer 2.": "Empleador 2.",
  "Physical Address 1.": "Dirección física 1.",
  "Physical Address 2.": "Dirección física 2.",
  "Physical Address.": "Dirección física.",
  "Beneficiary's Physical Address.": "Dirección física del beneficiario.",
  "Relationship (You are the Petitioner.": "Parentesco (usted es el peticionario.",
  "Your relative is the Beneficiary).": "Su familiar es el beneficiario).",
  "Current Marital Status.": "Estado civil actual.",
  "Marital Status.": "Estado civil.",
  "Information About Your Eligibility Category.": "Información sobre su categoría de elegibilidad.",
  "Eligibility Category.": "Categoría de elegibilidad.",
  "Your U.S.": "Su",
  "U.S.": "EE. UU.",
  "Embassy or U.S.": "Embajada o de EE. UU.",
  "Select U.S.": "Seleccione EE. UU.",
  "Enter U.S.": "Ingrese EE. UU.",
  "Applicant's Statement, Contact Information, Declaration, Certification, and Signature.":
    "Declaración del solicitante, información de contacto, certificación y firma.",
  "Address of Attorney or Accredited Representative.": "Dirección del abogado o representante acreditado.",
  "Mailing Address of Client.": "Dirección postal del cliente.",
  "Provide all other names you have ever used, including aliases, maiden name, and nicknames.":
    "Indique todos los otros nombres que haya usado, incluyendo alias, apellido de soltera y apodos.",
  "Beneficiary's Entry Information.": "Información de entrada del beneficiario.",
  "Petitioner's Statement, Contact Information, Declaration, and Signature.":
    "Declaración del peticionario, información de contacto, declaración y firma.",
  "If you need extra space to complete this section, use the space provided in Part 6.":
    "Si necesita más espacio para completar esta sección, use el espacio provisto en la Parte 6.",
  "Information About Your Last Arrival in the United States.":
    "Información sobre su última entrada a Estados Unidos.",
  "Parent One's Information.": "Información del primer padre/madre.",
  "Parent Two's Information.": "Información del segundo padre/madre.",
  "Full Name of Parent One.": "Nombre completo del primer padre/madre.",
  "Full Name of Parent Two.": "Nombre completo del segundo padre/madre.",
  "Eye Color (Select only one box).": "Color de ojos (seleccione solo una casilla).",
  "Hair Color (Select only one box).": "Color de cabello (seleccione solo una casilla).",
  "Other Names Used.": "Otros nombres usados.",
  "Other Names Used, if any.": "Otros nombres usados, si aplica.",
  "Names of All Your Spouses, if any.": "Nombres de todos sus cónyuges, si aplica.",
  "Names of Beneficiary's Spouses, if any.": "Nombres de los cónyuges del beneficiario, si aplica.",
  "Spouse 1.": "Cónyuge 1.",
  "Spouse 2.": "Cónyuge 2.",
  "Preparer's Statement.": "Declaración del preparador.",
  "This signature field can not be signed with a digital signature and the signee's name can not be typewritten into this space.":
    "Este campo de firma no se puede firmar digitalmente ni escribir a máquina el nombre del firmante en este espacio.",
  "This is a protected field.": "Este es un campo protegido.",
  "This is a read only field.": "Este es un campo de solo lectura.",
  "This field pre-populates from page 1.": "Este campo se completa automáticamente desde la página 1.",
  "This field is pre-populated from Part 3.": "Este campo se completa automáticamente desde la Parte 3.",
  "Print and sign in ink.": "Imprima y firme con tinta.",
  "This appearance relates to immigration matters before (select only one box).":
    "Esta comparecencia se relaciona con asuntos migratorios ante (seleccione solo una casilla).",
  "Person 1.": "Persona 1.",
  "Person 2.": "Persona 2.",
  "Person 3.": "Persona 3.",
  "Person 4.": "Persona 4.",
  "Person 5.": "Persona 5.",
  "Relative 1.": "Familiar 1.",
  "Relative 2.": "Familiar 2.",
  "Interpreter's Signature.": "Firma del intérprete.",
  "Interpreter's Contact Information.": "Información de contacto del intérprete.",
  "Preparer's Contact Information.": "Información de contacto del preparador.",
  "Preparer's Signature.": "Firma del preparador.",
  "Preparer's Full Name.": "Nombre completo del preparador.",
  "Information About Client (Applicant, Petitioner, Requestor, Beneficiary or Derivative, Respondent, or Authorized Signatory for an Entity).":
    "Información sobre el cliente (solicitante, peticionario, requirente, beneficiario o derivado, demandado, o firmante autorizado de una entidad).",
  "Race (Select all applicable boxes).": "Raza (seleccione todas las casillas que apliquen).",
  "Ethnicity (Select only one box).": "Etnia (seleccione solo una casilla).",
  "Petitioner's Statement.": "Declaración del peticionario.",
  "Applicant's Statement.": "Declaración del solicitante.",
  "I enter my appearance as an attorney or accredited representative at the request of the, (select only one box).":
    "Presento mi comparecencia como abogado o representante acreditado a solicitud de, (seleccione solo una casilla).",
  "Signature of Attorney or Accredited Representative.": "Firma del abogado o representante acreditado.",
  "Client's Consent to Representation and Signature.": "Consentimiento del cliente a la representación y firma.",
  "Client's Contact Information.": "Información de contacto del cliente.",
  "Signature of Client or Authorized Signatory for an Entity.":
    "Firma del cliente o firmante autorizado de una entidad.",
  "To be completed by an attorney or accredited representative, if any.":
    "Debe completarlo un abogado o representante acreditado, si aplica.",
  "I am filing this petition for my (Select only one box).":
    "Presento esta petición para mi (seleccione solo una casilla).",
  "If you are filing this petition for your child or parent, select the box that describes your relationship (Select only one box).":
    "Si presenta esta petición para su hijo/a o padre/madre, seleccione la casilla que describe su relación (seleccione solo una casilla).",
  "Place of Your Current Marriage, if married.": "Lugar de su matrimonio actual, si está casado/a.",
  "Place of Beneficiary's Current Marriage, if married.":
    "Lugar del matrimonio actual del beneficiario, si está casado/a.",
  "If you answered \"Yes,\" select the type of proceedings and provide the location and date of the proceedings.":
    "Si contestó \"Sí\", seleccione el tipo de procedimiento e indique el lugar y la fecha del mismo.",
  "If applicable, select the box for Item Number 2.": "Si aplica, seleccione la casilla del artículo número 2.",
  "List the city / town / village, state / province, and country where you were born.":
    "Indique la ciudad/pueblo/aldea, estado/provincia y país donde nació.",
  "Applicant's Contact Information.": "Información de contacto del solicitante.",
  "Contact Information of Attorney or Accredited Representative.":
    "Información de contacto del abogado o representante acreditado.",
  "Your Full Name.": "Su nombre completo.",
  "Your Full Legal Name.": "Su nombre legal completo.",
  "Beneficiary's Full Name.": "Nombre completo del beneficiario.",
  "Interpreter's Full Name.": "Nombre completo del intérprete.",
  "Name of Attorney or Accredited Representative.": "Nombre del abogado o representante acreditado.",
  "My citizenship was acquired through (Select only one box).":
    "Adquirí mi ciudadanía a través de (seleccione solo una casilla).",
  "If you answered \"Yes\" to Item Number 38., complete the following.":
    "Si contestó \"Sí\" en el número 38, complete lo siguiente.",
  "Weight.": "Peso.",
  "Height.": "Estatura.",
  "Place of Birth.": "Lugar de nacimiento.",
  "Family Name (Last Name).": "Apellido.",
  "Reason for Applying.": "Motivo de la solicitud.",
  "I am applying for (select only one box).": "Estoy solicitando (seleccione solo una casilla).",
  "Date of Signature.": "Fecha de la firma.",
  "Social Security Number, if any.": "Número de Seguro Social, si tiene uno.",
  "Is your current mailing address the same as your physical address? Select Yes.":
    "¿Su dirección postal actual es la misma que su dirección física? Seleccione Sí.",
  "Is your current mailing address the same as your physical address? Select No.":
    "¿Su dirección postal actual es la misma que su dirección física? Seleccione No.",
  "Date To.": "Fecha de fin.",
  "Present.": "Presente.",
  "No Entry.": "Sin entrada.",
  "I am a (Select only one box).": "Soy (seleccione solo una casilla).",
  "Place of Admission.": "Lugar de admisión.",
  "Did you gain lawful permanent resident status through marriage to a U.S.":
    "¿Obtuvo la residencia permanente legal mediante matrimonio con un ciudadano de EE. UU.",

  // Longer boilerplate instructions that recur across forms
  "mailing address.": "dirección postal.",
  "Number), if any.": "número), si aplica.",
  "or 1.": "o 1.",
  "Petitioner's Contact Information.": "Información de contacto del peticionario.",
  "Petitioner's Signature.": "Firma del peticionario.",
  "NOTE: Select the box for either Item Number 1.": "NOTA: Seleccione la casilla del número 1",
  "The beneficiary will not apply for adjustment of status in the United States, but he or she will apply for an immigrant visa abroad at the U.S.":
    "El beneficiario no solicitará el ajuste de estatus en Estados Unidos, sino que solicitará una visa de inmigrante en el extranjero en la embajada o consulado de EE. UU.",
  "The beneficiary is in the United States and will apply for adjustment of status to that of a lawful permanent resident at the U.S.":
    "El beneficiario está en Estados Unidos y solicitará el ajuste de estatus a residente permanente legal en la oficina de USCIS en",
  "Citizenship and Immigration Services (U S C I S) office in.": "Servicios de Ciudadanía e Inmigración (USCIS) en.",
  "Interpreter's Certification.": "Certificación del intérprete.",
  "Provide the following information about the preparer.": "Proporcione la siguiente información sobre el preparador.",
  "Given Name (First Name).": "Primer nombre.",
  "Middle Name.": "Segundo nombre.",
  "Your Country or Countries of Citizenship or Nationality.": "Su país o países de ciudadanía o nacionalidad.",
  "List all countries where you are currently a citizen or national.":
    "Enumere todos los países donde actualmente es ciudadano o nacional.",
  "If you need extra space to complete this item, use the space provided in Part 6.":
    "Si necesita más espacio para completar este punto, use el espacio provisto en la Parte 6.",
  "(c)(8) Eligibility Category.": "Categoría de elegibilidad (c)(8).",
  "Applicant's Signature.": "Firma del solicitante.",
  "This form can not be signed electronically.": "Este formulario no se puede firmar electrónicamente.",
  "The name of the applicant can not be typewritten into this space.":
    "El nombre del solicitante no se puede escribir a máquina en este espacio.",
  "Provide the following information concerning the interpreter: Interpreter's Full Name.":
    "Proporcione la siguiente información sobre el intérprete: nombre completo del intérprete.",
  "(This field is pre-populated from Part 1.)": "(Este campo se completa automáticamente desde la Parte 1.)",
  "I (select only one box).": "Yo (seleccione solo una casilla).",
  "If you are subject to any orders, use the space provided in Part 6.":
    "Si está sujeto a alguna orden, use el espacio provisto en la Parte 6.",
  "Additional Information to provide an explanation.": "Información adicional para proporcionar una explicación.",
  "List the specific matter in which appearance is entered.":
    "Indique el asunto específico en el que se presenta la comparecencia.",
  "Enter Feet.": "Ingrese pies.",
  "Enter Inches.": "Ingrese pulgadas.",
  "Select Black or African American.": "Seleccione Negro o Afroamericano.",
  "Select American Indian or Alaska Native.": "Seleccione Indígena Americano o Nativo de Alaska.",
  "Select Asian.": "Seleccione Asiático.",
  "Select Native Hawaiian or Other Pacific Islander.": "Seleccione Nativo de Hawái u otra isla del Pacífico.",
};

export function translateLabel(label: string): string {
  const segments = label.split(/(?<=[.])\s+/);
  return segments
    .map((seg) => {
      const trimmed = seg.trim();
      if (PHRASES[trimmed]) return PHRASES[trimmed];
      const throughMatch = trimmed.match(/^through\s+(\d+)\.$/i);
      if (throughMatch) return `hasta el ${throughMatch[1]}.`;
      return seg;
    })
    .join(" ");
}
