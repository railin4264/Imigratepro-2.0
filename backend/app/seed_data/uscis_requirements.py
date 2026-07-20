"""Curated "what USCIS generally asks for" reference per form, grounded in
USCIS's own published checklists/instructions -- NOT a legal determination,
NOT case-specific advice, and explicitly NOT AI-generated (no model was asked
to guess what a form requires; every category below traces to the cited
official source). Same "no adivinar" discipline as
app/seed_data/conditional_rules.py: only forms with a real, verifiable source
are listed here.

uscis.gov itself blocks automated fetches (403), so each entry was verified
against the official USCIS page/checklist named in `source_url` by a human
research pass on `verified_on`, cross-checked against a specialized filing
-assistance service (CitizenPath) for completeness. Filing FEES are
deliberately NOT included here -- fee amounts are in active flux (a 2025-2026
federal fee-schedule overhaul changed several of them, including a paused
H.R. 1 EAD fee as of this writing) and change far more often than procedural
requirements, so a hardcoded number would go stale fast and mislead someone
relying on it. Always send staff to the live USCIS Fee Calculator instead.

7 of the 16 catalog forms have an entry: I-130, I-485, I-765, N-400, I-751,
I-131, I-90. The other 9 (I-130A, I-589, I-864, G-28, N-336, N-470, N-565,
N-600, N-600K) don't yet -- same reasoning as conditional_rules.py: better to
have no reference than a guessed one."""

from dataclasses import dataclass


@dataclass
class RequirementCategory:
    title: str
    items: list[str]


@dataclass
class FormRequirements:
    source_url: str
    source_label: str
    verified_on: str  # ISO date this entry was last checked against the source
    categories: list[RequirementCategory]


FEE_CALCULATOR_URL = "https://www.uscis.gov/feecalculator"

