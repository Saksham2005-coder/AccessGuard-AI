import { apiClient } from "./client";

export interface KnowledgeSource {
  id: string;
  source_key: string;
  title: string;
  standard_version?: string;
  canonical_url: string;
  description?: string;
  is_active: boolean;
}

export interface EvidenceItem {
  chunk_id: string;
  chunk_key: string;
  criterion_id?: string;
  criterion_level?: string;
  title: string;
  source_title: string;
  source_url: string;
  content_type: string;
  excerpt: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeSearchResponse {
  query: string;
  retrieval_mode: string;
  evidence: EvidenceItem[];
  total_candidates: number;
  abstain: boolean;
  abstain_reason?: string | null;
}

export async function listKnowledgeSourcesApi(): Promise<KnowledgeSource[]> {
  const response = await apiClient.get<KnowledgeSource[]>("/knowledge/sources");
  return response.data;
}

export async function searchKnowledgeApi(payload: {
  query: string;
  limit?: number;
  retrieval_mode?: "dense" | "lexical" | "hybrid";
  criterion_id?: string;
}): Promise<KnowledgeSearchResponse> {
  const response = await apiClient.post<KnowledgeSearchResponse>("/knowledge/search", {
    query: payload.query,
    limit: payload.limit ?? 10,
    retrieval_mode: payload.retrieval_mode ?? "hybrid",
    criterion_id: payload.criterion_id || undefined,
  });
  return response.data;
}

export async function getCriterionDetailsApi(criterionId: string): Promise<EvidenceItem[]> {
  const response = await apiClient.get<EvidenceItem[]>(`/knowledge/criteria/${criterionId}`);
  return response.data;
}
