// ─── Types matching the FastAPI backend response ──────────────────────────────

export type DocumentType = "MATERIAL" | "RESEARCH" | "THESIS";
export type SourceType = "OCW_UI" | "CORE" | "DOAJ" | "REPOSITORY";
export type RetrievalMode = "tfidf" | "bm25";
export type AggregationStrategy = "max+2nd" | "max" | "topN_avg";
export type TolerantMode = "auto" | "always" | "off";

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
  best_page_start?: number | null;
  best_page_end?: number | null;
  chunk_count?: number | null;
  aggregation_strategy?: string;
  source_url: string | null;
  doi: string | null;
  keywords: string[];
}

export interface TolerantCorrection {
  source: string;
  target: string;
  type: string;
  confidence: number;
  note?: string;
}

export interface TolerantMetadata {
  applied: boolean;
  mode: TolerantMode;
  original_query: string;
  effective_query: string;
  did_you_mean?: string | null;
  corrections: TolerantCorrection[];
  expanded_terms: string[];
  fallback_triggered: boolean;
  confidence: number;
  explanation?: string;
}

export interface SearchResponse {
  query: string;
  retrieval_mode: string;
  aggregation_strategy: string;
  total: number;
  results: SearchResult[];
  tolerant_metadata?: TolerantMetadata | null;
}

export interface SuggestionResponse {
  query: string;
  did_you_mean?: string | null;
  suggestions: string[];
  corrections: TolerantCorrection[];
  expanded_terms: string[];
  confidence: number;
}

export interface SearchFilters {
  documentType: DocumentType | null;
  yearFrom: string;
  yearTo: string;
  language: string;
  retrievalMode?: RetrievalMode;
  aggregationStrategy?: AggregationStrategy;
  tolerantMode?: TolerantMode;
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
  if (filters.retrievalMode) params.set("retrieval_mode", filters.retrievalMode);
  if (filters.aggregationStrategy) params.set("aggregation_strategy", filters.aggregationStrategy);
  if (filters.tolerantMode) params.set("tolerant_mode", filters.tolerantMode);

  const res = await fetch(`${API_BASE}/api/search?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Search failed");
  }
  return res.json();
}

export async function fetchSuggestions(
  query: string,
  limit = 5
): Promise<SuggestionResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  const res = await fetch(`${API_BASE}/api/tolerant/suggest?${params.toString()}`);
  if (!res.ok) {
    throw new Error("Failed to fetch suggestions");
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

export async function fetchProvenance() {
  const res = await fetch(`${API_BASE}/api/provenance`);
  return res.json();
}
