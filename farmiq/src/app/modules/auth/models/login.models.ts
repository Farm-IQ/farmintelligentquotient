/**
 * LOGIN MODELS
 * 
 * Models for user authentication and login flows
 * Supports: Email/Password, OAuth (Google, GitHub), Magic Link, Web3
 */

/**
 * Login request with email and password
 */
export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Login response from Supabase
 */
export interface LoginResponse {
  success: boolean;
  user?: AuthUser;
  session?: Session;
  message?: string;
  error?: string;
  requiresEmailVerification?: boolean;
}

/**
 * Authentication user from Supabase Auth
 */
export interface AuthUser {
  id: string;
  email?: string;
  email_confirmed_at?: string;
  phone?: string;
  phone_confirmed_at?: string;
  last_sign_in_at?: string;
  app_metadata?: {
    provider?: string;
    providers?: string[];
  };
  user_metadata?: {
    [key: string]: any;
  };
  aud?: string;
  confirmation_sent_at?: string;
  confirmed_at?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Session object containing access and refresh tokens
 */
export interface Session {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: any; // Supabase User type - compatible with AuthUser structure
}

/**
 * Magic Link request for passwordless login
 */
export interface MagicLinkRequest {
  email: string;
  redirectUrl?: string;
}

/**
 * Magic Link response
 */
export interface MagicLinkResponse {
  success: boolean;
  message: string;
  error?: string;
}

/**
 * OTP verification request
 */
export interface OtpVerificationRequest {
  email: string;
  token: string;
  type: 'email' | 'sms';
}

/**
 * OTP verification response
 */
export interface OtpVerificationResponse {
  success: boolean;
  user?: AuthUser;
  session?: Session;
  message?: string;
  error?: string;
}

/**
 * OAuth login result (legacy; use oauth.models.OAuthLoginResult instead)
 */
export interface LoginOAuthResult {
  provider: 'google' | 'github' | 'web3';
  url?: string;
  success: boolean;
  message?: string;
  error?: string;
}

/**
 * Password reset request
 */
export interface PasswordResetRequest {
  email: string;
}

/**
 * Password reset response
 */
export interface PasswordResetResponse {
  success: boolean;
  message: string;
  error?: string;
}

/**
 * Password reset verification (from reset email link)
 */
export interface PasswordResetVerification {
  token: string;
  newPassword: string;
}

/**
 * Password reset verification response
 */
export interface PasswordResetVerificationResponse {
  success: boolean;
  user?: AuthUser;
  message?: string;
  error?: string;
}

/**
 * Login state for reactive management
 */
export interface LoginState {
  isLoading: boolean;
  isAuthenticated: boolean;
  user: AuthUser | null;
  session: Session | null;
  error: string | null;
  requiresEmailVerification: boolean;
  unverifiedEmail: string | null;
  lastLoginTime: Date | null;
}

/**
 * Session persistence data
 */
export interface SessionPersistenceData {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  user: AuthUser;
  farmiqId: string;
}

/**
 * Email validation result
 */
export interface EmailValidationResult {
  valid: boolean;
  error?: string;
  suggestion?: string;
}

/**
 * Login error types
 */
export enum LoginErrorType {
  INVALID_CREDENTIALS = 'INVALID_CREDENTIALS',
  EMAIL_NOT_VERIFIED = 'EMAIL_NOT_VERIFIED',
  ACCOUNT_DISABLED = 'ACCOUNT_DISABLED',
  TOO_MANY_ATTEMPTS = 'TOO_MANY_ATTEMPTS',
  NETWORK_ERROR = 'NETWORK_ERROR',
  SESSION_EXPIRED = 'SESSION_EXPIRED',
  OAUTH_ERROR = 'OAUTH_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

/**
 * Structured login error
 */
export interface LoginError {
  type: LoginErrorType;
  message: string;
  details?: string;
  recoverable: boolean;
}

/**
 * Sign-in request (extended login)
 */
export interface SignInRequest extends LoginRequest {
  captchaToken?: string;
}

/**
 * Sign-in response
 */
export interface AuthResponse {
  user: AuthUser | null;
  session: Session | null;
  error?: string;
}

/**
 * Sign-up request with email and password
 */
export interface SignUpRequest {
  email: string;
  password: string;
  password_confirm: string;
  full_name?: string; // Optional full name for profile
  phone_number?: string; // Optional phone number
  accept_terms: boolean;
  accept_privacy: boolean;
}

/**
 * Update profile request
 */
export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  full_name?: string; // Alternative to first/last names
  email?: string;
  phone?: string;
  phone_number?: string;
  avatar_url?: string;
  user_metadata?: Record<string, any>;
}
