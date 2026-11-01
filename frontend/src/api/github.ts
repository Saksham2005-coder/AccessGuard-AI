import { apiClient } from "./client";

export interface GitHubIntegration {
  id: string;
  project_id: string;
  repo_owner: string;
  repo_name: string;
  installation_id: string | null;
  webhook_secret_preview: string;
  webhook_secret?: string | null;
  webhook_url: string;
  has_token: boolean;
  target_branch: string;
  enabled: boolean;
  auto_review_prs: boolean;
  created_at: string;
  updated_at: string;
}

export interface GitHubIntegrationCreate {
  repo_owner: string;
  repo_name: string;
  installation_id?: string | null;
  webhook_secret?: string | null;
  access_token?: string | null;
  target_branch?: string;
  enabled?: boolean;
  auto_review_prs?: boolean;
}

export interface GitHubIntegrationUpdate {
  target_branch?: string;
  enabled?: boolean;
  auto_review_prs?: boolean;
  access_token?: string | null;
}

export interface GitHubReviewRecord {
  id: string;
  integration_id: string;
  project_id: string;
  delivery_id: string;
  pr_number: number;
  pr_title: string;
  pr_author: string | null;
  head_sha: string;
  base_sha: string;
  scan_id: string | null;
  status: string; // 'received' | 'scanning' | 'reviewed' | 'skipped' | 'failed'
  comment_id: string | null;
  summary_markdown: string | null;
  error_message: string | null;
  created_at: string;
}

export interface TestReviewRequest {
  pr_number: number;
  pr_title: string;
  pr_author?: string;
  head_sha?: string;
  base_sha?: string;
}

export async function getProjectIntegration(projectId: string): Promise<GitHubIntegration | null> {
  try {
    const res = await apiClient.get<GitHubIntegration>(`/projects/${projectId}/github/integration`);
    return res.data;
  } catch (err: unknown) {
    if (err && typeof err === "object" && "response" in err) {
      const axiosErr = err as { response?: { status?: number } };
      if (axiosErr.response?.status === 404) {
        return null;
      }
    }
    throw err;
  }
}

export async function connectProjectRepo(
  projectId: string,
  data: GitHubIntegrationCreate
): Promise<GitHubIntegration> {
  const res = await apiClient.post<GitHubIntegration>(`/projects/${projectId}/github/integration`, data);
  return res.data;
}

export async function updateProjectRepo(
  projectId: string,
  data: GitHubIntegrationUpdate
): Promise<GitHubIntegration> {
  const res = await apiClient.patch<GitHubIntegration>(`/projects/${projectId}/github/integration`, data);
  return res.data;
}

export async function disconnectProjectRepo(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/github/integration`);
}

export async function listProjectReviews(projectId: string): Promise<GitHubReviewRecord[]> {
  const res = await apiClient.get<GitHubReviewRecord[]>(`/projects/${projectId}/github/reviews`);
  return res.data;
}

export async function triggerTestReview(
  projectId: string,
  data: TestReviewRequest
): Promise<GitHubReviewRecord> {
  const res = await apiClient.post<GitHubReviewRecord>(`/projects/${projectId}/github/test-review`, data);
  return res.data;
}
