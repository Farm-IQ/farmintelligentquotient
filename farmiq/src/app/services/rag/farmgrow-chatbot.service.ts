/**
 * FarmGrow RAG Chatbot Service
 * Integrates with the FastAPI backend at localhost:8000
 * Handles all RAG chatbot API calls
 */

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, Subject } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { v4 as uuidv4 } from 'uuid';
import { FarmiqIdService } from '../core/farmiq-id.service';

// Interfaces
export interface ChatRequest {
  conversation_id?: string;
  message: string;
  crop_type?: string;
  farm_location?: string;
  input_type?: 'text' | 'image' | 'audio';
  model?: string;  // Optional: specify which LLM to use
  stream?: boolean;  // Enable streaming for real-time responses
  top_k?: number;  // Number of documents to retrieve (default: 5)
  similarity_threshold?: number;  // Similarity threshold for retrieval (default: 0.3)
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  confidence: number;
  sources: DocumentSource[];
  processing_time_ms: number;
  timestamp: string;
  model_used: string;  // Which model generated this response
}

export interface DocumentSource {
  id: string;
  title: string;
  page?: number;
  similarity: number;
}

export interface Conversation {
  id: string;
  user_id?: string;
  title: string;
  started_at: string;
  last_message_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  messages: Message[];
}

export interface CorpusStatus {
  total_documents: number;
  indexed_documents: number;
  total_chunks: number;
  total_embeddings: number;
  last_sync?: string;
}

export interface ModelConfig {
  name: string;
  parameters: number;
  ram_required_gb: number;
  speed_tier: string;
  strengths: string[];
  use_case: string;
  quantization: string;
  context_length: number;
}

export interface AvailableModelsResponse {
  available_models: ModelConfig[];
  recommended_model: string;
  recommendations: Record<string, string>;
}

@Injectable({
  providedIn: 'root'
})
export class FarmGrowChatbotService {
  private apiUrl = 'http://localhost:8000/api/v1/farmgrow';  // Updated to correct endpoint
  private farmiqIdService = inject(FarmiqIdService);  // Inject FarmIQ ID service
  
  // State management
  private currentConversationId$ = new BehaviorSubject<string | null>(null);
  private messages$ = new BehaviorSubject<Message[]>([]);
  private isLoading$ = new BehaviorSubject<boolean>(false);
  private error$ = new BehaviorSubject<string | null>(null);
  private corpusStatus$ = new BehaviorSubject<CorpusStatus | null>(null);
  
  // Real-time events
  private newMessageEvent$ = new Subject<Message>();
  private conversationCreatedEvent$ = new Subject<Conversation>();

  constructor(private http: HttpClient) {
    this.initializeService();
  }

  private initializeService(): void {
    // Check if API is reachable
    this.checkApiHealth().subscribe(
      (health) => console.log('✅ FarmGrow API connected:', health),
      (error) => console.error('❌ FarmGrow API error:', error)
    );
  }

  /**
   * Generate a UUID v4 format string
   */
  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  /**
   * Health check endpoint
   */
  checkApiHealth(): Observable<any> {
    return this.http.get(`http://localhost:8000/health`);
  }

  /**
   * Chat endpoint - main RAG chatbot interaction
   * Supports both streaming (stream: true) and non-streaming responses
   * Authentication: Automatically handled via X-FarmIQ-ID header in interceptor
   */
  chat(request: ChatRequest): Observable<ChatResponse | any> {
    // Use unified /chat endpoint
    // Supports both streaming and non-streaming based on request.stream
    
    // Generate conversation ID if not provided
    if (!request.conversation_id) {
      request.conversation_id = uuidv4();
    }
    
    // Use streaming if enabled
    if (request.stream !== false) {
      return this.chatWithStream(request);
    }
    
    // Non-streaming mode
    return this.chatNonStreaming(request);
  }

  /**
   * Non-streaming chat using unified /chat endpoint
   */
  private chatNonStreaming(request: ChatRequest): Observable<ChatResponse> {
    this.isLoading$.next(true);

    // Get or generate FarmIQ ID
    let farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) {
      farmiqId = this.farmiqIdService.generateFarmiqId();
      sessionStorage.setItem('farmiq_id', farmiqId);
    }

    // Get or generate User ID
    let userId = sessionStorage.getItem('user_id');
    if (!userId) {
      userId = this.generateUUID();
      sessionStorage.setItem('user_id', userId);
    }

    // Build request body for unified /chat endpoint
    const payload = {
      query: request.message,  // Query text
      user_id: userId,
      conversation_id: request.conversation_id,
      input_type: request.input_type || 'text',
      stream: false,  // Non-streaming mode
      top_k: 5,
      similarity_threshold: 0.3,
      retrieval_method: 'hybrid'
    };

