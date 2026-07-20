# Immigration Case Manager

Plataforma de gestión de casos migratorios: clientes, casos, documentos con extracción por IA, generación de formularios USCIS, seguimiento de citas, solicitudes de evidencia (RFE), panel diario por preparador, detección de documentos faltantes y cronograma del caso para el cliente.

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic, Python 3.13
- **Frontend**: Next.js (App Router) + React + TypeScript + Tailwind
- **Datos**: PostgreSQL en producción (SQLite por defecto en desarrollo local), Redis para tareas en background (Celery)

## Estructura

```
backend/    API FastAPI, modelos, migraciones Alembic
frontend/   Next.js
docker-compose.yml   Postgres + Redis + backend
```

## Desarrollo local (sin Docker)

Backend:

```
cd backend
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt
./.venv/Scripts/python -m alembic upgrade head
./.venv/Scripts/python -m app.seed_admin
./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Por defecto usa SQLite (`backend/migratepro.db`). Para usar Postgres, copia `backend/.env.example` a `backend/.env` y ajusta `DATABASE_URL`.

`app.seed_admin` crea el primer login (`admin@migratepro.local` / `changeme123` por defecto, o lo que digan `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` en `.env`) — **sin esto no hay forma de entrar**, porque todos los endpoints internos requieren sesión (ver [Autenticación](#autenticación) más abajo). Cambia la contraseña después del primer login.

Frontend:

```
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Abre http://localhost:3000. La API se sirve en http://localhost:8000/api/v1 (docs interactivas en http://localhost:8000/docs).

### Formularios USCIS

Los PDFs oficiales rellenables viven en `backend/form_templates/` — **16 formularios**: I-90, I-130, I-130A, I-131, I-485, I-589, I-751, I-765, I-864, G-28, N-336, N-400, N-470, N-565, N-600, N-600K. Después de aplicar las migraciones, carga el catálogo de formularios una vez:

```
cd backend
./.venv/Scripts/python -m app.seed_forms
```

Los formularios generados (con datos reales del cliente) se guardan en `backend/generated_forms/` — **contienen PII y nunca se deben commitear** (ya están en `.gitignore`).

**El formulario electrónico cubre el 100% de los campos del PDF en los 16 formularios** (desde 97 campos en G-28 hasta 736 en I-485): el inventario completo se extrae una vez por formulario con `scripts/extract_form_fields.py` (usa el tooltip oficial `/TU` de cada campo como etiqueta — texto real de USCIS con referencia de Parte/línea) y se guarda en `app/seed_data/field_inventories/*.json`. Al generar un formulario:

1. Se crea un `GeneratedForm` con una entrada por cada campo del PDF (texto, checkbox o choice), vacía por defecto.
2. El **autofill map** (`backend/app/seed_data/form_field_maps.py`) pre-llena automáticamente el subconjunto que sabemos resolver de forma confiable desde el cliente/caso: nombre, fecha de nacimiento, número A, país de nacimiento, dirección, sexo, estado civil, SSN, teléfonos y email — **298 mapeos en total** repartidos entre los 16 formularios, cada uno verificado campo por campo contra la etiqueta oficial del inventario (no adivinado por patrón de texto). Los checkboxes ligados a un valor tipo enum (sexo, estado civil) usan `match_value`/`set_value` en el mapeo: solo se marcan si el dato del cliente coincide con esa opción. Sigue siendo un subconjunto curado, no el 100%, porque el resto (historial migratorio, empleo, matrimonios previos, etc.) no se puede inferir de forma segura del modelo de datos actual y debe completarlo un abogado o paralegal. En formularios con más de un rol involucrado (I-864 "Affidavit of Support": patrocinador + inmigrante principal; G-28: abogado + beneficiario) el autofill respeta el rol correcto de cada sección — no mezcla los datos del patrocinador con los del inmigrante, por ejemplo.
3. En `/forms/{id}` (botón "Abrir formulario electrónico") se edita el resto campo por campo, agrupado por **Parte** del formulario (no por página — se parsea del propio tooltip oficial), con buscador de campos, barra de progreso y selector de fecha nativo para los campos de fecha.
4. Cada "Guardar" regenera el PDF completo con pypdf, incluyendo checkboxes y menús desplegables (verificado que `/AS` y `/V` quedan sincronizados para que el PDF se vea marcado correctamente en un lector real).

Para agregar un formulario nuevo: bajar el PDF a `form_templates/` (nombre de archivo en minúsculas, sin espacios ni acentos — ej. `i-485.pdf`, no el nombre descriptivo del portal de descarga de USCIS), correr `python scripts/extract_form_fields.py <archivo>.pdf`, y agregar la entrada en `FORM_TEMPLATES` de `form_field_maps.py` (el autofill map es opcional, el formulario funciona igual de completo sin él — `tests/test_forms.py` verifica que cada formulario del catálogo genere un PDF completo y descargable, así que un formulario nuevo mal registrado se detecta ahí).

