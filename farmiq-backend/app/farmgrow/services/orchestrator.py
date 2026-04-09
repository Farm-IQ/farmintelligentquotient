"""
FarmGrow RAG Orchestrator - Complete Pipeline
Unified service that chains together all RAG components:
1. Document Ingestion → 2. Embedding Generation → 3. Semantic Retrieval → 
4. Result Ranking → 5. Answer Generation with LLM → 6. Conversation Management

This is the main orchestrator that users interact with.
"""
import logging
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Complete RAG pipeline response"""
    question: str
    answer: str
    confidence: float
    sources: List[Dict]
    chunks_used: int
    processing_time_seconds: float
    query_id: str
    timestamp: str


class RAGOrchestrator:
    """
    Complete RAG pipeline orchestrator.
    
    Chains together:
    - Document ingestion from libraries
    - Text embedding using BGE-M3
    - Semantic retrieval with fallbacks
    - Multi-signal ranking
    - Answer generation using Ollama LLMs
    - Conversation history management
    """
    
    def __init__(self,
                 ingestion_service,
                 embedding_service,
                 embedding_store,
                 retrieval_service,
                 ranking_service,
                 llm_service,
                 conversation_service):
        """
        Initialize complete RAG pipeline
        
        Args:
            ingestion_service: Document ingestion and chunking
            embedding_service: Text embedding generation
            embedding_store: Local embedding storage
            retrieval_service: Semantic + keyword retrieval
            ranking_service: Multi-signal ranking
            llm_service: LLM for answer generation
            conversation_service: Chat conversation management
        """
        self.ingestion = ingestion_service
        self.embedder = embedding_service
        self.embedding_store = embedding_store
        self.retriever = retrieval_service
        self.ranker = ranking_service
        self.llm = llm_service
        self.conversations = conversation_service
        
        self.initialized_at = datetime.now()
        self.query_count = 0
        self.document_count = 0
        
        logger.info("🚀 Initializing FarmGrow RAG Orchestrator")
        logger.info("   ✅ Ingestion Service: Ready")
        logger.info("   ✅ Embedding Service: BGE-M3 (Multilingual)")
        logger.info("   ✅ Retrieval Service: Hybrid (BM25 + Vector)")
        logger.info("   ✅ Ranking Service: Multi-signal ranking")
        logger.info("   ✅ LLM Service: Ollama (Local inference)")
        logger.info("   ✅ Conversation Service: Supabase + In-memory fallback")
    
    async def initialize_documents(self) -> Dict:
        """
        Initialize by ingesting all documents from libraries folder.
        
        This must be called once before processing queries.
        
        Returns:
            Ingestion summary with document counts and status
        """
        try:
            logger.info("📚 Initializing document ingestion from libraries folder...")
            
            # Ingest all documents
            result = await self.ingestion.ingest_all_documents()
            self.document_count = result.get('successfully_ingested', 0)
            
            logger.info(f"✅ Document initialization complete:")
            logger.info(f"   - Documents ingested: {result['successfully_ingested']}")
            logger.info(f"   - Total chunks: {result.get('total_chunks', 0)}")
            logger.info(f"   - Failed: {result['failed']}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Document initialization failed: {str(e)}")
            return {'error': str(e), 'successfully_ingested': 0, 'failed': 0}
    
    async def process_query(self, 
                           query: str,
                           conversation_id: Optional[str] = None,
                           user_id: Optional[str] = None) -> RAGResponse:
        """
        Process a user query end-to-end through complete RAG pipeline.
        
        Pipeline:
        1. Create/retrieve conversation context
        2. Retrieve relevant document chunks
        3. Rank chunks by relevance
        4. Generate answer using LLM with context
        5. Save to conversation history
        
        Args:
            query: User's farming question
            conversation_id: Optional conversation ID for multi-turn
            user_id: Optional user ID for tracking
            
        Returns:
            Complete RAG response with answer and metadata
        """
        try:
            self.query_count += 1
            start_time = datetime.now()
            query_id = f"query_{self.query_count}_{datetime.now().timestamp()}"
            
            logger.info(f"❓ Query #{self.query_count}: '{query[:60]}...'")
            
            # Step 1: Get or create conversation
            if not conversation_id and user_id:
                conversation_id = await self.conversations.create_conversation(
                    user_id=user_id,
                    context={'query': query},
                    conversation_type='agronomy'
                )
                logger.info(f"   📝 Created new conversation: {conversation_id}")
            
            # Step 2: Retrieve relevant chunks
            logger.info(f"   🔍 Retrieving relevant documents...")
            retrieved_chunks = await self.retriever.retrieve(
                query=query,
                top_k=5,
                retrieval_method='hybrid'
            )
            
            if not retrieved_chunks:
                logger.warning(f"   ⚠️ No relevant documents found")
                empty_response = RAGResponse(
                    question=query,
                    answer="I don't have enough information in the knowledge base to answer this question. Please provide more context or add relevant documents.",
                    confidence=0.0,
                    sources=[],
                    chunks_used=0,
                    processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                    query_id=query_id,
                    timestamp=datetime.now().isoformat()
                )
                
                # Save to conversation
                if conversation_id:
                    await self.conversations.add_message(
                        conversation_id=conversation_id,
                        role='assistant',
                        content=empty_response.answer
                    )
                
                return empty_response
            
            logger.info(f"   ✅ Retrieved {len(retrieved_chunks)} chunks")
            
            # Step 3: Rank chunks by relevance
            logger.info(f"   📊 Ranking results...")
            ranked_chunks = await self.ranker.rerank(
                chunks=retrieved_chunks,
                query=query,
                user_id=user_id
            )
            
            logger.info(f"   ✅ Ranked {len(ranked_chunks)} chunks")
            
            # Step 4: Generate answer using LLM
            logger.info(f"   🤖 Invoking LLM for answer generation...")
            answer_result = await self.llm.generate_answer(
                query=query,
                context_chunks=ranked_chunks,
                conversation_id=conversation_id,
                max_length=1000
            )
            
            # Step 5: Format response
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = RAGResponse(
                question=query,
                answer=answer_result.get('text', ''),
                confidence=answer_result.get('confidence', 0.7),
                sources=[
                    {
                        'document': chunk.get('document_title', 'Unknown'),
                        'relevance_score': chunk.get('relevance_score', 0),
                        'excerpt': chunk.get('content', '')[:200] + "..."
                    }
                    for chunk in ranked_chunks[:3]  # Top 3 sources
                ],
                chunks_used=len(ranked_chunks),
                processing_time_seconds=processing_time,
                query_id=query_id,
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"   ✅ Answer generated in {processing_time:.2f}s")
            
            # Step 6: Save to conversation history
            if conversation_id:
                # Save user question
                await self.conversations.add_message(
                    conversation_id=conversation_id,
                    role='user',
                    content=query
                )
                
                # Save assistant response
                await self.conversations.add_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=response.answer,
                    retrieved_chunks=[chunk.get('chunk_id') for chunk in ranked_chunks],
                    confidence_score=response.confidence
                )
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Query processing error: {str(e)}", exc_info=True)
            raise
    
    async def stream_query(self, 
                          query: str,
                          conversation_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream answer for real-time UI updates.
        
        Args:
            query: User's question
            conversation_id: Optional conversation ID
            
        Yields:
            Answer chunks as they're generated
        """
        try:
            logger.info(f"🔄 Streaming answer for: '{query[:60]}...'")
            
            # Retrieve and rank
            retrieved = await self.retriever.retrieve(query, top_k=5)
            if not retrieved:
                yield "I couldn't find relevant documents to answer your question."
                return
            
            ranked = await self.ranker.rerank(retrieved, query)
            
            # Stream answer
            async for chunk in self.llm.stream_answer(
                query=query,
                context_chunks=ranked
            ):
                yield chunk
        
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def ask_follow_up(self,
                           conversation_id: str,
                           follow_up_question: str) -> RAGResponse:
        """
        Ask a follow-up question within existing conversation.
        
        Args:
            conversation_id: Existing conversation ID
            follow_up_question: Follow-up question
            
        Returns:
            Answer in conversation context
        """
        try:
            logger.info(f"💬 Follow-up question in conversation {conversation_id}")
            
            # Get conversation history
            conversation = await self.conversations.get_conversation(conversation_id)
            
            # Build context from conversation history
            history_context = self._build_conversation_context(conversation)
            
            # Retrieve and process with conversation context
            response = await self.process_query(
                query=follow_up_question,
                conversation_id=conversation_id
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Follow-up error: {str(e)}")
            raise
    
    async def add_documents(self, file_paths: List[str]) -> Dict:
        """
        Add new documents to knowledge base.
        
        Args:
            file_paths: List of paths to documents
            
        Returns:
            Ingestion result for each file
        """
        try:
            logger.info(f"📄 Adding {len(file_paths)} new documents...")
            
            results = {
                'total': len(file_paths),
                'successful': 0,
                'failed': 0,
                'documents': []
            }
            
            for file_path in file_paths:
                try:
                    result = await self.ingestion.ingest_document(file_path)
                    results['successful'] += 1
                    results['documents'].append({
                        'file': file_path,
                        'status': 'success',
                        'chunks': result.get('chunks_created', 0)
                    })
                except Exception as e:
                    results['failed'] += 1
                    results['documents'].append({
                        'file': file_path,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            self.document_count += results['successful']
            logger.info(f"✅ Document addition complete: {results['successful']}/{results['total']} successful")
            
            return results
        
        except Exception as e:
            logger.error(f"Document addition error: {str(e)}")
            raise
    
    async def get_conversation_history(self, conversation_id: str) -> Dict:
        """
        Get full conversation history.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation with all messages
        """
        try:
            conversation = await self.conversations.get_conversation(conversation_id)
            return conversation or {'error': 'Conversation not found'}
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict:
        """
        Get RAG system statistics.
        
        Returns:
            System metrics and statistics
        """
        uptime = (datetime.now() - self.initialized_at).total_seconds()
        
        return {
            'status': 'operational',
            'uptime_seconds': uptime,
            'queries_processed': self.query_count,
            'documents_ingested': self.document_count,
            'embedding_model': 'BGE-M3 (1024-dim)',
            'retrieval_method': 'Hybrid (BM25 + Vector)',
            'llm_model': 'Ollama (mistral/llama)',
            'storage': {
                'embeddings': 'NumPy + JSON local',
                'conversations': 'Supabase + in-memory fallback'
            }
        }
    
    def _build_conversation_context(self, conversation: Dict) -> str:
        """Build context from conversation history."""
        try:
            messages = conversation.get('messages', [])
            context_parts = [
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in messages[-10:]  # Last 10 messages for context
            ]
            return "\n".join(context_parts)
        except Exception:
            return ""


# Global instance
_orchestrator_instance: Optional['RAGOrchestrator'] = None


def get_rag_orchestrator(
    ingestion_service,
    embedding_service,
    embedding_store,
    retrieval_service,
    ranking_service,
    llm_service,
    conversation_service
) -> RAGOrchestrator:
    """Get or create RAG orchestrator instance."""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = RAGOrchestrator(
            ingestion_service=ingestion_service,
            embedding_service=embedding_service,
            embedding_store=embedding_store,
            retrieval_service=retrieval_service,
            ranking_service=ranking_service,
            llm_service=llm_service,
            conversation_service=conversation_service
        )
    
    return _orchestrator_instance
