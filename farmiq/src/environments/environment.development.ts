/**
 * DEVELOPMENT environment configuration
 * Uses LOCAL Supabase instance at 127.0.0.1:54321
 * 
 * Environment variables are loaded from:
 * 1. Build-time injection via __ENV__ global
 * 2. Runtime globals (globalThis.__ENV__)
 * 3. .env.local file (via Vite)
 * 
 * For local development, ensure your local Supabase is running:
 * $ supabase start
 * 
 * Local Supabase services:
 * - Studio: http://127.0.0.1:54323
 * - REST API: http://127.0.0.1:54321/rest/v1
 * - GraphQL: http://127.0.0.1:54321/graphql/v1
 * - Mailpit: http://127.0.0.1:54324
 * - Database: postgresql://postgres:postgres@127.0.0.1:54322/postgres
 */

export const environment = {
  production: false,
  
  // Supabase configuration - PRODUCTION INSTANCE FOR OAUTH (even in dev)
  // Use production Supabase for OAuth since local instance doesn't have OAuth providers configured
  supabase: {
    url: (globalThis as any)['__ENV__']?.SUPABASE_URL || 'https://faqunsqeomncgngjewyf.supabase.co',
    anonKey: (globalThis as any)['__ENV__']?.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcXVuc3Flb21uY2duZ2pld3lmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODIzOTQsImV4cCI6MjA4NTI1ODM5NH0.7wCHgdY0F7nIjdL7e6WNbkrMVSjpf3jCLgnofWsmG04',
    serviceRole: (globalThis as any)['__ENV__']?.SUPABASE_SERVICE_ROLE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcXVuc3Flb21uY2duZ2pld3lmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTY4MjM5NCwiZXhwIjoyMDg1MjU4Mzk0fQ.nwILhTuX10mUg9GtYl7oNLY7c-Y2a5Q9SJdT9w9GSz4',
    jwtSecret: (globalThis as any)['__ENV__']?.SUPABASE_JWT_SECRET || 'voOKdm0b1ifKIiXdYqNjnOPVUTaJS32qUC+mPr1CBFtoumq75nBar4PZrv+JeeKz+t9k2+BJB5apIQxncOTzfg==',
  },
  
  // API Configuration - Local backend
  apiUrl: (globalThis as any)['__ENV__']?.API_URL || 'http://localhost:8000/',
  backendUrl: (globalThis as any)['__ENV__']?.BACKEND_URL || (globalThis as any)['__ENV__']?.API_URL || 'http://localhost:8000/',
  
  // OAuth Callback URLs - Using Supabase production hosted callback
  // Development uses production Supabase for OAuth support
  authCallbackUrl: (globalThis as any)['__ENV__']?.AUTH_CALLBACK_URL || '/auth-callback',
  authCallbackFullUrl: (globalThis as any)['__ENV__']?.AUTH_CALLBACK_FULL_URL || 'https://faqunsqeomncgngjewyf.supabase.co/auth/v1/callback',
  
  // Dashboard URL
  dashboardUrl: '/farmgrow',
  
  // Africa's Talking Configuration (Sandbox for development)
  africastalking: {
    apiKey: (globalThis as any)['__ENV__']?.AFRICAS_TALKING_API_KEY || 'atsk_4a5f8a5c76737fa8027e4f80d9e5de311bc4ff1237c0d6a836b9875bcfe370f7215de8bd',
    username: (globalThis as any)['__ENV__']?.AFRICAS_TALKING_USERNAME || 'Sandbox',
    shortcode: (globalThis as any)['__ENV__']?.AFRICAS_TALKING_SHORTCODE || '384',
  },
  
  // Hedera Configuration (Testnet for development)
  hedera: {
    accountId: (globalThis as any)['__ENV__']?.HEDERA_ACCOUNT_ID || '',
    privateKey: (globalThis as any)['__ENV__']?.HEDERA_PRIVATE_KEY || '',
    network: ((globalThis as any)['__ENV__']?.HEDERA_NETWORK || 'testnet') as 'mainnet' | 'testnet',
    creditScoringContractId: (globalThis as any)['__ENV__']?.HEDERA_CREDIT_SCORING_CONTRACT_ID || '',
    fiqTokenContractId: (globalThis as any)['__ENV__']?.HEDERA_FIQ_TOKEN_CONTRACT_ID || '',
    mirrorNodeUrl: (globalThis as any)['__ENV__']?.HEDERA_MIRROR_NODE_URL || 'https://testnet.mirrornode.hedera.com',
  },
  
  // Wallet Configuration (Testnet for development)
  walletConfig: {
    metaMask: {
      enabled: true,
      chainIds: [1, 5, 11155111, 137, 80001, 42161, 421613],
    },
    hashpack: {
      enabled: true,
      network: ((globalThis as any)['__ENV__']?.HASHPACK_NETWORK || 'testnet') as 'mainnet' | 'testnet',
    },
  },

  // GIS & Mapping Configuration
  gis: {
    // TomTom API Configuration (Development)
    tomtom: {
      // Custom TomTom style URL with embedded API key
      styleUrl: (globalThis as any)['__ENV__']?.TOMTOM_STYLE_URL || 
                'https://api.tomtom.com/style/2/custom/style/dG9tdG9tQEBAWkVqTm1wMzdMTjF0TXhxSzvGyUpBrM9MI6XioLrOOSsB/drafts/0.json?key=SXAULjM9GNVNoIO70Ng7UsFHirhRCeHM',
      
      // TomTom API key
      apiKey: (globalThis as any)['__ENV__']?.TOMTOM_API_KEY || 'SXAULjM9GNVNoIO70Ng7UsFHirhRCeHM',
      baseUrl: 'https://api.tomtom.com',
      mapsApiVersion: '2',
    },
    // MapLibre GL Configuration
    maplibre: {
      style: 'https://demotiles.maplibre.org/style.json',
      defaultCenter: [36.8219, -1.2921] as [number, number], // Nairobi
      defaultZoom: 13,
    },
  },
};
