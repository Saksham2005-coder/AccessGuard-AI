import { useState } from "react";
import {
  Database,
  ExternalLink,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

interface WCAGDoc {
  id: string;
  title: string;
  category: "Standard" | "Guidance" | "Techniques" | "ARIA";
  version: string;
  description: string;
  status: "Indexed & Active" | "Reference";
  sourceUrl: string;
  chunkCount: number;
  embeddingModel: string;
}

const knowledgeCorpus: WCAGDoc[] = [
  {
    id: "wcag-22-rec",
    title: "WCAG 2.2 Recommendation (Official W3C)",
    category: "Standard",
    version: "2.2",
    description: "Web Content Accessibility Guidelines covers wide range of recommendations for making Web content more accessible to people with disabilities.",
    status: "Indexed & Active",
    sourceUrl: "https://www.w3.org/TR/WCAG22/",
    chunkCount: 248,
    embeddingModel: "all-MiniLM-L6-v2 (384d)",
  },
  {
    id: "wcag-22-understanding",
    title: "Understanding WCAG 2.2",
    category: "Guidance",
    version: "2.2",
    description: "Detailed explanatory rationale, user intent, benefits, and examples for each success criterion across Level A, AA, and AAA.",
    status: "Indexed & Active",
    sourceUrl: "https://www.w3.org/WAI/WCAG22/Understanding/",
    chunkCount: 412,
    embeddingModel: "Dense + BM25 Lexical (RRF)",
  },
  {
    id: "wcag-techniques",
    title: "Techniques for WCAG 2.2",
    category: "Techniques",
    version: "2.2",
    description: "Sufficient techniques, advisory techniques, and documented common failures for web technologies (HTML, CSS, ARIA, Client JS).",
    status: "Indexed & Active",
    sourceUrl: "https://www.w3.org/WAI/WCAG22/Techniques/",
    chunkCount: 310,
    embeddingModel: "Dense + BM25 Lexical (RRF)",
  },
  {
    id: "aria-apg",
    title: "WAI-ARIA Authoring Practices Guide (APG)",
    category: "ARIA",
    version: "1.2",
    description: "Accessible design patterns, keyboard interactions, ARIA role hierarchies, and live region specifications for complex UI components.",
    status: "Indexed & Active",
    sourceUrl: "https://www.w3.org/WAI/ARIA/apg/",
    chunkCount: 185,
    embeddingModel: "all-MiniLM-L6-v2 (384d)",
  },
];

export function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const filteredDocs = knowledgeCorpus.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || doc.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
          WCAG Knowledge Base
        </h1>
        <p className="text-sm text-[#9CA3AF] mt-1">
          Official W3C WCAG 2.2 criteria, techniques, and grounded RAG vector collections.
        </p>
      </div>

      {/* RAG Engine Status Overview Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-[#171A1F]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8]">
              <Database className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#F3F4F6]">Qdrant Vector DB</div>
              <div className="text-[11px] text-[#9CA3AF]">Collection: wcag_chunks (384d)</div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-[#171A1F]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#34D399]/15 border border-[#34D399]/30 text-[#34D399]">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#F3F4F6]">Citation Validator</div>
              <div className="text-[11px] text-[#9CA3AF]">100% Provenance Grounded</div>
            </div>
          </div>
        </Card>

        <Card className="p-4 bg-[#171A1F]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#60A5FA]/15 border border-[#60A5FA]/30 text-[#60A5FA]">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[#F3F4F6]">Hybrid RRF Fusion</div>
              <div className="text-[11px] text-[#9CA3AF]">Dense Vector + BM25 (k=60)</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-[#171A1F]">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
            <input
              type="text"
              placeholder="Search standards, criterion numbers, or techniques..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-full rounded-lg border border-[#303741] bg-[#171C23] pl-9 pr-3 text-xs text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:border-[#38BDF8] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]/20 transition-colors"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {["All", "Standard", "Guidance", "Techniques", "ARIA"].map((cat) => (
              <Button
                key={cat}
                size="sm"
                variant={selectedCategory === cat ? "default" : "outline"}
                onClick={() => setSelectedCategory(cat)}
                className="text-xs h-8 px-3"
              >
                {cat}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* Corpus Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filteredDocs.map((doc) => (
          <Card key={doc.id} className="hover:border-[#38BDF8]/40 transition-all flex flex-col justify-between">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px] font-mono uppercase">
                      {doc.category}
                    </Badge>
                    <span className="text-[11px] text-[#6B7280]">v{doc.version}</span>
                  </div>
                  <CardTitle className="text-base font-semibold">{doc.title}</CardTitle>
                </div>
                <Badge variant="success" className="text-xs shrink-0">
                  {doc.status}
                </Badge>
              </div>
              <CardDescription className="pt-2">{doc.description}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-3 pt-0">
              <div className="p-3 rounded-lg bg-[#171C23] border border-[#303741] space-y-1.5 text-xs">
                <div className="flex justify-between text-[#9CA3AF]">
                  <span>Vector Index Chunks:</span>
                  <span className="text-[#F3F4F6] font-mono">{doc.chunkCount} indexed</span>
                </div>
                <div className="flex justify-between text-[#9CA3AF]">
                  <span>Retriever Engine:</span>
                  <span className="text-[#38BDF8] font-mono">{doc.embeddingModel}</span>
                </div>
              </div>

              <div className="pt-1 flex items-center justify-between">
                <a
                  href={doc.sourceUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-[#38BDF8] hover:underline font-medium"
                >
                  <span>View official W3C specification</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
