// src/types/auth.d.ts
export interface User {
  id: string;
  email: string;
  username: string;
  fullName?: string;
  role: string;
  createdAt: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user_id: string;
  email?: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  fullName?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
