# Revisión de Producto — Imigratepro-2.0

PM: Hermes (guía: product-manager de agency-agentsss).
Fecha: 2026-07-22. Contexto: SaaS gestión de casos de inmigración para despachos legales.
Estado actual: casos, clientes, documentos, formularios USCIS (16 de ~107), facturación, RFEs,
citas, portal de cliente (dark mode, i18n ES/EN 100%), notificaciones por rol, formularios por
categoría, casos con fechas clave + parent (packages), seguridad (IDOR/RBAC parcial/audit).

## 1. Features faltantes vs competencia (Docketwise / Clio / LawLogix)
Priorización impacto (1-5) / esfuerzo (1-5). ROI = impacto/esfuerzo.

| # | Feature | Impacto | Esfuerzo | ROI | Notas |
|---|---------|:---:|:---:|:---:|-------|
| 1 | Cobertura de formularios USCIS (16→60+) | 5 | 4 | 1.25 | Es EL diferenciador del sector; 16/107 es bajo. Priorizar los top-20 por volumen (I-130,485,765,131,864,90,751,129,140,539,821,600,824,600A,I-864EZ...) |
| 2 | MFA / 2FA para staff y portal | 5 | 2 | 2.5 | Post-brecha Docketwise 2026 es tabla-stakes. Quick win. |
| 3 | Permisos granulares por rol/equipo (asignación paralegal) | 4 | 3 | 1.33 | Cierra el gap IDOR de lectura; habilita despachos con contratistas. |
| 4 | Recordatorios automáticos de deadlines (priority_date, RFE due, decision_deadline) | 5 | 2 | 2.5 | Ya existen los campos de fecha (Fase E). Solo falta el scheduler + notif. ALTO ROI. |
| 5 | E-signature integrada (o DocuSign/Dropbox Sign) | 4 | 3 | 1.33 | Existe modelo e_signature; falta flujo completo cliente. |
| 6 | Portal de cliente: subida de documentos con checklist por tipo de caso | 4 | 3 | 1.33 | Reduce ida-y-vuelta con el cliente. |
| 7 | Reportes/analytics (casos por estado, ingresos, SLA) | 3 | 3 | 1.0 | Retención de despachos; dashboards de gerencia. |
| 8 | Integración USCIS case status (bulk polling) | 4 | 3 | 1.33 | Ya hay manejo de la API USCIS; falta polling programado + alertas. |
| 9 | Plantillas de comunicación / email al cliente | 3 | 2 | 1.5 | Quick win; correos de estado automatizados. |
| 10 | Time tracking + trust accounting (IOLTA) | 4 | 4 | 1.0 | Clio lo tiene; crítico para facturación legal correcta. |

## 2. Huecos de workflow
- **Intake → Caso**: falta un wizard de intake que cree cliente + caso + checklist de documentos en un flujo. Hoy son pasos sueltos.
- **Caso → Formularios**: falta "autollenado en cascada" (datos del cliente → todos los forms del caso). Reduciría el trabajo manual del paralegal drásticamente.
- **Formularios → Firma → Presentación**: la cadena e-sign → generar PDF final → marcar "filed" con receipt number no está unificada (los campos existen tras Fase E, falta el flujo).
- **Packages (parent_case_id)**: el modelo ya soporta paquetes (I-130+I-485+I-765) — falta UI para crear/gestionar el paquete como unidad y compartir datos entre sub-casos.
- **Notificaciones**: ahora son dirigidas por rol (Fase C) — falta el canal (email/push), hoy es solo feed in-app.

## 3. Cumplimiento (post-brecha Docketwise 2026 — sector standard)
| Gap | Severidad | Acción |
|-----|:---:|--------|
| MFA ausente | ALTA | Implementar TOTP para staff + portal (feature #2). |
| Retención/borrado de datos (PII) | ALTA | Política de retención + borrado seguro (SSN/A-number); export bajo demanda. |
| Scope de lectura amplio (cualquier staff ve todo) | MEDIA | Permisos por equipo (feature #3). |
| Cifrado en reposo de PII | ALTA | Verificar cifrado de columnas sensibles (SSN/pasaporte) o cifrado a nivel DB. |
| Registro de auditoría de accesos de LECTURA | MEDIA | Hoy se audita escritura/borrado; añadir log de acceso a PII para cumplimiento. |
| Backups + DR | MEDIA | Definir RPO/RTO; hoy SQLite local, prod requiere PostgreSQL gestionado + backups. |

## 4. Quick wins (hacer ya) vs apuestas grandes
QUICK WINS (alto ROI, bajo esfuerzo):
- #2 MFA/2FA.
- #4 Recordatorios de deadlines (los campos ya existen).
- #9 Plantillas de email al cliente.
- Fix RBAC de clients.py/create_case (ver revisión de seguridad).

APUESTAS GRANDES (alto impacto, mayor esfuerzo):
- #1 Cobertura de formularios USCIS (el foso competitivo real).
- #10 Trust accounting / IOLTA.
- Autollenado en cascada de formularios del caso.

## Recomendación de secuencia (próximos 3 sprints)
1. Sprint 1 (seguridad+cumplimiento): fixes RBAC + MFA + recordatorios de deadlines.
2. Sprint 2 (workflow): wizard de intake + autollenado en cascada + packages UI.
3. Sprint 3 (foso): ampliar cobertura de formularios USCIS (top-20 por volumen) + USCIS status polling.
