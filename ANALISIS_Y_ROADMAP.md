# Análisis Profundo + Roadmap — Imigratepro-2.0

> Generado la noche del 2026-07-21. El usuario revisa mañana. NO se hizo merge a master; todo el trabajo vive en la rama `app-nuevo-feature` (worktrees `wt-i18n`, `wt-portal`).
> Pendiente del usuario: matar el backend zombie en :8000 (bloqueó el kill por terminal). Mientras tanto, usar el frontend en :3000 que apunta a :8001.

---

## 1. BUG: "contraseña incorrecta" al entrar al portal del cliente

### Diagnóstico (reproducido con E2E real contra :8001)
- Script E2E: login staff → crear cliente → activar portal (`/client-auth/register`) → login cliente con la MISMA contraseña.
- Resultado: **staff login 200, create 201, register 200, client login 200, wrong-pass 401**.
- Conclusión: **el backend funciona 100%. El bug NO está en la lógica de hash/verify.**

### Causa más probable en el navegador
Hay DOS backends corriendo (zombie en :8000 + limpio en :8001) compartiendo el MISMO `migratepro.db`. Tu pestaña del navegador cargó el frontend cuando `.env.local` apuntaba a :8000, así que sigue haciendo fetch a :8000 en memoria. El zombie :8000 puede ser una versión del código previa (antes de `client_auth`) o simplemente confunde el estado de rate-limit/lock del cliente.

### Solución inmediata (mañana)
1. Cierra TODA pestaña de localhost:3000 / :8000.
2. Abre **http://localhost:3000** (el dev server nuevo ya lee `NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1`).
3. Crea un cliente NUEVO en `/clients` → "Activar acceso" → usa EXACTAMENTE la contraseña que te muestra.
4. Login en `/client/login` con ese email + esa contraseña.

Si quieres matar el zombie :8000 (recomendado para evitar confusión), en una terminal normal (no por mí, el usuario lo bloqueó):
```
taskkill /F /T /PID 34408
```
(o el PID que escuche en :8000 — ver con `Get-NetTCPConnection -LocalPort 8000`).

### Nota de robustez (no crítico, para producción)
El mensaje es "Invalid email or password" genérico (bien, no filtra si el email existe). Pero el lockout por `failed_login_attempts` es por CLIENTE, no por IP+email combinado; si el zombie :8000 acumuló intentos fallidos en el mismo cliente, puede estar `locked_until`. Al usar :8001 la DB es la misma, así que un lock previo sí aplica. Si ves 423 (locked), espera o resetea `locked_until` en la DB.

---

## 2. ESTRUCTURA DE CASOS — análisis y propuesta

### Lo que YA existe (modelo `Case`)
- `CaseType`: family_based, employment_based, asylum, naturalization, adjustment_of_status, work_permit, other.
- `CaseStatus`: intake, preparing, filed, rfe, approved, denied, closed.
- `ParticipantRole`: petitioner, beneficiary, derivative, sponsor (vía `CaseParticipant` que linkea Client↔Case con rol).
- `service_id` + `workflow_stage_id`: un Case aplica un Service (paquete: forms + checklist + stages) y está en un stage del workflow.
- Relaciones: participants, documents, generated_forms, appointments, invoices, checklist_items, rfes, service, workflow_stage, assigned_attorney.
- **IDs**: UUID. `case_number` único (USCIS-style, lo genera el sistema).

### Fortalezas
- Modelo sólido y normalizado. El concepto de "Service como catálogo que materializa checklist+stages+forms en el Case" es bueno (DRY).
- Participantes con rol es correcto para casos familiares (petitioner/beneficiary/derivative/sponsor).

### Gaps / propuestas de mejora
1. **Fechas clave del caso**: no hay `filed_date`, `deadline`/`priority_date`, ni `uscis_receipt_number` a nivel de Case (sí existe en GeneratedForm). Para追踪 deadlines reales (¡crítico en inmigración!), el Case debería tener `priority_date`, `filed_date`, `decision_deadline`. Hoy el receipt solo está en el form, no en el caso.
2. **USCIS Case Status a nivel de Case**: el chequeo de USCIS API vive en GeneratedForm (`uscis_receipt_number`, `uscis_status_raw`). Para un caso hay varios forms; sería mejor un `Case.uscis_receipt_number` + un agregado de estado, o al menos vincular el receipt del caso principal.
3. **"my_role" en el portal**: `getMyCases()` devuelve `my_role` del `CaseParticipant`. Bien. Pero el portal solo muestra forms del caso, no el árbol de participantes. Para el cliente beneficiario es OK; para petitioner que patrocina a un derivativo, faltaría distinguir.
4. **Jerarquía de casos**: casos relacionados (I-130 + I-485 + I-765 como un "package") no tienen link padre/hijo. Sugerir `parent_case_id` self-FK para agrupar el "package" y mostrarlo como un conjunto en el dashboard.
5. **Índice de búsqueda**: `case_number` está indexado; faltaría índice en `status` para filtros del dashboard staff.

