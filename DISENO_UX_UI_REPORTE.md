# REPORTE DE DISEÑO — UX / UI — Imigratepro-2.0

Fecha: 2026-07-20
Alcance: Diseño, UX y design-system del frontend (read-only, NO se modificó ningún archivo)
Autor: Hermes Agent (2 subagentes en paralelo: UX/usabilidad, design-system/UI-engineering)
        + contraste contra `design/*.md` (intención de marca/UX declarada) y README

---

## 1. RESUMEN EJECUTIVO

El frontend es **funcional y bastante pulido para un MVP**: navegación lateral coherente,
componentes compartidos (`Button`, `Card`, `Badge`), portal de cliente con autosave por pasos,
buen manejo de estados vacíos, responsive móvil decente, y multi-idioma ES/EN. La base es sólida.

Pero hay **dos frentes de deuda**:
1. **Flujo (UX):** no existe página de detalle de caso (todo inline), el editor interno de
   formularios (el flujo CORE) NO tiene autosave ni protección de navegación, y faltan
   edición/eliminación de clientes y casos.
2. **Design system:** es **ad-hoc sobre utilidades Tailwind, no un sistema de tokens**. Hay un
   bug real de tipografía (Arial anula Geist), no hay tokens semánticos, el modo oscuro funciona
   "por sistema" pero sin tokens ni toggle (viola la intención declarada en `design/`), se
   duplican colores de estado en 3 sitios, y faltan skeletons/empty states.

**Conteo de hallazgos:** 6 Critical/High, 17 Medium, 16 Low.

---

## 2. HALLAZGOS DE UX / USABILIDAD

### 🔴 CRÍTICO / ALTO

**C1 — No existe página de detalle de caso (`cases/[id]`).** Todo el detalle (participantes,
servicio/checklist, RFE, formularios, citas, facturas) se renderiza inline como acordeón dentro
de `cases/page.tsx:246-689`. No hay URL deep-linkable ni breadcrumb; navegar a formularios/citas
es unidireccional. `handleOpenFromBoard` (`:123-126`) hace un truco frágil.
→ Fix: crear `cases/[id]/page.tsx` y mover el detalle ahí.

**C2 — El editor interno de formularios NO tiene autosave** (solo el portal cliente). `forms/[id]/page.tsx:149-168`
guarda solo al pulsar "Guardar y regenerar PDF". Para un I-485 de ~736 campos, una caída de
conexión pierde el trabajo. El portal cliente sí autosavea por paso (`client/forms/[token]/page.tsx:130-156`).
→ Fix: autosave debounced en el editor interno.

**C3 — El sidebar no protege contra pérdida de cambios.** `beforeunload` no cubre navegación
client-side de Next (`forms/[id]/page.tsx:137-139`); un clic en "Casos" pierde cambios sin aviso.
→ Fix: interceptar navegación del router cuando `isDirty`.

**C4 — Enlaces "Mi día" apuntan a `/cases` genérico, no al caso.** `page.tsx:64-65,97,119`.
Rompe el flujo intake→form→review del preparador.
→ Fix: enlazar a `/cases/[id]`.

**C5 — No se pueden editar ni eliminar clientes.** `clients/page.tsx` solo crea y lista
(`:263-292`, solo lectura). Para CRM de inmigración (datos que cambian) es un hueco grave.
→ Fix: edición inline + eliminación.

**C6 — Generar formulario desde un caso fuerza re-seleccionar el caso.** `cases/page.tsx:672-679`
→ `/forms` donde hay que volver a elegir en `<select>` (`forms/page.tsx:111-122`).
→ Fix: botón "Generar formulario para este caso" con caso preseleccionado.

### 🟠 MEDIUM

- **M1** Editor no pagina por Partes (solo `<details>`); el portal SÍ paga por parte
  (`forms/[id]/page.tsx:460-511` vs `client/...:196-295`). → Reutilizar patrón wizard.
- **M2** Progreso excluye checkboxes y engaña (`forms/[id]/page.tsx:104-106`, label ES
  `i18n.tsx:160` lo confirma). En I-485 hay decenas de "Select only one box".
- **M3** Idioma default del editor = ES (referencia), no EN (oficial) `forms/[id]/page.tsx:52`.
  En formulario legal el inglés debería ser default.
- **M4** `<html lang>` estático "en" (`layout.tsx:29`); no cambia al pasar a ES. Afecta
  lectores de pantalla/SEO. → actualizar `document.documentElement.lang` en `setLang`.
- **M5** Contraste insuficiente: `text-zinc-400/500` ~2.5-3:1, bajo WCAG AA 4.5:1
  (`CaseTimeline.tsx:27-28`, `clients/page.tsx:270-285`). → subir a `zinc-600`.
