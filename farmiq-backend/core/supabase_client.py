"""
Supabase Client Module for FarmIQ Backend
Handles all Supabase database operations
"""
import os
from typing import Optional, List, Dict, Any
import logging

# Optional Supabase import - graceful degradation if not installed
try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    Client = None
    create_client = None

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Supabase client wrapper for FarmIQ backend
    Manages connections and operations to Supabase database
    """
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one Supabase client instance"""
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client with credentials from environment"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Supabase client with environment credentials or hardcoded fallbacks"""
        if not HAS_SUPABASE:
            logger.warning('⚠️ Supabase not installed. Running in degraded mode.')
            self._client = None
            return
            
        try:
            # Use environment variables with hardcoded fallbacks
            supabase_url = os.getenv('SUPABASE_URL') or 'https://faqunsqeomncgngjewyf.supabase.co'
            supabase_key = os.getenv('SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhcXVuc3Flb21uY2duZ2pld3lmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2ODIzOTQsImV4cCI6MjA4NTI1ODM5NH0.7wCHgdY0F7nIjdL7e6WNbkrMVSjpf3jCLgnofWsmG04'
            
            if not supabase_url or not supabase_key:
                logger.warning('⚠️ Supabase credentials not configured. Database operations will fail.')
                self._client = None
                return
            
            self._client = create_client(supabase_url, supabase_key)
            logger.info('✅ Supabase client initialized successfully')
        except TypeError as e:
            # Handle httpx/gotrue compatibility issue
            logger.warning(f'⚠️ Supabase client initialization skipped due to dependency compatibility: {str(e)}')
            self._client = None
        except Exception as e:
            logger.error(f'⚠️ Failed to initialize Supabase client: {str(e)}')
            self._client = None
    
    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client instance"""
        return self._client
    
    # ============================================================================
    # CONVERSATION OPERATIONS
    # ============================================================================
    
    async def create_conversation(self, user_id: Optional[str],
                                 title: Optional[str] = None,
                                 crop_type: Optional[str] = None,
                                 farm_location: Optional[str] = None,
                                 context: Optional[Dict] = None,
                                 conversation_type: str = "rag") -> Optional[Dict]:
        """
        Create a new conversation in Supabase
        
        Args:
            user_id: User ID for the conversation
            title: Conversation title
            crop_type: (Farmer-specific) Type of crop
            farm_location: (Farmer-specific) Farm location
            context: Additional context data
            conversation_type: Type of conversation (rag, support, etc)
        
        Returns:
            Conversation data dict with id, or None if failed
        """
        try:
            if not self._client:
                logger.warning('Supabase client not initialized')
                return None
            
            data = {
                'user_id': user_id,
                'context': context or {},
                'conversation_type': conversation_type,
                'title': title or 'New Conversation',
                'crop_type': crop_type,
                'farm_location': farm_location,
                'is_active': True
            }
            
            response = self._client.table('conversations').insert(data).execute()
            
            if response.data and len(response.data) > 0:
                conversation = response.data[0]
                logger.info(f'✅ Conversation created: {conversation.get("id")}')
                return conversation
            
            logger.warning('No conversation returned from Supabase')
            return None
            
        except Exception as e:
            logger.error(f'❌ Error creating conversation: {str(e)}')
            return None
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation details from Supabase"""
        try:
            if not self._client:
                return None
            
            response = self._client.table('conversations').select('*').eq('id', conversation_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f'❌ Error fetching conversation: {str(e)}')
            return None
    
    async def list_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """List conversations for a user from Supabase"""
        try:
            if not self._client:
                return []
            
            response = self._client.table('conversations').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f'❌ Error listing conversations: {str(e)}')
            return []
    
    # ============================================================================
    # MESSAGE OPERATIONS
    # ============================================================================
    
    async def add_message(self, conversation_id: str, role: str, 
                         content: str, metadata: Optional[Dict] = None) -> Optional[Dict]:
        """
        Add a message to conversation in Supabase
        
        Returns:
            Message data dict with id, or None if failed
        """
        try:
            if not self._client:
                logger.warning('Supabase client not initialized')
                return None
            
            data = {
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'metadata': metadata or {}
            }
            
            response = self._client.table('messages').insert(data).execute()
            
            if response.data and len(response.data) > 0:
                message = response.data[0]
                logger.info(f'✅ Message added: {message.get("id")}')
                return message
            
            return None
            
        except Exception as e:
            logger.error(f'❌ Error adding message: {str(e)}')
            return None
    
    async def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation from Supabase"""
        try:
            if not self._client:
                return []
            
            response = self._client.table('messages').select('*').eq('conversation_id', conversation_id).order('created_at', desc=False).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f'❌ Error fetching messages: {str(e)}')
            return []
    
    # ============================================================================
    # DOCUMENT OPERATIONS
    # ============================================================================
    
    async def store_document(self, file_name: str, file_path: str, 
                           content_type: str, user_id: Optional[str] = None) -> Optional[str]:
        """Store document metadata in Supabase"""
        try:
            if not self._client:
                return None
            
            data = {
                'file_name': file_name,
                'file_path': file_path,
                'content_type': content_type,
                'user_id': user_id,
                'status': 'uploaded'
            }
            
            response = self._client.table('documents').insert(data).execute()
            
            if response.data and len(response.data) > 0:
                doc_id = response.data[0]['id']
                logger.info(f'✅ Document stored: {doc_id}')
                return doc_id
            
            return None
            
        except Exception as e:
            logger.error(f'❌ Error storing document: {str(e)}')
            return None
    
    async def get_documents(self, limit: int = 100) -> List[Dict]:
        """Get all documents from Supabase"""
        try:
            if not self._client:
                return []
            
            response = self._client.table('documents').select('*').order('created_at', desc=True).limit(limit).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f'❌ Error fetching documents: {str(e)}')
            return []
    
    # ============================================================================
    # EMBEDDING OPERATIONS
    # ============================================================================
    
    async def store_embedding(self, document_id: str, chunk_id: str, 
                             chunk_text: str, embedding_vector: List[float],
                             metadata: Optional[Dict] = None) -> Optional[str]:
        """Store embedding in Supabase with pgvector extension"""
        try:
            if not self._client:
                return None
            
            data = {
                'document_id': document_id,
                'chunk_id': chunk_id,
                'chunk_text': chunk_text,
                'embedding': embedding_vector,  # pgvector handles this
                'metadata': metadata or {}
            }
            
            response = self._client.table('embeddings').insert(data).execute()
            
            if response.data and len(response.data) > 0:
                embedding_id = response.data[0]['id']
                logger.info(f'✅ Embedding stored: {embedding_id}')
                return embedding_id
            
            return None
            
        except Exception as e:
            logger.error(f'❌ Error storing embedding: {str(e)}')
            return None
    
    async def search_embeddings(self, query_vector: List[float], 
                               limit: int = 5, threshold: float = 0.5) -> List[Dict]:
        """Search embeddings using vector similarity in Supabase"""
        try:
            if not self._client:
                return []
            
            # Use Supabase RPC for pgvector similarity search
            response = self._client.rpc('search_embeddings', {
                'query_embedding': query_vector,
                'match_limit': limit,
                'match_threshold': threshold
            }).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f'❌ Error searching embeddings: {str(e)}')
            return []
    
    # ============================================================================
    # EDGE FUNCTION OPERATIONS
    # ============================================================================
    
    async def call_edge_function(self, function_name: str, payload: Dict[str, Any]) -> Optional[Dict]:
        """
        Call a Supabase edge function and return the response
        
        Args:
            function_name: Name of the edge function to call
            payload: Data to send to the function
        
        Returns:
            Response from the edge function or None if failed
        """
        import json
        
        try:
            if not self._client:
                logger.error('Supabase client not initialized')
                return None
            
            response = self._client.functions.invoke(
                function_name,
                invoke_options={
                    "body": json.dumps(payload)
                }
            )
            
            # Parse response - it may come as bytes or dict
            if isinstance(response, bytes):
                response = json.loads(response.decode('utf-8'))
            elif isinstance(response, str):
                response = json.loads(response)
            
            logger.info(f'✅ Edge function "{function_name}" called successfully')
            return response
            
        except Exception as e:
            logger.error(f'❌ Error calling edge function "{function_name}": {str(e)}')
            return None
    
    # ============================================================================
    # UTILITY OPERATIONS
    # ============================================================================
    
    def is_connected(self) -> bool:
        """Check if Supabase client is initialized"""
        return self._client is not None
    
    def health_check(self) -> bool:
        """Check Supabase connection health"""
        try:
            if not self._client:
                logger.error('❌ Supabase client not initialized')
                return False
            
            # Try a simple query to verify connection
            response = self._client.table('conversations').select('count').execute()
            logger.info('✅ Supabase connection healthy')
            return True
            
        except Exception as e:
            logger.error(f'❌ Supabase connection failed: {str(e)}')
            return False


# Singleton instance - Initialize with error handling
try:
    supabase_client = SupabaseClient()
except Exception as e:
    logger.warning(f'⚠️ Supabase client creation failed: {str(e)}, continuing with degraded mode')
    supabase_client = None
