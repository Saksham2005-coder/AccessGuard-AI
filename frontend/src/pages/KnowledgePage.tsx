import { ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";

export function KnowledgePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">WCAG Knowledge Base</h1>
        <p className="text-sm text-slate-500 mt-1">
          Official W3C WCAG 2.2 criteria, techniques, and grounded RAG vector collections.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">WCAG 2.2 Recommendation</CardTitle>
              <Badge variant="success">Active Corpus</Badge>
            </div>
            <CardDescription>W3C Web Content Accessibility Guidelines</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-2">
            <p>Principles: Perceivable, Operable, Understandable, Robust</p>
            <p className="text-xs text-slate-400">Embedding model: all-MiniLM-L6-v2 (384d)</p>
            <a
              href="https://www.w3.org/TR/WCAG22/"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-[#4657D8] font-medium hover:underline pt-2"
            >
              <span>View official W3C specification</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">W3C Understanding WCAG 2.2</CardTitle>
              <Badge variant="success">Active Corpus</Badge>
            </div>
            <CardDescription>Official intent, benefits, and examples</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-slate-600 space-y-2">
            <p>Techniques: Sufficient, Advisory, and Common Failures</p>
            <p className="text-xs text-slate-400">Retriever: Dense Vector + Lexical BM25 (RRF)</p>
            <a
              href="https://www.w3.org/WAI/WCAG22/Understanding/"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-[#4657D8] font-medium hover:underline pt-2"
            >
              <span>View W3C Understanding guidance</span>
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
