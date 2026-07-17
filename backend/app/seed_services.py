"""Seed one example service package ("Peticion Familiar") to demonstrate the
service catalog: bundles I-130 + G-28, a starter checklist, and workflow
stages, matching the example the user described.

Run with: ./.venv/Scripts/python.exe -m app.seed_services
"""

from app.core.database import SessionLocal
from app.models.form import FormTemplate
from app.models.service import Service, ServiceChecklistItem, ServiceFormTemplate, WorkflowStage

STAGES = [
    "Consulta",
    "Contrato",
    "Pago inicial",
    "Recibir documentos",
    "Completar formularios",
    "Revisión",
    "Firma",
    "Enviado a USCIS",
    "Biometría",
    "Entrevista",
    "Aprobado",
    "Cerrado",
]

CHECKLIST = [
    "Solicitar pasaporte",
    "Acta de nacimiento",
    "Acta de matrimonio",
    "Fotos tipo pasaporte",
    "Pago de tarifa USCIS",
    "Firma del cliente",
    "Enviar paquete a USCIS",
]

FORM_CODES = ["I-130", "G-28"]


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Service).filter_by(name="Petición Familiar").one_or_none()
        if existing:
            print("Service 'Petición Familiar' already exists, skipping.")
            return

        service = Service(
            name="Petición Familiar",
            description="Petición de familiar (I-130) con representación de abogado (G-28).",
            price=2500.0,
            estimated_days=270,
        )
        db.add(service)
        db.flush()

        for index, stage_name in enumerate(STAGES):
            db.add(WorkflowStage(service_id=service.id, name=stage_name, order=index))

        for index, label in enumerate(CHECKLIST):
            db.add(ServiceChecklistItem(service_id=service.id, label=label, order=index))

        for code in FORM_CODES:
            template = db.query(FormTemplate).filter_by(code=code).one_or_none()
            if template:
                db.add(ServiceFormTemplate(service_id=service.id, form_template_id=template.id))

        db.commit()
        print("Seeded service 'Petición Familiar'.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
