# REPORTE AVANZADO — POTENCIACIÓN CON IA (LEGAL Y ÉTICA)

Proyecto: Imigratepro-2.0  ·  Fecha: 2026-07-20
Alcance: Cómo llevar la IA del sistema al máximo nivel SIN incurrir en práctica ilegal de la
abogacía (UPL), protegiendo PII y manteniendo responsabilidad del abogado. Read-only: no se
modificó ningún archivo de código. Investigación con fuentes primarias + diseño de arquitectura.

> AVISO: Esto es contexto de ingeniería/cumplimiento, NO asesoramiento jurídico. Las normas
> varían por estado. Validar con un abogado colegiado antes de desplegar.

---

## 0. PRINCIPIO RECTOR (la línea que nunca se cruza)

La IA en este producto es una **herramienta bajo supervisión de un abogado colegiado**, no un
prestador de servicios legales. El sistema **ensambla, detecta y señala**; el **abogado decide y
firma**. En cuanto la IA "determina elegibilidad" o "da consejo legal" autónomamente, se cruza a
**UPL (Unauthorized Practice of Law)** — ilegal en todos los estados.

El repositorio YA acierta en el patrón base: el módulo RFE (`rfe_ai.py`) devuelve sugerencias
como **borrador editable** que el preparador acepta uno por uno; y toda la IA degrada a 503 sin
`ANTHROPIC_API_KEY`. Esa es la postura correcta — este reporte la eleva a nivel avanzado y la
extiende a todos los módulos.

---

## 1. MARCO LEGAL / ÉTICO (con fuentes)

### 1.1 Práctica Ilegal de la Abogacía (UPL)
- La IA que da consejo o decide elegibilidad = ejercicio ilegal de la abogacía. Debe ser
  herramienta bajo supervisión humana.
- Fuentes: **ABA Formal Op. 512 (2024)**, **California COPRAC** (enmiendas propuestas a las
  Reglas 1.1, 1.4, 1.6, 3.3, 5.1, 5.3 — aprobadas para comentario público el 13 mar 2026),
  **Florida Bar Op. 24-1 (2024)**, guías de **AILA**.
- Implicación de diseño: nunca un endpoint de IA que responda "eres elegible/aprobado/denegado".
  El agente debe tener un validador de salida que rechace lenguaje de determinación y produzca
  `needs_attorney_decision`.

### 1.2 Supervisión y deber de competencia (Model Rules)
- **1.1 (Competencia)**: el juicio profesional no se delega a la IA; el abogado debe entender la
  herramienta y verificar su salida.
- **5.1 / 5.3 (Supervisión)**: el abogado responsable debe instruir y supervisar el uso de IA por
  personal no abogado. → El SaaS debe permitir documentar: inventario de herramientas, evaluación
  de riesgo por tipo de caso, política de uso escrita, y formación.
- **1.4 (Comunicación)**: el cliente debe saber (y poder cuestionar) el estado de su caso; la IA
  no debe ser la única fuente de "verdad" mostrada al cliente sin sello humano.
- Fuente: **CLINIC (Catholic Legal Immigration Network), "How to Safely Incorporate AI Into Your
  Immigration Practice", 17 dic 2025** — lista usos permitidos (borradores, edición, resumen,
  traducción, investigación *con análisis humano*) y exige verificar salida de la IA.

### 1.3 Confidencialidad y PII (dato más sensible)
- Inmigración = PII de nivel crítico: SSN, A-number, pasaporte, biometría, datos médicos.
- **Regla 1.6 / 1.6(c)** + **ABA Formal Op. 483 (2018)** (deber de monitorear proveedores de
  servicios). Enviar datos de cliente a un LLM de terceros es una "divulgación" que exige
  protección.
- **Obligación técnica**: usar la **API comercial con ZDR (Zero Data Retention)** de Anthropic
  (no retiene prompts tras la respuesta, no entrena sin permiso) — NUNCA la app de consumo
  (ChatGPT/Claude web). Exigir **DPA (Data Processing Agreement)** y cláusulas de no-entrenamiento.
- **Precedente real — Docketwise (2025-2026)**: brecha confirmada feb 2026 que expuso **116.666
  registros** de inmigración (SSN, pasaporte, datos médicos) por compromiso de credenciales en un
  proveedor legal. Esto elevó el estándar del sector: la seguridad (ver AUDIT_REPORTE.md, C1/C2/H5)
  ya no es "nice to have", es la base del cumplimiento de IA.

