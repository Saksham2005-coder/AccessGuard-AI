import { apiClient, setAccessToken } from "./client";

export interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  display_name: string;
}

export interface MessageResponse {
  message: string;
}

export async function loginApi(credentials: LoginCredentials): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", credentials);
  setAccessToken(response.data.access_token);
  return response.data;
}

export async function registerApi(credentials: RegisterCredentials): Promise<User> {
  const response = await apiClient.post<User>("/auth/register", credentials);
  return response.data;
}

export async function refreshApi(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/refresh");
  setAccessToken(response.data.access_token);
  return response.data;
}

export async function logoutApi(): Promise<MessageResponse> {
  try {
    const response = await apiClient.post<MessageResponse>("/auth/logout");
    return response.data;
  } finally {
    setAccessToken(null);
  }
}

export async function getMeApi(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}
