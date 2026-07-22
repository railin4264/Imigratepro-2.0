const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// Auth lives in httpOnly cookies the backend sets on /auth/login (see
// backend/app/api/v1/endpoints/auth.py) -- nothing here reads or stores a
// token in JS-visible state. `credentials: "include"` on every fetch below
// is what makes the browser attach those cookies; no Authorization header
// is set from the frontend at all. This also removes what used to be a real
// race: a page's very first request on a hard reload no longer needs to
// wait for anything to "load" a token before it can go out correctly, since
// the browser attaches the cookie regardless of React's render/effect timing.

// Access tokens are short-lived (30 min, see backend ACCESS_TOKEN_EXPIRE_MINUTES)
// so they expire routinely during a normal session. Rather than have every
// page handle that, fetchJson transparently asks the backend to rotate the
// session (via the refresh_token cookie) on a 401 and retries once.
// `refreshPromise` dedupes concurrent refreshes -- the refresh token rotates
// on use, so two requests racing to refresh at once would have the second
// one fail against an already-consumed token.
let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({}),
        });
        return res.ok;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

export const SEX_OPTIONS = ["male", "female"] as const;
export const MARITAL_STATUS_OPTIONS = [
  "single",
  "married",
  "divorced",
  "widowed",
  "separated",
  "annulled",
] as const;

export type Client = {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  mobile_phone: string | null;
  date_of_birth: string | null;
  country_of_birth: string | null;
  nationality: string | null;
  a_number: string | null;
  passport_number: string | null;
  ssn: string | null;
  sex: (typeof SEX_OPTIONS)[number] | null;
  marital_status: (typeof MARITAL_STATUS_OPTIONS)[number] | null;
  address_line: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  country: string | null;
  created_at: string;
};

export const CASE_TYPES = [
  "family_based",
  "employment_based",
  "asylum",
  "naturalization",
  "adjustment_of_status",
  "work_permit",
  "other",
] as const;

export const CASE_STATUSES = [
  "intake",
  "preparing",
  "filed",
  "rfe",
  "approved",
  "denied",
  "closed",
] as const;

export const PARTICIPANT_ROLES = ["petitioner", "beneficiary", "derivative", "sponsor"] as const;

export type Case = {
  id: string;
  case_number: string;
  case_type: (typeof CASE_TYPES)[number];
  status: (typeof CASE_STATUSES)[number];
  assigned_attorney_id: string | null;
  created_at: string;
  priority_date: string | null;
  filed_date: string | null;
  decision_deadline: string | null;
  uscis_receipt_number: string | null;
  parent_case_id: string | null;
};

export const USER_ROLES = [
  "owner",
  "admin",
  "attorney",
  "paralegal",
  "legal_assistant",
  "intake",
  "billing",
  "contract_attorney",
] as const;

export type User = {
  id: string;
  full_name: string;
  email: string;
  role: (typeof USER_ROLES)[number];
  is_active: boolean;
  created_at: string;
};

export type Participant = {
  id: string;
  case_id: string;
  client_id: string;
  role: (typeof PARTICIPANT_ROLES)[number];
};

export type Service = {
  id: string;
  name: string;
  description: string | null;
  price: number | null;
  estimated_days: number | null;
  created_at: string;
  form_codes: string[];
  checklist_items: string[];
  stages: string[];
};

export const CHECKLIST_PRIORITIES = ["low", "medium", "high"] as const;

export type ChecklistItem = {
  id: string;
  label: string;
  order: number;
  done: boolean;
  done_at: string | null;
  assigned_to_id: string | null;
  due_date: string | null;
  priority: (typeof CHECKLIST_PRIORITIES)[number];
};

export type CaseServiceView = {
  service: Service | null;
  stages: string[];
  current_stage: string | null;
  current_stage_index: number | null;
  checklist: ChecklistItem[];
};

export type FormTemplate = {
  id: string;
  code: string;
  name: string;
  edition_date: string | null;
};

export type GeneratedForm = {
  id: string;
  case_id: string;
  form_template_id: string;
  form_code: string;
  status: string;
  created_at: string;
  access_token: string;
  client_link_enabled: boolean;
  uscis_receipt_number: string | null;
  uscis_status_checked_at: string | null;
};

export type ShowIfCondition = {
  field: string;
  equals: string;
};

