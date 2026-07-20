# ANÁLISIS PROFUNDO — ADMINISTRACIÓN Y OPERACIONES (Oficina de Inmigración)

Proyecto: Imigratepro-2.0  ·  Fecha: 2026-07-20
Alcance: Jerarquía/roles/permisos + facilidad de interacción del cliente. Read-only: no se modificó
ningún archivo. Basado en lectura de código (file:line) + investigación de mejores prácticas
(Clio, MyCase, Filevine, Docketwise, eImmigration, Case Status, LegistAI, USCIS, ABA).

---

## PARTE A — JERARQUÍA / ROLES / PERMISOS

### A.1 Estado actual (con file:line)
- **3 roles planos** (`backend/app/models/user.py:11-14`): `ADMIN`, `ATTORNEY`, `PARALEGAL`. No hay
  rol cliente, asistente, intake, billing, ni contract attorney.
- `User` (`user.py:17-40`): `role` (default PARALEGAL), `is_active`, `hashed_password` nullable.
  **No hay `is_superuser`, ni `office_id`, ni `created_by/managed_by`.** Campos de abogado
  (bar_number, firm_name…) viven en User.
- **Auth** (`core/security.py:48-61`): JWT HS256; **no hay revocación de access tokens** (solo refresh).
- **RBAC** (`api/deps.py:55-77`): `require_roles(*allowed)` + `RequireAdminOrAttorney`. El docstring
  dice: lectura/trabajo rutinario abierto a todos; solo destructivas/dinero requieren admin/attorney.
- **SÍ se aplica** en `/users` (crear/editar solo ADMIN) y borrados/dinero
  (`cases.py:69`, `clients.py:47`, `documents.py:132`, `rfes.py:128`, `appointments.py:102`,
  `billing.py:72,93,105,114,142`).
- **NO se aplica (brechas):**
  - Crear/editar caso/cliente/RFE/cita/form/documento → abierto a **cualquier rol** (paralegal incluido).
  - **IDOR (C1): sin control de propiedad.** `get/update_case` (`cases.py:33,41`),
    `get/update_document` (`documents.py:112,119`), `get_invoice` (`billing.py:85`),
    `get_user` (`users.py:90`) → cualquier rol lee/edita objetos ajenos.
  - `Case.assigned_attorney_id` existe (`case.py`) pero **no se usa para autorizar**.
- **Notificaciones** (`notification.py:23-27`): feed **global compartido**, no por usuario/rol.
- **UI staff** (`AppShell.tsx:136-147`): menú idéntico para los 3 roles; nada oculto por rol.

### A.2 Brechas vs un despacho real
1. No hay rol **cliente** de primera clase (clientes son filas `Client`, no usuarios con login).
2. Faltan roles operativos: Owner/Managing Attorney, Legal Assistant, Intake, Billing, Contract Attorney.
3. No hay **jerarquía granular** (solo-lectura, "ver solo sus casos", "puede facturar pero no borrar").
4. Falta **asignación por caso / ownership** (un abogado solo debería ver sus casos).
5. Falta **multi-oficina** (`office_id`).
6. Falta **revocación de access tokens**.
7. Falta **audit log** de acciones (crítico para cumplimiento/PII).
8. Visibilidad financiera sin restricción (paralegal ve facturas).

### A.3 Jerarquía recomendada + matriz de permisos
Roles: `OWNER`, `ADMIN`, `ATTORNEY`, `PARALEGAL`, `LEGAL_ASSISTANT`, `INTAKE_SPECIALIST`,
`BILLING`, `CONTRACT_ATTORNEY`, `CLIENT`.

| Acción | OWNER | ADMIN | ATTY | PARA | ASST | INTAKE | BILLING | CONTRACT | CLIENT |
|---|---|---|---|---|---|---|---|---|---|
| Ver personal | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crear/editar usuarios | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ver **sus** casos | ✓ | ✓ | ✓ | ✓ | lectura | ✗ | ✗ | asignados | propios |
| Crear caso/cliente | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| Editar documentos (caso propio) | ✓ | ✓ | ✓ | ✓ | subir | ✗ | ✗ | ✓ | ✓ |
| Borrar registros | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Facturas/pagos | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| Panel financiero | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| RFE/citas/form. (caso propio) | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Mensajería cliente | ✓ | ✓ | ✓ | ✓ | lectura | ✗ | ✗ | ✓ | ✓ |
| e-sign (G-28) | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |

\* "Casos asignados" = `assigned_attorney_id == current_user` o `CaseParticipant` incluye al usuario.

**Pasos de implementación:**
1. Extender `UserRole`; añadir `office_id`, `managed_office_ids`, `is_superuser` a `User`.
2. Crear `require_case_access(case_id)` en `deps.py` (dueño/participante/admin) → mata el IDOR.
3. Aplicar `require_case_access`/`require_own_or_admin` en get/update de case, document, invoice, user.
4. Tabla `audit_log` + middleware para writes destructivos.
5. Frontend consciente del rol (`AppShell`) para ocultar rutas (defensa en profundidad).