- **M6** Desincronización de `<details>` al buscar (`forms/[id]/page.tsx:462-478`).
- **M7** Confirmaciones destructivas con `window.confirm` nativo (`documents:144`,
  `appointments:82`, `billing:101,135`, `RfePanel:88`). → modal con contexto.
- **M8** Casos no se pueden eliminar (`cases/page.tsx`). → añadir borrado con confirmación.
- **M9** Falta breadcrumb en editor y portal. → ruta de migas.
- **M10** Editor no valida requeridos antes de guardar/PDF (`forms/[id]/page.tsx:283-284`).
  → resumen de vacíos.
- **M11** Lista de casos sin paginación/orden a escala (`cases/page.tsx:351-684`).
- **M12** Servicios y equipo: solo crear, sin editar/borrar (`services/page.tsx`, `team/page.tsx`).

### 🟡 LOW (consistencia)

- **L1** Cada página redefine `inputClass`/`labelClass` localmente → extraer `TextField`/`SelectField`.
- **L2** Anchos inconsistentes: editor `max-w-3xl` vs portal `max-w-2xl`.
- **L3** `Badge` reutilizado con semántica equivocada para citas (`appointments/page.tsx:199`).
- **L4** Gráfico "casos por tipo" monocolor (`stats/page.tsx:166`).
- **L5** Estado de carga global solo texto (`AppShell.tsx:204-210`).
- **L6** Drawer móvil sin focus-trap ni `Esc` (`AppShell.tsx:221-242`).
- **L7** `NotificationBell` sin `aria-live` (`:58-111`).
- **L8** `LanguageSwitcher` comportamiento distinto en auth vs AppShell.
- **L9** Portal cliente: límite 20 MB solo aparece en error (`client/forms/[token]/page.tsx:222`).
- **L10** "Mi día" desaparece silenciosamente si no hay actividad (`page.tsx:37`).

**Lo bueno (mantener):** portal cliente con autosave + "continuando donde lo dejaste" + dots de
navegación; `FieldRow`/`CheckboxGroupField` memoizados (400+ filas); pills táctiles 44px;
`CaseTimeline` con `sr-only`; `Button` con `focus-visible:ring`; estados vacíos consistentes.

---

## 3. HALLAZGOS DE DESIGN SYSTEM / UI ENGINEERING

### 🔴 HIGH (riesgo de escalado / bug de marca)

**H1 — `globals.css:25` fuerza `font-family: Arial` y anula Geist** cableada en `layout.tsx:7-15,30`.
La marca "Geist" nunca se aplica; todo el sitio renderiza en Arial.
→ Fix: `font-family: var(--font-geist-sans), system-ui, sans-serif;` (o `font-sans`).

**H2 — No existe sistema de design tokens semánticos.** `globals.css:3-13` solo
`--background/--foreground/--font-*`. Todos los colores (`indigo-600`, `zinc-200`, `amber-50`…),
radios y sombras están hardcodeados como utilidades dispersas. Riesgo alto de deriva.
→ Fix: bloque `@theme` con `--color-brand`, semánticos `success/warning/error/info`, escala
`radius/shadow`.

**H3 — Modo oscuro inconsistente + sin toggle** (viola `design-ux-architect.md:26` y
`design-ui-designer.md:31`). Superficies oscuras mezclan 4 niveles sin criterio
(`dark:bg-black`/`zinc-950`/`zinc-900`/`zinc-800`). `globals.css:15-20` usa solo
`@media (prefers-color-scheme)` → no hay toggle claro/oscuro/sistema ni `data-theme`.
→ Fix: tokens de superficie `--surface-1/2/3` + toggle con `data-theme` + ThemeManager.

**H4 — Lógica de color de estados duplicada en 3 sitios.** `Badge.tsx:1-24` (22 entradas
`COLOR_MAP`), `page.tsx:11-15` (`PRIORITY_CLASSES`), `page.tsx:79` (inline `bg-red-50…`).
Cualquier cambio de paleta exige editar 3 lugares.
→ Fix: módulo único `statusColors.ts`.

### 🟠 MEDIUM

- **M1** Cero skeletons/empty states/spinners (`skeleton|loading|empty|animate-spin` → 0 en `src`).
  `MyDaySection` hace `return null` mientras carga. Viola `design-ui-designer.md:292-294`.
- **M2** Sistema de iconos ad-hoc: 13 SVG inline en `AppShell` + glifos Unicode en el dashboard
  (`page.tsx:138-146` ◒ ▤ ◕ ◈…). Lenguajes visuales distintos. → `components/icons.tsx` o `lucide-react`.