export type FieldSchemaEntry = {
  name: string;
  type: "text" | "checkbox" | "choice";
  label: string;
  page: number | null;
  on_value?: string | null;
  options?: string[] | null;
  show_if?: ShowIfCondition[] | null;
};

export type FormTemplateSchema = {
  code: string;
  name: string;
  fields: FieldSchemaEntry[];
};

export type ReviewFinding = {
  severity: "high" | "medium" | "low";
  field_label: string;
  issue: string;
};

export type AiReview = {
  overall_assessment: string;
  findings: ReviewFinding[];
};

export type USCISHistCaseStatus = {
  date: string;
  completed_text_en: string;
  completed_text_es: string;
};

// Raw shape USCIS's Case Status API returns, stored/passed through as-is (see
// backend/app/services/uscis_case_status.py for why). submittedDate/modifiedDate
// are absent for IOE-prefixed receipt numbers per USCIS's own schema split.
export type USCISCaseStatus = {
  case_status: {
    receiptNumber: string;
    formType: string;
    submittedDate?: string;
    modifiedDate?: string;
    current_case_status_text_en: string;
    current_case_status_desc_en: string;
    current_case_status_text_es: string;
    current_case_status_desc_es: string;
    hist_case_status?: USCISHistCaseStatus[];
  };
  message: string;
};

export type GeneratedFormDetail = GeneratedForm & {
  data: Record<string, string>;
  form_code: string;
  ai_review: AiReview | null;
  ai_reviewed_at: string | null;
  uscis_status_raw: USCISCaseStatus | null;
};

export type PublicFormView = {
  form_code: string;
  form_name: string;
  case_number: string;
  fields: FieldSchemaEntry[];
  data: Record<string, string>;
  client_wizard_step: number;
};

export const DOCUMENT_TYPES = [
  "passport",
  "birth_certificate",
  "marriage_certificate",
  "i94",
  "photo_id",
  "evidence",
  "other",
] as const;

export type UploadedDocument = {
  id: string;
  client_id: string | null;
  case_id: string | null;
  document_type: string;
  status: string;
  original_filename: string;
  content_type: string | null;
  created_at: string;
};

export type DocumentExtractedData = {
  document_type: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  country_of_birth: string;
  nationality: string;
  passport_number: string;
  a_number: string;
  expiration_date: string;
  confidence_notes: string;
  error?: string;
};

export type DocumentDetail = UploadedDocument & {
  extracted_data: DocumentExtractedData | null;
};

const _AUTH_EXEMPT_PREFIXES = [
  "/public/",
  "/auth/login",
  "/auth/refresh",
  "/auth/forgot-password",
  "/auth/reset-password",
  // Client-portal sessions use their own token type and their own refresh
  // endpoint (/client-auth/refresh), not the staff one -- exempting the
  // whole prefix keeps a client's expired-session 401 from triggering the
  // staff authFetch's retry-via-/auth/refresh path, which would never work
  // for a client token and would misfire the staff "unauthorized" event.
  "/client-auth/",
];

// Shared by fetchJson and downloadFile: sends the session cookie, retries
// once on 401 after a token refresh, and normalizes auth failure handling.
// `credentials: "include"` is required on every call -- without it the
// browser won't attach the httpOnly cookies at all, since the frontend
// (localhost:3000) and backend (localhost:8000) are different origins.
async function authFetch(path: string, init?: RequestInit, _retried = false): Promise<Response> {
  const exempt = _AUTH_EXEMPT_PREFIXES.some((p) => path.startsWith(p));

  const res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init, credentials: "include" });

  if (res.status === 401) {
    if (!exempt && !_retried && (await tryRefresh())) {
      return authFetch(path, init, true);
    }
    if (typeof window !== "undefined" && !exempt) {
      window.dispatchEvent(new Event("migratepro-unauthorized"));
    }
    throw new Error(`Request to ${path} failed: 401`);
  }
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  return res;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await authFetch(path, init);
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

// Fetches a protected file and returns it as a blob + the filename the
// server chose (from Content-Disposition). Goes through fetch() rather than
// a plain <a href> mainly to show a loading state and surface errors in the
// UI -- a same-site <a href> would actually carry the auth cookie now too,
// but a bare link can't show "downloading..." or a failure message.
async function fetchFile(path: string): Promise<{ blob: Blob; filename: string | null }> {
  const res = await authFetch(path);
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  return { blob: await res.blob(), filename: match ? match[1] : null };
}

