# Revisión de Seguridad — Imigratepro-2.0 (rama app-nuevo-feature)

Auditor: Hermes (agentes agency-agentsss como guía: security-ai-generated-code-auditor, security-appsec-engineer).
Fecha: 2026-07-22. Alcance: cambios A/C/D/E generados por IA + reglas BLOQUEANTES de CLAUDE.md.
Método: lectura del código real en disco + grep. Confianza indicada por hallazgo.

## Resumen ejecutivo
El scoping IDOR (C1) quedó BIEN aplicado en cases/documents/billing/rfes/appointments/forms.
El allowlist del portal (C2/H4) es CORRECTO. Tokens (H5/H7) OK (cookies, no localStorage).
Quedan 2 gaps RBAC reales en `clients.py` y `create_case`, y 1 decisión de diseño a ratificar.

---

## P1 — RBAC incompleto en clients.py (CWE-862 Missing Authorization)
Archivo: backend/app/api/v1/endpoints/clients.py
- `create_client` (L18-24), `get_client` (L27-32), `update_client` (L35-44): NO tienen RequireRole.
- El router se monta con `dependencies=[_protected]` (router.py L35), así que exigen LOGIN — no es acceso anónimo.
- PERO cualquier rol logueado (paralegal, intake, billing, legal_assistant) puede crear/leer/editar CUALQUIER cliente. El CLAUDE.md (H1) dice "paralegal must NOT create ... delete everything".
- `update_client` además NO escribe audit log (M6), a diferencia de `delete_client` que sí (L52).
Confianza: ALTA.
Fix (1 commit): añadir `requester: RequireIntakeOrAbove` (o el rol correcto) a create/update y `RequireOwnerOrAdmin`-equivalente donde aplique; agregar `log_action(db, requester, "client.updated", ...)` en update.

## P1 — create_case sin RBAC (CWE-862)
Archivo: backend/app/api/v1/endpoints/cases.py L32 `create_case(payload, db)` — sin RequireRole.
- update/delete SÍ usan RequireOwnerOrAdmin (L78-80), pero CREATE queda abierto a cualquier staff.
- CLAUDE.md H1: paralegal no debe crear casos.
Confianza: ALTA.
Fix: añadir `requester: RequireAdminOrAttorney` a create_case + audit log "case.created".

## P2 — Decisión de diseño IDOR lectura vs escritura (ratificar)
Archivo: backend/app/api/deps.py L108-128.
- `require_case_access` (escritura): OWNER/ADMIN o ATTORNEY asignado. Correcto y estricto.
- `require_case_access_read` (lectura): devuelve el caso a CUALQUIER staff logueado ("shared firm-wide visibility").
- Esto es intencional (diseño de despacho) pero el CLAUDE.md C1 dice "every /{id} route MUST scope by ownership". Tensión real.
- Riesgo: un paralegal/intake puede LEER casos de cualquier cliente del despacho (PII: SSN, A-number). Aceptable si el despacho es de confianza; NO si hay contratistas.
Confianza: ALTA (es una decisión, no un bug).
Recomendación: si se requiere scope estricto en lectura, añadir `assigned_paralegal_id`/equipo al modelo Case y filtrarlo. Si no, documentarlo formalmente como aceptado por el despacho.

## OK verificado (sin acción)
- IDOR C1 escritura: require_case_access aplicado en documents/billing/rfes/appointments/forms/cases (grep confirma ~25 call sites). CORRECTO.
- Allowlist C2/H4 (public_forms.py L80-93): rechaza campos desconocidos con 422 Y filtra attorney-only. CORRECTO.
- Tokens H5/H7: no hay JWT en localStorage (única mención localStorage es idioma en i18n.tsx). Usa cookies httpOnly. CORRECTO.
- SECRET_KEY H2: guard con sys.exit en prod (main.py). CORRECTO.
- Notificaciones (C): filtro por recipient_user_id/role/is_global correcto; no fuga notifs de otros. CORRECTO.
- Migración consolidada f9c1d2e3a4b5: server_default en category, backfill idempotente, batch_alter_table para SQLite. CORRECTO.

## Pendiente de auditar (no cubierto por falta de cuota de agentes)
- Rate limiting en endpoints de escritura masiva.
- Validación de tamaño/tipo de uploads (más allá de uuid4 en storage).
- CORS efectivo en prod (settings.CORS_ORIGINS = ["http://localhost:3000"] — cambiar a dominio prod).