### 1.4 Responsabilidad
- Siempre recae en el abogado. Si un formulario llenado por IA es incorrecto y USCIS lo deniega,
  el abogado responde. → El patrón "borrador para aceptar/rechazar" (ya presente en RFE) es
  **conforme a la ética** y debe extenderse a todos los módulos. Nunca "llenar y presentar" sin
  paso de firma explícita.

### 1.5 Divulgación / transparencia (FTC)
- **16 CFR Part 461** (regla de suplantación de la FTC, vigente abr 2024) y caso **DoNotPay**
  (orden FTC feb 2025, $193k multa) prohíben presentar la IA como "abogado robot" o suplantar
  abogado.
- El producto debe: decir al cliente que se usa IA; etiquetar claramente el contenido generado; no
  implicar un abogado donde no lo hay; mostrar disclaimers en el portal del cliente.

### 1.6 Tabla de guardas obligatorias (checklist de cumplimiento)
| Guarda | Mecanismo | Estado en repo |
|---|---|---|
| Audit log de toda acción IA | `audit_log` append-only + hash-chain | FALTA (ver AUDIT_REPORTE M6) |
| Firma/atención de abogado antes de entregar | gate de aprobación | Parcial (solo RFE) |
| Procedencia de dato extraído | `source_bbox/page` + cita | Parcial (document_ai tiene `confidence_notes`) |
| DPA + ZDR en LLM | API comercial Anthropic con ZDR | Configurable (falta forzar) |
| Monitoreo de subprocesadores | alertas de brecha | FALTA |
| Pruebas de sesgo | bias testing de modelos | FALTA |
| Model cards | documentar modelo/versión/límites | FALTA |
| Red-team de inyección de prompts | injection_guard | FALTA (ver §3.5) |
| Degradación sin API key | fallback 503 | ✓ YA LO HACE |
| Disclaimers al cliente | banner portal | FALTA/mejorable |

---

## 2. ARQUITECTURA DE IA AVANZADA (legal by design)

### 2.1 Diagrama de componentes
```
 CAPA PRESENTACIÓN (Next.js)
 Intake UI · Case Dashboard · Attorney Review Queue · Audit Viewer
        │ REST/WS
 API GATEWAY / FastAPI  ·  AuthN/Z (roles) · Rate limit · WAF
        │
 TASK QUEUE (Celery+Redis)  ·  ORCHESTRATOR (reliability_layer)
        │
 MULTIMODAL    RAG          AGENT         VALIDATION     INJECTION
 INTAKE         (pgvector)   (bounded)     ENGINE         GUARD
 (OCR+vision)   voyage-law-2  LangGraph    ruleset        sanitizer
        │
 POSTGRES(pgvector) · S3 · REDIS · audit_log(append-only, hash-chain)
        │
 OBSERVABILITY (OTel, Langfuse, Prometheus/Grafana)
```

### 2.2 Flujo extremo a extremo
Cliente sube/completa → [INGEST] clasifica+OCR+visión → campos+confianza (baja confianza ⇒ cola
humana) → [RAG] consulta USCIS (forms/instructions/Policy Manual) → passages con citas →
[VALIDATION] consistencia cruzada (A-number/DOB) + requeridos + deadline → [AGENT ensamblador]
arma checklist + borrador → ✋ PARADA: aprobación de abogado → [ATTEST] acepta/rechaza/edita →
registrado en audit_log → [DELIVER] PDF + memo de fuentes (SIN envío automático a USCIS).

### 2.3 RAG sobre fuentes oficiales USCIS (anti-alucinación)
- **Stack**: `PostgreSQL + pgvector` (reutiliza la DB existente, facilita auditoría) + LlamaIndex/
  LangChain. Embeddings **`voyage-law-2`** (especializado en derecho) con respaldo
  `text-embedding-3-large`.
- **Ingesta**: formularios PDF, *Instructions*, *USCIS Policy Manual*, *Adjudicator's Field
  Manual*. **Chunking estructurado** por Part→Section→Field-group (NO por tamaño ciego) para
  formularios de ~700 campos; conservar metadatos `form_number, part, section, field_ids, page`.
- **Grounding obligatorio**: toda afirmación sustantiva debe llevar `citation_label`
  (form_id/part/page); validador posterior rechaza salida sin cita → "No determinado".