### Recomendación corta
Mantener la estructura. Añadir a `Case`: `priority_date`, `filed_date`, `decision_deadline` (nullable), y `parent_case_id` (self-FK, nullable) para "packages". Mover el receipt principal al Case y dejar el de GeneratedForm como detalle por form.

---

## 3. NOTIFICACIONES SEGMENTADAS POR ROL — análisis y propuesta

### Lo que YA existe (modelo `Notification`)
- `Notification`: type, message, case_id. **Es un feed GLOBAL compartido** (el comentario del modelo lo dice: "Intentionally still a shared, global feed rather than scoped to a specific user or role").
- `NotificationSeen` (tabla `notification_reads`): marca user_id + notification_id (solo estado de leído por usuario).
- `NotificationType`: case_assigned, stage_advanced, document_uploaded, ai_review_flagged, appointment_scheduled, appointment_reminder, invoice_overdue, payment_received, rfe_received.

### El problema que señalas
Hoy TODOS ven TODO. Quieres que la notificación llegue **al rol / persona asignada** correcta. Esto es correcto para una firma: un paralegal no necesita ver "invoice_overdue" del cliente X si no es su caso; el attorney asignado sí.

### Propuesta de cambio (migración a notificaciones dirigidas)
Añadir a `Notification`:
- `recipient_user_id: UUID | None` (FK users.id, index) → notificación 1:1 a un usuario.
- `recipient_role: UserRole | None` → notificación a todos los de un rol (ej. todas las paralegales).
- `is_global: bool = False` → para anuncios firm-wide (default False).
- Mantener `case_id` para contexto.

Lógica de creación (en los servicios que hoy hacen `db.add(Notification(...))`):
- `case_assigned` → recipient = assigned_attorney.
- `stage_advanced` → recipient = assigned_attorney + paralegal del caso (si hay).
- `document_uploaded` (por cliente vía portal) → recipient = assigned_attorney + paralegal.
- `ai_review_flagged` → recipient = assigned_attorney.
- `appointment_scheduled/reminder` → recipient = assigned_attorney + el cliente (vía su portal, si tiene).
- `invoice_overdue` / `payment_received` → recipient = admin + assigned_attorney (billing).
- `rfe_received` → recipient = assigned_attorney + paralegal.

Endpoint de lectura: `GET /notifications?scope=mine` devuelve las where `recipient_user_id == current_user.id OR recipient_role == current_user.role OR is_global`, marcando read vía `NotificationSeen` como hoy.

### Beneficio
- El cliente ve SUS notificaciones en el portal (hoy el portal ni siquiera muestra notificaciones — solo el staff).
- Staff ve solo lo relevante → menos ruido.
- Cumple tu pedido literal: "segmentada por roles a quién está asignado".

### Esfuerzo estimado
Mediano. Requiere: (a) migración Alembic añadiendo las 3 columnas, (b) wrapper `notify(case, type, message, recipients)` en `app/services/notifications.py` para centralizar la lógica de destinatarios, (c) actualizar los ~9 lugares que crean notificaciones, (d) nuevo endpoint + UI de filtro en el campanita del staff y en el portal del cliente.

---

## 4. FORMULARIOS AGRUPADOS POR TIPO — análisis y propuesta

### Lo que YA existe
- `FormTemplate`: code (I-130), name, edition_date, pdf_template_path, field_schema, autofill_map.
- `GeneratedForm`: case_id, form_template_id, status (draft/generated/filed), data, ai_review, access_token (link portal), client_link_enabled, client_wizard_step, uscis_receipt_number.
- `ServiceFormTemplate`: linkea un Service con los forms que incluye (un Service "Family Petition" trae I-130 + I-485 + I-864, etc.).

### El problema que señalas
Hoy los formularios se listan por `form_code` suelto, sin categoría. Quieres agruparlos por TIPO (Familia, Empleo, Asilo, General...). Esto encaja con `CaseType`.

### Propuesta
Añadir a `FormTemplate`:
- `category: FormCategory` enum: FAMILY, EMPLOYMENT, ASYLUM, NATURALIZATION, ADJUSTMENT, GENERAL, OTHER (mapea 1:1 con CaseType para consistencia).
- `requires_sponsor: bool = False` (I-864, I-134) → útil para el wizard del portal (mostrar solo si hay sponsor).
- `is_intake: bool = False` → forms de "intake" que el cliente llena primero.

UI:
- En el editor staff (`/forms`) y en el portal del cliente, agrupar por `category` con headers colapsables (accordion). Ej. "Family Forms", "Employment Forms".
- En el dashboard del cliente, mostrar los forms de SU caso agrupados por category, no una lista plana.

