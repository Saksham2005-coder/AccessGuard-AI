import { create } from "zustand";
import {
  getMeApi,
  LoginCredentials,
  loginApi,
  logoutApi,
  refreshApi,
  RegisterCredentials,
  registerApi,
  User,
} from "../api/auth";
import { setAccessToken } from "../api/client";

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  clearError: () => set({ error: null }),

  setUser: (user) =>
    set({
      user,
      isAuthenticated: Boolean(user),
    }),

  login: async (credentials: LoginCredentials) => {
    set({ isLoading: true, error: null });
    try {
      const data = await loginApi(credentials);
      set({
        user: data.user,
        accessToken: data.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      let errorMessage = "Invalid email or password.";
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response &&
        err.response.data &&
        typeof err.response.data === "object" &&
        "detail" in err.response.data &&
        typeof err.response.data.detail === "string"
      ) {
        errorMessage = err.response.data.detail;
      }
      set({
        isLoading: false,
        error: errorMessage,
        isAuthenticated: false,
        user: null,
        accessToken: null,
      });
      throw err;
    }
  },

  register: async (credentials: RegisterCredentials) => {
    set({ isLoading: true, error: null });
    try {
      await registerApi(credentials);
      // Automatically log in after registration
      const loginData = await loginApi({
        email: credentials.email,
        password: credentials.password,
      });
      set({
        user: loginData.user,
        accessToken: loginData.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (err: unknown) {
      let errorMessage = "Registration failed. Please check your details.";
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response &&
        err.response.data &&
        typeof err.response.data === "object" &&
        "detail" in err.response.data &&
        typeof err.response.data.detail === "string"
      ) {
        errorMessage = err.response.data.detail;
      }
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw err;
    }
  },

  logout: async () => {
    try {
      await logoutApi();
    } catch {
      // Ignore network errors on logout
    } finally {
      setAccessToken(null);
      set({
        user: null,
        accessToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  },

  checkAuth: async () => {
    if (get().isAuthenticated && get().user) {
      set({ isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      // First attempt to refresh token via cookie
      const tokenData = await refreshApi();
      set({
        user: tokenData.user,
        accessToken: tokenData.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch {
      // Refresh failed or no session cookie, check if we have a current token for getMe
      try {
        const user = await getMeApi();
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch {
        setAccessToken(null);
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    }
  },
}));