    // Build headers with FarmIQ ID
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'X-FarmIQ-ID': farmiqId
    });

    // Call unified /chat endpoint with stream=false
    return this.http.post<any>(`${this.apiUrl}/chat`, payload, { headers }).pipe(
      tap((response) => {
        this.isLoading$.next(false);
        this.currentConversationId$.next(request.conversation_id!);
        this.error$.next(null);
        
        // Map response to Message format
        const newMessage: Message = {
          id: response.message_id || this.generateUUID(),
          role: 'assistant',
          content: response.answer,
          confidence: response.confidence_score,
          created_at: new Date().toISOString()
        };
        
        // Update messages array
        const currentMessages = this.messages$.value;
        this.messages$.next([...currentMessages, newMessage]);
        
        // Emit message event
        this.newMessageEvent$.next(newMessage);
      }),
      catchError((error) => {
        this.isLoading$.next(false);
        const errorMessage = error.error?.detail || error.message || 'Chat failed';
        this.error$.next(errorMessage);
        console.error('Error in chat:', errorMessage);
        throw error;
      })
    );
  }

  /**
   * Streaming chat - tokens arrive in real-time using the unified /chat endpoint
   * Uses fetch API with ReadableStream to handle POST streaming
   */
  private chatWithStream(request: ChatRequest): Observable<any> {
    return new Observable((observer) => {
      this.isLoading$.next(true);
      this.currentConversationId$.next(request.conversation_id!);
      let fullResponse = '';
      let tokenCount = 0;
      
      // Get or generate FarmIQ ID
      let farmiqId = sessionStorage.getItem('farmiq_id');
      if (!farmiqId) {
        farmiqId = this.farmiqIdService.generateFarmiqId();
        sessionStorage.setItem('farmiq_id', farmiqId);
      }

      // Get or generate User ID
      let userId = sessionStorage.getItem('user_id');
      if (!userId) {
        userId = this.generateUUID();
        sessionStorage.setItem('user_id', userId);
      }

      // Build request payload for unified /chat endpoint with streaming
      const streamPayload = {
        query: request.message,
        user_id: userId,
        conversation_id: request.conversation_id,
        input_type: request.input_type || 'text',
        stream: true,  // Enable streaming in unified endpoint
        top_k: request.top_k || 5,
        similarity_threshold: request.similarity_threshold || 0.3
      };

      // Use fetch API with ReadableStream for POST streaming
      // This works with the unified /chat endpoint which requires POST
      fetch(`${this.apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-FarmIQ-ID': farmiqId
        },
        body: JSON.stringify(streamPayload)
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Get the response body as a ReadableStream
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        const processStream = async (): Promise<void> => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              // Decode chunk and append to buffer
              buffer += decoder.decode(value, { stream: true });

              // Process complete lines (server sends data\n format)
              const lines = buffer.split('\n');
              buffer = lines.pop() || ''; // Keep incomplete line in buffer

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const jsonStr = line.substring(6); // Remove 'data: ' prefix
                  if (jsonStr.trim()) {
                    try {
                      const data = JSON.parse(jsonStr);

                      if (data.status === 'started') {
                        console.log('Stream started:', data.query);
                        observer.next({
                          status: 'started',
                          query: data.query,
                          isStreaming: true
                        });
                      } else if (data.token) {
                        // Token received - append to response
                        fullResponse += data.token;
                        tokenCount++;

                        observer.next({
                          token: data.token,
                          fullResponse,
                          tokenCount,
                          isStreaming: true
                        });

                        // Log every 10 tokens
                        if (tokenCount % 10 === 0) {
                          console.log(`Streamed ${tokenCount} tokens...`);
                        }
                      } else if (data.status === 'complete') {
                        console.log('Stream complete:', data.tokens, 'tokens');
                        this.isLoading$.next(false);

                        // Create final message
                        const newMessage: Message = {
                          id: this.generateUUID(),
                          role: 'assistant',
                          content: fullResponse,
                          confidence: 0.85,
                          created_at: new Date().toISOString()
                        };

                        // Update messages
                        const currentMessages = this.messages$.value;
                        this.messages$.next([...currentMessages, newMessage]);

                        // Emit completion
                        observer.next({
                          status: 'complete',
                          fullResponse,
                          tokenCount: data.tokens,
                          isStreaming: false
                        });

                        observer.complete();
                      } else if (data.status === 'error') {
                        throw new Error(data.message || 'Unknown streaming error');
                      }
                    } catch (parseError) {
                      console.error('Error parsing JSON:', parseError, jsonStr);
                    }
                  }
                }
              }
            }
          } catch (error) {
            console.error('Stream processing error:', error);
            this.isLoading$.next(false);
            observer.error(error);
          }
        };

        processStream();
      })
      .catch((error) => {
        console.error('Fetch error:', error);
        this.isLoading$.next(false);
        const errorMessage = error.message || 'Streaming connection failed';
        this.error$.next(errorMessage);
        observer.error(error);
      });

      // Cleanup on unsubscribe (no-op since fetch doesn't have explicit abort here)
      return () => {
        // Stream will continue but observer is unsubscribed
      };
    });
  }

  /**
   * Upload documents for RAG ingestion
   */
  uploadDocuments(files: File[]): Observable<any> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('file', file);
    });

    // Get FarmIQ ID for header
    let farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) {
      farmiqId = this.farmiqIdService.generateFarmiqId();
      sessionStorage.setItem('farmiq_id', farmiqId);
    }

    const headers = new HttpHeaders({
      'X-FarmIQ-ID': farmiqId
    });

    return this.http.post(`${this.apiUrl}/upload`, formData, { headers }).pipe(
      tap((response) => {
        console.log('Documents uploaded:', response);
      }),
      catchError((error) => {
        this.error$.next(error.error?.detail || 'Upload failed');
        throw error;
      })
    );
  }

  /**
   * Get user conversations
   */
  getUserConversations(userId: string): Observable<any> {
    let farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) {
      farmiqId = this.farmiqIdService.generateFarmiqId();
      sessionStorage.setItem('farmiq_id', farmiqId);
    }

    const headers = new HttpHeaders({
      'X-FarmIQ-ID': farmiqId
    });

    return this.http.get(`${this.apiUrl}/conversations/${userId}`, { headers });
  }

  /**
   * Delete conversation
   */
  deleteConversation(conversationId: string, userId: string): Observable<any> {
    let farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) {
      farmiqId = this.farmiqIdService.generateFarmiqId();
      sessionStorage.setItem('farmiq_id', farmiqId);
    }

    const headers = new HttpHeaders({
      'X-FarmIQ-ID': farmiqId
    });

    return this.http.delete(`${this.apiUrl}/conversations/${conversationId}?user_id=${userId}`, { headers }).pipe(
      tap(() => {
        if (this.currentConversationId$.value === conversationId) {
          this.currentConversationId$.next(null);
          this.messages$.next([]);
        }
      })
    );
  }

  /**
   * Set messages array (for internal use)
   */
  setMessages(messages: Message[]): void {
    this.messages$.next(messages);
  }

  /**
   * Clear error message
   */
  clearError(): void {
    this.error$.next(null);
  }

  // ===== Observables for component subscription =====

  get currentConversationId(): Observable<string | null> {
    return this.currentConversationId$.asObservable();
  }

  get messages(): Observable<Message[]> {
    return this.messages$.asObservable();
  }

  get isLoading(): Observable<boolean> {
    return this.isLoading$.asObservable();
  }

  get error(): Observable<string | null> {
    return this.error$.asObservable();
  }

  get corpusStatus(): Observable<CorpusStatus | null> {
    return this.corpusStatus$.asObservable();
  }

  get newMessage$(): Observable<Message> {
    return this.newMessageEvent$.asObservable();
  }

  get conversationCreated$(): Observable<Conversation> {
    return this.conversationCreatedEvent$.asObservable();
  }

  // ===== Utility methods =====

  private getUserId(): string {
    // Generate or retrieve user ID from localStorage
    let userId = localStorage.getItem('farmiq_user_id');
    if (!userId) {
      userId = `farmer_${uuidv4()}`;
      localStorage.setItem('farmiq_user_id', userId);
    }
    return userId;
  }

  getCurrentConversationIdValue(): string | null {
    return this.currentConversationId$.value;
  }

  getCurrentMessagesValue(): Message[] {
    return this.messages$.value;
  }

  // ===== Model Management Methods =====

  /**
   * Get available models
   */
  getAvailableModels(): Observable<any> {
    let farmiqId = sessionStorage.getItem('farmiq_id');
    if (!farmiqId) {
      farmiqId = this.farmiqIdService.generateFarmiqId();
      sessionStorage.setItem('farmiq_id', farmiqId);
    }

    const headers = new HttpHeaders({
      'X-FarmIQ-ID': farmiqId
    });

    return this.http.get(`${this.apiUrl}/models`, { headers }).pipe(
      tap((response) => {
        console.log('Available models:', response);
      }),
      catchError((error) => {
        console.error('Error fetching models:', error);
        throw error;
      })
    );
  }

  /**
   * Send a chat message with optional model specification
   * @param message - The user message
   * @param cropType - Optional crop type for context
   * @param farmLocation - Optional farm location for context
   * @param modelName - Optional specific model to use
   * @returns Observable of chat response
   */
  sendMessageWithModel(
    message: string,
    cropType?: string,
    farmLocation?: string,
    modelName?: string
  ): Observable<ChatResponse> {
    const conversationId = this.currentConversationId$.value || this.generateConversationId();
    
    const request: ChatRequest = {
      conversation_id: conversationId,
      message,
      crop_type: cropType,
      farm_location: farmLocation,
      input_type: 'text',
      model: modelName
    };

    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, request).pipe(
      tap((response) => {
        if (!this.currentConversationId$.value) {
          this.currentConversationId$.next(conversationId);
        }

        // Add assistant message to local state
        const assistantMessage: Message = {
          id: response.message_id,
          role: 'assistant',
          content: response.response,
          confidence: response.confidence,
          created_at: response.timestamp
        };

        const currentMessages = this.messages$.value;
        this.messages$.next([...currentMessages, assistantMessage]);
        this.newMessageEvent$.next(assistantMessage);
        
        console.log(`✅ Response from model [${response.model_used}]:`, response);
      }),
      catchError((error) => {
        this.error$.next('Failed to send message');
        console.error('Chat error:', error);
        throw error;
      })
    );
  }

  private generateConversationId(): string {
    return `conv_${uuidv4()}`;
  }
}
