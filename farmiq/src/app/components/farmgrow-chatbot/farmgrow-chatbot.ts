import { Component, OnInit, ViewChild, ElementRef, OnDestroy, inject, SecurityContext } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators, FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { trigger, transition, style, animate } from '@angular/animations';
import { Router } from '@angular/router';
import { FarmGrowChatbotService, Message as ServiceMessage } from '../../services/rag/farmgrow-chatbot.service';
import { RAGManagementService, RAGConversation } from '../../services/rag/rag-management.service';
import { EmbeddingStorageService } from '../../services/rag/embedding-storage.service';
import { AuthRoleService } from '../../modules/auth/services/auth-role';
import { Subscription, Subject } from 'rxjs';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  displayTime?: string;  // Pre-formatted time string (immutable)
  confidence?: number;
  created_at?: string;
}

@Component({
  selector: 'app-farmgrow-chatbot',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './farmgrow-chatbot.html',
  styleUrls: ['./farmgrow-chatbot.scss'],
  animations: [
    trigger('slideDown', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('slideIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class FarmgrowChatbotComponent implements OnInit, OnDestroy {
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  private router = inject(Router);
  private authRoleService = inject(AuthRoleService);
  private ragService = inject(RAGManagementService);
  private embeddingService = inject(EmbeddingStorageService);
  private destroy$ = new Subject<void>();

  chatForm!: FormGroup;
  messages: Message[] = [];
  isLoading = false;
  error: any = null;
  isFormValid = false;
  
  currentConversationId: string | null = null;
  currentConversation: RAGConversation | null = null;
  
  // Request cancellation
  private currentRequest$: Subscription | null = null;

  // Form options
  cropTypes = [
    'Maize (Corn)',
    'Beans',
    'Wheat',
    'Cabbage',
    'Tomato',
    'Coffee',
    'Tea',
    'Mango',
    'Avocado',
    'Banana',
    'Sugarcane',
    'Sorghum',
    'Millet',
    'Potato',
    'Onion',
    'Chili Pepper'
  ];

  farmRegions = [
    'Central Kenya',
    'Eastern Kenya',
    'Western Kenya',
    'Nairobi Region',
    'Coast Region',
    'Rift Valley',
    'North Eastern Kenya'
  ];

  inputTypes = [
    { value: 'text', label: 'Text Question' },
    { value: 'audio', label: 'Voice Question' },
    { value: 'image', label: 'Image with Question' }
  ];

  // Model selection
  availableModels: any[] = [];
  selectedModel: string = '';

  constructor(
    private fb: FormBuilder,
    private chatbotService: FarmGrowChatbotService,
    private sanitizer: DomSanitizer
  ) {
    this.initializeForm();
  }

  ngOnInit(): void {
    this.subscribeToService();
    this.loadAvailableModels();
    this.initializeConversation();
  }

  ngOnDestroy(): void {
    this.cancelRequest();
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize the reactive form
   */
  private initializeForm(): void {
    this.chatForm = this.fb.group({
      message: [{ value: '', disabled: false }, [Validators.required, Validators.minLength(3), Validators.maxLength(500)]]
    });

    // Watch for form changes to update validation state
    this.chatForm.statusChanges.subscribe(() => {
      this.isFormValid = this.chatForm.valid && !this.isLoading;
    });
  }

  /**
   * Subscribe to service observables
   */
  private subscribeToService(): void {
    this.chatbotService.messages.subscribe(messages => {
      this.messages = messages.map(msg => {
        const timestamp = new Date(msg.created_at);
        return {
          id: msg.id || '',
          content: msg.content,
          role: msg.role as 'user' | 'assistant',
          timestamp,
          displayTime: this.formatTime(timestamp),  // Pre-format time (immutable)
          confidence: msg.confidence
        };
      });
      this.scrollToBottom();
    });

    this.chatbotService.isLoading.subscribe(loading => {
      this.isLoading = loading;
      this.isFormValid = this.chatForm.valid && !this.isLoading;
      // Enable/disable the message control based on loading state
      const messageControl = this.chatForm.get('message');
      if (messageControl) {
        if (loading) {
          messageControl.disable();
        } else {
          messageControl.enable();
        }
      }
      if (loading) this.scrollToBottom();
    });

    this.chatbotService.error.subscribe((error: string | null) => {
      if (error) {
        this.error = {
          title: 'Error',
          message: error
        };
      } else {
        this.error = null;
      }
    });
  }

  /**
   * Submit the chat message
   */
  onSubmit(): void {
    const messageControl = this.chatForm.get('message');
    if (!messageControl || messageControl.invalid || this.isLoading) return;

    const message = messageControl.value.trim();
    if (!message) return;

    // Clear input FIRST to prevent double submission
    this.chatForm.reset();
    this.isFormValid = false;
    this.isLoading = true;

    // Create user message
    const now = new Date();
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: 'user',
      timestamp: now,
      displayTime: this.formatTime(now),  // Pre-format time
      created_at: now.toISOString()
    };
    
    // Add user message to display (single point of truth)
    this.addMessageToDisplay(userMessage);
    
    // Save user message to database (async, non-blocking)
    this.saveMessageToDatabase('user', message).catch(err => 
      console.warn('Failed to save user message:', err)
    );

    // Send to service with streaming enabled ⚡
    const chatRequest: any = {
      message,
      query: message,
      input_type: 'text',
      stream: true  // ⚡ Enable streaming for real-time responses
    };
    
    // Add model if one is selected
    if (this.selectedModel) {
      chatRequest.model = this.selectedModel;
    }

    // Create placeholder for AI response
    const aiNow = new Date();
    const aiMessageId = Date.now().toString() + '_ai';
    const aiMessage: Message = {
      id: aiMessageId,
      content: '',  // Will be filled with streaming tokens
      role: 'assistant',
      timestamp: aiNow,
      displayTime: this.formatTime(aiNow),  // Pre-format time
      created_at: aiNow.toISOString(),
      confidence: 0
    };
    this.addMessageToDisplay(aiMessage);

    // Handle streaming response with proper token accumulation
    this.currentRequest$ = this.chatbotService.chat(chatRequest).subscribe({
      next: (response: any) => {
        // Handle streaming tokens
        if (response.isStreaming) {
          if (response.token) {
            // Token arrived - update last AI message content
            const messages = [...this.messages];
            const lastMessageIndex = messages.length - 1;
            
            if (lastMessageIndex >= 0 && messages[lastMessageIndex].role === 'assistant') {
              // Update with full accumulated response
              messages[lastMessageIndex].content = response.fullResponse || '';
              
              // Show token count during streaming
              if (response.tokenCount) {
                messages[lastMessageIndex].confidence = response.tokenCount / 100; // Rough progress indicator
              }
              
              this.messages = [...messages];
              this.scrollToBottom();
            }
          }
        }
        
        // When streaming complete
        if (response.status === 'complete' || !response.isStreaming) {
          this.currentRequest$ = null;
          this.isLoading = false;
          
          // Update final message with completion info
          const messages = [...this.messages];
          const lastMessageIndex = messages.length - 1;
          if (lastMessageIndex >= 0 && messages[lastMessageIndex].role === 'assistant') {
            messages[lastMessageIndex].confidence = 0.95; // Mark as complete
            
            // Save AI response to database (async, non-blocking)
            const aiResponse = messages[lastMessageIndex].content;
            this.saveMessageToDatabase('assistant', aiResponse).catch(err => 
              console.warn('Failed to save AI message:', err)
            );
          }
          this.messages = [...messages];
          
          this.scrollToBottom();
        }
      },
      error: (error: any) => {
        this.isLoading = false;
        
        // Remove placeholder on error and show error message
        const messages = this.messages.filter(m => m.id !== aiMessageId);
        this.messages = messages;
        
        // Don't show error if request was cancelled by user
        if (error.name !== 'AbortError') {
          this.error = {
            title: 'Error',
            message: error.error?.detail || error.message || 'Failed to send message'
          };
          console.error('Chat error:', error);
        }
        this.currentRequest$ = null;
      }
    });
  }

  /**
   * Send a sample message from intro suggestions
   */
  sendSampleMessage(message: string): void {
    this.chatForm.patchValue({ message });
    setTimeout(() => this.onSubmit(), 100);
  }

  /**
   * Add message to display array
   */
  private addMessageToDisplay(message: Message): void {
    this.messages = [...this.messages, message];
    this.scrollToBottom();
  }

  /**
   * Format time for display
   */
  formatTime(date: Date): string {
    if (!date) return '';
    const now = new Date();
    const messageDate = new Date(date);
    const diffMs = now.getTime() - messageDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return messageDate.toLocaleDateString();
  }

  /**
   * Handle file upload
   */
  openMediaUpload(): void {
    this.fileInput?.nativeElement?.click();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'audio/mpeg', 'audio/wav'];
    if (!validTypes.includes(file.type)) {
      this.error = {
        title: 'Invalid File',
        message: 'Please upload an image (JPG, PNG, GIF) or audio (MP3, WAV) file'
      };
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      this.error = {
        title: 'File Too Large',
        message: 'File must be less than 5MB'
      };
      return;
    }

    // Process file (for now, just show it was received)
    const fileName = file.name;
    const fileType = file.type.startsWith('image') ? 'Image' : 'Audio';
    const messageText = `[${fileType}: ${fileName}] - Please analyze this`;

    this.chatForm.patchValue({ message: messageText });
    this.onSubmit();

    // Reset file input
    input.value = '';
  }

  /**
   * Clear all messages
   */
  clearMessages(): void {
    if (confirm('Clear all messages?')) {
      this.messages = [];
      this.chatForm.reset();
      this.chatbotService.clearError();
    }
  }

  /**
   * Start new conversation
   */
  startNewConversation(): void {
    this.clearMessages();
    this.currentConversationId = null;
  }

  /**
   * Delete current conversation
   */
  deleteConversation(): void {
    if (!this.currentConversationId) return;
    if (!confirm('Delete this conversation?')) return;

    const userId = sessionStorage.getItem('user_id') || 'unknown';
    this.chatbotService.deleteConversation(this.currentConversationId, userId).subscribe({
      next: () => {
        this.messages = [];
        this.currentConversationId = null;
        this.error = null;
      },
      error: (error: any) => {
        this.error = {
          title: 'Error',
          message: 'Failed to delete conversation'
        };
      }
    });
  }

  /**
   * Cancel the current API request
   */
  cancelRequest(): void {
    if (this.currentRequest$) {
      this.currentRequest$.unsubscribe();
      this.currentRequest$ = null;
    }
    this.isLoading = false;
    this.isFormValid = this.chatForm.valid;
    this.chatbotService.clearError();
  }

  /**
   * Scroll messages container to bottom
   */
  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesContainer) {
        const element = this.messagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }

  /**
   * Go back to role-specific dashboard
   */
  goBackToDashboard(): void {
    const currentRole = this.authRoleService.getCurrentRole();
    if (currentRole) {
      this.authRoleService.navigateToRoleDashboard(currentRole);
    } else {
      // Fallback to login if no role is available
      this.router.navigateByUrl('/login');
    }
  }

  /**
   * Load available models from the backend
   */
  private loadAvailableModels(): void {
    this.chatbotService.getAvailableModels().subscribe({
      next: (response: any) => {
        this.availableModels = response.available_models || [];
        // Set the recommended model as default
        if (response.recommended_model) {
          this.selectedModel = response.recommended_model;
        }
        console.log('📊 Available models loaded:', this.availableModels);
      },
      error: (error) => {
        console.error('Failed to load available models:', error);
        // Continue without model selection if it fails
      }
    });
  }

  /**
   * Handle model change event
   */
  onModelChange(): void {
    if (this.selectedModel) {
      console.log('Selected model:', this.selectedModel);
      // Model can be passed in chat request via ChatRequest.model property
      // No need for separate model switch endpoint
    }
  }

  /**
   * Initialize or load conversation using RAGManagementService
   * This replaces the old manage-rag edge function approach
   */
  private async initializeConversation(): Promise<void> {
    try {
      // Check if conversation ID exists in session
      const savedConvId = sessionStorage.getItem('conversation_id');
      
      if (savedConvId) {
        // Load existing conversation with all messages
        const conv = await this.ragService.getConversation(savedConvId);
        this.currentConversation = conv;
        this.currentConversationId = conv.id;
        console.log('✅ Loaded conversation:', conv.title);
      } else {
        // Create new conversation
        const conv = await this.ragService.createConversation('New Farm Chat');
        this.currentConversation = conv;
        this.currentConversationId = conv.id;
        sessionStorage.setItem('conversation_id', conv.id);
        console.log('✅ Created conversation:', conv.id);
      }
      
      // Subscribe to real-time message updates (NEW feature!)
      this.subscribeToRealtimeMessages();
    } catch (error) {
      console.error('Failed to initialize conversation:', error);
      this.error = {
        title: 'Error',
        message: 'Failed to initialize chat conversation'
      };
    }
  }

  /**
   * Subscribe to real-time message updates
   * This was NOT possible with edge functions - NEW feature!
   */
  private subscribeToRealtimeMessages(): void {
    if (!this.currentConversationId) return;

    this.ragService.subscribeToMessages(this.currentConversationId)
      .pipe()
      .subscribe({
        next: (messages) => {
          console.log('📨 Real-time messages updated:', messages.length);
          // Messages automatically update in real-time
        },
        error: (error) => {
          console.error('Real-time subscription error:', error);
          // Fallback to polling if subscription fails
        }
      });
  }

  /**
   * Save message to database using RAGManagementService
   * This replaces calls to manage-rag edge function
   */
  private async saveMessageToDatabase(role: 'user' | 'assistant', content: string): Promise<void> {
    if (!this.currentConversationId) return;

    try {
      const message = await this.ragService.addMessage(
        this.currentConversationId,
        role,
        content
      );
      console.log('✅ Message saved:', message.id);
    } catch (error) {
      console.error('Failed to save message:', error);
      // Don't show error to user - chat still works even if DB save fails
    }
  }

  /**
   * Get conversation history from database
   */
  async getConversationHistory(): Promise<void> {
    if (!this.currentConversationId) return;

    try {
      const conv = await this.ragService.getConversation(this.currentConversationId);
      this.currentConversation = conv;
      console.log('✅ Loaded conversation history:', conv.messages?.length, 'messages');
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  }

  /**
   * Copy message to clipboard
   */
  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      // Show brief feedback
      console.log('✅ Copied to clipboard');
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  }

  /**
   * Dismiss error message
   */
  dismissError(): void {
    this.error = null;
  }

  /**
   * Render markdown content as safe HTML
   * Converts **bold**, *italic*, and line breaks to HTML
   */
  renderMarkdown(text: string): SafeHtml {
    if (!text) return this.sanitizer.bypassSecurityTrustHtml('');
    
    let html = text
      // Escape HTML special characters first
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      // Bold: **text** or __text__
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.+?)__/g, '<strong>$1</strong>')
      // Italic: *text* or _text_ (but not in code)
      .replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
      .replace(/_([^_\n]+?)_/g, '<em>$1</em>')
      // Code blocks: ```code```
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      // Inline code: `code`
      .replace(/`([^`]+?)`/g, '<code>$1</code>')
      // Line breaks - handle double newlines first
      .replace(/\n\n+/g, '</p><p>')
      .replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags
    html = '<p>' + html + '</p>';
    
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}