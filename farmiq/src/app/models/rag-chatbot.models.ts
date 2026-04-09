/**
 * RAG CHATBOT MODELS
 * 
 * Models for the Retrieval Augmented Generation (RAG) chatbot system
 * Includes document ingestion, embeddings, conversations, and messages
 */

// ============================================================================
// DOCUMENT MODELS (RAG Document Ingestion)
// ============================================================================

/**
 * Document in the knowledge base
 */
export interface Document {
  id: string;
  title: string;
  content: string;
  
  // Document metadata
  document_type: 'guide' | 'article' | 'manual' | 'faq' | 'research' | 'other';
  category?: string;
  tags?: string[];
  
  // Source information
  source?: string;
  source_url?: string;
  author?: string;
  published_date?: string;
  
  // Processing info
  chunked: boolean;
  total_chunks?: number;
  
  // Status
  is_active: boolean;
  indexed_for_rag: boolean;
  indexed_at?: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Document chunk (split from document for embedding)
 */
export interface DocumentChunk {
  id: string;
  document_id: string;
  
  // Chunk content
  content: string;
  chunk_number: number;
  
  // Size info
  token_count?: number;
  character_count: number;
  
  // Vector embedding
  embedding_id?: string;
  embedding_model?: string; // e.g., 'all-MiniLM-L6-v2'
  has_embedding: boolean;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Document ingestion request (for adding documents to RAG)
 */
export interface DocumentIngestionRequest {
  title: string;
  content: string;
  document_type: string;
  category?: string;
  tags?: string[];
  source?: string;
  source_url?: string;
  author?: string;
  published_date?: string;
}

/**
 * Document ingestion response
 */
export interface DocumentIngestionResponse {
  success: boolean;
  document_id?: string;
  chunks_created?: number;
  embeddings_created?: number;
  message?: string;
  error?: string;
}

// ============================================================================
// EMBEDDING MODELS
// ============================================================================

/**
 * Vector embedding for a document chunk
 * Embeddings are 384-dimensional vectors (from all-MiniLM-L6-v2 model)
 */
export interface Embedding {
  id: string;
  chunk_id: string;
  document_id: string;
  
  // The actual embedding vector (384 dimensions)
  // Stored as array of numbers or pgvector format
  embedding: number[];
  
  // Embedding metadata
  embedding_model: string; // 'all-MiniLM-L6-v2'
  vector_size: number; // Should be 384
  
  // Indexing for search
  is_indexed: boolean;
  indexed_at?: string;
  
  // Timestamps
  created_at: string;
}

/**
 * Search query with embedding
 */
export interface SearchQuery {
  query_text: string;
  embedding?: number[]; // Will be generated from query_text
  similarity_threshold?: number; // Default 0.6
  max_results?: number; // Default 5
}

/**
 * Search result
 */
export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  content: string;
  
  // Relevance
  similarity_score: number; // 0-1, higher = more relevant
  rank: number; // 1 = most relevant
}

// ============================================================================
// CONVERSATION MODELS
// ============================================================================

/**
 * Conversation session (chat history)
 */
export interface Conversation {
  id: string;
  user_id: string;
  
  // Conversation info
  title: string;
  description?: string;
  
  // Participants
  participants: string[]; // User IDs in conversation
  
  // Status
  status: 'active' | 'archived' | 'closed';
  
  // Messages count
  message_count: number;
  last_message_at?: string;
  
  // Configuration
  model?: string; // LLM model used (e.g., 'gpt-3.5-turbo')
  system_prompt?: string;
  
  // Context/metadata
  context?: Record<string, any>;
  tags?: string[];
  
  // Timestamps
  created_at: string;
  updated_at: string;
  archived_at?: string;
}

/**
 * Conversation creation request
 */
export interface ConversationCreateRequest {
  title: string;
  description?: string;
  model?: string;
}

/**
 * Conversation update request
 */
export interface ConversationUpdateRequest {
  title?: string;
  description?: string;
  status?: 'active' | 'archived' | 'closed';
  tags?: string[];
}

/**
 * Conversation response
 */
export interface ConversationResponse {
  success: boolean;
  conversation?: Conversation;
  message?: string;
  error?: string;
}

// ============================================================================
// MESSAGE MODELS
// ============================================================================

/**
 * Message in a conversation
 */
export interface Message {
  id: string;
  conversation_id: string;
  
  // Sender info
  sender_id: string;
  sender_type: 'user' | 'assistant';
  
  // Message content
  content: string;
  