**14 de los 16 formularios ya tienen reglas condicionales** (`app/seed_data/conditional_rules.py`, ver [Formulario dinámico](#formulario-dinámico-campos-condicionales) abajo) — I-130A y N-600K quedaron deliberadamente sin reglas porque no se encontró un patrón "If you answered..." limpio y verificable en su texto oficial; en esos dos, todos los campos se siguen mostrando siempre (mostrar de más es preferible a ocultar por error).

Antes de usar un PDF generado en una presentación real ante USCIS, un abogado debe revisarlo campo por campo contra las instrucciones vigentes de la edición correspondiente.

### Multi-idioma

Selector ES/EN fijo en la esquina superior derecha (`frontend/src/lib/i18n.tsx`, contexto + diccionario, persistido en `localStorage`). Cubre toda la interfaz propia de la app (navegación, formularios, mensajes). Las etiquetas oficiales del formulario electrónico tienen además un botón independiente "Ver traducción al español" en `/forms/{id}`: es una traducción de referencia por sustitución de frases (`frontend/src/lib/formLabelTranslations.ts`), pensada para ayudar a completar el formulario — **no reemplaza el texto oficial en inglés**, que es el único válido para presentar ante USCIS. Las frases no reconocidas se dejan en inglés en vez de adivinarse — el diccionario de frases se construyó contra I-130/I-765/G-28, así que en los 13 formularios agregados después (ver [Formularios USCIS](#formularios-uscis)) la cobertura de esta traducción de referencia es más baja por ahora; el formulario en sí funciona igual, solo se ve más texto en inglés en ese botón de referencia. `backend/scripts/check_translation_coverage.py` mide la cobertura pero solo revisa esos 3 formularios originales todavía.

### Formulario dinámico (campos condicionales)

Algunos campos solo se muestran si la respuesta a otro campo lo amerita — por ejemplo, la dirección física del peticionario (I-130 Línea 12) solo aparece si contestó "No" a "¿Es su dirección postal la misma que su dirección física?" (Línea 11); las opciones de "hijo/padre" (Parte 1, Línea 2) solo aparecen si seleccionó "Child" o "Parent" en la Línea 1. Estas reglas viven en `backend/app/seed_data/conditional_rules.py` como `show_if: [{field, equals}]` adjuntado a cada entrada del `field_schema`, y **solo se agregaron para relaciones verificadas textualmente contra el tooltip oficial de la pregunta compuerta** (busca "If you answered..." o "If you are filing..." en el texto) — no se infirió condicionalidad por adivinanza, porque ocultar un campo requerido por error sería peor que mostrar uno de más. Al cambiar la respuesta que oculta un campo, su valor se limpia automáticamente al guardar para no dejar datos contradictorios en el PDF.

### Equipo (`/team`) y asignación de casos

Gestionar personal solía ser un formulario rápido embebido en `/cases` ("+ Nuevo miembro del equipo"). Ahora es su propio módulo, `/team`, con vista de directorio + carga de trabajo:

- `GET /users/workload` calcula, en una sola pasada (sin N+1 por usuario), la carga de cada miembro del personal: casos asignados (y su desglose por estado), RFEs abiertas en esos casos, e ítems de checklist vencidos asignados a esa persona — la versión "para todo el equipo" del panel ["Mi día"](#panel-mi-día-dashboard-del-preparador) de cada individuo.
- `PATCH /users/{id}` (nuevo, antes solo existía `POST` para crear) permite a un `admin` editar rol, datos de contacto, y **desactivar/reactivar** una cuenta (`is_active`, ya existía en el modelo `User` pero no estaba expuesto). Dos guardarraíles del lado del servidor: nadie puede desactivar su propia cuenta, y no se puede quitar el rol de admin al último admin activo del sistema (evita quedarse sin nadie que pueda administrar).
- El personal desactivado **deja de aparecer como opción al asignar trabajo nuevo** — en el selector "Asignado a" de `/cases`, en el responsable de un ítem del checklist, y en el selector de reasignación del tablero Kanban — pero conserva su nombre visible en los casos que ya tenía asignados (no se pierde el historial).
- `POST /users` (crear) y `POST /users/{id}/password` (resetear la contraseña de otra persona) siguen restringidos a `admin` del lado del servidor — ver [Autenticación](#autenticación).

`/cases` mantiene el selector "Asignado a" por caso (`PATCH /cases/{id}` con `assigned_attorney_id`), y ahora enlaza a "Gestionar equipo →" en vez de abrir el formulario embebido.

### Enlace seguro para que el cliente complete el formulario

Cada `GeneratedForm` tiene un `access_token` aleatorio (`secrets.token_urlsafe`, no es el UUID interno) que da acceso — sin login — únicamente a ESE formulario y a subir documentos para ESE caso, nada más (no se puede listar otros casos ni clientes a través del token). El botón "Copiar enlace" en `/forms/{id}` genera `/client/forms/{token}`, una página pública (`frontend/src/app/client/forms/[token]/page.tsx`) con el mismo editor de campos (reutiliza `FieldInput` y los helpers de `formFieldHelpers.ts`) más una sección de subida de documentos.

Backend: `app/api/v1/endpoints/public_forms.py` — `GET/PATCH /public/forms/{token}` (mismo motor de relleno de PDF que el endpoint interno) y `POST /public/forms/{token}/documents` (multipart, guarda en `backend/uploaded_documents/{case_id}/`, máx. 20 MB, nunca confía en el nombre original del archivo para la ruta en disco). El enlace se puede desactivar poniendo `client_link_enabled=false` sin perder el token (por si se reactiva).

**Nota de seguridad importante**: a propósito, `/public/forms/{token}` sigue sin requerir login (así es como el cliente accede sin cuenta) — la "seguridad" del enlace depende enteramente de la aleatoriedad del token (24 bytes, no adivinable) y de que cada token solo destrabe un formulario puntual — no es aún un sistema con expiración, límite de usos, ni verificación adicional (ej. confirmar fecha de nacimiento antes de mostrar el formulario). Razonable para una demo/MVP; antes de producción real conviene agregar expiración y, si se quiere más rigor, un segundo factor de verificación.

## Con Docker

```
docker compose up --build
```

Levanta Postgres, Redis y el backend. El frontend sigue corriendo con `npm run dev` en desarrollo.

## Diseño

`frontend/src/components/AppShell.tsx` es el layout compartido de toda la app interna: sidebar con navegación (Panel, Clientes, Casos, Servicios, Formularios, Documentos, Citas, Facturación, Reportes) + barra superior con el selector de idioma. `AppShell` también es donde vive la protección de sesión: si `useAuth()` no está autenticado, redirige a `/login` en vez de renderizar la página (así ninguna pantalla interna necesita repetir esa lógica). Primitivas reutilizables en `components/ui/` (`Button`, `Card`, `Badge` con color por estado) reemplazan los botones/contenedores repetidos a mano. Acento de color: índigo (antes todo era blanco/negro). El portal público del cliente (`/client/forms/{token}`) y `/login` **no** usan el AppShell a propósito — son pantallas aparte, sin la navegación interna, con su propio selector de idioma flotante.

### Auditoría UX/UI y correcciones

Tras una revisión de accesibilidad y responsividad se corrigieron varios problemas reales encontrados en el código:

- **Responsive real**: la app no tenía ni un solo breakpoint (`sm:`/`md:`) — el sidebar fijo de 224px rompía cualquier pantalla angosta. Ahora `AppShell` tiene un drawer móvil (botón hamburguesa + overlay) y el sidebar de escritorio se oculta bajo `md:`; las tablas usan `overflow-x-auto`; el editor de 438 campos (`FieldRow.tsx`) apila el label sobre el input en móvil en vez de forzar dos columnas.
- **Íconos reales en vez de glifos Unicode**: el sidebar usaba caracteres tipo `◆ ◒ ▤` sin relación visual entre sí. Se reemplazaron por SVG en línea (sin dependencia externa) con `aria-hidden`.
- **Labels accesibles**: varios formularios (clientes, casos, servicios, documentos) usaban `placeholder` como único indicador del campo — falla WCAG porque no hay nombre accesible ni el texto persiste al escribir. Todos los inputs ahora tienen `<label>` visibles.
- **Selects sin traducir**: tipo de caso, estado, rol de participante, rol de usuario y tipo de documento se mostraban en inglés/snake_case sin importar el idioma elegido. Se agregaron diccionarios `enum.*` en `lib/i18n.tsx` y `Badge` ahora acepta un `label` separado del `value` que determina el color.
- **Estado vacío roto**: agregar un participante a un caso sin clientes cargados dejaba un `<select>` vacío y fallaba en silencio. Ahora se muestra un mensaje explicando qué falta.
- **Objetivos táctiles**: checkboxes de checklist y del formulario electrónico ahora usan una `<label>` envolvente con `min-h-11` (44px) como área de toque, no solo el cuadrito visual de 16-20px.
- **Foco de teclado consistente**: `Button` ahora tiene el mismo anillo de foco (`focus-visible:ring-2 ring-indigo-400`) que los inputs, antes dependía del outline por defecto del navegador.

## Catálogo de servicios y workflow

Implementa la pieza que pediste priorizar de la visión de ERP: un `Service` (ej. "Petición Familiar") empaqueta qué formularios USCIS incluye, un checklist, y las etapas del flujo de trabajo. Al aplicar un servicio a un caso (`POST /cases/{id}/apply-service`):

1. Se copia el checklist del catálogo al caso (`CaseChecklistItem` — snapshot, no una referencia, para que editar el catálogo después no cambie casos ya abiertos).
2. El caso queda en la primera etapa del workflow (`Case.workflow_stage_id`).
3. **Se generan automáticamente los formularios que el servicio incluye** (reutiliza el mismo motor de autofill + relleno de PDF que la generación manual) — es decir, aplicar "Petición Familiar" ya deja el I-130 y el G-28 generados y listos para completar, sin que el abogado tenga que ir uno por uno a `/forms`.

Desde `/cases`, cada caso expandido muestra el servicio aplicado, las etapas (con la actual resaltada y un botón para avanzar), el checklist con checkboxes, y links directos a los formularios que ese servicio generó. `/services` es el catálogo: crear un servicio nuevo pide nombre/precio/tiempo estimado, qué formularios incluye (checkboxes sobre los `FormTemplate` existentes), el checklist (una línea por ítem) y las etapas (una línea por etapa, en orden). Viene precargado un servicio de ejemplo ("Petición Familiar": I-130 + G-28, 7 ítems de checklist, 12 etapas) vía `backend/app/seed_services.py`.

### Checklist con responsable, fecha límite y prioridad

Cada ítem del checklist (`CaseChecklistItem`) ahora tiene `assigned_to_id` (referencia a `User`), `due_date` y `priority` (baja/media/alta), editables inline desde `/cases` sin salir de la fila del checklist. `PATCH /cases/{id}/checklist/{item_id}` acepta cualquier subconjunto de `done`/`assigned_to_id`/`due_date`/`priority`.

### Tablero Kanban de casos

`/cases` tiene un selector Lista/Tablero. El tablero (`frontend/src/components/CasesBoard.tsx`) agrupa los casos por `Case.status` (el estado global de 7 valores, no las etapas de servicio que son específicas de cada `Service`) en columnas arrastrables — soltar una tarjeta en otra columna llama a `PATCH /cases/{id}` con el nuevo estado (drag-and-drop nativo de HTML5, sin librería). Un clic en el número de caso cambia a la vista de lista con ese caso ya expandido.

**Asignación directa desde la tarjeta**: antes, reasignar un caso desde el tablero requería salir a la vista de lista. Cada tarjeta ahora tiene un chip con las iniciales del responsable (color determinístico por `user.id`, así la misma persona siempre se ve igual en todo el tablero) junto a un selector inline — cambiar el responsable ahí mismo llama a `PATCH /cases/{id}` sin salir del tablero ni perder el drag-and-drop (el click en el `<select>` detiene la propagación para no disparar el `onClick` de apertura de la tarjeta). El selector solo ofrece personal activo (ver [Equipo](#equipo-team-y-asignación-de-casos)), salvo que el caso ya esté asignado a alguien desactivado — en ese caso esa persona aparece igual como opción actual, para no perder de vista quién lo tiene. Un selector "Filtrar por responsable" arriba del tablero reduce las columnas a los casos de una sola persona (o a los sin asignar) sin tocar el servidor — filtrado en el cliente sobre los casos ya cargados.

### Centro de notificaciones

Los *eventos* siguen siendo un feed global (`Notification`) en vez de estar filtrados por usuario o rol — todo el personal de un mismo despacho suele querer ver los mismos eventos de caso. Lo que **sí** es por usuario es el estado de lectura: `NotificationSeen` (`user_id`, `notification_id`) registra qué notificaciones vio cada quien, calculado del lado del servidor (`GET /notifications` devuelve `read` por notificación para el usuario autenticado; `POST /notifications/mark-read` y `POST /notifications/mark-all-read` marcan). Antes de tener login esto vivía en `localStorage` (un "última vez visto" por navegador); con sesión real, el contador de no leídas ahora es consistente entre pestañas/dispositivos para la misma persona. Eventos que generan notificación: caso reasignado, etapa de servicio avanzada, documento subido (tanto desde `/documents` como desde el enlace público del cliente), revisión de IA de un formulario con al menos un hallazgo, cita programada, recordatorio de cita enviado, pago recibido, y factura vencida. Campanita en la barra superior (`components/NotificationBell.tsx`), con sondeo cada 30s — sin infraestructura de tiempo real ni de correo (salvo los recordatorios/vencidas, que sí mandan correo — ver [Recordatorios automáticos por correo](#recordatorios-automáticos-por-correo)).

## Documentos + extracción por IA

`backend/app/services/document_ai.py` envía una imagen o PDF de un documento de identidad (pasaporte, actas, I-94) a Claude (`claude-opus-4-8`, salida forzada a JSON vía `output_config.format`/json_schema) y devuelve nombre, apellido, fecha de nacimiento, país de nacimiento, nacionalidad, número de pasaporte, número A y notas de confianza (el modelo deja vacío lo que no pueda leer con certeza, en vez de adivinar). Requiere `ANTHROPIC_API_KEY` en `backend/.env`; si no está configurada, `GET /api/v1/documents/ai-status` reporta `configured: false`, el botón "Extraer datos con IA" se oculta en `/documents`, y el endpoint `POST /documents/{id}/extract` responde 503 en vez de fallar de forma confusa — el resto del módulo (subir, listar, borrar documentos) funciona igual sin la key.

Desde `/documents`: subir un documento (vinculado a un caso, opcionalmente a un cliente, con tipo de documento), extraer sus datos con un clic, y "Aplicar al cliente" copia los campos extraídos (nombre, apellido, fecha de nacimiento, país de nacimiento, nacionalidad, pasaporte, número A) directo al `Client` vinculado — solo si el documento tiene un cliente asignado. Backend: `app/api/v1/endpoints/documents.py` (`GET/POST /cases/{id}/documents`, `GET/PATCH/DELETE /documents/{id}`, `POST /documents/{id}/extract`, `POST /documents/{id}/apply-to-client`).

## Revisión de formularios con IA

En `/forms/{id}` (el formulario electrónico), el botón "Revisar con IA" envía las respuestas ya llenadas del formulario más los datos de referencia del cliente/caso (`build_case_context`) a Claude (`app/services/form_review_ai.py`, mismo modelo `claude-opus-4-8`, con thinking adaptativo porque cruzar decenas de campos contra los datos del cliente es una tarea de razonamiento no trivial) y devuelve una lista de hallazgos con severidad (alta/media/baja) — contradicciones entre el formulario y los datos del cliente, contradicciones internas del propio formulario (ej. fecha de fin antes que fecha de inicio), valores mal formados, o respuestas que parecen placeholder ("asdf", "N/A"). Se guarda en `GeneratedForm.ai_review`/`ai_reviewed_at` para no perderse al recargar la página. **Es una ayuda de revisión, no una revisión legal final** — cada hallazgo debe verificarse, y el propio modelo recibe instrucciones explícitas de no inventar problemas que los datos no respalden. Igual que la extracción de documentos, requiere `ANTHROPIC_API_KEY`; sin ella el botón se oculta y el endpoint (`POST /forms/{id}/review`) responde 503 en vez de fallar de forma confusa.

## Rendimiento del editor de formularios

Escribir en un campo del formulario de 438 campos causaba que TODO el formulario se volviera a renderizar en cada tecla (porque el `onChange` de cada campo se recreaba en cada render y ningún campo estaba memoizado), lo cual se sentía como que la página se congelaba un instante por cada letra escrita. Se resolvió extrayendo cada fila de campo a un componente memoizado (`frontend/src/components/FieldRow.tsx`, usado tanto en `/forms/{id}` como en el portal público del cliente) con un callback de cambio estable (`useCallback`) — ahora escribir en un campo solo vuelve a renderizar ESE campo, no los otros ~400.

## Estado del caso ante USCIS (API oficial)

En `/forms/{id}`, una vez que un formulario tiene número de recibo (asignado por USCIS cuando se presenta), se puede guardar ese número y consultar el estado del caso directamente contra la **Case Status API** oficial de USCIS (`developer.uscis.gov`, plataforma "Torch") — sin scraping, sin cookies de sesión, sin automatizar el portal `myUSCIS`: es la API pública documentada, con OAuth 2.0 client-credentials (`app/services/uscis_case_status.py`). Es una consulta de **solo lectura**, un número de recibo a la vez — no permite presentar nada, no lista los casos de un despacho en bloque, y no empuja notificaciones (hay que volver a preguntar para ver si algo cambió).

Requiere `USCIS_API_CLIENT_ID`/`USCIS_API_CLIENT_SECRET` en `backend/.env`; sin ellas `GET /api/v1/uscis/status` reporta `configured: false`, el botón "Consultar estado" se oculta en `/forms/{id}` (aunque guardar el número de recibo sigue funcionando igual, sin requerir la API), y `POST /forms/{id}/check-status` responde 503 en vez de fallar de forma confusa — mismo patrón de degradación que la integración con Claude.

**Obtener credenciales reales no es algo que este código pueda hacer por vos**: hay que registrar una app de desarrollador en `developer.uscis.gov`, probarla contra el sandbox (funciona de inmediato con los números de recibo de prueba que publica USCIS, sin registro aparte para esa capa) durante un mínimo de 5 días consecutivos, y después pedir acceso a producción escribiendo a `developersupport@uscis.dhs.gov`. El sandbox limita a 5 TPS / 1.000 solicitudes por día; producción sube a 10 TPS / 400.000 por día (el cupo se reinicia a medianoche hora del Este). El propio Terms of Use de USCIS reconoce esta modalidad como una categoría de cuenta legítima y separada del portal de trámites ("managed technical access to the developer portal") — exige usar tus propias credenciales de desarrollador registradas, nunca automatizar ni compartir el login del portal `myUSCIS`, que es exactamente lo que hace esta integración.

`get_case_status()` reintenta una vez con un token nuevo si la API responde 401 (el token puede haber expirado del lado de USCIS entre el caché local y la llamada), y traduce los códigos de error documentados a mensajes claros: 404 (recibo no encontrado, o protegido bajo 8 U.S.C. § 1367 — la respuesta no permite distinguir cuál), 422 (formato de recibo inválido), 429 (límite de tasa excedido) y 503 (mantenimiento del lado de USCIS). La respuesta cruda se guarda tal cual en `GeneratedForm.uscis_status_raw` (texto de estado y descripción en inglés y español, más el historial `hist_case_status`) junto con `uscis_status_checked_at` — no se fuerza una estructura interna fija porque el sandbox no permite verificar de antemano cómo luce cada variante real de la respuesta (el esquema difiere levemente para números de recibo con prefijo IOE).

## Autenticación

Login por email/contraseña con un access token JWT de corta duración (HS256, firmado y verificado a mano en `app/core/security.py` con `hmac`/`hashlib`/`secrets` de la librería estándar — sin dependencias nuevas) combinado con un refresh token opaco de larga duración:

- `POST /auth/login` devuelve `access_token` (30 min, `ACCESS_TOKEN_EXPIRE_MINUTES`) + `refresh_token` (30 días, `REFRESH_TOKEN_EXPIRE_DAYS`). El refresh token se guarda hasheado (SHA-256) en la tabla `refresh_tokens`, nunca en texto plano, así una fuga de la base de datos no entrega sesiones usables.
- `POST /auth/refresh` cambia un refresh token válido por un par nuevo y **revoca el anterior** (rotación de un solo uso) — si alguien reproduce un refresh token robado después de que el dueño legítimo ya lo usó, falla.
- `POST /auth/logout` revoca el refresh token actual del lado del servidor (no solo lo borra del navegador).
- El frontend (`frontend/src/lib/api.ts`) guarda ambos tokens en `localStorage`, adjunta el access token como `Authorization: Bearer` en cada request, y si una respuesta llega 401, intenta refrescar una vez y reintenta la petición original antes de rendirse y mandar al login — transparente para cada página, no hace falta manejarlo caso por caso.

**Todos los endpoints internos requieren sesión** (`app/api/v1/router.py` aplica `Depends(get_current_user)` a cada router salvo `auth` y `public_forms`) — el enlace público del cliente y `/health` siguen sin login, sin cambios ahí.

Solo un `admin` puede crear personal nuevo (`POST /users`) o resetear la contraseña de otra persona (`POST /users/{id}/password`); cualquier usuario puede cambiar la suya propia. El botón "+ Nuevo miembro del equipo" en `/cases` también se oculta del lado del cliente si el usuario logueado no es admin (`isAdmin` en `frontend/src/app/cases/page.tsx`), aunque la aplicación real de la regla es siempre el backend. Como no hay ningún usuario al arrancar una base nueva, `app/seed_admin.py` crea el primer admin directamente en la base de datos (ver arriba) — es la única puerta de entrada que no pasa por la API.

### Olvidé mi contraseña

`POST /auth/forgot-password` genera un `PasswordResetToken` de un solo uso (60 min, `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`, guardado hasheado igual que el refresh token) y manda un correo con el enlace `/reset-password/{token}` vía `app/services/email.py` — **siempre responde 204**, exista o no una cuenta con ese correo, para no filtrar qué emails están registrados. `POST /auth/reset-password` valida el token (no usado, no vencido), cambia la contraseña, marca el token como usado, y **revoca todos los refresh tokens activos de ese usuario** (si alguien tenía acceso y cambiaste la contraseña por eso, esa sesión muere ahí). Frontend: `/forgot-password` y `/reset-password/[token]`.

**Nota de seguridad**: el JWT sigue siendo deliberadamente simple — un solo `SECRET_KEY`, sin rotación de llaves. Razonable para una demo/MVP de un solo despacho; para multi-tenant real conviene una librería de JWT dedicada con soporte de rotación de llaves.

### Protección contra fuerza bruta

`app/core/rate_limit.py` es un limitador de ventana deslizante en memoria (sin Redis — mismo supuesto de una sola instancia que ya asume el scheduler, ver más abajo). Tres capas, cada una defendiendo un escenario distinto:

- **Bloqueo por cuenta**: `User.failed_login_attempts`/`locked_until` — tras `MAX_LOGIN_ATTEMPTS` (5) contraseñas incorrectas seguidas, la cuenta queda bloqueada `LOCKOUT_MINUTES` (15) sin importar desde qué IP se intente (`423 Locked`). Un login exitoso resetea el contador.
- **Límite por IP en `/auth/login`**: `LOGIN_RATE_LIMIT_PER_IP` intentos (20) cada `LOGIN_RATE_LIMIT_WINDOW_SECONDS` (5 min) — frena a alguien probando muchas cuentas distintas desde la misma IP, que el bloqueo por cuenta no cubre.
- **Límite por IP y por email en `/auth/forgot-password`**: `FORGOT_PASSWORD_RATE_LIMIT_PER_IP` (5) cada `FORGOT_PASSWORD_RATE_LIMIT_WINDOW_SECONDS` (15 min) — evita que se use el endpoint para bombardear la bandeja de entrada de alguien con correos de restablecimiento. Siempre responde 204 incluso rate-limitado, por la misma razón que responde 204 con emails inexistentes.

Cada solicitud de `forgot-password` también **invalida los enlaces de restablecimiento anteriores sin usar** de ese usuario — si pedís uno nuevo, el que quedó en un correo viejo (o filtrado) deja de servir.

Un sweep del scheduler (`app/services/token_cleanup.py`) borra periódicamente los refresh tokens y tokens de restablecimiento ya vencidos/revocados/usados (con 7 días de margen, por si hace falta mirarlos) — nada se rompe si nunca corre, solo evita que esas tablas crezcan indefinidamente.

## Citas y vencimientos

`/appointments` — cada `Appointment` (biométricos, entrevista, vencimiento de RFE, audiencia, consulta, u otro) está ligada a un caso, con fecha/hora, lugar y notas opcionales. Crear una cita notifica en el centro de notificaciones (`appointment_scheduled`). El modelo ya existía en el esquema inicial pero no estaba expuesto por la API; esta es la primera vez que tiene endpoints (`app/api/v1/endpoints/appointments.py`) y pantalla propia.

## Facturación y pagos

`/billing` — cada caso puede tener una o más `Invoice` (número autogenerado `INV-00001`, monto, descripción, fecha de vencimiento). Los pagos (`Payment`, con método y fecha) se registran contra una factura; `amount_paid` y `status` (borrador/enviada/pago parcial/pagada/vencida/cancelada) se **derivan** de la suma de pagos en vez de editarse a mano (`app/services/billing.py:recalculate`), así nunca quedan inconsistentes entre sí. Registrar un pago notifica `payment_received`; marcar vencidas (ver abajo) notifica `invoice_overdue`.

## Recordatorios automáticos por correo

`app/services/email.py` envía correo por SMTP si `SMTP_HOST` está configurado en `.env`; si no, **registra el mensaje en el log en vez de fallar** (mismo patrón de degradación elegante que la integración con Claude — probado de verdad contra un servidor SMTP local además de contra el camino sin configurar, no solo asumido). La lógica de cada sweep vive una sola vez en `app/services/reminders.py` (`send_appointment_reminders`, `mark_overdue_invoices`), compartida por dos caminos:

- **El scheduler en proceso** (`app/services/scheduler.py`): una tarea de `asyncio` arrancada desde el `lifespan` de FastAPI en `app/main.py` que corre ambos sweeps cada `SCHEDULER_INTERVAL_MINUTES` (60 por defecto). No es Celery beat — para dos consultas periódicas livianas, levantar un worker + beat scheduler separados era más infraestructura de la que esto necesita; Celery/Redis siguen en el stack para trabajo en segundo plano más pesado a futuro. Si el backend corre en más de una instancia, hay que apagar el scheduler en todas menos una (`SCHEDULER_ENABLED=false`) para no duplicar el trabajo, o migrar a Celery beat para que quede centralizado.
- **Los mismos endpoints manuales** (`POST /appointments/send-reminders`, `POST /invoices/mark-overdue`) siguen ahí por si quieres dispararlos a demanda (ej. justo después de cargar datos de prueba) — ya no son la única forma en que corren.

`app/main.py` también configura logging básico (`logging.basicConfig`) para que estos mensajes — y cualquier otro `logger.info`/`logger.exception` de la app — realmente aparezcan en algún lado; Uvicorn por defecto solo configura sus propios loggers (`uvicorn`, `uvicorn.access`), así que sin esto los mensajes de `email.py`/`scheduler.py` se perdían en silencio incluso estando "logueados".

## Panel de reportes

`/stats` — un solo vistazo al estado del despacho: clientes, casos totales/abiertos, casos por estado y por tipo, documentos, citas próximas (7 días) y sin recordatorio vencidas, facturación total/cobrada/pendiente, facturas vencidas, e ingresos facturados vs. cobrados de los últimos 6 meses. Todo calculado al vuelo en `app/api/v1/endpoints/stats.py` (sin tabla de agregados ni caché) — razonable mientras el volumen de datos sea el de un despacho, no el de una plataforma multi-tenant.

Nota técnica: SQLite ignora el `timezone=True` de las columnas `DateTime` y devuelve datetimes *naive* (Postgres sí los devuelve *aware*) — comparar eso directamente contra un `datetime.now(timezone.utc)` en Python (no en un filtro SQL) revienta con `TypeError: can't compare offset-naive and offset-aware datetimes`. `_as_aware()` en `stats.py` normaliza antes de comparar; hay una prueba de regresión específica para esto en `tests/test_stats.py`.

## Alineación con el modelo de negocio (blueprint del despacho)

El despacho compartió un documento de modelo de negocio describiendo cómo debería operar el sistema de punta a punta: intake → formularios → documentos → revisión → expediente → seguimiento. Cuatro piezas concretas de ese documento se implementaron en esta ronda; dos quedaron explícitamente fuera de alcance (ver abajo) en vez de construirse a medias.

### Solicitudes de evidencia (RFE)

Antes, un RFE de USCIS solo existía como un valor de `CaseStatus` (`rfe`) sin ningún lugar donde registrar qué pedía la carta ni armar la respuesta. Ahora es una entidad propia: `RFE` (fecha de recepción, fecha límite de respuesta, estado abierta/respondida/cerrada, texto de la notificación) con una lista de `RFEEvidenceItem` (checklist de qué reunir, con estado pendiente/reunida/enviada). `POST /cases/{id}/rfes` registra una nueva RFE, mueve el caso a estado `rfe` (solo si venía de intake/preparación/presentado — nunca pisa un estado posterior como aprobado o denegado) y genera una notificación. `backend/app/services/rfe_ai.py` (mismo patrón que la extracción de documentos y la revisión de formularios: requiere `ANTHROPIC_API_KEY`, degrada a 503 sin ella) puede sugerir ítems de checklist a partir del texto pegado de la notificación — **siempre como borrador editable, nunca se agregan automáticamente sin que el preparador los revise y acepte uno por uno** (botón "Agregar al checklist" por sugerencia, ver `RfePanel.tsx`). Esto es la versión real del "asistente de RFE" descrito en el documento: un wizard no habría sido más que este mismo flujo con más pasos.

### Panel "Mi día" (dashboard del preparador)

El documento describe un panel por preparador tipo "Leonel Salvador — Hoy tiene: 12 expedientes, 3 entrevistas, 5 expedientes listos para revisión, 2 RFEs pendientes". `GET /dashboard/me` calcula exactamente eso para el usuario logueado: casos asignados, citas de hoy, ítems de checklist vencidos o por vencer asignados a esa persona (sin importar de qué caso), RFEs abiertas en sus casos, y casos en estado "preparando" con el checklist 100% completo (listos para pasar a revisión). Se muestra arriba de la grilla de módulos en la página de inicio (`frontend/src/app/page.tsx`) — no es una pantalla nueva separada, es lo primero que se ve al entrar.

### Documentos e información faltante (gap analysis)

El documento da ejemplos concretos: "Falta el pasaporte", "el acta de matrimonio no fue cargada", "existe un matrimonio anterior y falta la sentencia de divorcio". De esos, se implementaron los que se pueden verificar de forma determinística contra el modelo de datos actual: falta petición/beneficiario en un caso, falta pasaporte o ID con foto, falta acta de nacimiento (beneficiario/derivado), falta acta de matrimonio (si `marital_status == married`), perfil de cliente incompleto (fecha de nacimiento/país/nacionalidad/dirección), y formularios del servicio aplicado que aún no se generaron. **A propósito no se implementó** verificar el ingreso mínimo del I-864 ni encadenar "hay un matrimonio anterior → falta la sentencia de divorcio" — ninguno de los dos se puede resolver de forma confiable con los campos que hoy tiene `Client` (no hay ingreso anual ni historial de matrimonios previos), y adivinar un umbral legal sería peor que no mostrarlo — mismo criterio ya aplicado a las reglas condicionales de formularios. `GET /cases/{id}/gap-analysis` (`app/services/gap_analysis.py`) se calcula al vuelo, sin tabla propia, y se muestra en el detalle de cada caso en `/cases`.

### Referencia de requisitos oficiales de USCIS (no un chatbot legal)

El pedido de "integrar la IA con todas las leyes de inmigración" es, tomado literalmente, una promesa que ninguna IA actual puede cumplir de forma confiable — USCIS actualiza su Policy Manual constantemente, los requisitos varían por categoría dentro del mismo formulario, y una respuesta plausible pero incorrecta de un modelo de lenguaje sobre un caso migratorio real es un riesgo serio, no una función. En vez de construir un chat abierto de "preguntale lo que quieras sobre inmigración" (que inevitablemente alucinaría en los casos límite donde más importa acertar), se construyó algo más angosto y verificable: una **biblioteca curada de qué pide USCIS oficialmente** para 7 de los 16 formularios del catálogo (I-130, I-485, I-765, N-400, I-751, I-131, I-90), extraída de una investigación real contra `uscis.gov` (`app/seed_data/uscis_requirements.py`) — **cero contenido generado por IA**: cada categoría de evidencia se verificó a mano contra la fuente oficial citada, no se le pidió a ningún modelo que "adivinara" qué requiere un formulario.

- `GET /form-templates/{code}/requirements` expone la ficha de un formulario (categorías + fuente + fecha de verificación); 404 (no una lista vacía) si el formulario todavía no tiene ficha, para que el frontend distinga "no hace falta nada" de "todavía no lo cubrimos" — mismo criterio que ya se usa en el resto de la app para no fingir cobertura que no existe.
- El endpoint de [gap analysis](#documentos-e-información-faltante-gap-analysis) ahora también devuelve `reference_checklist`: la ficha oficial de cada formulario ya generado en el caso, para verla junto a (pero **separada de**) los faltantes calculados automáticamente — un dato es una regla determinística sobre los datos del caso, el otro es texto oficial de USCIS; mezclarlos habría hecho parecer que la IA "sabe" algo que en realidad es una cita.
- Cada ficha se muestra con un `<details>` colapsable (`frontend/src/components/FormRequirementsDetails.tsx`, reusado en el detalle de caso y en `/forms` al elegir un formulario para generar) con enlace a la fuente oficial, fecha de verificación, y el mismo disclaimer siempre visible: *"Referencia informativa, no es asesoría legal — verifica contra las instrucciones oficiales vigentes antes de presentar."*
- **Deliberadamente sin montos de cuotas (`filing fees`)**: USCIS cambió buena parte de su esquema de cuotas recientemente (incluyendo una pausa temporal en la cuota del I-765 bajo la ley H.R. 1) y las fuentes consultadas durante esta investigación ya mostraban cifras contradictorias entre sí para el mismo formulario según la fecha de la fuente — un monto fijo en el código quedaría desactualizado más rápido que los requisitos procedimentales, y mostraría un número mal a alguien presentando un caso real. La app no calcula cuotas; en su lugar, siempre hay que remitirse a la [calculadora oficial de USCIS](https://www.uscis.gov/feecalculator).
- `uscis.gov` bloquea fetches automatizados (403), así que cada ficha se verificó con una pasada de investigación humana en la fecha registrada como `verified_on` por formulario, cruzada contra un servicio especializado de trámites (CitizenPath) para completitud — no es una integración en vivo que vuelva a consultar la fuente en cada request, es una instantánea con fecha, igual que un abogado consultaría el sitio oficial periódicamente en vez de asumir que nunca cambia.

Los otros 9 formularios del catálogo (I-130A, I-589, I-864, G-28, N-336, N-470, N-565, N-600, N-600K) no tienen ficha todavía — mismo criterio que las reglas condicionales y el gap analysis: mejor no tener referencia que tener una inventada.

### Cronograma visual para el cliente

El documento pide reducir llamadas dejando que el cliente vea el estado de su caso: "✔️ Consulta inicial, ✔️ Contrato, ✔️ Formularios... 🟡 Enviado a USCIS, ⚪ Biométricos, ⚪ Entrevista, ⚪ Decisión". `app/services/timeline.py` arma exactamente esa secuencia de 9 pasos a partir de datos que ya existen (servicio aplicado, formularios generados, documentos subidos, checklist, `Case.status`, tipo de citas) — nada nuevo que mantener a mano. Es deliberadamente **secuencial y no independiente por paso**: si un caso llega a "aprobado" sin haber pasado por "expediente preparado" (por ejemplo, se cambió el estado a mano sin completar el checklist), el cronograma muestra el primer paso realmente incumplido como "en curso" en vez de saltar directo a "decisión" — más legible para un cliente que un tablero de casillas sueltas que no cuentan una historia coherente. Visible en dos lugares: dentro de cada caso en `/cases` (vista interna) y arriba del formulario en el portal público `/client/forms/{token}` (vista del cliente, sin login) vía `frontend/src/components/CaseTimeline.tsx`.

### Explícitamente fuera de alcance en esta ronda

El documento también describe una **aplicación móvil** y **"JTLS Academy"** (un área de contenido educativo dentro del portal: videos, guías por tipo de trámite, preguntas frecuentes, recomendaciones para entrevistas, novedades migratorias revisadas por la firma). Ninguna de las dos se construyó — no porque sean poco importantes, sino porque una versión real de cualquiera de las dos es un proyecto en sí mismo (una app móvil nativa/híbrida completa; una plataforma de contenido con autoría, revisión editorial y versionado) y una versión superficial (una pantalla estática con texto de relleno, o un WebView del mismo Next.js sin nada específico de móvil) no sería honesta como "implementación" de lo que el documento describe. Quedan como gaps conocidos, no como hechas a medias.

Tampoco se construyó un **asistente de IA de preguntas y respuestas abierto sobre inmigración** ("chatea con la IA sobre tu caso" / "IA que conoce todas las leyes"). Cada integración de IA que existe en la app (extracción de documentos, revisión de formularios, sugerencias de evidencia para RFE) sigue el mismo patrón a propósito: la IA solo procesa datos que el usuario ya proveyó, nunca inventa hechos legales, y todo lo que produce queda como borrador editable que un humano revisa antes de que cuente para algo. Un chat abierto rompe ese patrón — no hay forma de garantizar que no alucine un requisito, una cuota, o un plazo que no existe. En su lugar se construyó la [referencia de requisitos oficiales de USCIS](#referencia-de-requisitos-oficiales-de-uscis-no-un-chatbot-legal): texto real citado, no generado, con fuente y fecha verificables.

## Auditoría de seguridad, verificación de formularios y pre-deploy

Revisión completa antes de exponer esto a tráfico real: seguridad del backend, generación electrónica de los 16 formularios, Docker, y UX del editor de formularios. Encontró y corrigió bugs reales, no solo cosas hipotéticas.

### Seguridad

- **Filtración de horario en el login (user enumeration)**: `POST /auth/login` corría `verify_password` (PBKDF2, ~260k iteraciones, deliberadamente lento) solo cuando el email existía — un email inexistente rechazaba visiblemente más rápido que una contraseña incorrecta para un email real, aunque el mensaje de error fuera idéntico en ambos casos. Se corrigió para que siempre corra el mismo hash PBKDF2 (uno de relleno cuando no hay usuario), igualando el tiempo de respuesta independientemente de si el email existe.
- **Validación de contraseña inconsistente**: `POST /users` (crear personal con contraseña inicial) no exigía el mínimo de 8 caracteres que sí exigen `POST /users/{id}/password` y `POST /auth/reset-password` — era el único punto de entrada de contraseña sin ese piso. Ahora los tres son consistentes.
- **Sin límite de tamaño en los datos del formulario**: `PATCH /forms/{id}` y `PATCH /public/forms/{token}` aceptaban un diccionario `data` de tamaño arbitrario (cualquier cantidad de campos, valores de cualquier largo) antes de guardarlo y pasarlo a pypdf. Ahora está acotado a 2000 campos (el formulario más grande del catálogo, I-485, tiene 736) y 20.000 caracteres por valor — de sobra para cualquier campo real, pero ya no ilimitado.
- **Sin límite de tasa en el portal público del cliente**: `/public/forms/{token}/*` no tenía ningún control de tasa — el token en sí es imposible de adivinar (24 bytes aleatorios), pero nada impedía que un cliente automatizado forzara regeneraciones de PDF (trabajo de CPU y disco) sin límite. Ahora está limitado a 60 solicitudes/minuto por token.
- **Advertencia de arranque si `SECRET_KEY` sigue siendo el valor por defecto**: antes no había ninguna señal si alguien desplegaba sin cambiar `change-me-in-production` — esa clave firma cada access token y verifica cada refresh/reset token. Ahora el arranque del backend deja un `WARNING` explícito en el log si no se cambió.
- **Auditoría de orden de rutas en FastAPI**: se revisaron sistemáticamente los 17 archivos de endpoints buscando el mismo patrón de bug ya encontrado dos veces antes (una ruta literal registrada *después* de una ruta con parámetro dinámico del mismo prefijo queda tapada — ver `/rfes/ai-status` y `/users/workload` en secciones anteriores). No se encontraron instancias nuevas.
- **`npm audit`**: una vulnerabilidad moderada (XSS en la salida de PostCSS, `GHSA-qx2v-qp2m-jg93`) vive dentro de la copia de PostCSS que Next.js empaqueta internamente como herramienta de build — no hay una versión estable de Next 16 que la resuelva todavía (el fix está en un canary/preview de 16.3, no en una versión estable), y el "fix" automático de `npm audit fix --force` degradaría a Next 9 (rompería toda la app). Riesgo práctico bajo: es una herramienta de build-time, la app nunca compila CSS suministrado por un usuario en tiempo de ejecución. Queda documentado para revisar cuando salga una 16.3 estable.
- **`pip-audit` no pudo correr en esta máquina** (error de verificación SSL al conectar con `pypi.org` desde este entorno) — recomendado correrlo en CI o en otra máquina antes de desplegar: `pip install pip-audit && pip-audit -r backend/requirements.txt`.

### Verificación real de que los 16 formularios se llenan electrónicamente

Más allá de "el PDF se genera y no tira error" (lo que ya cubría `test_forms.py`), se armaron dos verificaciones nuevas y permanentes:

1. **Cada entrada de cada mapa de autofill (`app/seed_data/form_field_maps.py`, 298 entradas) referencia un campo que realmente existe** en el inventario oficial del formulario (`field_inventories/*.json`). Sin esto, un nombre de campo mal tipeado falla en silencio: `pypdf.update_page_form_field_values()` simplemente ignora nombres de campo que no reconoce, así que el PDF se genera igual, con el mismo conteo de campos, sin ningún error visible — el campo específico nunca se llena y nada lo detecta. **Esto no era hipotético**: encontró un bug real en **N-565** (3 campos de nombre del beneficiario apuntaban a `#subform[1]` en vez de `#subform[0]`, el índice correcto según el inventario real), ya corregido. Mismo chequeo aplicado también a las 127 reglas condicionales (`show_if`) de `conditional_rules.py` — esas sí estaban todas correctas.
2. **Los valores realmente llegan al PDF descargado**: se genera cada uno de los 16 formularios para un caso con datos completos (peticionario, beneficiario, patrocinador), se descarga el PDF resultante, y se leen los valores reales de sus campos AcroForm con `pypdf` para confirmar que coinciden exactamente con lo que `GeneratedForm.data` dice que se guardó — cierra el círculo completo: base de datos → generación de PDF → archivo que un cliente realmente descarga.

Ambas verificaciones ahora son pruebas de `pytest` permanentes (47 pruebas nuevas, parametrizadas por los 16 formularios + las reglas condicionales), no scripts sueltos — corren en cada `pytest` y quedan en CI para siempre, así una regresión futura (agregar un formulario nuevo con un typo en su mapa de autofill, por ejemplo) se detecta sola.

### Docker / pre-deploy

- **Faltaba `.dockerignore`**: sin él, `docker build ./backend` podía copiar `.venv/`, `migratepro.db` (con datos reales si existiera), y **`generated_forms/`/`uploaded_documents/` — directorios que contienen PII real de clientes** — directo a la imagen. Se agregó `backend/.dockerignore` excluyendo exactamente lo mismo que ya excluye `.gitignore` para esos directorios, por la misma razón.
- **`docker-compose.yml` montaba `./backend:/app` como volumen sobre el contenedor de backend**: esto hace que el contenedor sirva el código del filesystem del host en vez del código que se copió a la imagen en el build — inofensivo en un flujo de desarrollo con `--reload`, pero el `CMD` no tiene `--reload`, así que el volumen no aportaba nada útil y sí introducía un riesgo real para un despliegue: el comportamiento en producción dependería del estado exacto del filesystem del host al arrancar el contenedor, no de la imagen versionada. Se quitó.
- **El contenedor corría como root**: se agregó un usuario `app` no-root en el `Dockerfile` (con los directorios de escritura en runtime pre-creados y con el dueño correcto) y `USER app` antes del `CMD`.
- **Build de Docker sigue sin verificarse end-to-end en esta máquina** — Docker Desktop seguía sin poder levantar el daemon (mismo problema documentado en una ronda anterior); los cambios se revisaron estáticamente pero no se confirmaron con un build real. Correr `docker compose up --build` en una máquina con Docker funcionando antes de desplegar.

### UX del editor de formularios

- **El indicador "Guardado ✓" quedaba obsoleto**: después de guardar, si seguías editando otro campo, el mensaje "Guardado ✓" seguía mostrándose aunque ya hubiera cambios nuevos sin guardar — parecía que el formulario estaba al día cuando no lo estaba. Ahora hay un estado "cambios sin guardar" explícito (punto ámbar + texto) que reemplaza al "Guardado ✓" en cuanto se edita cualquier campo después de guardar.
- **Sin aviso al salir con cambios sin guardar**: con formularios de hasta 736 campos, perder ediciones por cerrar la pestaña, recargar, o hacer clic en "← Volver" por accidente es un riesgo real y costoso. Ahora ambas páginas (`/forms/{id}` interno y el portal público `/client/forms/{token}`) advierten con el diálogo nativo del navegador si intentás cerrar/recargar/salir con cambios sin guardar, y el enlace "← Volver" del editor interno pide confirmación explícita antes de navegar. **Límite conocido**: esto no intercepta navegación interna de Next.js hacia *otras* páginas de la app (por ejemplo, hacer clic en "Casos" en el menú lateral mientras editás un formulario) — cubre los casos más comunes de pérdida accidental (cerrar pestaña, recargar, el botón "Volver"), no todos los posibles.

## Tests

### Backend

Suite de `pytest` en `backend/tests/` (147 pruebas): login/refresh/logout/forgot-reset-password, bloqueo de cuenta y límites de tasa, invalidación de enlaces de restablecimiento viejos, permisos de admin, CRUD de citas y su sweep de recordatorios, facturas/pagos y el recálculo de saldo, el panel de reportes (incluyendo la regresión de timezone de arriba), la limpieza de tokens vencidos, generación completa de los 16 formularios USCIS, las cuatro piezas de alineación con el modelo de negocio (RFEs, panel "Mi día", gap analysis, cronograma del caso), el equipo/workload y la biblioteca de requisitos de USCIS, el endurecimiento de seguridad (timing del login, límites de tamaño, límite de tasa del portal público), y la verificación real de que los 16 formularios se llenan electrónicamente (validez de cada entrada de autofill y de cada regla condicional contra el inventario real de campos, más el round-trip completo de valores hacia el PDF descargado — ver [Auditoría de seguridad, verificación de formularios y pre-deploy](#auditoría-de-seguridad-verificación-de-formularios-y-pre-deploy)). Tres pruebas de regresión específicas para el mismo tipo de bug de orden de rutas de FastAPI (una ruta literal registrada *después* de una ruta con parámetro dinámico queda "tapada" y nunca se alcanza): `/rfes/ai-status`, `/users/workload`, y una auditoría sistemática de los 17 archivos de endpoints que no encontró instancias nuevas. Corre contra una base SQLite propia y aislada (`backend/tests/test_migratepro.db`, se recrea entera antes de cada prueba — no comparte estado con `migratepro.db`).

```
cd backend
./.venv/Scripts/pip install -r requirements-dev.txt
./.venv/Scripts/python -m pytest tests/ -v
```

### Frontend (end-to-end)

Suite de `@playwright/test` en `frontend/tests/e2e/` (13 pruebas) contra la app real — sin mocks: login (incluye la regresión de la carrera del token de auth en recarga completa, ver `api.ts`), contraseña incorrecta, sesión que sobrevive un reload duro, contraseña olvidada, cada página interna carga sin redirigir a `/login` ni tirar un error de consola, y que crear un caso expone las secciones de Citas/Facturas inline. Como usa el backend real, hay que levantarlo primero (con un admin sembrado — ver arriba); Playwright solo administra el servidor de frontend:

```
cd backend && ./.venv/Scripts/python -m uvicorn app.main:app --port 8000        # en una terminal
cd frontend && npm run test:e2e                                                  # en otra
```

Corre contra `http://localhost:3000`/`http://localhost:8000` por defecto; para apuntar a otro lado, `PLAYWRIGHT_BASE_URL`/`NEXT_PUBLIC_API_URL`. Usa el admin sembrado (`admin@migratepro.local`/`changeme123` salvo que hayas cambiado `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD`) — sobreescribible con `TEST_ADMIN_EMAIL`/`TEST_ADMIN_PASSWORD`. Corre en un solo worker a propósito (`fullyParallel: false`): las pruebas comparten esa cuenta y una sesión de login concurrente entre pruebas paralelas se pisaría.

## Módulos implementados (MVP)

- [x] Clientes (CRUD)
- [x] Casos migratorios (CRUD, tipos, estados, participantes con rol, asignación a abogado/paralegal)
- [x] Generación de formularios USCIS (16 formularios: I-90, I-130, I-130A, I-131, I-485, I-589, I-751, I-765, I-864, G-28, N-336, N-400, N-470, N-565, N-600, N-600K — 100% de los campos editables, motor genérico, agregar más formularios es solo extraer + mapear)
- [x] Enlace seguro para que el cliente complete el formulario y suba documentos, sin login
- [x] Multi-idioma (ES/EN) en toda la UI + traducción de referencia de las etiquetas del formulario
- [x] Catálogo de servicios + motor de workflow básico (checklist + etapas + auto-generación de formularios al aplicar un servicio)
- [x] Diseño consistente (AppShell, sidebar, componentes UI compartidos)
- [x] Documentos y evidencias + extracción por IA (subida, listado y borrado interno en `/documents`; extracción con Claude vision requiere `ANTHROPIC_API_KEY`, degrada con gracia sin ella)
- [x] Revisión de formularios con IA (detección de inconsistencias contra los datos del cliente)
- [x] Checklist con responsable, fecha límite y prioridad + tablero Kanban de casos por estado + centro de notificaciones
- [x] Seguimiento de citas y vencimientos (`/appointments`, recordatorios por correo, con citas/facturas también visibles inline en el detalle de cada caso en `/cases`)
- [x] Facturación y pagos (`/billing`, saldo derivado de los pagos, marcado de vencidas)
- [x] Envío automático de correos y recordatorios (scheduler en proceso cada hora + endpoints manuales; SMTP opcional con degradación a log, verificado extremo a extremo contra un servidor SMTP real)
- [x] Panel administrativo con estadísticas (`/stats`)
- [x] Autenticación / login (access token + refresh token con rotación y revocación, recuperación de contraseña por correo, bloqueo de cuenta y límites de tasa contra fuerza bruta, todos los endpoints internos requieren sesión salvo el portal público del cliente)
- [x] Suite de pruebas de backend (`pytest`, 147 pruebas) cubriendo auth, citas, facturación, reportes, las piezas del modelo de negocio (RFEs, dashboard, gap analysis, cronograma), equipo/requisitos de USCIS, endurecimiento de seguridad, y verificación real de generación electrónica de los 16 formularios
- [x] Módulo de Equipo (`/team`): directorio de personal, carga de trabajo por persona, edición de rol/datos, desactivación con guardarraíles
- [x] Asignación directa desde el tablero Kanban (chip de responsable + selector inline por tarjeta) y filtro por responsable
- [x] Referencia curada de requisitos oficiales de USCIS (7 formularios, con fuente y fecha verificada) integrada al gap analysis y al catálogo de formularios
- [x] Auditoría de seguridad pre-deploy (timing del login, validación de contraseña, límites de tamaño/tasa, advertencia de `SECRET_KEY` por defecto) y de Docker (`.dockerignore` faltante, bind mount inseguro, usuario no-root)
- [x] Verificación permanente (no un script suelto) de que los 298 mapeos de autofill y las 127 reglas condicionales apuntan a campos reales del PDF, más el round-trip de valores hacia el PDF descargado en los 16 formularios — encontró y corrigió un bug real en N-565
- [x] UX del editor de formularios: indicador de "cambios sin guardar" (ya no queda un "Guardado ✓" obsoleto) y advertencia antes de salir con cambios sin guardar, interno y portal público
- [x] Suite de pruebas end-to-end de frontend (`@playwright/test`, 13 pruebas) contra la app real
- [x] Solicitudes de evidencia (RFE): registro, checklist de evidencia, sugerencias opcionales con IA (ver [Alineación con el modelo de negocio](#alineación-con-el-modelo-de-negocio-blueprint-del-despacho))
- [x] Panel "Mi día" por preparador (casos asignados, citas de hoy, checklist vencido, RFEs pendientes, casos listos para revisión)
- [x] Documentos e información faltante (gap analysis) por caso, basado en reglas verificables contra los datos existentes
- [x] Cronograma visual del caso, interno y en el portal público del cliente

## Gaps conocidos (no resueltos a propósito)

- **Sin multi-tenant / múltiples despachos** — es una base de datos por instalación.
- **Notificaciones sin filtrar por rol o asignación** — todo el personal ve todos los eventos (ver [Centro de notificaciones](#centro-de-notificaciones)).
- **Scheduler y rate limiting en memoria/en proceso, no Celery beat ni Redis** — si se corre más de una instancia del backend detrás de un load balancer, hay que coordinar manualmente o migrar a Redis (ver [Recordatorios automáticos por correo](#recordatorios-automáticos-por-correo) y [Protección contra fuerza bruta](#protección-contra-fuerza-bruta)).
- **Build de Docker sigue sin verificarse end-to-end en esta máquina** — Docker Desktop sigue con el motor caído localmente (mismo problema documentado en una ronda anterior, persiste). El `Dockerfile`, `docker-compose.yml` y el nuevo `.dockerignore` se corrigieron y revisaron estáticamente (ver [Docker / pre-deploy](#docker--pre-deploy)) pero no con un build real — correr `docker compose up --build` antes de desplegar.
- **`npm audit` reporta una vulnerabilidad moderada sin fix estable disponible** (PostCSS dentro de Next.js, `GHSA-qx2v-qp2m-jg93`) — riesgo práctico bajo (herramienta de build-time, no de runtime), pendiente de una versión 16.3 estable de Next.js.
- **`pip-audit` no pudo correr en esta máquina** (falla de verificación SSL contra pypi.org desde este entorno) — correr `pip-audit -r backend/requirements.txt` en CI o en otra máquina antes de desplegar.
- **La advertencia de "cambios sin guardar" no cubre navegación interna de Next.js** (ej. hacer clic en otro ítem del menú lateral mientras se edita un formulario) — solo cierre de pestaña, recarga, URL nueva, y el enlace "← Volver" del propio editor (ver [UX del editor de formularios](#ux-del-editor-de-formularios)).
- **I-130A y N-600K no tienen reglas condicionales** — los otros 14 formularios sí (ver [Formularios USCIS](#formularios-uscis)).
- **Sin aplicación móvil** — el documento de modelo de negocio la describe como uno de los 4 productos; no se construyó ni siquiera una versión reducida (ver [Explícitamente fuera de alcance](#explícitamente-fuera-de-alcance-en-esta-ronda)).
- **Sin "JTLS Academy"** (portal de contenido educativo: videos, guías, FAQ, novedades migratorias revisadas por la firma) — mismo criterio que la app móvil: no se construyó una versión superficial solo para marcar la casilla.
- **Gap analysis no cubre ingreso mínimo del I-864 ni matrimonios previos** — el modelo de datos actual (`Client`) no captura ingreso anual ni historial de matrimonios, y no se quiso adivinar un umbral legal ni inferir relaciones que el dato no respalda (ver [Documentos e información faltante](#documentos-e-información-faltante-gap-analysis)).
- **Referencia de requisitos de USCIS cubre 7 de 16 formularios** (I-130, I-485, I-765, N-400, I-751, I-131, I-90) — los otros 9 no tienen ficha todavía, mismo criterio de "no inventar" (ver [Referencia de requisitos oficiales de USCIS](#referencia-de-requisitos-oficiales-de-uscis-no-un-chatbot-legal)).
- **Sin cuotas de USCIS (`filing fees`) en la app** — deliberado: las cifras están en flujo activo (cambios recientes de la ley H.R. 1) y un monto hardcodeado se desactualizaría rápido y de forma engañosa; siempre remitir a la calculadora oficial de USCIS.
- **Sin asistente de IA de preguntas abiertas sobre inmigración** — deliberado, por riesgo de alucinación en un dominio legal; ver [Explícitamente fuera de alcance](#explícitamente-fuera-de-alcance-en-esta-ronda).