---

## PARTE B — EXPERIENCIA DEL CLIENTE

### B.1 Estado actual (file:line)
- **Portal por token** (`frontend/src/app/client/forms/[token]/page.tsx`, 395 líns): carga por
  `access_token`, SIN login. El cliente PUEDE: rellenar formulario por partes (wizard) con
  autoguardado (`saveData:130-147`, reanuda paso `:54-61`), subir documentos con rol de participante
  (`handleUpload:167-184`), ver timeline (`public_forms.py:116-123`) y lista de docs (`:126-129`).
- **Backend** (`public_forms.py`): `PATCH /{token}` dropea campos de abogado silenciosamente
  (`:56-66`) — buen diseño. PERO `GET /{token}/documents` devuelve **TODOS los documentos del caso**,
  no solo los del formulario (`:126-129`) → un token expone todo el caso.
- **Calidad UX (positiva):** progreso visible, pasos navegables, aviso de reanudado, `beforeunload`,
  i18n ES/EN, responsive. El formulario en sí es bueno y móvil-amigable.

### B.2 Brechas vs portales de referencia (Clio Connect, MyCase, Lawfully)
1. **Sin login de cliente** (solo token link; quien tenga el link accede sin contraseña).
2. **Sin mensajería bidireccional** (0 modelos de message en backend) — **la mayor carencia**.
3. **Sin e-sign** (0 coincidencias signature/esign).
4. **Estado limitado:** solo timeline genérico; no explica "RFE recibido → envía X antes de fecha",
   biometrics, entrevista.
5. **Sin notificaciones al cliente** (el sistema de notificaciones es interno del staff).
6. **Exposición de documentos demasiado amplia** (un token de formulario expone todo el caso).
7. **Sin pagos** en el portal.
8. **Sin hub unificado:** un cliente con varios formularios recibe varios enlaces sueltos.

### B.3 Mejoras recomendadas (para que sea completo, friendly, interactivo, fácil)
**Alta:**
1. **Login de cliente de primera clase** (rol `CLIENT` + `ClientUser`); portal central `/client`
   con sus casos; el token queda como invitación única de alta.
2. **Mensajería segura bidireccional** por hilo de caso (modelo `Message` + `/client/messages`).
3. **e-sign** en el wizard (G-28 firma del abogado en staff).
4. **Notificaciones al cliente** (email/SMS) en los mismos eventos del staff.
**Media:**
5. **Hub unificado del cliente** con "qué se necesita de ti" (checklist pendiente).
6. **Timeline en lenguaje claro** con fechas límite (RFE, biometrics, entrevista) + recordatorios.
7. **Estrechar exposición de documentos** (`shared_with_client=True`).
8. **Portal de pagos** (ver/pagar facturas).
**Baja:**
9. App móvil / PWA. 10. Multilingüe ampliado.

---

## PARTE C — OPERACIONES (lo que reduce riesgo en inmigración)
- **Motor de fechas clave**: Visa Bulletin / priority dates / retrogradación + cuenta regresiva de
  plazos RFE (perder un RFE = denegación).
- **Biblioteca de formularios versionada** + auto-llenado de datos compartidos (formulario obsoleto
  puede perder elegibilidad).
- **RFE automatizado**: al recibir RFE → crear tareas, notificar cliente, contar regresivo.
- **USCIS case-status** ya integrado → mapear a hitos del caso y notificar.
- **Recordatorios multi-canal** para reducir no-shows (entrevista/biometrics).
- **Transparencia 24/7** del estado → reduce ansiedad del cliente y llamadas de "¿qué pasa?".

---

## PARTE D — MULTI-OFICINA / ESCALA
- Jerarquía **Organization → Office → Team → User**; segregación por oficina + visión transversal
  del Owner.
- Permisos por **equipo** (onboarding rápido).
- Audit logs **exportables** para e-discovery/cumplimiento de barra.
- Aislamiento de datos por firma/oficina (si va multi-tenant).

---

## RESUMEN EJECUTIVO
- Roles: solo 3, RBAC parcial, **IDOR confirmado** (cualquier rol lee/edita objetos ajenos).
- Cliente: formulario por token decente y móvil-amigable, pero **sin login, sin mensajería, sin
  e-sign, sin notificaciones, sin estado explicado, sin pagos**; un token expone todo el caso.
- Recomendado: matriz de **9 roles** + `require_case_access` (mata IDOR); **login de cliente**,
  **mensajería bidireccional**, **e-sign**, **notificaciones**, **hub unificado**, **documentos
  selectivos**, **motor de fechas clave**, **audit log**. Todo esto hace el sistema completo,
  friendly, interactivo y fácil de usar para staff y clientes.
