"""
FarmGrow Conversation Management Service
Manages RAG chatbot conversations and message history.
Primary storage: Supabase | Fallback: In-memory for development
"""
import logging
import uuid
import os
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Represents a single message in conversation"""
    id: str
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    input_type: str = 'text'  # 'text', 'image', 'file'
    retrieved_chunks: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Conversation:
    """Represents a conversation"""
    id: str
    user_id: Optional[str]
    title: str
    conversation_type: str
    context: Dict
    messages: List[Dict]
    is_active: bool
    started_at: str
    last_message_at: str
    created_at: str


class ConversationService:
    """
    Manage RAG chatbot conversations and message history.
    
    Features:
    - Create new conversations
    - Add messages to conversations
    - Retrieve conversation history
    - Update conversation metadata
    - Delete conversations
    - Fallback to in-memory storage
    """
    
    def __init__(self, supabase_client=None):
        """
        Initialize conversation service
        
        Args:
            supabase_client: Optional Supabase client for persistence
        """
        self.supabase = supabase_client
        self.use_supabase = supabase_client is not None and os.getenv('CONVERSATION_STORAGE', 'memory') == 'supabase'
        
        # In-memory fallback storage
        self.conversations_cache: Dict[str, Dict] = {}
        self.messages_cache: Dict[str, List[Dict]] = {}
        
        if self.use_supabase:
            logger.info("✅ Using Supabase for conversation storage")
        else:
            logger.info("⚠️ Using in-memory storage for conversations (development mode)")
    
    async def create_conversation(self,
                                 user_id: Optional[str] = None,
                                 title: Optional[str] = None,
                                 context: Optional[Dict] = None,
                                 conversation_type: str = "agronomy") -> str:
        """
        Create a new conversation.
        
        Args:
            user_id: Optional user ID
            title: Optional conversation title
            context: Conversation context (crop_type, location, etc.)
            conversation_type: Type of conversation (agronomy, loan, etc.)
        
        Returns:
            Conversation ID
        """
        try:
            conversation_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "conversation_type": conversation_type,
                "context": context or {},
                "is_active": True,
                "started_at": now,
                "last_message_at": now,
                "created_at": now,
                "messages": []
            }
            
            # Try Supabase first
            if self.use_supabase and self.supabase:
                try:
                    result = await self.supabase.create_conversation(
                        user_id=user_id,
                        title=conversation['title'],
                        context=context,
                        conversation_type=conversation_type
                    )
                    
                    if result:
                        logger.info(f"✅ Conversation created in Supabase: {conversation_id}")
                        return result
                except Exception as e:
                    logger.warning(f"Supabase creation failed: {str(e)}, falling back to in-memory")
            
            # Fallback to in-memory
            self.conversations_cache[conversation_id] = conversation
            self.messages_cache[conversation_id] = []
            
            logger.info(f"✅ Conversation created (in-memory): {conversation_id}")
            return conversation_id
        
        except Exception as e:
            logger.error(f"❌ Error creating conversation: {str(e)}")
            raise
    
    async def add_message(self,
                         conversation_id: str,
                         role: str,
                         content: str,
                         input_type: str = "text",
                         retrieved_chunks: Optional[List[str]] = None,
                         confidence_score: Optional[float] = None) -> str:
        """
        Add a message to conversation.
        
        Args:
            conversation_id: Conversation ID
            role: 'user' or 'assistant'
            content: Message content
            input_type: 'text', 'image', 'file'
            retrieved_chunks: Chunks used for this message (for assistant messages)
            confidence_score: Confidence score of response
        
        Returns:
            Message ID
        """
        try:
            message_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            message = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "input_type": input_type,
                "retrieved_chunks": retrieved_chunks,
                "confidence_score": confidence_score,
                "timestamp": now
            }
            
            # Try Supabase first
            if self.use_supabase and self.supabase:
                try:
                    result = await self.supabase.add_message(
                        conversation_id=conversation_id,
                        role=role,
                        content=content
                    )
                    
                    if result:
                        logger.info(f"✅ Message saved to Supabase: {message_id}")
                        return result
                except Exception as e:
                    logger.warning(f"Supabase save failed: {str(e)}, falling back to in-memory")
            
            # Fallback to in-memory
            if conversation_id not in self.messages_cache:
                self.messages_cache[conversation_id] = []
            
            self.messages_cache[conversation_id].append(message)
            
            # Update conversation last_message_at
            if conversation_id in self.conversations_cache:
                self.conversations_cache[conversation_id]['last_message_at'] = now
            
            logger.info(f"✅ Message added (in-memory): {message_id}")
            return message_id
        
        except Exception as e:
            logger.error(f"❌ Error adding message: {str(e)}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get conversation with all messages.
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            Conversation object with messages, or None if not found
        """
        try:
            # Try Supabase first
            if self.use_supabase and self.supabase:
                try:
                    result = await self.supabase.get_conversation(conversation_id)
                    if result:
                        logger.info(f"✅ Retrieved conversation from Supabase: {conversation_id}")
                        return result
                except Exception as e:
                    logger.warning(f"Supabase retrieval failed: {str(e)}, checking in-memory")
            
            # Fallback to in-memory
            if conversation_id in self.conversations_cache:
                conversation = self.conversations_cache[conversation_id].copy()
                conversation['messages'] = self.messages_cache.get(conversation_id, [])
                logger.info(f"✅ Retrieved conversation (in-memory): {conversation_id}")
                return conversation
            
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Error retrieving conversation: {str(e)}")
            raise
    
    async def get_user_conversations(self, user_id: str) -> List[Dict]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of conversations
        """
        try:
            # Try Supabase first
            if self.use_supabase and self.supabase:
                try:
                    results = await self.supabase.get_user_conversations(user_id)
                    if results:
                        logger.info(f"✅ Retrieved {len(results)} conversations from Supabase for user {user_id}")
                        return results
                except Exception as e:
                    logger.warning(f"Supabase retrieval failed: {str(e)}, checking in-memory")
            
            # Fallback to in-memory
            conversations = [
                conv for conv in self.conversations_cache.values()
                if conv.get('user_id') == user_id
            ]
            
            logger.info(f"✅ Retrieved {len(conversations)} conversations (in-memory) for user {user_id}")
            return conversations
        
        except Exception as e:
            logger.error(f"❌ Error retrieving user conversations: {str(e)}")
            raise
    
    async def update_conversation(self,
                                 conversation_id: str,
                                 title: Optional[str] = None,
                                 context: Optional[Dict] = None,
                                 is_active: Optional[bool] = None) -> bool:
        """
        Update conversation metadata.
        
        Args:
            conversation_id: Conversation ID
            title: New title
            context: Updated context
            is_active: Active status
        
        Returns:
            True if successful
        """
        try:
            # Try Supabase first
            if self.use_supabase and self.supabase:
                try:
                    result = await self.supabase.update_conversation(
                        conversation_id=conversation_id,
                        title=title,
                        context=context,
                        is_active=is_active
                    )
                    
                    if result:
                        logger.info(f"✅ Conversation updated in Supabase: {conversation_id}")
                        return True
                except Exception as e:
                    logger.warning(f"Supabase update failed: {str(e)}, trying in-memory")
            
            # Fallback to in-memory
            if conversation_id in self.conversations_cache:
                if title:
                    self.conversations_cache[conversation_id]['title'] = title
                if context:
                    self.conversations_cache[conversation_id]['context'] = context
                if is_active is not None:
                    self.conversations_cache[conversation_id]['is_active'] = is_active
                
                logger.info(f"✅ Conversation updated (in-memory): {conversation_id}")
                return True
            
            logger.warning(f"Conversation not found: {conversation_id}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Error updating conversation: {str(e)}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation.
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            True if successful
        """
        try:
            # Try Supabase first
            if self.use_supabase and self.supabase:
                try:
                    result = await self.supabase.delete_conversation(conversation_id)
                    if result:
                        logger.info(f"✅ Conversation deleted from Supabase: {conversation_id}")
                        return True
                except Exception as e:
                    logger.warning(f"Supabase delete failed: {str(e)}, trying in-memory")
            
            # Fallback to in-memory
            if conversation_id in self.conversations_cache:
                del self.conversations_cache[conversation_id]
            
            if conversation_id in self.messages_cache:
                del self.messages_cache[conversation_id]
            
            logger.info(f"✅ Conversation deleted (in-memory): {conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error deleting conversation: {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict:
        """Get conversation statistics."""
        return {
            'total_conversations': len(self.conversations_cache),
            'total_messages': sum(len(msgs) for msgs in self.messages_cache.values()),
            'active_conversations': sum(
                1 for conv in self.conversations_cache.values()
                if conv.get('is_active', True)
            ),
            'storage_mode': 'supabase' if self.use_supabase else 'in-memory'
        }


# Global instance
_conversation_service_instance: Optional[ConversationService] = None


def get_conversation_service(supabase_client=None) -> ConversationService:
    """Get or create conversation service instance."""
    global _conversation_service_instance
    
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService(supabase_client=supabase_client)
    
    return _conversation_service_instance
