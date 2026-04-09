/**
 * Auth Module Configuration
 * Central configuration for auth module behavior and constants
 * 
 * This file should be imported in app.config.ts to configure
 * the auth module globally across the application.
 */

import { InjectionToken } from '@angular/core';

/**
 * Configuration interface for auth module
 */
export interface AuthConfig {
  /** Supabase project URL */
  supabaseUrl: string;
  
  /** Supabase anonymous key */
  supabaseKey: string;
  
  /** Token refresh threshold (ms before expiration to refresh) */
  tokenRefreshThreshold: number;
  
  /** Session timeout (ms of inactivity before logout) */
  sessionTimeout: number;
  
  /** Whether to store tokens in localStorage (true) or sessionStorage (false) */
  persistTokens: boolean;
  
  /** OAuth redirect URI */
  oauthRedirectUri: string;
  
  /** OAuth providers configuration */
  oauthProviders: OAuthProviderConfig[];
  
  /** Email verification link base URL */
  emailVerificationBaseUrl: string;
  
  /** Password reset link base URL */
  passwordResetBaseUrl: string;
  
  /** Maximum login attempts before rate limiting */
  maxLoginAttempts: number;
  
  /** Rate limit window (ms) */
  rateLimitWindow: number;
}

/**
 * OAuth provider configuration
 */
export interface OAuthProviderConfig {
  name: 'google' | 'github' | 'github_business';
  clientId: string;
  scope: string[];
  enabled: boolean;
}

/**
 * Default configuration values
 */
export const DEFAULT_AUTH_CONFIG: AuthConfig = {
  supabaseUrl: 'https://your-project.supabase.co',
  supabaseKey: 'your-anon-key',
  tokenRefreshThreshold: 5 * 60 * 1000, // 5 minutes
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
  persistTokens: true,
  oauthRedirectUri: `${window.location.origin}/auth/oauth-callback`,
  oauthProviders: [
    {
      name: 'google',
      clientId: '',
      scope: ['email', 'profile'],
      enabled: false,
    },
    {
      name: 'github',
      clientId: '',
      scope: ['user:email'],
      enabled: false,
    },
    {
      name: 'github_business',
      clientId: '',
      scope: ['user:email'],
      enabled: false,
    },
  ],
  emailVerificationBaseUrl: `${window.location.origin}/auth/verify-email`,
  passwordResetBaseUrl: `${window.location.origin}/auth/reset-password`,
  maxLoginAttempts: 5,
  rateLimitWindow: 15 * 60 * 1000, // 15 minutes
};

/**
 * Injection token for auth configuration
 * Use this token to inject auth config in services and components
 */
export const AUTH_CONFIG = new InjectionToken<AuthConfig>('auth.config');

/**
 * Default auth configuration provider
 * Use this in app.config.ts:
 * 
 * ```typescript
 * import { authConfig } from '@auth';
 * 
 * export const appConfig: ApplicationConfig = {
 *   providers: [
 *     ...
 *     authConfig(),
 *     ...
 *   ]
 * };
 * ```
 */
export function authConfig(customConfig?: Partial<AuthConfig>) {
  return {
    provide: AUTH_CONFIG,
    useValue: {
      ...DEFAULT_AUTH_CONFIG,
      ...customConfig,
    } as AuthConfig,
  };
}

/**
 * Environment-specific configuration factory
 * Use this to provide different configs for dev/staging/prod
 * 
 * Example:
 * ```typescript
 * import { environment } from 'src/environments/environment';
 * import { getAuthConfigForEnvironment } from '@auth';
 * 
 * export const appConfig: ApplicationConfig = {
 *   providers: [
 *     ...
 *     getAuthConfigForEnvironment(environment),
 *     ...
 *   ]
 * };
 * ```
 */
export function getAuthConfigForEnvironment(env: any) {
  const baseConfig: Partial<AuthConfig> = {
    supabaseUrl: env['auth.supabaseUrl'],
    supabaseKey: env['auth.supabaseKey'],
    oauthRedirectUri: env['auth.oauthRedirectUri'] || DEFAULT_AUTH_CONFIG.oauthRedirectUri,
    emailVerificationBaseUrl: env['auth.emailVerificationBaseUrl'] || DEFAULT_AUTH_CONFIG.emailVerificationBaseUrl,
    passwordResetBaseUrl: env['auth.passwordResetBaseUrl'] || DEFAULT_AUTH_CONFIG.passwordResetBaseUrl,
  };

  const oauthProviders: OAuthProviderConfig[] = DEFAULT_AUTH_CONFIG.oauthProviders.map(provider => ({
    ...provider,
    clientId: env[`auth.oauth.${provider.name}.clientId`] || provider.clientId,
    enabled: env[`auth.oauth.${provider.name}.enabled`] !== false,
  }));

  return authConfig({
    ...baseConfig,
    oauthProviders,
  });
}

/**
 * Auth error messages
 */
export const AUTH_ERROR_MESSAGES = {
  INVALID_CREDENTIALS: 'Invalid email or password',
  USER_NOT_FOUND: 'User not found',
  USER_ALREADY_EXISTS: 'User already exists',
  EMAIL_NOT_VERIFIED: 'Please verify your email address',
  WEAK_PASSWORD: 'Password is too weak',
  SESSION_EXPIRED: 'Your session has expired. Please log in again.',
  UNAUTHORIZED: 'You are not authorized to perform this action',
  FORBIDDEN: 'Access denied',
  RATE_LIMIT_EXCEEDED: 'Too many attempts. Please try again later.',
  OAUTH_FAILED: 'OAuth authentication failed',
  TOKEN_REFRESH_FAILED: 'Failed to refresh token. Please log in again.',
  NETWORK_ERROR: 'Network error. Please check your connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
} as const;

/**
 * Auth success messages
 */
export const AUTH_SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Logged in successfully',
  LOGOUT_SUCCESS: 'Logged out successfully',
  REGISTRATION_SUCCESS: 'Registration successful',
  EMAIL_VERIFIED: 'Email verified successfully',
  PASSWORD_RESET_SENT: 'Password reset email sent',
  PASSWORD_RESET_SUCCESS: 'Password reset successfully',
  ROLE_ASSIGNED: 'Role assigned successfully',
  ROLE_REVOKED: 'Role revoked successfully',
} as const;

/**
 * Storage keys for auth data
 */
export const AUTH_STORAGE_KEYS = {
  CURRENT_USER: 'farmiq_current_user',
  ACCESS_TOKEN: 'farmiq_access_token',
  REFRESH_TOKEN: 'farmiq_refresh_token',
  TOKEN_EXPIRY: 'farmiq_token_expiry',
  OAUTH_STATE: 'farmiq_oauth_state',
} as const;

/**
 * Regular expressions for validation
 */
export const AUTH_REGEX = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^\+?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/,
  PASSWORD_STRONG: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
  URL: /^https?:\/\/.+/,
  ALPHA_NUMERIC: /^[a-zA-Z0-9]*$/,
} as const;

/**
 * HTTP status codes for auth
 */
export const AUTH_HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
} as const;
