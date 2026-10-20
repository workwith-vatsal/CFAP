export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  mobile?: string | null;
  role: string;
  auth_provider: string;
  is_verified: boolean;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
  user: {
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    mobile?: string | null;
    is_verified: boolean;
  };
}

export interface MessageResponse {
  message: string;
}

export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
  status?: number;
}

export type Language = 'en' | 'hi';

export * from './dataset';
export * from './analysis';
export * from './analytics';
export * from './assistant';
export * from './report';
export * from './benchmark';
export * from './admin';
