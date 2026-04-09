/**
 * Vite plugin to inject environment variables from .env files
 * This plugin reads environment variables and injects them into the app
 */

import { Plugin } from 'vite';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

export function envInjectionPlugin(): Plugin {
  let config: any;

  return {
    name: 'env-injection-plugin',
    configResolved(resolvedConfig) {
      config = resolvedConfig;
    },
    transform(code: string, id: string) {
      // Load environment variables from .env files
      const envFiles = [
        path.resolve(process.cwd(), '.env'),
        path.resolve(process.cwd(), `.env.${process.env.NODE_ENV}`),
        path.resolve(process.cwd(), '.env.local'),
      ];

      let env: Record<string, string> = {};

      // Load in order (later files override earlier ones)
      for (const envFile of envFiles) {
        if (fs.existsSync(envFile)) {
          const envConfig = dotenv.config({ path: envFile });
          if (envConfig.parsed) {
            env = { ...env, ...envConfig.parsed };
          }
        }
      }

      // Filter for public env variables (VITE_ prefix is standard)
      // For farmiq, we'll include specific keys for security
      const publicEnv: Record<string, string> = {};
      const allowedKeys = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE',
        'API_URL',
        'AUTH_CALLBACK_URL',
        'AUTH_CALLBACK_FULL_URL',
        'AFRICAS_TALKING_API_KEY',
        'AFRICAS_TALKING_USERNAME',
        'AFRICAS_TALKING_SHORTCODE',
        'HEDERA_ACCOUNT_ID',
        'HEDERA_PRIVATE_KEY',
        'HEDERA_NETWORK',
        'HEDERA_CREDIT_SCORING_CONTRACT_ID',
        'HEDERA_FIQ_TOKEN_CONTRACT_ID',
        'HEDERA_MIRROR_NODE_URL',
        'METAMASK_ENABLED',
        'HASHPACK_ENABLED',
        'HASHPACK_NETWORK',
      ];

      for (const key of allowedKeys) {
        if (env[key]) {
          publicEnv[key] = env[key];
        }
      }

      // Only inject into main.ts and environment files
      if (id.includes('main.ts') || id.includes('environment')) {
        // Replace the globalThis.__ENV__ reference with actual values
        let transformedCode = code.replace(
          /globalThis\['__ENV__'\]/g,
          JSON.stringify(publicEnv)
        );

        return {
          code: transformedCode,
          map: null,
        };
      }

      return null;
    },
  };
}
