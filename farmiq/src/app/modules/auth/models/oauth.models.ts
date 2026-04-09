/**
 * OAuth Module Models
 * OAuth provider types and flow models
 */

export type OAuthProvider = 'google' | 'github';

export interface OAuthConfig {
  provider: OAuthProvider;
  redirectUrl: string;
  scopes: string[];
}

export interface OAuthProviderInfo {
  provider: OAuthProvider;
  email: string;
  displayName?: string;
  avatarUrl?: string;
}

export interface OAuthLoginResult {
  success: boolean;
  provider: OAuthProvider;
  url?: string;
  error?: string;
}

export interface OAuthUserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  provider: OAuthProvider;
  providerUserId: string;
  avatarUrl?: string;
  createdAt: Date;
}