### 2.4 Intake multimodal de documentos
- Clasificador (pasaporte, acta, I-94, W-2, I-20, cert. matrimonio) + **Azure Document Intelligence**
  o **AWS Textract** + fallback Claude Vision.
- Extracción con **esquemas Pydantic** por tipo: `value, confidence (0–1), source_bbox/page`.
- **Cola de revisión humana**: umbral `<0.85` ⇒ `needs_review` ⇒ Attorney/Paralegal Review Queue.
  Baja confianza NUNCA se escribe al cliente sin revisión. (El repo ya hace allowlist de campos en
  `apply_to_client`, pero no valida formato SSN/A-number — ver §3 gap M8 del AUDIT.)

### 2.5 Agente de ensamblaje (acotado, no libre)
- Máquina de estados determinista **LangGraph** con checkpoints y gates (no loop de agente libre).
- **Allowlist estricto de herramientas**: `kb_lookup`, `draft_form`, `check_consistency`,
  `flag_for_attorney` (única salida terminal).
- **Anti-elegibilidad**: system prompt prohíbe "eres elegible/aprobado"; validador de salida
  (regex+clasificador) rechaza determinación y produce `needs_attorney_decision`.
- **Sin presentación autónoma**: el agente NO tiene herramienta de envío a USCIS.
- **Presupuesto de pasos** + timebox para evitar bucles.

### 2.6 Motor de consistencia / validación
- `Pydantic` + `JSON Schema` para campos requeridos (derivados de Instructions en RAG).
- **Consistencia cruzada**: comparar A-number/DOB/nombre legal/nº recibo entre I-130/I-485/I-765/
  I-131; diff y reporte discrepancia. (El repo ya hace autofill con `petitioner/beneficiary/
  attorney`; falta el cross-form y el sponsor faltante rompe I-864 en blanco — ver AUDIT M10.)
- **Motor de deadlines**: ingesta *Visa Bulletin* (DOS) + *priority dates*; calcula fechas límite
  por categoría/país y alerta. Hoy el repo solo tiene citas/recordatorios manuales.

### 2.7 Fiabilidad (reliability layer) — GAP CRÍTICO ACTUAL
El AUDIT_REPORTE ya señaló: las llamadas IA **no tienen timeout, reintentos ni tope de coste**
(`document_ai.py:93`, `form_review_ai.py:92`, `rfe_ai.py:71`). Esto es tanto técnico como de
cumplimiento (un cuelgue de API bloquea un hilo y retrasa un caso real).
- **`AIClient` wrapper**: `httpx` timeout (5s/60s); `tenacity` backoff (solo 5xx/429, 3–5 reint.);
  **cost cap por caso** en Redis (INCRBY tokens, límite diario/caso ⇒ fallo controlado + alerta);
  **model fallback** (Claude Opus/Sonnet → Haiku/OpenAI, sin cambio silencioso); **cola Celery/
  Redis** para cargas pesadas; **observabilidad** OTel + Langfuse + Prometheus/Grafana.

### 2.8 Defensa contra inyección de prompts (datos del cliente = hostiles)
Texto del cliente (campos de formulario, cartas RFE pegadas) es **datos no confiables**.
- **Separación de canales**: system prompt (firmado) vs contenido de usuario como bloque delimitado
  `<<<USER_DATA>>>`, nunca interpolado en instrucciones.
- **Detección**: si el contenido trae "ignora instrucciones anteriores"/"system:"/role-swap →
  clasificador aísla/escapa.
- **Function calling estructurado**: texto cliente siempre como *argumento string* de una tool, no
  como prompt → el modelo no lo reinterpretra como instrucción.
- **Validación de salida**: el guard revisa que no ejecute acciones fuera de allowlist ni revele el
  system prompt.
- **Canary tokens**: marcadores invisibles en el system prompt; si reaparecen en la salida ⇒ fuga
  de contexto detectada.

### 2.9 Auditoría y procedencia
- `audit_log` append-only (Postgres) por llamada IA: `timestamp, case_id, actor, prompt_hash
  (SHA-256), model, tokens_in/out, output_hash, citations, latency, cost_usd`.
- **Hash-chain**: cada registro incluye `prev_hash` ⇒ cadena tamper-evident.
- **Acción del abogado**: `accept|reject|edit` con diff, obligatoria antes de entregar.
- **Retención**: 7 años (expedientes legales), export a **WORM storage (S3 Object Lock)**.
- **Audit Viewer** en Next.js para traza completa de una decisión.

---

