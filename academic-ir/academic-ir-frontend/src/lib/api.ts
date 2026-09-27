// ─── Types matching the FastAPI backend response ──────────────────────────────

export type DocumentType = "MATERIAL" | "RESEARCH" | "THESIS";
export type SourceType = "OCW_UI" | "CORE" | "DOAJ" | "REPOSITORY";

export interface SearchResult {
  id: string;
  document_id: string;
  document_type: DocumentType;
  title: string;
  authors: string[];
  year: number | null;
  source: string;
  institution: string | null;
  course: string | null;
  language: string | null;
  relevance_score: number;
  rank: number;
  snippet: string;
  page: number | null;
  source_url: string | null;
  doi: string | null;
  keywords: string[];
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

export interface SearchFilters {
  documentType: DocumentType | null;
  yearFrom: string;
  yearTo: string;
  language: string;
}

// ─── Labels & styling ─────────────────────────────────────────────────────────

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  MATERIAL: "Course Material",
  RESEARCH: "Research Paper",
  THESIS: "Thesis / Dissertation",
};

export const DOCUMENT_TYPE_COLORS: Record<DocumentType, string> = {
  MATERIAL: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  RESEARCH: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  THESIS: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
};

// ─── API client ───────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function searchDocuments(
  query: string,
  filters: SearchFilters,
  topK = 20
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  if (filters.documentType) params.set("document_type", filters.documentType);
  if (filters.yearFrom) params.set("year_from", filters.yearFrom);
  if (filters.yearTo) params.set("year_to", filters.yearTo);
  if (filters.language) params.set("language", filters.language);

  const res = await fetch(`${API_BASE}/api/search?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Search failed");
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`);
  return res.json();
}
