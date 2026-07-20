# AUDITORÍA — Formularios electrónicos · Traducción · UX/UI · Benchmark de mercado

**Proyecto:** Imigratepro-2.0
**Fecha:** 2026-07-20
**Alcance:** Auditoría READ-ONLY (no se modificó ningún archivo). 3 agentes en paralelo
(formularios/backend, traducción, UX/UI) + investigación de mercado 2026.
**Objetivo del encargo:** verificar si TODOS los formularios electrónicos están correctos,
si tienen traducción, si el UX/UI es perfecto para cualquier usuario, e investigar qué falta
para ser potencia — con plan de ejecución.

---

## 0. VEREDICTO EN UNA LÍNEA

El motor es sólido y la arquitectura es de nivel producto real, pero **NO está listo para
"cualquier usuario"**: solo **24 de 97 formularios precargan datos**, solo **17% de las
etiquetas de formulario están en español** (el 83% se muestra en inglés crudo al inmigrante),
y hay **4 bloqueadores de UX** en el portal del cliente. Ninguno es un defecto de código
"roto"; son huecos de completitud. Todos son ejecutables.

---

## 1. FORMULARIOS ELECTRÓNICOS — ¿están correctos?

**Cobertura de PDFs/schema: impecable.** 97/97 PDFs presentes, 97/97 JSON de inventario de
campos, 0 campos sin name/type/label/page, 0 checkboxes sin `on_value`, 0 mapeos rotos.
El llenado usa `pypdf`, desencripta el owner-password de USCIS, borra `/XFA` (clave para que
Adobe Reader muestre lo rellenado) y maneja checkboxes/radios/fechas correctamente.

**El hueco real: AUTOFILL (precarga de datos del cliente).**

| Grupo | Estado | Cantidad | Detalle |
|---|---|---|---|
| **A — Completo** | Autofill + lógica condicional `show_if` | **15** | I-130, I-130A, I-765, I-131, I-485, I-589, I-751, I-864, I-90, N-336, N-565, N-400, N-470, N-600, N-600K |
| **B — Autofill sin `show_if`** | Precarga, pero campos condicionales siempre visibles | **9** | G-28, I-129F, I-360, N-300, N-426, N-648, I-601, I-601A, I-612 |
| **C — Integrado pero VACÍO** | Genera PDF pero sale en blanco, 100% a mano | **73** | I-129, I-140, I-539, I-765V, I-9, I-821D, EB-5 (I-526/I-956...), etc. |
| **Rotos** | — | **0** | — |

- Funcionan punta a punta con precarga: **24**. Salen en blanco: **73**. Rotos: **0**.
- **`show_if` (lógica condicional):** solo 13 de 97 formularios la tienen → 84 muestran
  campos que no aplican (riesgo de que el usuario llene lo que no debe).
- **Riesgo silencioso en `pdf_filler.py`:** si USCIS cambia la edición y un campo del schema
  ya no existe en el PDF real, `pypdf` lo ignora SIN error → el dato se pierde sin aviso.
- **Vigencia:** 88 VIGENTES / 0 desactualizados / 9 "sin validar" (EOIR-29, G-1145, G-1256,
  G-1650, G-28, G-28I, I-193, I-865, G-325R). Edition dates viejos sin alerta: G-28 (2018),
  G-28I (2018), G-1145 (2014), I-865 (2020).
- **Desorden de carpetas:** `uscis_forms/` tiene `i-854` (sin formulario en el sistema) y le
  falta `i-130a`; el código realmente usa la carpeta plana `form_templates/`.

---

## 2. TRADUCCIÓN AL ESPAÑOL — ¿la tiene?

**UI de la app (menús, botones, mensajes): excelente.** 480 claves i18n con paridad ES/EN
del 100% (solo 8 valores idénticos, y son términos correctos como "USCIS"). Español natural
y correcto.

