export type DocumentType = "journal" | "conference" | "thesis" | "book" | "preprint";

export interface SearchResult {
  id: string;
  title: string;
  authors: string[];
  year: number;
  source: string;
  documentType: DocumentType;
  relevanceScore: number;
  snippet: string;
  url?: string;
  doi?: string;
  keywords: string[];
}

export interface SearchFilters {
  documentTypes: DocumentType[];
  yearFrom: number | null;
  yearTo: number | null;
  minRelevance: number;
}

export const MOCK_RESULTS: SearchResult[] = [
  {
    id: "1",
    title: "BM25 and Beyond: A Comprehensive Survey of Term-Based Information Retrieval",
    authors: ["Ahmad Fauzi", "Budi Santoso", "Chen Wei"],
    year: 2023,
    source: "Journal of Information Science",
    documentType: "journal",
    relevanceScore: 0.97,
    snippet:
      "This paper presents a comprehensive survey of term-based retrieval models, focusing on BM25 and its variants. We analyze the strengths and limitations of probabilistic models and propose extensions that improve performance on domain-specific corpora...",
    doi: "10.1177/01655515231234567",
    keywords: ["BM25", "information retrieval", "term weighting", "probabilistic models"],
  },
  {
    id: "2",
    title: "Dense Retrieval with Pretrained Language Models for Academic Search",
    authors: ["Sarah Johnson", "Mohammad Al-Rashid"],
    year: 2024,
    source: "ACM SIGIR Conference on Research and Development in Information Retrieval",
    documentType: "conference",
    relevanceScore: 0.93,
    snippet:
      "We present a dense retrieval approach leveraging transformer-based language models for academic document search. Our method outperforms sparse retrieval baselines by 12% on the BEIR benchmark across multiple academic domains...",
    doi: "10.1145/3626772.3657789",
    keywords: ["dense retrieval", "BERT", "semantic search", "neural IR"],
  },
  {
    id: "3",
    title: "TF-IDF Revisited: Adaptive Term Frequency Normalization for Scientific Literature",
    authors: ["Dewi Rahayu"],
    year: 2022,
    source: "Universitas Indonesia — Master Thesis",
    documentType: "thesis",
    relevanceScore: 0.88,
    snippet:
      "This thesis investigates adaptive normalization strategies for TF-IDF in the context of scientific literature retrieval. We propose a corpus-aware normalization factor that accounts for document length distribution in academic collections...",
    keywords: ["TF-IDF", "normalization", "scientific literature", "corpus analysis"],
  },
  {
    id: "4",
    title: "Hybrid Retrieval Systems: Combining Sparse and Dense Methods",
    authors: ["James Park", "Lena Müller", "Yuki Tanaka"],
    year: 2024,
    source: "arXiv preprint",
    documentType: "preprint",
    relevanceScore: 0.85,
    snippet:
      "Hybrid retrieval systems that combine sparse (BM25) and dense (bi-encoder) methods have shown consistent improvements over individual approaches. In this work, we study optimal fusion strategies and their sensitivity to domain shift...",
    keywords: ["hybrid retrieval", "BM25", "bi-encoder", "reciprocal rank fusion"],
  },
  {
    id: "5",
    title: "Introduction to Modern Information Retrieval",
    authors: ["G. Salton", "M. J. McGill"],
    year: 2021,
    source: "Academic Press — 4th Edition",
    documentType: "book",
    relevanceScore: 0.79,
    snippet:
      "The fourth edition of this classic textbook provides updated coverage of information retrieval fundamentals, including vector space models, probabilistic retrieval, and neural approaches. Ideal for graduate students and practitioners...",
    keywords: ["information retrieval", "vector space model", "textbook"],
  },
  {
    id: "6",
    title: "Evaluation Metrics for Information Retrieval: A Practitioner's Guide",
    authors: ["Anisa Putri", "Roberto García"],
    year: 2023,
    source: "Information Processing & Management",
    documentType: "journal",
    relevanceScore: 0.74,
    snippet:
      "We provide a practitioner-oriented guide to evaluation metrics in information retrieval, covering precision, recall, MAP, NDCG, and MRR. Special attention is given to statistical significance testing and metric sensitivity to annotation quality...",
    doi: "10.1016/j.ipm.2023.103456",
    keywords: ["evaluation", "MAP", "NDCG", "precision", "recall"],
  },
];

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  journal: "Journal Article",
  conference: "Conference Paper",
  thesis: "Thesis / Dissertation",
  book: "Book / Textbook",
  preprint: "Preprint",
};

export const DOCUMENT_TYPE_COLORS: Record<DocumentType, string> = {
  journal: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  conference: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  thesis: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  book: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  preprint: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
};
