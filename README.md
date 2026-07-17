# Immigration Case Manager

Plataforma de gestión de casos migratorios: clientes, casos, documentos con extracción por IA, generación de formularios USCIS y seguimiento de citas.

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
./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

Por defecto usa SQLite (`backend/migratepro.db`). Para usar Postgres, copia `backend/.env.example` a `backend/.env` y ajusta `DATABASE_URL`.

Frontend:

```
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Abre http://localhost:3000. La API se sirve en http://localhost:8000/api/v1 (docs interactivas en http://localhost:8000/docs).

### Formularios USCIS

Los PDFs oficiales rellenables viven en `backend/form_templates/` (I-130, I-765, G-28). Después de aplicar las migraciones, carga el catálogo de formularios una vez:

```
cd backend
./.venv/Scripts/python -m app.seed_forms
```

Los formularios generados (con datos reales del cliente) se guardan en `backend/generated_forms/` — **contienen PII y nunca se deben commitear** (ya están en `.gitignore`).

**El formulario electrónico cubre el 100% de los campos del PDF** (438 en I-130, 154 en I-765, 97 en G-28): el inventario completo se extrae una vez con `scripts/extract_form_fields.py` (usa el tooltip oficial `/TU` de cada campo como etiqueta — texto real de USCIS con referencia de Parte/línea) y se guarda en `app/seed_data/field_inventories/*.json`. Al generar un formulario:

1. Se crea un `GeneratedForm` con una entrada por cada campo del PDF (texto, checkbox o choice), vacía por defecto.
2. El **autofill map** (`backend/app/seed_data/form_field_maps.py`) pre-llena automáticamente el subconjunto que sabemos resolver de forma confiable desde el cliente/caso: nombre, fecha de nacimiento, número A, dirección, sexo, estado civil, SSN, teléfonos y email (para esto último, `Client` tiene `sex`/`marital_status`/`ssn`/`mobile_phone` además de los campos originales). Los checkboxes ligados a un valor tipo enum (sexo, estado civil) usan `match_value`/`set_value` en el mapeo: solo se marcan si el dato del cliente coincide con esa opción. Sigue siendo un subconjunto curado, no el 100%, porque el resto (historial migratorio, empleo, matrimonios previos, etc.) no se puede inferir de forma segura del modelo de datos actual y debe completarlo un abogado o paralegal.
3. En `/forms/{id}` (botón "Abrir formulario electrónico") se edita el resto campo por campo, agrupado por **Parte** del formulario (no por página — se parsea del propio tooltip oficial), con buscador de campos, barra de progreso y selector de fecha nativo para los campos de fecha.
4. Cada "Guardar" regenera el PDF completo con pypdf, incluyendo checkboxes y menús desplegables (verificado que `/AS` y `/V` quedan sincronizados para que el PDF se vea marcado correctamente en un lector real).

Para agregar un formulario nuevo (I-485, I-864, ...): bajar el PDF a `form_templates/`, correr `python scripts/extract_form_fields.py <archivo>.pdf`, y agregar la entrada en `FORM_TEMPLATES` de `form_field_maps.py` (el autofill map es opcional, el formulario funciona igual de completo sin él).

Antes de usar un PDF generado en una presentación real ante USCIS, un abogado debe revisarlo campo por campo contra las instrucciones vigentes de la edición correspondiente.

### Multi-idioma

Selector ES/EN fijo en la esquina superior derecha (`frontend/src/lib/i18n.tsx`, contexto + diccionario, persistido en `localStorage`). Cubre toda la interfaz propia de la app (navegación, formularios, mensajes). Las etiquetas oficiales del formulario electrónico tienen además un botón independiente "Ver traducción al español" en `/forms/{id}`: es una traducción de referencia por sustitución de frases (`frontend/src/lib/formLabelTranslations.ts`), pensada para ayudar a completar el formulario — **no reemplaza el texto oficial en inglés**, que es el único válido para presentar ante USCIS. Las frases no reconocidas se dejan en inglés en vez de adivinarse.

### Formulario dinámico (campos condicionales)

Algunos campos solo se muestran si la respuesta a otro campo lo amerita — por ejemplo, la dirección física del peticionario (I-130 Línea 12) solo aparece si contestó "No" a "¿Es su dirección postal la misma que su dirección física?" (Línea 11); las opciones de "hijo/padre" (Parte 1, Línea 2) solo aparecen si seleccionó "Child" o "Parent" en la Línea 1. Estas reglas viven en `backend/app/seed_data/conditional_rules.py` como `show_if: [{field, equals}]` adjuntado a cada entrada del `field_schema`, y **solo se agregaron para relaciones verificadas textualmente contra el tooltip oficial de la pregunta compuerta** (busca "If you answered..." o "If you are filing..." en el texto) — no se infirió condicionalidad por adivinanza, porque ocultar un campo requerido por error sería peor que mostrar uno de más. Al cambiar la respuesta que oculta un campo, su valor se limpia automáticamente al guardar para no dejar datos contradictorios en el PDF.

### Asignación de casos

`POST /users` / `GET /users` crea y lista personal (abogado/paralegal/admin) — el rol es informativo por ahora, **no hay login ni autenticación todavía**, así que "admin" no se aplica del lado del servidor, es solo la persona que usa la UI de asignación. Desde `/cases`, cada caso expandido tiene un selector "Asignado a" que llama a `PATCH /cases/{id}` con `assigned_attorney_id` (el campo ya existía en el modelo `Case`, solo faltaba exponerlo en la UI). Si no hay personal creado, hay un botón "+ Nuevo miembro del equipo" en la misma página.

### Enlace seguro para que el cliente complete el formulario

Cada `GeneratedForm` tiene un `access_token` aleatorio (`secrets.token_urlsafe`, no es el UUID interno) que da acceso — sin login — únicamente a ESE formulario y a subir documentos para ESE caso, nada más (no se puede listar otros casos ni clientes a través del token). El botón "Copiar enlace" en `/forms/{id}` genera `/client/forms/{token}`, una página pública (`frontend/src/app/client/forms/[token]/page.tsx`) con el mismo editor de campos (reutiliza `FieldInput` y los helpers de `formFieldHelpers.ts`) más una sección de subida de documentos.

Backend: `app/api/v1/endpoints/public_forms.py` — `GET/PATCH /public/forms/{token}` (mismo motor de relleno de PDF que el endpoint interno) y `POST /public/forms/{token}/documents` (multipart, guarda en `backend/uploaded_documents/{case_id}/`, máx. 20 MB, nunca confía en el nombre original del archivo para la ruta en disco). El enlace se puede desactivar poniendo `client_link_enabled=false` sin perder el token (por si se reactiva).

**Nota de seguridad importante**: como todavía no hay autenticación en ningún endpoint del backend, la "seguridad" del enlace del cliente depende enteramente de la aleatoriedad del token (24 bytes, no adivinable) y de que cada token solo destrabe un formulario puntual — no es aún un sistema con expiración, límite de usos, ni verificación adicional (ej. confirmar fecha de nacimiento antes de mostrar el formulario). Razonable para una demo/MVP; antes de producción real conviene agregar expiración y, si se quiere más rigor, un segundo factor de verificación.

## Con Docker

```
docker compose up --build
```

Levanta Postgres, Redis y el backend. El frontend sigue corriendo con `npm run dev` en desarrollo.

## Diseño

`frontend/src/components/AppShell.tsx` es el layout compartido de toda la app interna: sidebar con navegación (Panel, Clientes, Casos, Servicios, Formularios, Documentos) + barra superior con el selector de idioma. Primitivas reutilizables en `components/ui/` (`Button`, `Card`, `Badge` con color por estado) reemplazan los botones/contenedores repetidos a mano. Acento de color: índigo (antes todo era blanco/negro). El portal público del cliente (`/client/forms/{token}`) **no** usa el AppShell a propósito — es una pantalla aparte, sin la navegación interna, con su propio selector de idioma flotante.

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

`/cases` tiene un selector Lista/Tablero. El tablero (`frontend/src/components/CasesBoard.tsx`) agrupa los casos por `Case.status` (el estado global de 7 valores, no las etapas de servicio que son específicas de cada `Service`) en columnas arrastrables — soltar una tarjeta en otra columna llama a `PATCH /cases/{id}` con el nuevo estado (drag-and-drop nativo de HTML5, sin librería). Un clic en la tarjeta cambia a la vista de lista con ese caso ya expandido.

### Centro de notificaciones

Como todavía no hay login, las notificaciones son un feed global (`Notification` — tabla nueva) en vez de estar ligadas a un usuario; el frontend guarda en `localStorage` la marca de "última vez visto" para calcular el contador de no leídas por navegador. Eventos que generan notificación: caso reasignado, etapa de servicio avanzada, documento subido (tanto desde `/documents` como desde el enlace público del cliente), y revisión de IA de un formulario con al menos un hallazgo. Campanita en la barra superior (`components/NotificationBell.tsx`), con sondeo cada 30s — sin infraestructura de tiempo real ni de correo.

## Documentos + extracción por IA

`backend/app/services/document_ai.py` envía una imagen o PDF de un documento de identidad (pasaporte, actas, I-94) a Claude (`claude-opus-4-8`, salida forzada a JSON vía `output_config.format`/json_schema) y devuelve nombre, apellido, fecha de nacimiento, país de nacimiento, nacionalidad, número de pasaporte, número A y notas de confianza (el modelo deja vacío lo que no pueda leer con certeza, en vez de adivinar). Requiere `ANTHROPIC_API_KEY` en `backend/.env`; si no está configurada, `GET /api/v1/documents/ai-status` reporta `configured: false`, el botón "Extraer datos con IA" se oculta en `/documents`, y el endpoint `POST /documents/{id}/extract` responde 503 en vez de fallar de forma confusa — el resto del módulo (subir, listar, borrar documentos) funciona igual sin la key.

Desde `/documents`: subir un documento (vinculado a un caso, opcionalmente a un cliente, con tipo de documento), extraer sus datos con un clic, y "Aplicar al cliente" copia los campos extraídos (nombre, apellido, fecha de nacimiento, país de nacimiento, nacionalidad, pasaporte, número A) directo al `Client` vinculado — solo si el documento tiene un cliente asignado. Backend: `app/api/v1/endpoints/documents.py` (`GET/POST /cases/{id}/documents`, `GET/PATCH/DELETE /documents/{id}`, `POST /documents/{id}/extract`, `POST /documents/{id}/apply-to-client`).

## Revisión de formularios con IA

En `/forms/{id}` (el formulario electrónico), el botón "Revisar con IA" envía las respuestas ya llenadas del formulario más los datos de referencia del cliente/caso (`build_case_context`) a Claude (`app/services/form_review_ai.py`, mismo modelo `claude-opus-4-8`, con thinking adaptativo porque cruzar decenas de campos contra los datos del cliente es una tarea de razonamiento no trivial) y devuelve una lista de hallazgos con severidad (alta/media/baja) — contradicciones entre el formulario y los datos del cliente, contradicciones internas del propio formulario (ej. fecha de fin antes que fecha de inicio), valores mal formados, o respuestas que parecen placeholder ("asdf", "N/A"). Se guarda en `GeneratedForm.ai_review`/`ai_reviewed_at` para no perderse al recargar la página. **Es una ayuda de revisión, no una revisión legal final** — cada hallazgo debe verificarse, y el propio modelo recibe instrucciones explícitas de no inventar problemas que los datos no respalden. Igual que la extracción de documentos, requiere `ANTHROPIC_API_KEY`; sin ella el botón se oculta y el endpoint (`POST /forms/{id}/review`) responde 503 en vez de fallar de forma confusa.

## Rendimiento del editor de formularios

Escribir en un campo del formulario de 438 campos causaba que TODO el formulario se volviera a renderizar en cada tecla (porque el `onChange` de cada campo se recreaba en cada render y ningún campo estaba memoizado), lo cual se sentía como que la página se congelaba un instante por cada letra escrita. Se resolvió extrayendo cada fila de campo a un componente memoizado (`frontend/src/components/FieldRow.tsx`, usado tanto en `/forms/{id}` como en el portal público del cliente) con un callback de cambio estable (`useCallback`) — ahora escribir en un campo solo vuelve a renderizar ESE campo, no los otros ~400.

## Módulos implementados (MVP)

- [x] Clientes (CRUD)
- [x] Casos migratorios (CRUD, tipos, estados, participantes con rol, asignación a abogado/paralegal)
- [x] Generación de formularios USCIS (I-130, I-765, G-28 — 100% de los campos editables, motor genérico, agregar más formularios es solo extraer + mapear)
- [x] Enlace seguro para que el cliente complete el formulario y suba documentos, sin login
- [x] Multi-idioma (ES/EN) en toda la UI + traducción de referencia de las etiquetas del formulario
- [x] Catálogo de servicios + motor de workflow básico (checklist + etapas + auto-generación de formularios al aplicar un servicio)
- [x] Diseño consistente (AppShell, sidebar, componentes UI compartidos)
- [x] Documentos y evidencias + extracción por IA (subida, listado y borrado interno en `/documents`; extracción con Claude vision requiere `ANTHROPIC_API_KEY`, degrada con gracia sin ella)
- [x] Revisión de formularios con IA (detección de inconsistencias contra los datos del cliente)
- [x] Checklist con responsable, fecha límite y prioridad + tablero Kanban de casos por estado + centro de notificaciones
- [ ] Seguimiento de citas y vencimientos
- [ ] Facturación y pagos
- [ ] Envío automático de correos y recordatorios
- [ ] Panel administrativo con estadísticas
- [ ] Autenticación / login (hoy ningún endpoint requiere sesión)