**Etiquetas de los formularios: hueco enorme.** Aquí está el problema para el inmigrante:
- Hay **21.298 etiquetas únicas** en los 97 formularios (22.749 en total).
- El diccionario `formLabelTranslations.ts` tiene **262 frases**.
- **Cobertura ≈ 17.1%.** Cuando una etiqueta no está en el diccionario, se muestra
  **en inglés crudo** (ej.: *"Part 2. Information About You (Petitioner). 3. Enter U.S.
  Social Security Number, if any."*).
- Consecuencia directa: un cliente hispanohablante ve ~83% de las preguntas de su formulario
  en inglés. Para el usuario objetivo, esto rompe la promesa bilingüe.
- Bug de calidad detectado: una entrada traduce mal ("Select Gray.").

---

## 3. UX/UI — ¿es perfecto para cualquier usuario?

Estructura del asistente (autosave, pasos, reanudación, aviso antes de salir): **sólida,
por encima de la media.** Pero hay bloqueadores para el usuario objetivo (inmigrante, móvil,
baja alfabetización digital, o con discapacidad):

**🔴 CRÍTICO**
- **C1 — Subida de documentos sin red de seguridad:** input sin `accept`, sin validar
  tamaño/formato en cliente, error genérico ("falló la subida") sin decir por qué, sin
  mostrar el límite, sin barra de progreso real, y **no se puede borrar** un archivo subido
  por error.
- **C2 — Labels no asociados a inputs** (falta `htmlFor`/`id`): un lector de pantalla no dice
  qué campo es. Viola WCAG 1.3.1/4.1.2 y afecta TODOS los campos de texto/fecha/select.
- **C3 — Sin validación de obligatorios ni pantalla de "enviado":** se puede terminar el
  formulario en blanco; al finalizar solo aparece un "Guardado" pequeño, sin confirmación
  clara de que ya terminó.
- **C4 — No existe `error.tsx` ni `loading.tsx`:** cualquier excepción (token vencido, fallo
  de API) deja **pantalla en blanco** sin salida.

**🟠 ALTO**
- A1 — Objetivos de toque < 44px (step dots 10px, botones idioma 36px) — WCAG 2.5.5.
- A2 — Etiquetas en `text-xs` (12px), contraste justo para móvil bajo sol.
- A3 — Sin ayuda/ejemplo por campo (A-Number, fechas, Given vs Middle name).
- A4 — Cambiar estado de caso (staff) solo por drag-and-drop: **inaccesible por teclado**.
- A5 — `<html lang="en">` fijo mientras la app arranca en español (WCAG 3.1.1).

**🟡 MEDIO:** barra de progreso ignora checkboxes; `role="tab"` mal usado en los dots;
contraste gris en modo oscuro; LanguageSwitcher se solapa con el título en pantallas
estrechas; sin toggle manual de tema; metadata genérica/mezcla idiomas.

Total UX: 4 críticos, 5 altos, 6 medios, 3 bajos.

---

## 4. BENCHMARK DE MERCADO 2026 — qué falta para ser potencia

Comparado con LegistAI, Docketwise ($69–109/usuario/mes), eImmigration (Cerenade), LollyLaw.
Baselines que hoy son ESTÁNDAR, no diferenciador:

| Capacidad estándar 2026 | Estado Imigratepro-2.0 | Gap |
|---|---|---|
| Biblioteca USCIS completa + versionado automático | 97 PDFs, 24 con autofill | Autofill en 73; sin auto-detección de nueva edición |
| Autofill multi-formulario desde 1 perfil de cliente | Parcial (motor sí, reglas no) | Completar reglas de los 73 |
| Portal cliente móvil profesional | Existe, pero con bloqueadores C1–C4 | Pulir UX |
| Multilingüe (idealmente con IA) | UI 100%, labels 17% | Traducir los ~21k labels (IA) |
| USCIS case-status tracking | ✓ ya lo tiene | Ampliar a push |
| AI research + drafting (RFE, cartas) | ✓ RFE AI, form review AI | Ampliar a cartas/petición |
| eFiling nativo (myUSCIS acepta I-130/I-485/N-400/I-765/I-90/I-129... online) | ✗ | FALTA — hoy solo PDF para enviar por correo |
| e-Signature | ✗ | FALTA |
| E-Verify / I-9 compliance (corporativo) | ✗ | FALTA |
| Visa Bulletin + calculadora de plazos por caso | Parcial (citas/recordatorios) | FALTA motor de plazos |
| IOLTA trust accounting + pago de fees USCIS | Facturación básica | FALTA trust + pago |
| Seguridad post-brecha Docketwise 2026 | Cripto sólida, pero IDOR/RBAC/cookies | Ya documentado en AUDIT_REPORTE.md (C1/C2/H1/H5) |

Nota: myUSCIS ya permite filing online de muchos de tus formularios top (I-130, I-485,
N-400, I-765, I-90, I-129, I-131, I-539, I-821D, I-907, N-336/565/600/600K). El eFiling es
el salto de valor más grande frente a "PDF por correo".

---

## 5. PLAN DE EJECUCIÓN (priorizado)

### P0 — Cerrar la promesa al usuario (lo que pediste: formularios + traducción + UX)
1. **Traducir el 83% faltante de labels** (mayor impacto/menor riesgo): generar diccionario
   completo de las 21.298 etiquetas con IA (script no destructivo, revisión humana de una
   muestra legal). Meta: 100% en español. Arreglar el bug "Select Gray.".
2. **Arreglar los 4 bloqueadores UX (C1–C4):** validación+ayuda+borrar en subida de
   archivos; asociar labels (`htmlFor`/`id`) en `FieldInput`/`FieldRow`; validar obligatorios
   + pantalla de "formulario enviado"; crear `app/error.tsx` y `app/loading.tsx`.
3. **Autofill para los 73 formularios en blanco:** extender `autofill_map` con el patrón
   existente. Priorizar por volumen del despacho (I-539, I-765V, I-129, I-140, I-9, I-821D,
   I-864A primero).
4. **`show_if` para los 9 del Grupo B** (ya tienen autofill) y luego el resto.

### P1 — Robustez de formularios
5. Validación post-fill en `pdf_filler.py` (comparar schema vs `writer.get_fields()`, alertar
   campos perdidos) → detecta cambios de edición de USCIS antes de que el cliente envíe un PDF
   a medio llenar.
6. Renovar los 9 "sin validar" + edition dates obsoletos; check automático vs uscis.gov en CI.
7. Unificar carpetas de plantillas (`form_templates/` como fuente única).
8. A11y ALTO: touch targets 44px, `text-sm` + contraste, hints por campo, alternativa de
   teclado al drag-and-drop, `<html lang>` correcto.

### P2 — Ser potencia (mercado)
9. **eFiling nativo** vía myUSCIS (empezar por I-130/I-485/N-400/I-765) — el mayor salto.
10. **e-Signature**, **Visa Bulletin + calculadora de plazos**, **E-Verify/I-9**,
    **IOLTA trust accounting + pago de fees**.
11. Cerrar los bloqueadores de SEGURIDAD ya documentados (IDOR/RBAC/cookies httpOnly/
    SECRET_KEY/audit log) antes de exponer a tráfico real con PII — ver `AUDIT_REPORTE.md`.

---

## 6. METODOLOGÍA / LIMITACIONES
- Read-only: ningún archivo del proyecto fue modificado. 3 subagentes leyeron backend,
  frontend, 97 JSON/PDF y ejecutaron conteos automatizados (verificados).
- No se ejecutó la app contra una BD viva; el llenado real de cada PDF debe validarse
  ejecutando contra los PDFs de `form_templates/`.
- Benchmark basado en fuentes 2026 (LegistAI, Docketwise, eImmigration, LollyLaw, uscis.gov
  "Forms Available to File Online", rev. 06/11/2026).
