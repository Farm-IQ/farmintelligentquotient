/**
 * CENTRALIZED MODEL EXPORTS - ROOT MODELS
 * 
 * Exports core, shared models that are used across multiple modules.
 * Role-specific profile models are exported from their respective modules.
 * 
 * Import Map:
 * - Auth models (including UserProfile) → import from '@auth' (src/app/modules/auth/models)
 * - Admin profile → import from 'src/app/modules/admin/models'
 * - Agent profile → import from 'src/app/modules/agent/models'
 * - Cooperative profile → import from 'src/app/modules/cooperative/models'
 * - Farmer profile & livestock models → import from 'src/app/modules/farmer/models'
 * - Lender profile → import from 'src/app/modules/lender/models'
 * - Vendor profile → import from 'src/app/modules/vendor/models'
 * - Worker profile → import from 'src/app/modules/worker/models'
 */

// ============================================================================
// CORE SHARED MODELS (Root /models)
// ============================================================================

/**
 * RAG Chatbot models - Shared chatbot/AI models
 */
export * from './rag-chatbot.models';
