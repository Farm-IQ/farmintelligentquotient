/**
 * PRODUCTION environment configuration
 * Uses environment variables injected at build time via __ENV__ global
 * 
 * Environment variables are provided through:
 * 1. Build-time injection (Vite env-injection plugin)
 * 2. Runtime globals (globalThis.__ENV__)
 * 3. Fallback to .env file values
 * 
 * Priority: Build-time env > Runtime globals > Fallback defaults
 */

export const environment = {
  production: true,
  
  // Supabase configuration - REMOTE PRODUCTION
  // Uses production instance
  supabase: {
    url: (globalThis as any)['__ENV__']?.SUPABASE_URL || 'https://faqunsqeomncgngjewyf.supabase.co',
    anonKey: (globalThis as any)['__ENV__']?.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcXVuc3Flb21uY2duZ2pld3lmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODIzOTQsImV4cCI6MjA4NTI1ODM5NH0.7wCHgdY0F7nIjdL7e6WNbkrMVSjpf3jCLgnofWsmG04',
    serviceRole: (globalThis as any)['__ENV__']?.SUPABASE_SERVICE_ROLE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcXVuc3Flb21uY2duZ2pld3lmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTY4MjM5NCwiZXhwIjoyMDg1MjU4Mzk0fQ.nwILhTuX10mUg9GtYl7oNLY7c-Y2a5Q9SJdT9w9GSz4',
    jwtSecret: (globalThis as any)['__ENV__']?.SUPABASE_JWT_SECRET || 'voOKdm0b1ifKIiXdYqNjnOPVUTaJS32qUC+mPr1CBFtoumq75nBar4PZrv+JeeKz+t9k2+BJB5apIQxncOTzfg==',
  },
  
  // API Configuration
  apiUrl: (globalThis as any)['__ENV__']?.API_URL || 'https://api.farmiq.com/api/',
  backendUrl: (globalThis as any)['__ENV__']?.BACKEND_URL || (globalThis as any)['__ENV__']?.API_URL || 'https://api.farmiq.com/api/',
  
  // OAuth Callback URLs
  authCallbackUrl: (globalThis as any)['__ENV__']?.AUTH_CALLBACK_URL || '/auth-callback',
  authCallbackFullUrl: (globalThis as any)['__ENV__']?.AUTH_CALLBACK_FULL_URL || 'https://farmiq.com/auth-callback',
  
  // Dashboard URL
  dashboardUrl: '/farmgrow',
  
  // Africa's Talking Configuration (SMS/USSD)
  africastalking: {
    apiKey: (globalThis as any)['__ENV__']?.AFRICAS_TALKING_API_KEY || '',
    username: (globalThis as any)['__ENV__']?.AFRICAS_TALKING_USERNAME || 'FarmIQ',
    shortcode: (globalThis as any)['__ENV__']?.AFRICAS_TALKING_SHORTCODE || '384',
  },
  
  // Hedera Configuration (Blockchain)
  hedera: {
    accountId: (globalThis as any)['__ENV__']?.HEDERA_ACCOUNT_ID || '',
    privateKey: (globalThis as any)['__ENV__']?.HEDERA_PRIVATE_KEY || '',
    network: ((globalThis as any)['__ENV__']?.HEDERA_NETWORK || 'mainnet') as 'mainnet' | 'testnet',
    creditScoringContractId: (globalThis as any)['__ENV__']?.HEDERA_CREDIT_SCORING_CONTRACT_ID || '',
    fiqTokenContractId: (globalThis as any)['__ENV__']?.HEDERA_FIQ_TOKEN_CONTRACT_ID || '',
    mirrorNodeUrl: (globalThis as any)['__ENV__']?.HEDERA_MIRROR_NODE_URL || 'https://mainnet.mirrornode.hedera.com',
  },
  
  // Wallet Configuration
  walletConfig: {
    metaMask: {
      enabled: true,
      chainIds: [1, 5, 11155111, 137, 80001, 42161, 421613],
    },
    hashpack: {
      enabled: true,
      network: ((globalThis as any)['__ENV__']?.HASHPACK_NETWORK || 'mainnet') as 'mainnet' | 'testnet',
    },
  },

  // GIS & Mapping Configuration
  gis: {
    // TomTom API Configuration
    tomtom: {
      // Custom TomTom style URL with embedded API key
      styleUrl: (globalThis as any)['__ENV__']?.TOMTOM_STYLE_URL || 
                'https://api.tomtom.com/style/2/custom/style/dG9tdG9tQEBAWkVqTm1wMzdMTjF0TXhxSzvGyUpBrM9MI6XioLrOOSsB/drafts/0.json?key=SXAULjM9GNVNoIO70Ng7UsFHirhRCeHM',
      apiKey: (globalThis as any)['__ENV__']?.TOMTOM_API_KEY || 'SXAULjM9GNVNoIO70Ng7UsFHirhRCeHM',
      baseUrl: 'https://api.tomtom.com',
      mapsApiVersion: '2',
    },
    // MapLibre GL Configuration
    maplibre: {
      // Uses TomTom vector tiles if API key is available, otherwise falls back to demo
      defaultCenter: [36.8219, -1.2921] as [number, number], // Nairobi
      defaultZoom: 13,
    },
  },
};
