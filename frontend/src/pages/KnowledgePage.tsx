import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ExternalLink,
  Search,
  Sparkles,
  BookOpen,
  X,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";
import {
  listKnowledgeSourcesApi,
  searchKnowledgeApi,
  EvidenceItem,
  KnowledgeSource,
} from "../api/knowledge";

export function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [retrievalMode, setRetrievalMode] = useState<"hybrid" | "dense" | "lexical">("hybrid");
  const [selectedItem, setSelectedItem] = useState<EvidenceItem | null>(null);

  // Query real knowledge sources from backend database
  const {
    data: sources = [],
    isLoading: isLoadingSources,
    isError: isSourcesError,
    refetch: refetchSources,
  } = useQuery<KnowledgeSource[]>({
    queryKey: ["knowledgeSources"],
    queryFn: listKnowledgeSourcesApi,
  });

  // Query search results when submittedQuery is non-empty
  const {
    data: searchResults,
    isLoading: isSearching,
    isError: isSearchError,
    refetch: refetchSearch,
  } = useQuery({
    queryKey: ["knowledgeSearch", submittedQuery, retrievalMode],
    queryFn: () =>
      searchKnowledgeApi({
        query: submittedQuery,
        retrieval_mode: retrievalMode,
        limit: 12,
      }),
    enabled: submittedQuery.trim().length > 0,
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setSubmittedQuery(searchQuery.trim());
      setSelectedItem(null);
    }
  };

  const handleClear = () => {
    setSearchQuery("");
    setSubmittedQuery("");
    setSelectedItem(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">
            WCAG Knowledge Base & Standards
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Search verified W3C WCAG 2.2 criteria, understanding documents, and techniques via hybrid vector & lexical RAG.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs px-2.5 py-1 flex items-center gap-1.5 border-[var(--border-graphite)]">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>Qdrant Local Vector DB</span>
          </Badge>
        </div>
      </div>

      {/* Official Verified Sources Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoadingSources ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="p-4 bg-[var(--bg-sidebar)]">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-3 w-32" />
            </Card>
          ))
        ) : isSourcesError ? (
          <div className="col-span-full p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-xs text-rose-300 flex items-center justify-between">
            <span>Failed to load knowledge source indices.</span>
            <Button variant="outline" size="sm" onClick={() => refetchSources()}>
              <RefreshCw className="h-3 w-3 mr-1" /> Retry
            </Button>
          </div>
        ) : (
          sources.map((src) => (
            <Card key={src.id} className="p-4 bg-[var(--bg-sidebar)] border-[var(--border-graphite)]">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-[11px] font-semibold text-[var(--electric-blue)] uppercase tracking-wider">
                    {src.standard_version || "Standard"}
                  </div>
                  <h2 className="text-xs font-bold text-[var(--text-primary)] truncate mt-0.5" title={src.title}>
                    {src.title}
                  </h2>
                </div>
                <a
                  href={src.canonical_url}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1 rounded text-[var(--text-secondary)] hover:text-[var(--electric-blue)] shrink-0"
                  title="View Official W3C Spec"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
              <p className="text-[11px] text-[var(--text-secondary)] mt-2 line-clamp-2 leading-relaxed">
                {src.description || "Official normative guidance document indexed for accessibility remediation."}
              </p>
            </Card>
          ))
        )}
      </div>

      {/* Search Input Bar */}
      <Card className="p-4 bg-[var(--bg-sidebar)] border-[var(--border-graphite)]">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search WCAG guidelines, criteria (e.g. 'contrast', '1.1.1', 'focus visible', 'alt text')..."
              className="w-full pl-10 pr-10 py-2.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--electric-blue)]"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                title="Clear search query"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center rounded-lg border border-[var(--border-graphite)] bg-[var(--bg-card)] p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setRetrievalMode("hybrid")}
                className={`px-2.5 py-1.5 rounded-md font-medium transition-colors ${
                  retrievalMode === "hybrid"
                    ? "bg-[var(--electric-blue)] text-[var(--bg-app)] font-semibold shadow-xs"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
                title="Dense semantic vectors fused with BM25 lexical keywords (Reciprocal Rank Fusion)"
              >
                Hybrid
              </button>
              <button
                type="button"
                onClick={() => setRetrievalMode("dense")}
                className={`px-2.5 py-1.5 rounded-md font-medium transition-colors ${
                  retrievalMode === "dense"
                    ? "bg-[var(--electric-blue)] text-[var(--bg-app)] font-semibold shadow-xs"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
                title="Dense neural embeddings only (all-MiniLM-L6-v2)"
              >
                Dense
              </button>
              <button
                type="button"
                onClick={() => setRetrievalMode("lexical")}
                className={`px-2.5 py-1.5 rounded-md font-medium transition-colors ${
                  retrievalMode === "lexical"
                    ? "bg-[var(--electric-blue)] text-[var(--bg-app)] font-semibold shadow-xs"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
                title="Exact keyword BM25 search"
              >
                Lexical
              </button>
            </div>

            <Button type="submit" variant="default" disabled={!searchQuery.trim() || isSearching}>
              {isSearching ? <RefreshCw className="h-4 w-4 animate-spin mr-1.5" /> : <Search className="h-4 w-4 mr-1.5" />}
              Search RAG
            </Button>
          </div>
        </form>
      </Card>

      {/* Main Results View */}
      {submittedQuery ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-xs text-[var(--text-secondary)]">
              Results for <strong className="text-[var(--text-primary)]">"{submittedQuery}"</strong>{" "}
              {searchResults ? `(${searchResults.evidence.length} chunks retrieved)` : ""}
            </div>
            {searchResults?.abstain && (
              <Badge variant="warning" className="text-xs">
                Low Confidence Abstention
              </Badge>
            )}
          </div>

          {isSearching ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Card key={i} className="p-5 bg-[var(--bg-card)]">
                  <Skeleton className="h-5 w-3/4 mb-3" />
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-5/6" />
                </Card>
              ))}
            </div>
          ) : isSearchError ? (
            <Card className="p-8 text-center bg-[var(--bg-card)] border-rose-500/20">
              <AlertCircle className="h-8 w-8 text-rose-400 mx-auto mb-3" />
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">RAG Search Query Failed</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-md mx-auto">
                Unable to complete search against Qdrant index. Please verify that the Qdrant service is online.
              </p>
              <Button variant="outline" size="sm" onClick={() => refetchSearch()} className="mt-4">
                <RefreshCw className="h-3 w-3 mr-1" /> Retry Search
              </Button>
            </Card>
          ) : searchResults?.evidence.length === 0 ? (
            <Card className="p-8 text-center bg-[var(--bg-card)]">
              <Search className="h-8 w-8 text-[var(--text-secondary)] mx-auto mb-3 opacity-50" />
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">No Relevant WCAG Guidelines Found</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-md mx-auto">
                Try searching for specific criteria (e.g., "1.4.3", "contrast", "keyboard", "alt text", "heading").
              </p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Evidence Cards Column */}
              <div className="lg:col-span-2 space-y-3">
                {searchResults?.evidence.map((item) => (
                  <Card
                    key={item.chunk_id}
                    onClick={() => setSelectedItem(item)}
                    className={`p-4 cursor-pointer transition-all border ${
                      selectedItem?.chunk_id === item.chunk_id
                        ? "border-[var(--electric-blue)] bg-[var(--bg-elevated)] ring-1 ring-[var(--electric-blue)]/50"
                        : "border-[var(--border-graphite)] bg-[var(--bg-card)] hover:border-[var(--electric-blue)]/50"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1.5">
                          {item.criterion_id && (
                            <Badge variant="primary" className="text-[10px] font-mono">
                              WCAG {item.criterion_id}
                            </Badge>
                          )}
                          {item.criterion_level && (
                            <Badge variant="outline" className="text-[10px]">
                              Level {item.criterion_level}
                            </Badge>
                          )}
                          <span className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider font-semibold">
                            {item.content_type}
                          </span>
                        </div>
                        <h2 className="text-sm font-bold text-[var(--text-primary)]">
                          {item.title}
                        </h2>
                      </div>
                      <span className="text-[11px] font-mono text-[var(--electric-blue)] shrink-0">
                        Score {(item.score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed line-clamp-3">
                      {item.excerpt}
                    </p>

                    <div className="mt-3 pt-2 border-t border-[var(--border-graphite)]/50 flex items-center justify-between text-[11px] text-[var(--text-secondary)]">
                      <span>Source: {item.source_title}</span>
                      <span className="text-[var(--electric-blue)] flex items-center gap-1 font-medium">
                        Inspect Guidance →
                      </span>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Side Details Drawer / Panel */}
              <div className="lg:col-span-1">
                {selectedItem ? (
                  <Card className="p-5 bg-[var(--bg-card)] border-[var(--border-graphite)] sticky top-20">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-semibold text-[var(--electric-blue)] uppercase tracking-wider">
                        Document Details
                      </span>
                      <button
                        type="button"
                        onClick={() => setSelectedItem(null)}
                        className="p-1 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                        title="Close detail panel"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>

                    <h2 className="text-base font-bold text-[var(--text-primary)] mb-2">
                      {selectedItem.title}
                    </h2>

                    <div className="flex flex-wrap items-center gap-2 mb-4">
                      {selectedItem.criterion_id && (
                        <Badge variant="primary" className="text-xs">
                          Criterion {selectedItem.criterion_id}
                        </Badge>
                      )}
                      {selectedItem.criterion_level && (
                        <Badge variant="outline" className="text-xs">
                          Level {selectedItem.criterion_level}
                        </Badge>
                      )}
                    </div>

                    <div className="space-y-3 text-xs text-[var(--text-secondary)] leading-relaxed">
                      <div>
                        <strong className="text-[var(--text-primary)] block mb-1">Normative Excerpt:</strong>
                        <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] font-sans whitespace-pre-wrap">
                          {selectedItem.excerpt}
                        </div>
                      </div>

                      <div>
                        <strong className="text-[var(--text-primary)] block mb-1">Official Reference:</strong>
                        <a
                          href={selectedItem.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[var(--electric-blue)] hover:underline inline-flex items-center gap-1.5 break-all"
                        >
                          <span>{selectedItem.source_url}</span>
                          <ExternalLink className="h-3 w-3 shrink-0" />
                        </a>
                      </div>
                    </div>
                  </Card>
                ) : (
                  <Card className="p-6 text-center bg-[var(--bg-card)] border-dashed border-[var(--border-graphite)] sticky top-20">
                    <BookOpen className="h-6 w-6 text-[var(--text-secondary)] mx-auto mb-2 opacity-60" />
                    <p className="text-xs text-[var(--text-secondary)]">
                      Select any retrieved guideline chunk on the left to inspect its full text and official W3C normative reference.
                    </p>
                  </Card>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <Card className="p-8 text-center bg-[var(--bg-card)] border-[var(--border-graphite)]">
          <Sparkles className="h-8 w-8 text-[var(--electric-blue)] mx-auto mb-3" />
          <h2 className="text-base font-bold text-[var(--text-primary)]">
            Explore Grounded Accessibility Knowledge
          </h2>
          <p className="text-xs text-[var(--text-secondary)] mt-1.5 max-w-lg mx-auto leading-relaxed">
            Query the official WCAG 2.2 corpus to review normative criteria, test techniques, and implementation examples
            used by the AI remediation engine during automated patch generation.
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            {["1.1.1 Non-text Content", "1.4.3 Contrast", "2.1.1 Keyboard", "2.4.7 Focus Visible", "4.1.2 Name, Role, Value"].map(
              (query) => (
                <button
                  key={query}
                  type="button"
                  onClick={() => {
                    setSearchQuery(query);
                    setSubmittedQuery(query);
                  }}
                  className="px-3 py-1 rounded-full text-xs font-medium border border-[var(--border-graphite)] bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--electric-blue)]/50 transition-colors"
                >
                  {query}
                </button>
              )
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
