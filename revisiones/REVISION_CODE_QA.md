# Revisión Code Review + QA — Imigratepro-2.0 (app-nuevo-feature)

Revisor: Hermes (guía: engineering-code-reviewer, testing-reality-checker, testing-api-tester).
Fecha: 2026-07-22. Método: lectura de código + grep + smoke test E2E previo.

## Resumen
Las 4 features están REALMENTE cableadas (no solo commiteadas). pytest 557 passed, tsc 0.
Gap principal: las features nuevas NO tienen tests dedicados. 2 hallazgos de calidad menores.

---

## Reality check (¿funciona de verdad o solo parece?)
| Feature | ¿Cableada? | Evidencia |
|---------|-----------|-----------|
| Notificaciones por rol (C) | SÍ | endpoints/notifications.py L15-21 filtra recipient_user_id/role/is_global; 10 call sites dirigidos |
| Categoría de formularios (D) | SÍ | client/dashboard/page.tsx L24,L121-124 agrupa por categoría con i18n `forms.category.*` |
| Fechas/parent de caso (E) | SÍ | schemas/case.py L15-19 y L31-35 expone los 5 campos en CaseRead y CaseUpdate |
| Scoping IDOR (A) | SÍ | ~25 call sites de require_case_access/_read en 6 endpoints |
| Smoke E2E | PASA | crear caso con priority_date→201, login portal→200, IDOR caso inexistente→404 |

Ninguna feature "fantasma" (commiteada sin conectar). Buen resultado para código IA.

## P1 — Cobertura de tests de las features nuevas = 0 (CWE-N/A, deuda de QA)
- grep en backend/tests/ NO encontró tests que ejerzan: recipient_role/notificaciones dirigidas, require_case_access (autorización por caso), category de forms, priority_date/parent_case.
- Los 557 tests que pasan son los PREEXISTENTES; no cubren la lógica nueva. Riesgo: una regresión futura en el scoping IDOR o en el filtro de notificaciones NO sería detectada.
Fix: añadir tests:
  - test_case_access.py: attorney no-asignado → 403 en PATCH; admin → 200; caso inexistente → 404.
  - test_notifications.py: notif con recipient_role=BILLING no la ve un ATTORNEY; is_global la ven todos.
  - test_forms_category.py: backfill categoriza I-130→family; endpoint agrupa.
  - test_cases_dates.py: crear/leer con priority_date, parent_case_id (package).

## P2 — update_client sin audit log (consistencia)
backend/app/api/v1/endpoints/clients.py L35-44: update_client no llama log_action, mientras delete_client sí. Inconsistente con el patrón M6 del repo. (También listado en revisión de seguridad.)

## P2 — Posible N+1 en dashboard de notificaciones/forms
Revisar que list_notifications y el dashboard del cliente (forms por caso) usen joinedload/selectinload y no disparen una query por fila. No confirmado por lectura; verificar con echo=True en dev.

## OK
- Estilo consistente con el repo (Annotated + Depends, SQLAlchemy 2.0, Pydantic v2).
- Migración consolidada limpia (un solo head f9c1d2e3a4b5).
- tsc --noEmit exit 0; tipos del frontend (Case, category) extendidos correctamente.

## No cubierto (falta cuota de agentes)
- Tests de carga / performance-benchmarker.
- Accesibilidad (testing-accessibility-auditor) del portal y dashboards.