## 3. ESTADO ACTUAL DEL CÓDIGO vs. NIVEL AVANZADO

Lo que el repo YA hace bien (mantener):
- `document_ai.py`: extracción estructurada con esquema + `confidence_notes` + `a_number` digits-only.
- `rfe_ai.py`: sugerencias como borrador editable (no auto-aplica) → patrón ético correcto.
- Degrada a 503 sin `ANTHROPIC_API_KEY`.
- `apply_to_client` usa allowlist de campos (aunque sin validar formato).

Gaps para llegar a "avanzado y legal":
| Capacidad avanzada | Estado | Referencia |
|---|---|---|
| RAG sobre USCIS (citas) | FALTA | §2.3 |
| Consistencia cruzada entre formularios | Parcial/roto (I-864) | AUDIT M10 |
| Motor de deadlines (Visa Bulletin) | FALTA | §2.6 |
| reliability_layer (timeout/retry/cost) | FALTA (crítico) | §2.7 / AUDIT M9 |
| injection_guard | FALTA | §2.8 / AUDIT M8 |
| audit_log + hash-chain + viewer | FALTA | §2.9 / AUDIT M6 |
| Validación de formato PII extraída | FALTA | AUDIT M8 |
| DPA + ZDR forzado en LLM | Configurable, no forzado | §1.3 |
| Disclaimers en portal cliente | Mejorable | §1.5 |
| Extender patrón "borrador aceptar/rechazar" a todos los módulos | Solo RFE | §1.4 |
| ZDR/sin-entrenamiento verificado en config | FALTA validación | §1.3 |

---

## 4. ROADMAP DE IA (priorizado, legal-first)

**P0 — Cumplimiento y seguridad (antes de tocar modelos nuevos)**
1. Forzar API comercial Anthropic con **ZDR** + DPA; fallar si no está configurado.
2. `reliability_layer` (timeout, retry, cost cap, fallback) en TODAS las llamadas IA existentes.
3. `audit_log` append-only + hash-chain + viewer; acción de abogado obligatoria antes de entregar.
4. `injection_guard` (separación de canales + sanitización de inputs cliente/RFE).
5. Extender patrón "borrador aceptar/rechazar" (RFE) a form_review y gap_analysis.
6. Disclaimers de uso de IA en portal de cliente + metadata de producto.

**P1 — Grounding y calidad**
7. Pipeline RAG: ingesta USCIS + pgvector + `voyage-law-2` + requisito de cita.
8. Motor de validación: Pydantic + consistencia cruzada A-number/DOB + deadlines (Visa Bulletin).
9. Validación de formato PII extraída (SSN 9 dígitos, A-number) antes de escribir al cliente.

**P2 — Intake y agente acotado**
10. Intake multimodal: clasificador + OCR/visión + esquemas de confianza + cola de revisión.
11. Agente ensamblador acotado (LangGraph) con gate de abogado y guardarraíles anti-elegibilidad.

**P3 — Operación**
12. Cola Celery/Redis; observabilidad (OTel+Langfuse+Prometheus/Grafana).
13. Model fallback secundario; chaos testing (inyección, fallo de modelo, sobrecosto).
14. Bias testing de modelos + model cards; monitoreo de subprocesadores (alerta de brecha).

---

## 5. FUENTES
- CLINIC, "How to Safely Incorporate AI Into Your Immigration Practice" (17 dic 2025).
- State Bar of California, COPRAC, Proposed Amendments to Rules 1.1/1.4/1.6/3.3/5.1/5.3 (mar 2026).
- ABA Formal Op. 512 (2024); ABA Formal Op. 483 (2018, proveedores).
- Florida Bar Op. 24-1 (2024, IA).
- National Center for State Courts, "Modernizing UPL Regulations to Embrace AI" (white paper).
- FTC 16 CFR Part 461 (AI impersonation rule, abr 2024); FTC v. DoNotPay (feb 2025, $193k).
- Anthropic docs: Zero Data Retention (ZDR), no-training-on-data.
- Precedente Docketwise breach (sep 2025 → confirmada feb 2026, 116.666 registros).
- AILA guidance sobre uso de IA en práctica de inmigración.

> Nota: el informe legal del subagente quedó en
> `C:\Users\Raili\AppData\Local\hermes\hermes-agent\informe_cumplimiento_IA_inmigracion.md`
> (fuera de la carpeta del proyecto). Este reporte consolida ambos y lo pone en el proyecto.
