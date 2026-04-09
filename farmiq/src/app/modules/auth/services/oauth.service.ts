import { Injectable, inject } from '@angular/core';
import { SupabaseService } from './supabase';
import { AuthRoleService } from './auth-role';

/**
 * OAuth Service - Unified OAuth handling for Google and GitHub
 * Standardizes OAuth flow and provider handling
 */
@Injectable({
  providedIn: 'root',
})
export class OAuthService {
  private supabase = inject(SupabaseService);
  private authRole = inject(AuthRoleService);

  // Supported OAuth providers
  private readonly OAUTH_PROVIDERS = {
    google: 'google',
    github: 'github',
  } as const;

  /**
   * Sign in/up with OAuth provider (Google or GitHub)
   * Initiates the OAuth flow and redirects to provider
   */
  async signInWithOAuth(provider: 'google' | 'github'): Promise<void> {
    if (!this.isValidProvider(provider)) {
      throw new Error(`Unsupported OAuth provider: ${provider}`);
    }

    try {
      const result = await this.initiateOAuthFlow(provider);
      if (result.url) {
        console.log(`🔗 Redirecting to ${provider.toUpperCase()} OAuth...`);
        window.location.href = result.url;
      } else {
        throw new Error(`No OAuth URL returned for ${provider}`);
      }
    } catch (error) {
      console.error(`${provider} OAuth error:`, error);
      throw error;
    }
  }

  /**
   * Initiate OAuth flow for the specified provider
   */
  private async initiateOAuthFlow(
    provider: 'google' | 'github'
  ): Promise<{ provider: string; url?: string }> {
    switch (provider) {
      case 'google':
        return this.supabase.signInWithGoogle();
      case 'github':
        return this.supabase.signInWithGitHub();
      default:
        throw new Error(`Unsupported provider: ${provider}`);
    }
  }

  /**
   * Detect OAuth provider from callback URL
   */
  async detectOAuthProvider(): Promise<
    { provider: 'google' | 'github'; email: string } | null
  > {
    try {
      const providerInfo = await this.supabase.getOAuthProviderInfo();

      if (
        providerInfo &&
        (providerInfo.provider === 'google' || providerInfo.provider === 'github')
      ) {
        // Get the current session to retrieve the user's email
        const session = await this.supabase.getSession();
        const email = session?.user?.email || '';

        return {
          provider: providerInfo.provider as 'google' | 'github',
          email,
        };
      }

      return null;
    } catch (error) {
      console.error('Error detecting OAuth provider:', error);
      return null;
    }
  }

  /**
   * Handle OAuth user profile creation
   */
  async setupOAuthProfile(
    userId: string | undefined,
    email: string | undefined,
    provider: 'google' | 'github',
    fullName?: string,
    avatarUrl?: string
  ): Promise<void> {
    if (!userId || !email) {
      throw new Error('User ID and email required for OAuth profile setup');
    }

    try {
      await this.supabase.createOAuthUserProfile(
        userId,
        email,
        provider,
        fullName,
        avatarUrl
      );
      console.log(`✅ OAuth profile created for ${provider} user`);
    } catch (error) {
      console.error(`Error setting up ${provider} profile:`, error);
      // Don't fail - user is authenticated, can proceed
      throw error;
    }
  }

  /**
   * Check if provider is valid
   */
  private isValidProvider(provider: string): provider is 'google' | 'github' {
    return provider === 'google' || provider === 'github';
  }

  /**
   * Get OAuth provider display name
   */
  getProviderDisplayName(provider: 'google' | 'github'): string {
    const names: Record<'google' | 'github', string> = {
      google: 'Google',
      github: 'GitHub',
    };
    return names[provider] || provider;
  }

  /**
   * Get OAuth provider icon/emoji
   */
  getProviderIcon(provider: 'google' | 'github'): string {
    const icons: Record<'google' | 'github', string> = {
      google: '🔍',
      github: '🐙',
    };
    return icons[provider] || '🔐';
  }
}