export function getClients(): Promise<Client[]> {
  return fetchJson("/clients");
}

export type NewClient = {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  mobile_phone?: string;
  date_of_birth?: string;
  country_of_birth?: string;
  nationality?: string;
  a_number?: string;
  ssn?: string;
  sex?: string;
  marital_status?: string;
  address_line?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
};

export function createClient(payload: NewClient): Promise<Client> {
  return fetchJson("/clients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getClient(clientId: string): Promise<Client> {
  return fetchJson(`/clients/${clientId}`);
}

export function updateClient(clientId: string, payload: Partial<NewClient>): Promise<Client> {
  return fetchJson(`/clients/${clientId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteClient(clientId: string): Promise<void> {
  return fetchJson(`/clients/${clientId}`, { method: "DELETE" });
}

export function getCases(): Promise<Case[]> {
  return fetchJson("/cases");
}

export function getCase(caseId: string): Promise<Case> {
  return fetchJson(`/cases/${caseId}`);
}

export function createCase(payload: {
  case_number: string;
  case_type: string;
  status: string;
}): Promise<Case> {
  return fetchJson("/cases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateCase(
  caseId: string,
  payload: Partial<{ assigned_attorney_id: string | null; status: string; case_type: string; notes: string }>,
): Promise<Case> {
  return fetchJson(`/cases/${caseId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteCase(caseId: string): Promise<void> {
  return fetchJson(`/cases/${caseId}`, { method: "DELETE" });
}

export function getUsers(): Promise<User[]> {
  return fetchJson("/users");
}

export function createUser(payload: {
  full_name: string;
  email: string;
  role: string;
  bar_number?: string;
  firm_name?: string;
  phone?: string;
}): Promise<User> {
  return fetchJson("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateUser(
  userId: string,
  payload: Partial<{
    full_name: string;
    role: string;
    is_active: boolean;
    bar_number: string;
    firm_name: string;
    phone: string;
    mobile_phone: string;
    address_line: string;
    city: string;
    state: string;
    zip_code: string;
  }>,
): Promise<User> {
  return fetchJson(`/users/${userId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export type UserWorkload = {
  user: User;
  assigned_case_count: number;
  cases_by_status: Record<string, number>;
  open_rfe_count: number;
  overdue_checklist_count: number;
};

export function getUserWorkload(): Promise<UserWorkload[]> {
  return fetchJson("/users/workload");
}

export function getParticipants(caseId: string): Promise<Participant[]> {
  return fetchJson(`/cases/${caseId}/participants`);
}

export function addParticipant(caseId: string, clientId: string, role: string): Promise<Participant> {
  return fetchJson(`/cases/${caseId}/participants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId, role }),
  });
}

export function getFormTemplates(): Promise<FormTemplate[]> {
  return fetchJson("/form-templates");
}

export function getGeneratedForms(caseId: string): Promise<GeneratedForm[]> {
  return fetchJson(`/cases/${caseId}/forms`);
}

export function generateForm(caseId: string, formCode: string): Promise<GeneratedForm> {
  return fetchJson(`/cases/${caseId}/forms`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ form_code: formCode }),
  });
}

// Downloads happen behind auth, so a plain <a href> can't be used (no way to
// attach the Authorization header to a browser-initiated navigation) --
// fetch the PDF as a blob and trigger the save via a throwaway object URL.
export async function downloadGeneratedForm(generatedFormId: string, fallbackFilename = "form.pdf"): Promise<void> {
  const { blob, filename } = await fetchFile(`/forms/${generatedFormId}/download`);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename ?? fallbackFilename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function getFormTemplateSchema(code: string): Promise<FormTemplateSchema> {
  return fetchJson(`/form-templates/${code}/schema`);
}

export function getGeneratedForm(id: string): Promise<GeneratedFormDetail> {
  return fetchJson(`/forms/${id}`);
}

export function updateGeneratedForm(id: string, data: Record<string, string>): Promise<GeneratedForm> {
  return fetchJson(`/forms/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  });
}

export function getServices(): Promise<Service[]> {
  return fetchJson("/services");
}

export function createService(payload: {
  name: string;
  description?: string;
  price?: number;
  estimated_days?: number;
  form_template_codes: string[];
  checklist_items: string[];
  stages: string[];
}): Promise<Service> {
  return fetchJson("/services", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getCaseService(caseId: string): Promise<CaseServiceView> {
  return fetchJson(`/cases/${caseId}/service`);
}

export function applyServiceToCase(caseId: string, serviceId: string): Promise<CaseServiceView> {
  return fetchJson(`/cases/${caseId}/apply-service`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ service_id: serviceId }),
  });
}

export function toggleChecklistItem(caseId: string, itemId: string, done: boolean): Promise<ChecklistItem> {
  return fetchJson(`/cases/${caseId}/checklist/${itemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ done }),
  });
}

