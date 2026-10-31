import { apiClient } from "./client";

export interface DomainVerification {
  id: string;
  project_id: string;
  domain: string;
  record_name: string;
  record_type: string;
  expected_value: string;
  status: "pending" | "verified" | "expired" | "failed" | string;
  expires_at: string;
  verified_at: string | null;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  base_domain: string;
  is_verified: boolean;
  latest_verification: DomainVerification | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface ProjectCreateRequest {
  name: string;
  base_domain: string;
}

export interface VerificationCheckResponse {
  verified: boolean;
  message: string;
  status: string;
  verification: DomainVerification;
}

export async function listProjectsApi(): Promise<ProjectListResponse> {
  const response = await apiClient.get<ProjectListResponse>("/projects");
  return response.data;
}

export async function getProjectApi(projectId: string): Promise<Project> {
  const response = await apiClient.get<Project>(`/projects/${projectId}`);
  return response.data;
}

export async function createProjectApi(data: ProjectCreateRequest): Promise<Project> {
  const response = await apiClient.post<Project>("/projects", data);
  return response.data;
}

export async function deleteProjectApi(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`);
}

export async function refreshVerificationApi(projectId: string): Promise<DomainVerification> {
  const response = await apiClient.post<DomainVerification>(
    `/projects/${projectId}/domain-verification`
  );
  return response.data;
}

export async function checkVerificationApi(
  projectId: string
): Promise<VerificationCheckResponse> {
  const response = await apiClient.post<VerificationCheckResponse>(
    `/projects/${projectId}/domain-verification/check`
  );
  return response.data;
}