USCIS_REQUIREMENTS_BY_FORM_CODE: dict[str, FormRequirements] = {
    "I-130": FormRequirements(
        source_url="https://www.uscis.gov/sites/default/files/document/checklists/I-130_Petition_Checklist.pdf",
        source_label="USCIS -- I-130 Petition Checklist",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory(
                "Prueba del estatus del peticionario",
                [
                    "Acta de nacimiento en EE. UU., certificado de naturalización o pasaporte estadounidense (ciudadano)",
                    "Copia de ambos lados de la tarjeta de residencia permanente (residente permanente)",
                ],
            ),
            RequirementCategory(
                "Prueba de la relación familiar",
                [
                    "Acta de matrimonio (cónyuge)",
                    "Actas de nacimiento que muestren la relación (padre/madre, hijo/a, hermano/a)",
                ],
            ),
            RequirementCategory(
                "Terminación de matrimonios previos",
                ["Sentencias de divorcio o actas de defunción de cualquier matrimonio anterior de cualquiera de las partes"],
            ),
            RequirementCategory(
                "Evidencia de matrimonio de buena fe (solo peticiones de cónyuge)",
                [
                    "Cuentas bancarias, contratos de arrendamiento o hipotecas conjuntas",
                    "Declaraciones de impuestos presentadas en conjunto",
                    "Pólizas de seguro que se designen mutuamente como beneficiarios",
                    "Fotos juntos, actas de nacimiento de hijos en común",
                ],
            ),
            RequirementCategory(
                "Otros",
                [
                    "2 fotos tipo pasaporte del peticionario y del beneficiario",
                    "Formulario I-130A (información suplementaria) si el beneficiario es cónyuge",
                    "Traducción certificada de cualquier documento que no esté en inglés",
                ],
            ),
        ],
    ),
    "I-485": FormRequirements(
        source_url="https://www.uscis.gov/forms/filing-guidance/checklist-of-required-initial-evidence-for-form-i-485-for-informational-purposes-only",
        source_label="USCIS -- Checklist of Required Initial Evidence for Form I-485",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory(
                "Identidad y entrada a EE. UU.",
                [
                    "Pasaporte (aunque esté vencido)",
                    "Registro I-94 de entrada/salida",
                    "2 fotos tipo pasaporte",
                    "Identificación con foto emitida por el gobierno",
                ],
            ),
            RequirementCategory(
                "Petición subyacente",
                [
                    "Recibo o notificación de aprobación del I-130 (o presentación concurrente)",
                    "Número A si ya fue emitido",
                ],
            ),
            RequirementCategory("Examen médico", ["Formulario I-693 completado por un médico civil autorizado por USCIS"]),
            RequirementCategory(
                "Respaldo financiero (casos familiares)",
                [
                    "Formulario I-864 (Declaración Jurada de Patrocinio Económico)",
                    "Declaraciones de impuestos, W-2 o 1099 del patrocinador más recientes",
                ],
            ),
            RequirementCategory(
                "Historial biográfico",
                [
                    "Historial de domicilios de los últimos 5 años",
                    "Historial de empleo de los últimos 5 años",
                    "Fechas de matrimonios y divorcios anteriores",
                ],
            ),
            RequirementCategory(
                "Casos de matrimonio", ["Evidencia de matrimonio de buena fe (ver requisitos del I-130)"]
            ),
            RequirementCategory("Otros", ["Traducción certificada de cualquier documento que no esté en inglés"]),
        ],
    ),
    "I-765": FormRequirements(
        source_url="https://www.uscis.gov/forms/filing-guidance/checklist-of-required-initial-evidence-for-form-i-765-for-informational-purposes-only",
        source_label="USCIS -- Checklist of Required Initial Evidence for Form I-765",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory(
                "Identidad",
                ["Identificación con foto emitida por el gobierno (pasaporte)", "2 fotos tipo pasaporte"],
            ),
            RequirementCategory(
                "Prueba de estatus migratorio",
                [
                    "Copia del I-94 (ambos lados), si está disponible",
                    "Copia del EAD anterior (ambos lados), si está renovando",
                    "Si es la primera solicitud: pasaporte, acta de nacimiento con identificación con foto, visa, o documento de identidad nacional",
                ],
            ),
            RequirementCategory(
                "Evidencia específica de la categoría de elegibilidad",
                [
                    "Varía según la categoría (a)/(c) marcada en el formulario -- verificar las instrucciones oficiales de la categoría específica"
                ],
            ),
        ],
    ),
    "N-400": FormRequirements(
        source_url="https://www.uscis.gov/n-400",
        source_label="USCIS -- N-400, Application for Naturalization",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory("Identidad", ["Copia de ambos lados de la tarjeta de residencia permanente"]),
            RequirementCategory(
                "Historial de nombre legal",
                ["Actas de matrimonio, sentencias de divorcio u órdenes judiciales por cualquier cambio de nombre legal"],
            ),
            RequirementCategory("Fotos", ["2 fotos tipo pasaporte (solo si presenta la solicitud desde el extranjero)"]),
            RequirementCategory(
                "Servicio Selectivo", ["Verificación de registro del Servicio Selectivo (hombres que fueron residentes permanentes entre los 18 y 26 años)"]
            ),
            RequirementCategory(
                "Evidencia adicional (puede ser solicitada)",
                [
                    "Transcripciones de impuestos de los últimos 5 años (o 3 años si aplica por matrimonio)",
                    "Registros de viaje de cualquier salida de 6 meses o más",
                ],
            ),
            RequirementCategory("Pago", ["Cuota de presentación o Formulario I-912 (exención de cuota)"]),
        ],
    ),
    "I-751": FormRequirements(
        source_url="https://www.uscis.gov/i-751",
        source_label="USCIS -- I-751, Petition to Remove Conditions on Residence",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory("Identidad", ["Copia de ambos lados de la tarjeta de residente condicional"]),
            RequirementCategory(
                "Evidencia financiera conjunta",
                ["Cuentas bancarias conjuntas", "Declaraciones de impuestos conjuntas", "Tarjetas de crédito conjuntas"],
            ),
            RequirementCategory(
                "Evidencia de vivienda conjunta", ["Contrato de arrendamiento o hipoteca conjunta", "Facturas de servicios conjuntas"]
            ),
            RequirementCategory(
                "Evidencia de relación",
                [
                    "Pólizas de seguro (vida/salud/auto) que se designen mutuamente",
                    "Fotos juntos a lo largo del tiempo",
                    "Declaraciones juradas de personas que conocen el matrimonio",
                ],
            ),
            RequirementCategory(
                "Si el matrimonio terminó (solicitud de exención)",
                [
                    "Sentencia de divorcio y evidencia de que el matrimonio fue de buena fe, o evidencia de abuso -- caso complejo, requiere revisión de un abogado"
                ],
            ),
        ],
    ),
    "I-131": FormRequirements(
        source_url="https://www.uscis.gov/i-131",
        source_label="USCIS -- I-131, Application for Travel Documents, Parole Documents, and Arrival/Departure Records",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory("Identidad", ["Copia del pasaporte", "Registro I-94"]),
            RequirementCategory(
                "Solicitud subyacente",
                ["Notificación de recibo de la solicitud pendiente que este documento de viaje acompaña, si aplica"],
            ),
            RequirementCategory("Fotos", ["2 fotos tipo pasaporte"]),
            RequirementCategory(
                "Evidencia específica del propósito",
                [
                    "Varía según el tipo: permiso adelantado de viaje (advance parole), documento de viaje para refugiado, o permiso de reingreso -- verificar las instrucciones oficiales del tipo específico"
                ],
            ),
        ],
    ),
    "I-90": FormRequirements(
        source_url="https://www.uscis.gov/i-90",
        source_label="USCIS -- I-90, Application to Replace Permanent Resident Card",
        verified_on="2026-07-18",
        categories=[
            RequirementCategory("Identidad", ["Copia de ambos lados de la tarjeta de residencia actual o vencida", "Identificación con foto emitida por el gobierno"]),
            RequirementCategory(
                "Evidencia según el motivo",
                [
                    "Tarjeta vencida o por vencer: no se requiere evidencia adicional además de la copia de la tarjeta",
                    "Cambio de nombre legal: acta de matrimonio, sentencia de divorcio u orden judicial",
                    "Error de USCIS en la tarjeta: la tarjeta con el error",
                    "Corrección de datos biográficos: documentos civiles que respalden la corrección",
                ],
            ),
            RequirementCategory("Pago", ["Cuota de presentación o Formulario I-912 (exención de cuota, solo por correo)"]),
        ],
    ),
}
