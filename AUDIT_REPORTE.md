# AUDIT REPORTE — Imigratepro-2.0

Fecha: 2026-07-20
Alcance: Code review (read-only, NO se modificó ningún archivo) + benchmark de mercado
Autor: Hermes Agent (3 subagentes en paralelo: backend/seguridad, pipeline PDF/IA, frontend) + investigación web

---

## 1. RESUMEN EJECUTIVO

Imigratepro-2.0 es un sistema **muy avanzado para un MVP**: FastAPI + Next.js, 16 formularios
USCIS generados electrónicamente, portal de cliente, IA para revisión/gap/RFE, facturación,
Kanban, dashboard, USCIS case-status API, 147 tests de backend. La criptografía de auth es
**sólida** (PBKDF2+salt, timing-safe, dummy hash anti-enum, refresh rotation).

El problema central NO es la criptografía: es **autorización a nivel de objeto (IDOR) y RBAC
casi inexistentes**, más un **portal público sin lista blanca de campos**, y **tokens en
localStorage** en el frontend. Tras el breach de Docketwise (2026, 116.666 registros por
credenciales comprometidas), el estándar del sector subió: estos gaps son bloqueantes para
exponer el sistema a tráfico real con PII migratoria (SSN, pasaporte, A-number).

**Conteo de hallazgos de código:** 2 Critical-equivalentes, 9 High, 13 Medium, 13 Low
(sumarizando los 3 subagentes; ver detalle en §2).

**Cobertura de formularios:** el sistema llena 16; USCIS tiene ~107 formularios vigentes.
(Se validó aparte: 97 formularios / 253 PDFs descargados y 88 vigentes contra uscis.gov.)

---

## 2. HALLAZGOS DE CÓDIGO (priorizados)

### 🔴 CRÍTICO

**C1 — IDOR total (backend).** Cualquier usuario autenticado puede leer/modificar/BORRAR
cualquier caso, cliente, documento, factura, RFE, cita y formulario. `router.py:30-43` solo
exige autenticación (`get_current_user`), no rol ni propiedad; los endpoints de entidad ni
reciben `current_user`. Afecta `cases.py`, `clients.py`, `documents.py`, `billing.py`,
`rfes.py`, `appointments.py`, `forms.py`.
→ Fix: dependencia `require_case_access(current_user, case_id)` (case.assigned_attorney_id ==
  current_user.id OR admin) en todos los `/{id}`; o filtrar `list_*` por usuario salvo admin.

**C2 — Portal público sin allowlist de campos (pipeline).** `public_forms.py:56-82`:
`generated.data = {**generated.data, **payload.data}` permite a un cliente no autenticado
sobrescribir CUALQUIER campo (SSN del peticionario, nº de colegiado del abogado, A-number).
Combinado con H2/H3 expone y exfilra datos de todo el caso.
→ Fix: validar `payload.data` contra `client_editable_fields` del `field_schema`; rechazar
  claves fuera del conjunto (422).

### 🟠 HIGH

**H1 — RBAC roto:** el enum de 3 roles solo se respeta en `/users`. `paralegal` puede crear
casos, facturas, aplicar servicios, borrar todo. `users.py:75,100,123` vs `cases.py:24`,
`billing.py:72,113`, `services.py:118,180`.
→ Fix: `RequireRole(UserRole)` en rutas mutativas sensibles.

**H2 — `SECRET_KEY` default `"change-me-in-production"` solo avisa y arranca.** `config.py:17`,
`main.py:21-28`. En prod sin sobreescribir → cualquiera firma JWT de admin.
→ Fix: `sys.exit` si default en prod; o `Settings` sin default + validador de longitud.

**H3 — PII/facturación expuestos a cualquier usuario autenticado.** `clients.py:26` devuelve
SSN/pasaporte/A-number; `forms.py:229` sirve PDF de cualquier caso; `billing.py` sin control
de rol (fraude). Combinar con C1.

**H4 — `PATCH /public/forms/{token}` no valida nombres de campo antes de `pdf_filler`.**
`public_forms.py:63` + `pdf_filler.py:21-23`. Claves arbitrarias se guardan en `data` JSON.
→ Fix: limitar claves a `{f["name"] for f in template.field_schema}`.

**H5 (frontend) — JWT access+refresh en `localStorage` (XSS-exfiltrrable).** `lib/api.ts:3-4,12-23`.
El refresh es de larga duración y rota; XSS = fuga silenciosa de credenciales + PII.
→ Fix: cookies `httpOnly; Secure; SameSite=Strict` fijadas por backend; borrar localStorage.

