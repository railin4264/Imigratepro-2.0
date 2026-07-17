const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

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
  nationality: string | null;
  ssn: string | null;
  sex: (typeof SEX_OPTIONS)[number] | null;
  marital_status: (typeof MARITAL_STATUS_OPTIONS)[number] | null;
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
};

export const USER_ROLES = ["admin", "attorney", "paralegal"] as const;

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
  status: string;
  created_at: string;
  access_token: string;
  client_link_enabled: boolean;
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

export type GeneratedFormDetail = GeneratedForm & {
  data: Record<string, string>;
  form_code: string;
  ai_review: AiReview | null;
  ai_reviewed_at: string | null;
};

export type PublicFormView = {
  form_code: string;
  form_name: string;
  case_number: string;
  fields: FieldSchemaEntry[];
  data: Record<string, string>;
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

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
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

export function getCases(): Promise<Case[]> {
  return fetchJson("/cases");
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

export function downloadUrl(generatedFormId: string): string {
  return `${API_URL}/forms/${generatedFormId}/download`;
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

export type NotificationType = "case_assigned" | "stage_advanced" | "document_uploaded" | "ai_review_flagged";

export type Notification = {
  id: string;
  type: NotificationType;
  message: string;
  case_id: string | null;
  case_number: string | null;
  created_at: string;
};

export function getNotifications(): Promise<Notification[]> {
  return fetchJson("/notifications");
}

export function clientLinkUrl(accessToken: string): string {
  const base = typeof window !== "undefined" ? window.location.origin : "";
  return `${base}/client/forms/${accessToken}`;
}

export function getPublicForm(token: string): Promise<PublicFormView> {
  return fetchJson(`/public/forms/${token}`);
}

export function updatePublicForm(token: string, data: Record<string, string>): Promise<PublicFormView> {
  return fetchJson(`/public/forms/${token}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  });
}

export function reviewGeneratedForm(id: string): Promise<GeneratedFormDetail> {
  return fetchJson(`/forms/${id}/review`, { method: "POST" });
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
