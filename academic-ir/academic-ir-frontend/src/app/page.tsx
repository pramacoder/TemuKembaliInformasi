"use client";

import { FilterSidebar } from "@/components/filter-sidebar";
import { ResultCard } from "@/components/result-card";
import { AppHeader, SearchBar } from "@/components/search-bar";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import {
  type DocumentType,
  type RetrievalMode,
  type AggregationStrategy,
  type SearchResult,
  searchDocuments,
} from "@/lib/api";
import { AlertCircle, BookOpen, SearchX } from "lucide-react";
import { useState } from "react";

const RESULTS_PER_PAGE = 5;

function ResultSkeleton() {
  return (
    <div className="space-y-3 p-4 border rounded-lg">
      <div className="flex gap-3">
        <Skeleton className="h-6 w-6 rounded-full shrink-0" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <Skeleton className="h-10 w-10 shrink-0" />
      </div>
      <div className="ml-9 space-y-2">
        <Skeleton className="h-3 w-1/3" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searchedQuery, setSearchedQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Filters & IR Model Configuration
  const [selectedType, setSelectedType] = useState<DocumentType | null>(null);
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [language, setLanguage] = useState("");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("tfidf");
  const [aggregationStrategy, setAggregationStrategy] = useState<AggregationStrategy>("max+2nd");

  const executeSearch = async (
    rawQuery?: unknown,
    opts: {
      type?: DocumentType | null;
      yFrom?: string;
      yTo?: string;
      lang?: string;
      mode?: RetrievalMode;
      strategy?: AggregationStrategy;
    } = {}
  ) => {
    const text = typeof rawQuery === "string" ? rawQuery : query;
    const searchQuery = (text || "").trim();
    if (!searchQuery) return;

    setIsLoading(true);
    setError(null);
    setCurrentPage(1);

    try {
      const data = await searchDocuments(
        searchQuery,
        {
          documentType: opts.type !== undefined ? opts.type : selectedType,
          yearFrom: opts.yFrom !== undefined ? opts.yFrom : yearFrom,
          yearTo: opts.yTo !== undefined ? opts.yTo : yearTo,
          language: opts.lang !== undefined ? opts.lang : language,
          retrievalMode: opts.mode !== undefined ? opts.mode : retrievalMode,
          aggregationStrategy: opts.strategy !== undefined ? opts.strategy : aggregationStrategy,
        },
        20
      );
      setResults(data.results);
      setSearchedQuery(data.query);
      setHasSearched(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Search failed. Is the API server running on port 8000?"
      );
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (q?: unknown) => {
    const targetQuery = typeof q === "string" ? q : query;
    executeSearch(targetQuery);
  };

  const handleRetrievalModeChange = (mode: RetrievalMode) => {
    setRetrievalMode(mode);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, { mode });
    }
  };

  const handleAggregationStrategyChange = (strategy: AggregationStrategy) => {
    setAggregationStrategy(strategy);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, { strategy });
    }
  };

  const handleTypeChange = (type: DocumentType | null) => {
    setSelectedType(type);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, { type });
    }
  };

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, { lang });
    }
  };

  const handleReset = () => {
    setSelectedType(null);
    setYearFrom("");
    setYearTo("");
    setLanguage("");
    setRetrievalMode("tfidf");
    setAggregationStrategy("max+2nd");
    setCurrentPage(1);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, {
        type: null,
        yFrom: "",
        yTo: "",
        lang: "",
        mode: "tfidf",
        strategy: "max+2nd",
      });
    }
  };

  const totalPages = Math.max(1, Math.ceil(results.length / RESULTS_PER_PAGE));
  const paginatedResults = results.slice(
    (currentPage - 1) * RESULTS_PER_PAGE,
    currentPage * RESULTS_PER_PAGE
  );

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />

      {/* Hero search */}
      <div className="bg-gradient-to-b from-muted/50 to-background border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex flex-col items-center gap-4">
            <div className="text-center space-y-1.5">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
                Sistem Temu Kembali Informasi Akademik
              </h1>
              <p className="text-sm text-muted-foreground max-w-lg">
                Pencarian multi-sumber: Bahan Ajar OCW, Artikel Riset Open Access, dan Tugas Akhir
              </p>
            </div>

            <div className="w-full max-w-2xl">
              <SearchBar
                query={query}
                onChange={setQuery}
                onSearch={handleSearch}
                isLoading={isLoading}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex gap-8">
            <div className="w-60 shrink-0 space-y-4">
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-px w-full" />
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
            <div className="flex-1 space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <ResultSkeleton key={i} />
              ))}
            </div>
          </div>
        ) : hasSearched ? (
          <div className="flex gap-8">
            {/* Sidebar */}
            <FilterSidebar
              selectedType={selectedType}
              yearFrom={yearFrom}
              yearTo={yearTo}
              language={language}
              retrievalMode={retrievalMode}
              aggregationStrategy={aggregationStrategy}
              onTypeChange={handleTypeChange}
              onYearFromChange={(v) => {
                setYearFrom(v);
                setCurrentPage(1);
              }}
              onYearToChange={(v) => {
                setYearTo(v);
                setCurrentPage(1);
              }}
              onLanguageChange={handleLanguageChange}
              onRetrievalModeChange={handleRetrievalModeChange}
              onAggregationStrategyChange={handleAggregationStrategyChange}
              onReset={handleReset}
              totalResults={results.length}
            />

            {/* Results */}
            <div className="flex-1 min-w-0 space-y-4">
              {error ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <AlertCircle className="h-10 w-10 text-destructive mb-3" />
                  <p className="text-base font-medium text-destructive">Search Error</p>
                  <p className="text-sm text-muted-foreground mt-1 max-w-sm">{error}</p>
                </div>
              ) : paginatedResults.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <SearchX className="h-10 w-10 text-muted-foreground mb-3" />
                  <p className="text-base font-medium">Tidak ada dokumen yang ditemukan</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Coba kata kunci lain atau sesuaikan filter pencarian
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between text-xs text-muted-foreground pb-1">
                    <span>
                      Menampilkan hasil untuk: <strong>&ldquo;{searchedQuery}&rdquo;</strong>
                    </span>
                    <span>
                      Model: <strong>{retrievalMode.toUpperCase()}</strong> | Agregasi:{" "}
                      <strong>{aggregationStrategy}</strong>
                    </span>
                  </div>

                  {paginatedResults.map((result) => (
                    <ResultCard key={result.id} result={result} />
                  ))}

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="pt-4">
                      <Pagination>
                        <PaginationContent>
                          <PaginationItem>
                            <PaginationPrevious
                              href="#"
                              onClick={(e) => {
                                e.preventDefault();
                                setCurrentPage((p) => Math.max(1, p - 1));
                              }}
                              aria-disabled={currentPage === 1}
                              className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
                            />
                          </PaginationItem>
                          {Array.from({ length: totalPages }).map((_, i) => {
                            const page = i + 1;
                            if (
                              page === 1 ||
                              page === totalPages ||
                              Math.abs(page - currentPage) <= 1
                            ) {
                              return (
                                <PaginationItem key={page}>
                                  <PaginationLink
                                    href="#"
                                    isActive={currentPage === page}
                                    onClick={(e) => {
                                      e.preventDefault();
                                      setCurrentPage(page);
                                    }}
                                  >
                                    {page}
                                  </PaginationLink>
                                </PaginationItem>
                              );
                            }
                            if (Math.abs(page - currentPage) === 2) {
                              return (
                                <PaginationItem key={page}>
                                  <PaginationEllipsis />
                                </PaginationItem>
                              );
                            }
                            return null;
                          })}
                          <PaginationItem>
                            <PaginationNext
                              href="#"
                              onClick={(e) => {
                                e.preventDefault();
                                setCurrentPage((p) => Math.min(totalPages, p + 1));
                              }}
                              aria-disabled={currentPage === totalPages}
                              className={
                                currentPage === totalPages ? "pointer-events-none opacity-50" : ""
                              }
                            />
                          </PaginationItem>
                        </PaginationContent>
                      </Pagination>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ) : (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <BookOpen className="h-12 w-12 text-muted-foreground/40 mb-4" />
            <h2 className="text-lg font-semibold text-muted-foreground">Mulai Pencarian Dokumen</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-xs">
              Ketikkan kata kunci untuk mencari di koleksi bahan kuliah, artikel penelitian, dan skripsi
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
