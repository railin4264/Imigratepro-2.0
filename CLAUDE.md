# Imigratepro-2.0 — Project Context (ROOT)

## What this is
Immigration Case Manager: FastAPI + Next.js platform for law firms managing
immigration cases. Handles PII (SSN, passport, A-number) — treat ALL data as
sensitive. Post-Docketwise-breach (2026) sector standard applies.

## Stack
- Backend: FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic, Python 3.13
- Frontend: Next.js (App Router) + React + TypeScript + Tailwind
- Data: PostgreSQL in prod (SQLite default local), Redis+Celery for bg tasks

## CRITICAL SECURITY RULES (from 2026-07-20 audit — MUST FIX before any real traffic)
These are BLOCKING. Do NOT introduce regressions:
- **IDOR (C1):** every `/{id}` entity route MUST scope by ownership
  (`case.assigned_attorney_id == current_user.id OR admin`). Add
  `require_case_access()` dependency. Affects cases/clients/documents/billing/rfes/appointments/forms.
- **RBAC (H1):** `RequireRole(UserRole)` on all sensitive mutating routes. paralegal
  must NOT create cases/invoices/delete everything.
- **Public portal field allowlist (C2/H4):** validate `payload.data` keys against
  `client_editable_fields` from field_schema; reject unknown keys with 422.
- **Tokens (H5):** NEVER put JWT in localStorage. Use httpOnly+Secure+SameSite=Strict
  cookies set by backend. Remove all localStorage token usage in frontend.
- **API URL (H6):** `NEXT_PUBLIC_API_URL` default MUST be `https://` and build must
  fail if unset.
- **Client portal token (H7):** do NOT put portal token in URL.
- **SECRET_KEY (H2):** no insecure default. `sys.exit` if default in prod.
- **Audit log (M6):** log all destructive/sensitive actions (legal compliance).

## Do NOT touch (audited as solid)
- ORM parameterized queries (no SQLi)
- `decode_access_token` HMAC recalc (immune to alg confusion)
- reset/refresh hashed + single-use, rate-limited login
- `storage.save_upload` uses uuid4 (no traversal)
- USCIS API handling (401/404/422/429/503)
- frontend: no `dangerouslySetInnerHTML`/`eval`

## How to run
Backend (local, SQLite):
  cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
  .venv/Scripts/python -m alembic upgrade head
  .venv/Scripts/python -m app.seed_admin
  .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
Frontend:
  cd frontend && npm install && npm run dev
Tests: backend `pytest` (147 tests), frontend `npm test` + Playwright e2e.

## Form coverage
System fills 16 of ~107 USCIS forms. Scripts in backend/form_templates/uscis_forms/
(VALIDATION.txt, INDICE.txt) validate against uscis.gov.