- **M3** `Card` no se usa consistentemente: `MyDayStat` y superficies de `AppShell` reimplementan
  a mano `rounded-lg border …` en vez de `<Card>`.
- **M4** Sin `cn`/`tailwind-merge` → overrides poco fiables (`Button.tsx:20`, `Card.tsx:6`
  concatenan strings). → `clsx` + `tailwind-merge`.
- **M5** Fragmentación de nombre de marca: "Imigratepro-2.0" (carpeta) / "MigratePro" (UI
  `AppShell.tsx:155,253`) / "Immigration Case Manager" (`layout.tsx:18` metadata). Tres identidades.

### 🟡 LOW

- **L1** Radios inconsistentes sin token (`rounded-xl`/`lg`/`md`/`full`). → escala `--radius`.
- **L2** `FieldInput` sin `focus-visible` ring (`:31,48,58`) mientras `Button`/`CheckboxGroupField` sí.
- **L3** `dark:text-zinc-50` (FieldInput) vs `dark:text-zinc-100` (page/Card).
- **L4** `AppShell` fondo oscuro `dark:bg-black` choca con `dark:bg-zinc-950` del sidebar.
- **L5** `prefers-color-scheme` sin `data-theme` → sin opción de forzar claro/oscuro.
- **L6** Padding de inputs `p-1.5` algo pequeño para formularios largos.

**Veredicto design-system:** sistema ad-hoc sobre Tailwind, NO design system coherente. Buenos
instintos (variantes de Button, Badge semántico, memo en filas, responsive decente) pero falta la
capa de tokens, hay duplicación de color de estado, iconos inconsistentes y un bug real de
tipografía. Responsividad: aceptable (Medium). Sin skeletons/empty states: gap claro vs `design/`.

---

## 4. CONTRASTE: INTENCIÓN DECLARADA vs IMPLEMENTACIÓN

La carpeta `design/` contiene 9 roles (Brand Guardian, UX Architect, UI Designer, UX Researcher,
etc.) con principios explícitos. La implementación cumple parcialmente:

| Principio declarado en `design/`            | Estado en código | Gap |
|---------------------------------------------|-----------------|-----|
| Design tokens semánticos (UX Architect)     | ✗ no hay        | H2 |
| Toggle claro/oscuro/sistema (UX Architect:26) | ✗ solo por sistema | H3 |
| Skeletons / empty / loading states (UI Designer:292) | ✗ 0 coincidencias | M1 |
| Librería de iconos coherente                | ✗ SVG inline + glifos Unicode | M2 |
| CSS variables + spacing scale + tipografía  | Parcial (Geist rota por Arial) | H1 |
| Marca coherente                             | ✗ 3 nombres     | M5 |
| Accesibilidad / labels / responsive         | ✓ (README documenta correcciones hechas) | ok |

Conclusión: el equipo (o los agentes de diseño) definió BUENOS principios, pero la implementación
se quedó a medias respecto a ellos. El work está hecho al 60-70%.

---

## 5. ROADMAP DE DISEÑO (priorizado)

### P0 — Flujo core (antes de cualquier demo a cliente)
1. C1: crear `cases/[id]/page.tsx` (desbloquea deep-links + breadcrumb).
2. C4: enlaces "Mi día" → caso concreto.
3. C2 + C3: autosave + protección de navegación en editor interno (evita pérdida de datos).
4. C5: edición/eliminación de clientes. C6: preseleccionar caso al generar.

### P1 — Design system (antes de escalar UI)
5. H1: arreglar tipografía (Geist, no Arial).
6. H2: capa de tokens semánticos (`@theme`).
7. H3: modo oscuro con tokens + toggle `data-theme`.
8. H4: unificar colores de estado en `statusColors.ts`.
9. M1: skeletons/empty states. M2: librería de iconos. M4: `cn()` + tailwind-merge. M5: un nombre.

### P2 — Pulido
10. M1/M2/M3 (paginación por parte, incluir checkboxes en progreso, default EN).
11. M4/M5 (lang dinámico, contraste zinc-600).
12. L1-L10 (consistencia de radios, focus ring, focus-trap drawer, aria-live, breadcrumbs,
    validación de requeridos, paginación de lista, edición de servicios/equipo).

---

## 6. METODOLOGÍA / LIMITACIONES
- Read-only: ningún archivo modificado. Los 2 subagentes leyeron ~35 archivos del frontend.
- No se ejecutó `next build` (fuera de alcance read-only). Tailwind v4 confirmado en node_modules.
- Contraste con `design/*.md` (intención) y README (correcciones ya hechas).
- Benchmark implícito: SaaS legales tipo Clio/MyCase exigen design tokens, dark mode, estados de
  carga y deep-links — estándar que este proyecto aún no alcanza del todo.