  // Message type
  message_type: 'text' | 'image' | 'document_reference' | 'system';
  
  // RAG context (for assistant messages)
  search_results?: SearchResult[];
  used_documents?: string[]; // Document IDs used for response
  
  // Message metadata
  tokens_used?: number;
  generation_time_ms?: number;
  
  // Response references
  response_to?: string; // ID of message this replies to
  
  // Edited status
  is_edited: boolean;
  edited_at?: string;
  
  // Reactions/feedback
  helpful?: boolean; // User feedback
  feedback_text?: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Message creation request
 */
export interface MessageCreateRequest {
  conversation_id: string;
  content: string;
  message_type?: 'text' | 'image' | 'document_reference';
  attachments?: MessageAttachment[];
}

/**
 * Message attachment (image, document reference, etc.)
 */
export interface MessageAttachment {
  type: 'image' | 'document' | 'link';
  url?: string;
  document_id?: string;
  content?: string;
}

/**
 * Message creation response
 */
export interface MessageCreateResponse {
  success: boolean;
  message?: Message;
  error?: string;
}

// ============================================================================
// RAG QUERY & RESPONSE
// ============================================================================

/**
 * RAG query request
 */
export interface RAGQueryRequest {
  query: string;
  conversation_id?: string; // Include previous context
  search_only?: boolean; // If true, only return search results, don't generate response
  max_search_results?: number;
  similarity_threshold?: number;
}

/**
 * RAG query response with LLM-generated answer
 */
export interface RAGResponse {
  success: boolean;
  
  // Generated response
  answer?: string;
  
  // Source information
  search_results: SearchResult[];
  sources: {
    document_id: string;
    document_title: string;
    chunks_used: string[];
  }[];
  
  // Metadata
  model_used?: string;
  generation_time_ms?: number;
  tokens_used?: number;
  
  // Confidence/reliability
  confidence_score?: number;
  
  // If there were issues
  error?: string;
  partial_results?: boolean;
}

/**
 * Streaming RAG response (for real-time chat)
 */
export interface RAGStreamEvent {
  type: 'search_complete' | 'chunk' | 'complete' | 'error';
  data: {
    chunk?: string; // For type='chunk'
    search_results?: SearchResult[]; // For type='search_complete'
    complete_response?: string; // For type='complete'
    error?: string; // For type='error'
  };
}

// ============================================================================
// CHATBOT CONFIGURATION
// ============================================================================

/**
 * Chatbot settings
 */
export interface ChatbotConfig {
  id: string;
  
  // Model configuration
  llm_model: string; // 'gpt-3.5-turbo', 'llama2', etc.
  embedding_model: string; // 'all-MiniLM-L6-v2'
  
  // RAG settings
  similarity_threshold: number;
  max_search_results: number;
  chunk_overlap: number; // For document chunking
  
  // Generation settings
  temperature: number; // 0-2, controls randomness
  max_tokens: number;
  top_p?: number;
  
  // System behavior
  system_prompt: string;
  
  // Restrictions
  restricted_topics?: string[];
  inappropriate_response_threshold?: number;
  
  // Features
  enable_search_results_display: boolean;
  enable_conversation_history: boolean;
  enable_feedback: boolean;
  enable_document_upload: boolean;
  
  // Performance
  cache_responses: boolean;
  cache_ttl_minutes?: number;
  
  // Updated by
  updated_by?: string;
  updated_at: string;
}

// ============================================================================
// CHATBOT USAGE & ANALYTICS
// ============================================================================

/**
 * Chatbot usage statistics
 */
export interface ChatbotUsageStats {
  id: string;
  
  // Time period
  date: string;
  
  // Usage metrics
  total_queries: number;
  total_conversations: number;
  active_users: number;
  
  // Performance
  avg_response_time_ms: number;
  avg_tokens_per_query: number;
  
  // Quality metrics
  user_satisfaction_score?: number;
  helpful_responses_percentage?: number;
  
  // Top queries
  top_queries?: string[];
  
  // Generated at
  generated_at: string;
}

/**
 * User feedback on chatbot response
 */
export interface ChatbotFeedback {
  id: string;
  message_id: string;
  conversation_id: string;
  user_id: string;
  
  // Feedback
  was_helpful: boolean;
  rating?: number; // 1-5
  comment?: string;
  
  // Feedback type
  feedback_type?: 'accuracy' | 'relevance' | 'completeness' | 'clarity' | 'other';
  
  // Timestamp
  created_at: string;
}
