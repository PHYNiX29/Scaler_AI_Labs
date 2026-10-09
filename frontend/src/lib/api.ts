import { Answers, AnswerValue, Form, FormResponse, FormStats, NextStep, Question } from "@/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

/** Uploaded media is stored as a path on the API server; external images are already absolute. */
export const mediaSrc = (url: string) => (url.startsWith("/") ? API_BASE + url : url);

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const isJson = !(options.body instanceof FormData);
  const response = await fetch(API_BASE + endpoint, {
    ...options,
    headers: isJson ? { "Content-Type": "application/json", ...options.headers } : options.headers,
  });
  if (!response.ok) {
    // FastAPI puts the reason in `detail`: a string, or an object/list for validation errors
    const detail = (await response.json().catch(() => null))?.detail;
    throw new Error(typeof detail === "string" ? detail : detail?.message || `Request failed (${response.status})`);
  }
  return response.json();
}

const json = (method: string, body?: unknown): RequestInit => ({ method, body: JSON.stringify(body ?? {}) });

export const api = {
  // Forms
  getForms: () => request<{ forms: Form[] }>("/api/forms"),
  getForm: (id: string) => request<{ form: Form }>(`/api/forms/${id}`),
  createForm: (title: string) => request<{ form: Form }>("/api/forms", json("POST", { title })),
  updateForm: (id: string, patch: Partial<Pick<Form, "title" | "description" | "theme_settings">>) =>
    request<{ form: Form }>(`/api/forms/${id}`, json("PUT", patch)),
  deleteForm: (id: string) => request(`/api/forms/${id}`, { method: "DELETE" }),
  duplicateForm: (id: string) => request<{ form: Form }>(`/api/forms/${id}/duplicate`, json("POST")),
  setPublished: (id: string, published: boolean) =>
    request<{ status: Form["status"]; slug: string }>(
      `/api/forms/${id}/publish`,
      json("POST", { status: published ? "published" : "draft" })
    ),

  // Questions
  addQuestion: (formId: string, question: Partial<Question>) =>
    request<{ question: Question }>(`/api/forms/${formId}/questions`, json("POST", question)),
  updateQuestion: (formId: string, question: Question) => {
    const { title, description, required, question_type, properties, media, logic_jumps } = question;
    return request<{ question: Question }>(
      `/api/forms/${formId}/questions/${question.id}`,
      json("PUT", { title, description, required, question_type, properties, media, logic_jumps })
    );
  },
  deleteQuestion: (formId: string, questionId: string) =>
    request(`/api/forms/${formId}/questions/${questionId}`, { method: "DELETE" }),
  reorderQuestions: (formId: string, questionIds: string[]) =>
    request<{ questions: Question[] }>(`/api/forms/${formId}/questions/reorder`, json("PUT", { question_ids: questionIds })),

  // Public respondent flow (no auth)
  getPublicForm: (slug: string) => request<{ form: Form }>(`/api/public/forms/${slug}`),
  startSession: (slug: string) => request<{ session_id: string }>(`/api/public/forms/${slug}/start`, json("POST")),
  validateStep: (slug: string, questionId: string, answer: AnswerValue) =>
    request<{ valid: boolean; error?: string } & Partial<NextStep>>(
      `/api/public/forms/${slug}/validate-step`,
      json("POST", { question_id: questionId, answer: answer ?? null })
    ),
  submitResponse: (slug: string, body: { session_id?: string; answers: Answers; time_taken_seconds: number }) =>
    request<{ response_id: string }>(`/api/public/forms/${slug}/submit`, json("POST", body)),

  // Results
  getResponses: (formId: string) =>
    request<{ total: number; responses: FormResponse[] }>(`/api/forms/${formId}/responses?per_page=100`),
  getResponse: (formId: string, responseId: string) =>
    request<{ response: FormResponse }>(`/api/forms/${formId}/responses/${responseId}`),
  deleteResponse: (formId: string, responseId: string) =>
    request(`/api/forms/${formId}/responses/${responseId}`, { method: "DELETE" }),
  getStats: (formId: string) => request<{ stats: FormStats }>(`/api/forms/${formId}/stats`),
  exportCsvUrl: (formId: string) => `${API_BASE}/api/forms/${formId}/export/csv`,

  uploadMedia: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<{ url: string; media_type: "image" | "video" }>("/api/upload", { method: "POST", body });
  },
};
