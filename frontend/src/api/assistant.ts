import { apiClient } from "./client";

export interface FindingEvidenceItem {
  finding_id: string;
  rule_id: string;
  impact: string | null;
  selector: string | null;
  description: string;
}

export interface WcagCitationItem {
  criterion_id: string;
  title: string;
  guidance: string;
  url: string | null;
}

export interface AssistantStructuredData {
  evidence_findings: FindingEvidenceItem[];
  wcag_citations: WcagCitationItem[];
  observed_facts: string[];
  guidance_notes: string[];
  suggested_action: string | null;
  limitations_notice: string;
}

export interface AssistantChatRequest {
  project_id: string;
  scan_id?: string | null;
  conversation_id?: string | null;
  message: string;
}

export interface AssistantMessageResponse {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  structured_data: AssistantStructuredData | null;
  created_at: string;
}

export interface AssistantConversationResponse {
  id: string;
  project_id: string;
  scan_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
  messages: AssistantMessageResponse[];
}

export async function sendAssistantChat(
  data: AssistantChatRequest
): Promise<AssistantMessageResponse> {
  const res = await apiClient.post<AssistantMessageResponse>("/assistant/chat", data);
  return res.data;
}

export async function listProjectConversations(
  projectId: string
): Promise<AssistantConversationResponse[]> {
  const res = await apiClient.get<AssistantConversationResponse[]>(
    `/projects/${projectId}/assistant/conversations`
  );
  return res.data;
}

export async function getConversationDetail(
  conversationId: string
): Promise<AssistantConversationResponse> {
  const res = await apiClient.get<AssistantConversationResponse>(
    `/assistant/conversations/${conversationId}`
  );
  return res.data;
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/assistant/conversations/${conversationId}`);
}