**H6 (frontend) — `NEXT_PUBLIC_API_URL` default `http://localhost:8000`.** `lib/api.ts:1`.
Sin `.env*`, este es el default efectivo: tokens Bearer + PII viajan por HTTP claro (MITM).
→ Fix: default `https://` obligatorio; fallar el build si no está seteada.

**H7 (frontend) — Token de portal de cliente en la URL** (`api.ts:625-628`,
`forms/[id]/page.tsx:201-206`). Viaja en historial/Referer/proxy. Quien tenga el link tiene
lectura/escritura total del formulario.

### 🟡 MEDIUM

- **M1** Reset token en logs cuando SMTP no está configurado (`email.py:34` loguea `body` con
  el token crudo). → Nunca loguear tokens.
- **M2** SQLite sin `PRAGMA foreign_keys=ON` (`database.py:8`). → Activar en connect.
- **M3** `delete_client` sin cascade → IntegrityError/huérfanos (`client.py:39-40`, `case.py:88`).
- **M4** `create_case` no valida `case_number` duplicado → 500 con SQL en detail (`cases.py:24-29`).
- **M5** `invoice_number` no es seguro ante concurrencia (`billing.py:41-43`). → sequence/retry.
- **M6** Sin audit log en acciones destructivas/sensibles. Crítico para cumplimiento legal.
- **M7** Config sin validación ni `.env.example` (M7 del backend). Commitear `.env.example`.
- **M8** Inyección de prompt → PII escrita en `Client` sin validar formato (SSN no se verifica
  como 9 dígitos) (`documents.py:174-203`, `rfe_ai.py:76`, `form_review_ai.py:84`).
- **M9** Llamadas IA sin timeout/reintentos/tope de coste → cuelgue de hilo (`document_ai.py:93`,
  `form_review_ai.py:92`, `rfe_ai.py:71`). → `timeout=30` + backoff + límite de tamaño.
- **M10** I-864 se genera en blanco silencioso si falta participante rol `SPONSOR`
  (`form_field_maps.py:211-238` vs `form_data.py:53-73`).
- **M11** `content_type` del cliente decide cómo se envía a Claude → `.exe` como `application/pdf`
  (`documents.py:154-157`, `storage.py:14`). → Validar por magic bytes.
- **M12** (frontend) Sin `middleware.ts` (gate de edge ausente) y sin headers de seguridad/HSTS
  en `next.config.ts`.
- **M13** (frontend) Sin `error.tsx`/error boundary → crash a pantalla blanca.

### 🟢 LOW (resumen)

L1 config drift `ACCESS_TOKEN_ALGORITHM` no usado · L2 `Client.email` no unique · L3
`CaseParticipant` sin unique constraint · L4 `asyncio.get_event_loop()` deprecado · L5 sin
HTTPS/HSTS en `CLIENT_PORTAL_BASE_URL` default http · L6 CORS `allow_methods/headers=["*"]`
(validar que `allow_origins` no sea `"*"` con creds) · L7 merge libre en `update_public_form` ·
L8 `create_engine` sin `pool_pre_ping` · L9 `.all()` + procesar en Python en stats/dashboard ·
L10 `postcss<8.5.10` (build, transitivo Next) · L11 sin linting de seguridad (eslint-plugin-security) ·
L12 código muerto (`N_600K_AUTOFILL` no está en catálogo; ~8/15 formularios sin reglas
condicionales) · L13 re-render de PDF en cada autosave del cliente (DoS leve, ya limitado).

**Lo bueno (no tocar):** sin SQLi (ORM parametrizado), `decode_access_token` recalcula HMAC
(inmune a algorithm confusion), reset/refresh hasheados y single-use, rate-limit login/forgot,
dummy hash anti-timing, `storage.save_upload` usa uuid4 (sin traversal), `DocumentRead` no expone
`storage_path`, USCIS API bien manejada (401/404/422/429/503, token en memoria), `access_token`
`secrets.token_urlsafe(24)` no adivinable, frontend sin `dangerouslySetInnerHTML`/`eval`.

---

## 3. BENCHMARK DE MERCADO — QUÉ DEFINE "COMPLETO" (2026)

Fuentes: eimmigration (Cerenade), Docketwise, MyCase/8am, Lawfully, INSZoom (Mitratech),
LollyLaw, US Immigration AI, Imagility. Características base que estos sistemas ofrecen y que
Imigratepro-2.0 tiene o le faltan:

| Capacidad (estándar de mercado)            | Estado en Imigratepro-2.0 | Gap |
|--------------------------------------------|---------------------------|-----|
| Biblioteca de formularios USCIS completa + versionado automático | 16 de ~107; validado vigente contra uscis.gov (script aparte) | FALTAN ~91 formularios; no hay auto-actualización de edición |
| Autofill con datos del cliente (una sola fuente de verdad) | ✓ (motor genérico) | — |
| eFiling / presentación electrónica nativa  | ✗ | FALTA (hoy solo PDF descargable para enviar por correo) |
| Visa Bulletin tracking + alertas           | ✗ | FALTA |
| USCIS case-status API (tracking de recibos/RFE/aprobación) | ✓ (`uscis_case_status.py`) | OK; ampliar a push/notificaciones |
| Client portal seguro (mensajería 2-vías, upload) | ✓ (portal con token) | Inseguro (C2/H7); falta cookie httpOnly |
| e-Signature                                | ✗ | FALTA |
| Billing + IOLTA trust accounting           | ✓ facturación básica | Falta trust accounting (IOLTA) y conciliación |
| USCIS fee payment (virtual cards / Smart Spend) | ✗ | FALTA |
| SAVE / E-Verify verification               | ✗ | FALTA (verificación de elegibilidad) |
| Deadline calculator + reglas por categoria (visa bulletin, priority dates) | Parcial (citas/recordatorios) | Falta motor de plazos legales por tipo de caso |
| Workflows por tipo de caso (templates)     | ✓ motor básico | Ampliar catálogo de workflows |
| Multi-idioma (ES/EN)                        | ✓ | — |
| Reportes / analytics para el despacho       | ✓ `/stats` | — |
| Audit log / compliance                      | ✗ | FALTA (M6) — crítico legalmente |
| Seguridad post-breach 2026 (httpOnly cookies, HTTPS obligatorio, role scoping) | ✗ | FALTAN (C1/C2/H5/H6) |
| Multi-tenant (varios despachos)             | ✗ (1 DB por instalación, documentado) | Decisión de producto; si se hace, C1 es crítico absoluto |
| Móvil / app cliente (iOS/Android)           | ✗ | Opcional pero esperado (Lawfully tiene app) |

---

## 4. ROADMAP — LO QUE FALTA PARA "COMPLETO"

### Bloqueante antes de exponer a tráfico real (P0)
1. Cerrar IDOR (C1) + RBAC (H1) en backend — scoping por caso/abogado en todos los `/{id}`.
2. Allowlist de campos editables por cliente en portal público (C2/H4).
3. Mover tokens a cookies httpOnly + default API `https://` (H5/H6).
4. `SECRET_KEY` sin default inseguro (H2).
5. Audit log de acciones destructivas/sensibles (M6).

### Importante para "completo" de mercado (P1)
6. Ampliar biblioteca de formularios a ~107 + auto-actualización de edición (hoy 16; el
   script de descarga/validación ya hecho puede alimentar esto).
7. eFiling nativo (API de presentación) o integración con proveedor.
8. Visa Bulletin tracking + deadline calculator por tipo de caso.
9. e-Signature (DocuSign/anchor u otro).
10. SAVE/E-Verify verification.
11. IOLTA trust accounting + USCIS fee payment.
12. HTTPS/HSTS obligatorio, security headers (CSP), `middleware.ts`, `error.tsx`.
13. Timeouts/reintentos en IA (M9), validación de formato PII extraída (M8), magic bytes en uploads (M11).

### Diferenciadores / pulido (P2)
14. Workflow templates por tipo de caso (catálogo amplio).
15. App móvil cliente.
16. Limpieza: código muerto (L12), CORS/SECRET validation (L6/L1), `pool_pre_ping` (L8).
17. `pip-audit` + `npm audit` en CI (bloqueado en esta máquina por SSL; correr en CI).

---

## 5. METODOLOGÍA / LIMITACIONES

- Read-only: ningún archivo fue modificado. Los 3 subagentes leyeron ~70 archivos del backend,
  el pipeline de servicios y el frontend.
- No se ejecutó el código (sin BD/entorno en la revisión); los hallazgos son estáticos. M3/L4
  (checkbox values) y la validación real de autofill requieren ejecutar contra los PDFs de
  `form_templates/`.
- Benchmark de mercado basado en sitios oficiales de eimmigration, Docketwise, MyCase, Lawfully,
  INSZoom, US Immigration AI (2026) y la cobertura del breach Docketwise 2026.

## 6. ARCHIVOS DE EVIDENCIA (en este repo, generados aparte, no parte del código del proyecto)

- `backend/form_templates/uscis_forms/VALIDACION.txt` — vigencia de 97 formularios vs uscis.gov
- `backend/form_templates/uscis_forms/INDICE.txt` — índice de formularios descargados