export function updateChecklistItem(
  caseId: string,
  itemId: string,
  payload: Partial<{ assigned_to_id: string | null; due_date: string | null; priority: string }>,
): Promise<ChecklistItem> {
  return fetchJson(`/cases/${caseId}/checklist/${itemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function advanceStage(caseId: string): Promise<CaseServiceView> {
  return fetchJson(`/cases/${caseId}/advance-stage`, { method: "POST" });
}

export type NotificationType =
  | "case_assigned"
  | "stage_advanced"
  | "document_uploaded"
  | "ai_review_flagged"
  | "appointment_scheduled"
  | "appointment_reminder"
  | "invoice_overdue"
  | "payment_received"
  | "rfe_received";

export type Notification = {
  id: string;
  type: NotificationType;
  message: string;
  case_id: string | null;
  case_number: string | null;
  created_at: string;
  read: boolean;
};

export function getNotifications(): Promise<Notification[]> {
  return fetchJson("/notifications");
}

export function markNotificationsRead(notificationIds: string[]): Promise<void> {
  return fetchJson("/notifications/mark-read", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notification_ids: notificationIds }),
  });
}

export function markAllNotificationsRead(): Promise<void> {
  return fetchJson("/notifications/mark-all-read", { method: "POST" });
}

export function clientLinkUrl(accessToken: string): string {
  const base = typeof window !== "undefined" ? window.location.origin : "";
  return `${base}/client/forms/${accessToken}`;
}

export function getPublicForm(token: string): Promise<PublicFormView> {
  return fetchJson(`/public/forms/${token}`);
}

export function updatePublicForm(
  token: string,
  data: Record<string, string>,
  clientWizardStep?: number
): Promise<PublicFormView> {
  return fetchJson(`/public/forms/${token}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data, client_wizard_step: clientWizardStep }),
  });
}

export function reviewGeneratedForm(id: string): Promise<GeneratedFormDetail> {
  return fetchJson(`/forms/${id}/review`, { method: "POST" });
}

export function getUscisApiStatus(): Promise<{ configured: boolean }> {
  return fetchJson("/uscis/status");
}

export function setReceiptNumber(id: string, receiptNumber: string | null): Promise<GeneratedForm> {
  return fetchJson(`/forms/${id}/receipt-number`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ uscis_receipt_number: receiptNumber }),
  });
}

export function checkUscisStatus(id: string): Promise<GeneratedFormDetail> {
  return fetchJson(`/forms/${id}/check-status`, { method: "POST" });
}

export function getAiStatus(): Promise<{ configured: boolean }> {
  return fetchJson("/documents/ai-status");
}

export function getDocuments(filters?: { caseId?: string; clientId?: string }): Promise<UploadedDocument[]> {
  const params = new URLSearchParams();
  if (filters?.caseId) params.set("case_id", filters.caseId);
  if (filters?.clientId) params.set("client_id", filters.clientId);
  const qs = params.toString();
  return fetchJson(`/documents${qs ? `?${qs}` : ""}`);
}

export function getCaseDocuments(caseId: string): Promise<UploadedDocument[]> {
  return fetchJson(`/cases/${caseId}/documents`);
}

export function uploadCaseDocument(
  caseId: string,
  file: File,
  options?: { clientId?: string; documentType?: string },
): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append("file", file);
  if (options?.clientId) formData.append("client_id", options.clientId);
  if (options?.documentType) formData.append("document_type", options.documentType);
  return fetchJson(`/cases/${caseId}/documents`, { method: "POST", body: formData });
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return fetchJson(`/documents/${id}`);
}

export function deleteDocument(id: string): Promise<void> {
  return fetchJson(`/documents/${id}`, { method: "DELETE" });
}

export function extractDocument(id: string): Promise<DocumentDetail> {
  return fetchJson(`/documents/${id}/extract`, { method: "POST" });
}

