"use client";

import { useState } from "react";
import { FilterSidebar } from "@/components/filter-sidebar";
import { ResultCard } from "@/components/result-card";
import { AppHeader, SearchBar } from "@/components/search-bar";
import { TolerantBanner } from "@/components/tolerant-banner";
import { HeroSection } from "@/components/landing/hero-section";
import { ProvenanceBar } from "@/components/landing/provenance-bar";
import { CategoryGrid } from "@/components/landing/category-grid";
import { FeaturedCarousel } from "@/components/landing/featured-carousel";
import { AcademicBookshelf } from "@/components/landing/academic-bookshelf";
import { FeatureHighlights } from "@/components/landing/feature-highlights";
import { Button } from "@/components/ui/button";
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
  type TolerantMode,
  type TolerantMetadata,
  type SearchResult,
  searchDocuments,
} from "@/lib/api";
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  LayoutGrid,
  List,
  SearchX,
  Sparkles,
} from "lucide-react";

const RESULTS_PER_PAGE = 6;

function ResultSkeleton() {
  return (
    <div className="space-y-3 p-4 border rounded-xl bg-card">
      <div className="flex gap-4">
        <Skeleton className="h-28 w-20 rounded-md shrink-0 hidden sm:block" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-14 w-full" />
          <div className="flex gap-2 pt-2">
            <Skeleton className="h-7 w-28" />
            <Skeleton className="h-7 w-28" />
          </div>
        </div>
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
  const [tolerantMetadata, setTolerantMetadata] = useState<TolerantMetadata | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  // Filters & IR Model Configuration
  const [selectedType, setSelectedType] = useState<DocumentType | null>(null);
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [language, setLanguage] = useState("");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("bm25");
  const [aggregationStrategy, setAggregationStrategy] = useState<AggregationStrategy>("max+2nd");
  const [tolerantMode, setTolerantMode] = useState<TolerantMode>("auto");

  const executeSearch = async (
    rawQuery?: unknown,
    opts: {
      type?: DocumentType | null;
      yFrom?: string;
      yTo?: string;
      lang?: string;
      mode?: RetrievalMode;
      strategy?: AggregationStrategy;
      tolMode?: TolerantMode;
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
          tolerantMode: opts.tolMode !== undefined ? opts.tolMode : tolerantMode,
        },
        30
      );
      setResults(data.results);
      setSearchedQuery(data.query);
      setTolerantMetadata(data.tolerant_metadata || null);
      setHasSearched(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Search failed. Is the API server running on port 8000?"
      );
      setResults([]);
      setTolerantMetadata(null);
      setHasSearched(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (q?: unknown, overrideMode?: TolerantMode) => {
    const targetQuery = typeof q === "string" ? q : query;
    executeSearch(targetQuery, overrideMode ? { tolMode: overrideMode } : {});
  };

  const handleLandingSearch = (searchQuery: string, docType?: DocumentType | null) => {
    setQuery(searchQuery);
    setSelectedType(docType ?? null);
    executeSearch(searchQuery, { type: docType ?? null });
  };

  const handleSelectCategory = (catQuery: string) => {
    setQuery(catQuery);
    executeSearch(catQuery);
  };

  const handleGoHome = () => {
    setHasSearched(false);
    setQuery("");
    setResults([]);
    setError(null);
    setTolerantMetadata(null);
  };

  const handleTolerantModeChange = (mode: TolerantMode) => {
    setTolerantMode(mode);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, { tolMode: mode });
    }
  };

  const handleSearchOriginal = (origQuery: string) => {
    setTolerantMode("off");
    executeSearch(origQuery, { tolMode: "off" });
  };

  const handleApplySuggested = (suggested: string) => {
    setQuery(suggested);
    executeSearch(suggested);
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
    setRetrievalMode("bm25");
    setAggregationStrategy("max+2nd");
    setTolerantMode("auto");
    setTolerantMetadata(null);
    setCurrentPage(1);
    if (hasSearched && searchedQuery) {
      executeSearch(searchedQuery, {
        type: null,
        yFrom: "",
        yTo: "",
        lang: "",
        mode: "bm25",
        strategy: "max+2nd",
        tolMode: "auto",
      });
    }
  };

  const totalPages = Math.max(1, Math.ceil(results.length / RESULTS_PER_PAGE));
  const paginatedResults = results.slice(
    (currentPage - 1) * RESULTS_PER_PAGE,
    currentPage * RESULTS_PER_PAGE
  );

  return (
    <div className="min-h-screen bg-background flex flex-col justify-between">
      <div>
        <AppHeader onGoHome={handleGoHome} onSelectCategory={() => {
          if (hasSearched) handleGoHome();
          const el = document.getElementById("category-section");
          el?.scrollIntoView({ behavior: "smooth" });
        }} />

        {/* ─── WHEN USER HAS NOT SEARCHED: SHOW FULL MODERN LANDING PAGE ─── */}
        {!hasSearched ? (
          <div>
            {/* 1. Hero Section (Pinterest Ref 1, 2, 3) */}
            <HeroSection
              query={query}
              onQueryChange={setQuery}
              onSearch={handleLandingSearch}
            />

            {/* 2. Provenance Repositories Strip (Pinterest Ref 2) */}
            <ProvenanceBar />

            {/* 3. Explore Categories Grid (Pinterest Ref 2) */}
            <div id="category-section">
              <CategoryGrid onSelectCategory={handleSelectCategory} />
            </div>

            {/* 4. "Deciding What to Read Next?" Featured Carousel (Pinterest Ref 2 & 4) */}
            <FeaturedCarousel onSearchTopic={handleSelectCategory} />

            {/* 5. Interactive Academic Bookshelf (Pinterest Ref 3) */}
            <AcademicBookshelf />

            {/* 6. System Capabilities & Feature Highlights */}
            <FeatureHighlights />
          </div>
        ) : (
          /* ─── WHEN USER IS SEARCHING: SEARCH RESULTS WORKSPACE ─── */
          <div>
            {/* Top Search Bar & Return to Home Navigation */}
            <div className="bg-gradient-to-b from-muted/40 via-background to-background border-b py-6">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
                
                <div className="flex items-center justify-between">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleGoHome}
                    className="text-xs text-muted-foreground hover:text-foreground gap-1.5 -ml-2"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    Kembali ke Beranda
                  </Button>

                  <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
                    <span>{results.length} Dokumen Ditemukan</span>
                  </div>
                </div>

                <div className="max-w-3xl">
                  <SearchBar
                    query={query}
                    onChange={setQuery}
                    onSearch={handleSearch}
                    isLoading={isLoading}
                    tolerantMode={tolerantMode}
                    onTolerantModeChange={handleTolerantModeChange}
                  />
                </div>
              </div>
            </div>

            {/* Results Workspace Layout */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {isLoading ? (
                <div className="flex gap-8">
                  <div className="w-60 shrink-0 space-y-4 hidden md:block">
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
              ) : (
                <div className="flex flex-col md:flex-row gap-8">
                  {/* Filter Sidebar */}
                  <div className="w-full md:w-60 shrink-0">
                    <FilterSidebar
                      selectedType={selectedType}
                      yearFrom={yearFrom}
                      yearTo={yearTo}
                      language={language}
                      retrievalMode={retrievalMode}
                      aggregationStrategy={aggregationStrategy}
                      tolerantMode={tolerantMode}
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
                      onTolerantModeChange={handleTolerantModeChange}
                      onReset={handleReset}
                      totalResults={results.length}
                    />
                  </div>

                  {/* Results Display Area */}
                  <div className="flex-1 min-w-0 space-y-4">
                    {/* Tolerant Retrieval Alert Banner */}
                    <TolerantBanner
                      metadata={tolerantMetadata}
                      onSearchOriginal={handleSearchOriginal}
                      onApplySuggested={handleApplySuggested}
                    />

                    {error ? (
                      <div className="flex flex-col items-center justify-center py-16 text-center border rounded-2xl bg-card">
                        <AlertCircle className="h-10 w-10 text-destructive mb-3" />
                        <p className="text-base font-semibold text-destructive">Kesalahan Pencarian</p>
                        <p className="text-sm text-muted-foreground mt-1 max-w-sm">{error}</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => executeSearch()}
                          className="mt-4 text-xs"
                        >
                          Coba Lagi
                        </Button>
                      </div>
                    ) : paginatedResults.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-16 text-center border rounded-2xl bg-card">
                        <SearchX className="h-10 w-10 text-muted-foreground mb-3" />
                        <p className="text-base font-bold">Tidak ada dokumen yang ditemukan</p>
                        <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                          Coba kata kunci lain, gunakan sinonim, atau sesuaikan filter di bilah samping.
                        </p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleReset}
                          className="mt-4 text-xs"
                        >
                          Reset Semua Filter
                        </Button>
                      </div>
                    ) : (
                      <>
                        {/* Results Toolbar: Meta Info + View Mode Toggle */}
                        <div className="flex flex-wrap items-center justify-between text-xs text-muted-foreground pb-2 gap-2 border-b border-border/60">
                          <div>
                            Menampilkan hasil untuk:{" "}
                            <strong className="text-foreground">&ldquo;{searchedQuery}&rdquo;</strong>
                          </div>

                          <div className="flex items-center gap-3">
                            {/* View Mode Toggle (List vs Grid) */}
                            <div className="flex items-center rounded-lg border border-border p-0.5 bg-muted/40">
                              <button
                                type="button"
                                onClick={() => setViewMode("list")}
                                className={`px-2 py-1 rounded-md text-xs flex items-center gap-1 transition-colors ${
                                  viewMode === "list"
                                    ? "bg-background text-foreground shadow-xs font-semibold"
                                    : "text-muted-foreground hover:text-foreground"
                                }`}
                              >
                                <List className="h-3.5 w-3.5" />
                                <span className="hidden sm:inline">Daftar</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setViewMode("grid")}
                                className={`px-2 py-1 rounded-md text-xs flex items-center gap-1 transition-colors ${
                                  viewMode === "grid"
                                    ? "bg-background text-foreground shadow-xs font-semibold"
                                    : "text-muted-foreground hover:text-foreground"
                                }`}
                              >
                                <LayoutGrid className="h-3.5 w-3.5" />
                                <span className="hidden sm:inline">Katalog</span>
                              </button>
                            </div>

                            <span className="hidden lg:flex items-center gap-2 font-mono text-[11px]">
                              <span>Model: <strong>{retrievalMode.toUpperCase()}</strong></span>
                              <span>|</span>
                              <span>Toleransi: <strong>{tolerantMode.toUpperCase()}</strong></span>
                            </span>
                          </div>
                        </div>

                        {/* Results Cards (List or Grid) */}
                        <div
                          className={
                            viewMode === "grid"
                              ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
                              : "space-y-4"
                          }
                        >
                          {paginatedResults.map((result) => (
                            <ResultCard
                              key={result.id}
                              result={result}
                              activeQuery={query}
                              viewMode={viewMode}
                            />
                          ))}
                        </div>

                        {/* Pagination */}
                        {totalPages > 1 && (
                          <div className="pt-6">
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
              )}
            </main>
          </div>
        )}
      </div>

      {/* ─── MODERN EDITORIAL FOOTER ─── */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 py-10 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-md bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center text-white dark:text-zinc-900 text-xs font-black">
                IR
              </div>
              <span className="font-extrabold text-sm text-zinc-900 dark:text-zinc-100">
                Academic Information Retrieval System
              </span>
            </div>

            <p className="text-xs text-zinc-500 dark:text-zinc-400 text-center">
              Ditenagai oleh TF-IDF VSM, BM25 Lexical Layer, Sastrawi &amp; Porter Stemmer, FastAPI, dan Next.js 15.
            </p>

            <div className="flex items-center gap-2 text-xs font-mono text-zinc-500 dark:text-zinc-400">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>Backend Ready (Port 8000)</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