### Esfuerzo estimado
Pequeño-mediano. Migración para añadir `category` a FormTemplate (backfill por código de form conocido: I-130/I-485/I-864 → FAMILY; I-140/I-129 → EMPLOYMENT; I-589 → ASYLUM; N-400 → NATURALIZATION; I-765 → ADJUSTMENT/WORK_PERMIT; etc.). Frontend: agrupar en los dos lugares.

---

## 5. QUÉ FALTA PARA PRODUCCIÓN (gaps P0 del CLAUDE.md + observaciones)

### Bloqueantes de seguridad (del CLAUDE.md, aún sin cerrar según el reporte de auditoría)
1. **IDOR (C1)**: rutas `/{id}` deben scope por ownership (`require_case_access()`). Afecta cases/clients/documents/billing/rfes/appointments/forms. → Prioridad #1.
2. **RBAC (H1)**: `RequireRole` en rutas mutantes sensibles. Paralegal NO debe crear cases/invoices/borrar.
3. **Allowlist de campos portal (C2/H4)**: validar `payload.data` contra `client_editable_fields`; rechazar keys desconocidas con 422.
4. **Tokens (H5)**: ya está en cookies httpOnly (bien). Verificar que NO haya localStorage de token en ningún lado (el clienteAuth.tsx ya usa cookie-session ✓).
5. **SECRET_KEY (H2)**: `sys.exit` si default en prod.
6. **Audit log (M6)**: log de acciones destructivas/sensibles.

### Observaciones adicionales para prod
- **CORS**: `settings.CORS_ORIGINS` debe ser el dominio real, no `*`. Verificar.
- **HTTPS / proxy**: en prod el API detrás de HTTPS; el `.env.local` de frontend debe ser `https://`.
- **Rate limiting**: el client-auth login tiene rate limit (bien). Falta en staff login y endpoints sensibles.
- **Migraciones**: pasar de SQLite a PostgreSQL en prod (el CLAUDE.md dice PostgreSQL en prod). Alembic debe estar al día.
- **Secrets**: `.env` de backend con SECRET_KEY, DB URL, USCIS API keys — fuera del repo.
- **Tests**: backend tiene 147 pytest (correr antes de prod). Frontend `npm test` + Playwright e2e.
- **CI/CD**: un pipeline que corra pytest + build + e2e en cada PR.
- **Backups**: SQLite local no es prod; PostgreSQL + backup.

---

## 6. ROADMAP PRIORIZADO (sugerido)

### Fase A — Seguridad (bloquea prod) — la más importante
1. `require_case_access()` en todas las rutas `/{id}` (IDOR).
2. `RequireRole` en rutas mutantes (RBAC).
3. Allowlist de campos en portal (C2/H4).
4. Audit log (M6).
5. SECRET_KEY guard + CORS restrictivo.

### Fase B — Portal del cliente (lo que veníamos haciendo)
- ✅ Traducción 100% (wt-i18n).
- ✅ Dark mode + UX/UI + build (wt-portal).
- ⬜ Mostrar notificaciones en el portal (requiere Fase C).
- ⬜ Agrupar forms por categoría en el dashboard del cliente (Fase D).

### Fase C — Notificaciones dirigidas (tu pedido)
- Migración + wrapper `notify()` + endpoint `GET /notifications?scope=mine` + UI staff (filtro por rol) + UI portal (sus notificaciones).

### Fase D — Formularios por tipo (tu pedido)
- `category` en FormTemplate + backfill + agrupación en editor y portal.

### Fase E — Casos (tu pedido)
- `priority_date`, `filed_date`, `decision_deadline`, `parent_case_id` en Case.
- Receipt principal a nivel Case.

### Fase F — Producción
- PostgreSQL + Alembic + secrets + CORS + HTTPS + CI + tests + backups.

---

## 7. ESTADO DE LOS WORKTREES (para revisar mañana)
- `wt-i18n` → `a879d2c` traducción 100%.
- `wt-portal` → `7c68c59` + `f23b591` dark mode + UX + build.
- Rama `app-nuevo-feature` = merge de ambos, SIN merge a master.
- Build verde, `tsc --noEmit` exit 0 en la rama.
- Backend :8001 corriendo (limpio), frontend :3000 corriendo (apunta a :8001).
- Cliente E2E `e2e_client_1@test.local` creado en la DB durante las pruebas (se puede borrar).

## 8. PREGUNTAS PARA EL USUARIO (mañana)
1. ¿Matamos el zombie :8000 para evitar la confusión del portal?
2. ¿Arrancamos Fase A (seguridad/IDOR/RBAC) primero, o Fase C/D/E (las mejoras de arquitectura que pediste)?
3. ¿Las notificaciones dirigidas las quieres también visibles en el portal del cliente, o solo segmentadas en el staff?
4. ¿El agrupado de formularios lo hacemos por `category` (Familia/Empleo/...) o por `Service` (paquete contratado)?