export function applyDocumentToClient(id: string, fields: string[]): Promise<DocumentDetail> {
  return fetchJson(`/documents/${id}/apply-to-client`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields }),
  });
}

export function listPublicDocuments(token: string): Promise<UploadedDocument[]> {
  return fetchJson(`/public/forms/${token}/documents`);
}

export function uploadPublicDocument(token: string, file: File, role?: string): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append("file", file);
  if (role) formData.append("role", role);
  return fetchJson(`/public/forms/${token}/documents`, {
    method: "POST",
    body: formData,
  });
}

// --- Auth ---------------------------------------------------------------

export type AuthUser = {
  id: string;
  full_name: string;
  email: string;
  role: (typeof USER_ROLES)[number];
};

export async function login(email: string, password: string): Promise<AuthUser> {
  // The response body still includes the tokens too (for non-browser API
  // clients), but the browser frontend ignores them -- the Set-Cookie
  // headers alongside this response are what actually establish the session.
  const result = await fetchJson<{ access_token: string; refresh_token: string; token_type: string; user: AuthUser }>(
    "/auth/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    },
  );
  return result.user;
}

export async function logout(): Promise<void> {
  // Best-effort: revoke server-side (reads the refresh_token cookie) so it
  // can't be replayed later, and clears the cookies in the response. Still
  // resolve even if this fails (offline, etc.) -- the caller clears local
  // React state regardless, so logging out always works from the user's POV.
  try {
    await fetchJson("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  } catch {
    // ignore
  }
}

export function getMe(): Promise<AuthUser> {
  return fetchJson("/auth/me");
}

export function forgotPassword(email: string): Promise<void> {
  return fetchJson("/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(token: string, password: string): Promise<void> {
  return fetchJson("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password }),
  });
}

export function setUserPassword(userId: string, password: string): Promise<User> {
  return fetchJson(`/users/${userId}/password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
}

// --- Appointments ---------------------------------------------------------

export const APPOINTMENT_TYPES = [
  "biometrics",
  "interview",
  "rfe_deadline",
  "court_hearing",
  "consultation",
  "other",
] as const;

export type Appointment = {
  id: string;
  case_id: string;
  case_number: string | null;
  appointment_type: (typeof APPOINTMENT_TYPES)[number];
  scheduled_at: string;
  location: string | null;
  notes: string | null;
  reminder_sent: boolean;
  created_at: string;
};

export function getAppointments(filters?: { caseId?: string; upcomingOnly?: boolean }): Promise<Appointment[]> {
  const params = new URLSearchParams();
  if (filters?.caseId) params.set("case_id", filters.caseId);
  if (filters?.upcomingOnly) params.set("upcoming_only", "true");
  const qs = params.toString();
  return fetchJson(`/appointments${qs ? `?${qs}` : ""}`);
}

export function getCaseAppointments(caseId: string): Promise<Appointment[]> {
  return fetchJson(`/cases/${caseId}/appointments`);
}

export function createAppointment(
  caseId: string,
  payload: {
    appointment_type: string;
    scheduled_at: string;
    location?: string;
    notes?: string;
  },
): Promise<Appointment> {
  return fetchJson(`/cases/${caseId}/appointments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteAppointment(id: string): Promise<void> {
  return fetchJson(`/appointments/${id}`, { method: "DELETE" });
}

// --- Billing ----------------------------------------------------------------

export const INVOICE_STATUSES = ["draft", "sent", "partially_paid", "paid", "overdue", "cancelled"] as const;
export const PAYMENT_METHODS = ["cash", "card", "bank_transfer", "check", "other"] as const;

export type Payment = {
  id: string;
  invoice_id: string;
  amount: number;
  method: (typeof PAYMENT_METHODS)[number];
  paid_at: string;
  notes: string | null;
};

export type Invoice = {
  id: string;
  case_id: string;
  case_number: string | null;
  invoice_number: string;
  description: string | null;
  amount: number;
  amount_paid: number;
  status: (typeof INVOICE_STATUSES)[number];
  due_date: string | null;
  paid_at: string | null;
  created_at: string;
};

export type InvoiceDetail = Invoice & { payments: Payment[] };

export function getInvoices(caseId?: string): Promise<Invoice[]> {
  const qs = caseId ? `?case_id=${caseId}` : "";
  return fetchJson(`/invoices${qs}`);
}

export function getInvoice(id: string): Promise<InvoiceDetail> {
  return fetchJson(`/invoices/${id}`);
}

export function createInvoice(
  caseId: string,
  payload: { description?: string; amount: number; due_date?: string },
): Promise<Invoice> {
  return fetchJson(`/cases/${caseId}/invoices`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateInvoice(
  id: string,
  payload: Partial<{ description: string; amount: number; due_date: string | null; status: string }>,
): Promise<Invoice> {
  return fetchJson(`/invoices/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteInvoice(id: string): Promise<void> {
  return fetchJson(`/invoices/${id}`, { method: "DELETE" });
}

export function addPayment(
  invoiceId: string,
  payload: { amount: number; method: string; paid_at?: string; notes?: string },
): Promise<InvoiceDetail> {
  return fetchJson(`/invoices/${invoiceId}/payments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deletePayment(invoiceId: string, paymentId: string): Promise<InvoiceDetail> {
  return fetchJson(`/invoices/${invoiceId}/payments/${paymentId}`, { method: "DELETE" });
}

// --- Stats ------------------------------------------------------------------

export type CountByKey = { key: string; count: number };

export type StatsOverview = {
  total_clients: number;
  total_cases: number;
  open_cases: number;
  cases_by_status: CountByKey[];
  cases_by_type: CountByKey[];
  total_documents: number;
  upcoming_appointments_7d: number;
  overdue_appointments: number;
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
  overdue_invoice_count: number;
  cases_created_last_30d: CountByKey[];
};

export type RevenuePoint = { month: string; invoiced: number; collected: number };

export function getStatsOverview(): Promise<StatsOverview> {
  return fetchJson("/stats/overview");
}

export function getRevenueByMonth(months = 6): Promise<RevenuePoint[]> {
  return fetchJson(`/stats/revenue?months=${months}`);
}

// --- RFEs (Requests for Evidence) --------------------------------------

export const RFE_STATUSES = ["open", "responded", "closed"] as const;
export const RFE_EVIDENCE_STATUSES = ["pending", "gathered", "submitted"] as const;

export type RFE = {
  id: string;
  case_id: string;
  case_number: string | null;
  status: (typeof RFE_STATUSES)[number];
  received_date: string;
  response_due_date: string | null;
  notes: string | null;
  created_at: string;
  evidence_count: number;
  evidence_gathered_count: number;
};

export type RFEEvidenceItem = {
  id: string;
  description: string;
  status: (typeof RFE_EVIDENCE_STATUSES)[number];
  order: number;
};

export type RFEDetail = RFE & {
  raw_text: string | null;
  evidence_items: RFEEvidenceItem[];
};

export function getCaseRfes(caseId: string): Promise<RFE[]> {
  return fetchJson(`/cases/${caseId}/rfes`);
}

export function createRfe(
  caseId: string,
  payload: { received_date: string; response_due_date?: string; raw_text?: string; notes?: string },
): Promise<RFE> {
  return fetchJson(`/cases/${caseId}/rfes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getRfe(id: string): Promise<RFEDetail> {
  return fetchJson(`/rfes/${id}`);
}

export function updateRfe(
  id: string,
  payload: Partial<{ status: string; response_due_date: string | null; raw_text: string; notes: string }>,
): Promise<RFEDetail> {
  return fetchJson(`/rfes/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteRfe(id: string): Promise<void> {
  return fetchJson(`/rfes/${id}`, { method: "DELETE" });
}

export function addRfeEvidenceItem(rfeId: string, description: string): Promise<RFEEvidenceItem> {
  return fetchJson(`/rfes/${rfeId}/evidence`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
}

export function updateRfeEvidenceItem(
  rfeId: string,
  itemId: string,
  payload: Partial<{ description: string; status: string }>,
): Promise<RFEEvidenceItem> {
  return fetchJson(`/rfes/${rfeId}/evidence/${itemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function deleteRfeEvidenceItem(rfeId: string, itemId: string): Promise<void> {
  return fetchJson(`/rfes/${rfeId}/evidence/${itemId}`, { method: "DELETE" });
}

export function getRfeAiStatus(): Promise<{ configured: boolean }> {
  return fetchJson("/rfes/ai-status");
}

export type RFESuggestion = { description: string; reason: string };

export function suggestRfeEvidence(rfeId: string, rawText?: string): Promise<{ suggestions: RFESuggestion[] }> {
  return fetchJson(`/rfes/${rfeId}/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: rawText }),
  });
}

// --- "Mi día" preparer dashboard -----------------------------------------

export type MyDayAppointment = {
  id: string;
  case_id: string;
  case_number: string;
  appointment_type: string;
  scheduled_at: string;
};

export type MyDayChecklistItem = {
  id: string;
  case_id: string;
  case_number: string;
  label: string;
  due_date: string | null;
  priority: string;
  overdue: boolean;
};

export type MyDayRFE = {
  id: string;
  case_id: string;
  case_number: string;
  status: string;
  response_due_date: string | null;
};

export type MyDayCase = { id: string; case_number: string; status: string };

export type MyDay = {
  assigned_case_count: number;
  appointments_today: MyDayAppointment[];
  checklist_due: MyDayChecklistItem[];
  open_rfes: MyDayRFE[];
  cases_ready_for_review: MyDayCase[];
};

export function getMyDay(): Promise<MyDay> {
  return fetchJson("/dashboard/me");
}

// --- Gap analysis -----------------------------------------------------------

export type GapItem = {
  severity: "high" | "medium" | "low";
  code: string;
  message: string;
  client_id: string | null;
};

export type RequirementCategory = {
  title: string;
  items: string[];
};

export type FormRequirements = {
  form_code: string;
  source_url: string;
  source_label: string;
  verified_on: string;
  categories: RequirementCategory[];
};

export type GapAnalysis = {
  case_id: string;
  checked_at: string;
  gaps: GapItem[];
  reference_checklist: FormRequirements[];
};

export function getCaseGapAnalysis(caseId: string): Promise<GapAnalysis> {
  return fetchJson(`/cases/${caseId}/gap-analysis`);
}

export function getFormRequirements(code: string): Promise<FormRequirements> {
  return fetchJson(`/form-templates/${code}/requirements`);
}

// --- Case timeline ------------------------------------------------------

export const TIMELINE_STEP_KEYS = [
  "intake",
  "contract",
  "forms",
  "evidence",
  "prepared",
  "filed",
  "biometrics",
  "interview",
  "decision",
] as const;

export type TimelineStep = {
  key: (typeof TIMELINE_STEP_KEYS)[number];
  status: "done" | "current" | "pending";
};

export type CaseTimeline = {
  case_number: string;
  steps: TimelineStep[];
};

export function getCaseTimeline(caseId: string): Promise<CaseTimeline> {
  return fetchJson(`/cases/${caseId}/timeline`);
}

export function getPublicCaseTimeline(token: string): Promise<CaseTimeline> {
  return fetchJson(`/public/forms/${token}/timeline`);
}

// --- Client portal (a client logging in to see their own cases/forms) ---
// Uses the same cookie names as the staff session but a distinct token
// "type" the backend checks (see get_current_client) -- exempted from the
// staff refresh/401-event logic above via _AUTH_EXEMPT_PREFIXES.

export type AuthenticatedClient = {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
};

export type ClientCaseFormSummary = {
  id: string;
  form_code: string;
  form_name: string;
  access_token: string;
  status: string;
};

export type ClientCaseSummary = {
  id: string;
  case_number: string;
  case_type: string;
  status: string;
  my_role: string;
  forms: ClientCaseFormSummary[];
};

export async function clientLogin(email: string, password: string): Promise<AuthenticatedClient> {
  const result = await fetchJson<{ access_token: string; refresh_token: string; client: AuthenticatedClient }>(
    "/client-auth/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    },
  );
  return result.client;
}

export async function clientLogout(): Promise<void> {
  try {
    await fetchJson("/client-auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
  } catch {
    // best-effort, same reasoning as the staff logout() above
  }
}

export function getClientMe(): Promise<AuthenticatedClient> {
  return fetchJson("/client-auth/me");
}

export function getMyCases(): Promise<ClientCaseSummary[]> {
  return fetchJson("/client-auth/me/cases");
}

// Staff-only: sets (or resets) a client's portal password. Requires a valid
// staff session (regular fetchJson/authFetch path, not the client-exempt
// one above) -- see POST /client-auth/register's CurrentUser dependency.
export function activateClientPortal(email: string, password: string): Promise<AuthenticatedClient> {
  return fetchJson("/client-auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function clientForgotPassword(email: string): Promise<void> {
  return fetchJson("/client-auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export function clientResetPassword(token: string, password: string): Promise<void> {
  return fetchJson("/client-auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password }),
  });
}
