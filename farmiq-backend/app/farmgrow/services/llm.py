"""
FarmGrow LLM Service - Complete Implementation with Legacy Logic
Interface layer for local LLM inference via Ollama

Integrated from legacy custom_llm_service.py and rag_reasoning_service.py:
- Ollama with mistral:7b-instruct optimization (5-6x faster than llama3.1:8b)
- HuggingFace GPT2 fallback
- Temperature control optimized to 0.3 for focused responses
- Max tokens set to 150 for streaming efficiency
- Context assembly with proper source attribution
- Confidence estimation from chunk similarity
- Full streaming support
- Comprehensive error handling

Handles:
- Prompt engineering for agricultural domain
- Context assembly and citation handling  
- Response streaming
- Token management
- Error handling and fallbacks
- Confidence scoring
"""

from typing import List, Optional, Dict, AsyncGenerator, Tuple
import aiohttp
import logging
import json
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Try to import HuggingFace as fallback
try:
    from transformers import pipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    pipeline = None

# Try to import Ollama service
try:
    from core.ollama_service import OllamaService
    OLLAMA_SERVICE_AVAILABLE = True
except ImportError:
    OLLAMA_SERVICE_AVAILABLE = False
    OllamaService = None


@dataclass
class LLMResponse:
    """LLM generated response with metadata"""
    answer: str
    model: str
    tokens_used: int
    generation_time_seconds: float
    context_chunks_used: List[str]
    confidence: float = 0.8


class OllamaLLMService:
    """
    Service for interacting with Ollama local LLM (optimized)
    
    Integrated from legacy custom_llm_service.py + rag_reasoning_service.py
    
    Features:
    - Ollama with mistral:7b-instruct (preferred) or fallback to HuggingFace GPT2
    - Temperature optimized to 0.3 for focused, deterministic responses
    - Max tokens optimized to 150 for fast streaming
    - Prompt engineering for agricultural context
    - Context injection from RAG with source attribution
    - Response parsing and validation
    - Token limit management
    - Streaming support
    - Confidence estimation from chunk similarity scores
    - Error handling with graceful fallbacks
    
    Attributes:
        ollama_host: Ollama server URL
        model_name: Ollama model name (optimized: mistral:7b-instruct)
        max_tokens: Maximum tokens in response (optimized: 150)
        temperature: Sampling temperature (optimized: 0.3)
        hf_generator: HuggingFace fallback generator
    """
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model_name: str = "mistral:7b-instruct",  # Fast model (5-6x faster than llama3.1)
        max_tokens: int = 75,  # Balanced: detailed answers (~3-4 sentences) in ~40-50s
        temperature: float = 0.3,  # Optimized for focused responses
        use_ollama_service: bool = True
    ):
        """
        Initialize Ollama LLM service with legacy optimizations
        
        Args:
            ollama_host: URL of Ollama API server
            model_name: Ollama model (mistral:7b-instruct recommended)
            max_tokens: Maximum tokens to generate (optimized: 150)
            temperature: Sampling temperature (optimized: 0.3)
            use_ollama_service: Whether to use ollama_service wrapper if available
        """
        self.ollama_host = ollama_host.rstrip("/")
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Legacy optimization: Use ollama_service if available
        self.ollama_service = None
        if use_ollama_service and OLLAMA_SERVICE_AVAILABLE and OllamaService:
            try:
                self.ollama_service = OllamaService()
                logger.info(f"✓ Using OllamaService wrapper (with {model_name})")
            except Exception as e:
                logger.warning(f"Could not initialize ollama_service: {e}")
        
        # HuggingFace fallback
        self.hf_generator = None
        if HF_AVAILABLE:
            try:
                self.hf_generator = pipeline("text-generation", model="gpt2", device=-1)
                logger.info("✓ HuggingFace GPT2 fallback loaded")
            except Exception as e:
                logger.warning(f"Could not load HuggingFace fallback: {e}")
        
        # Agriculture-specific system prompt
        self.system_prompt = """You are an agricultural expert assistant helping farmers in Africa
optimize farming practices, access credit, and improve crop yields.

Your knowledge covers:
- Crop cultivation techniques (maize, cassava, millet, beans, etc.)
- Pest and disease management
- Soil health and fertilization
- Water management and irrigation
- Weather patterns and seasonal planning
- Agricultural financing and credit
- Market prices and trading
- Sustainable farming practices

When answering:
1. Be practical and actionable - farmers will implement your advice
2. Consider African climate, soil, and resource constraints
3. Provide specific quantities and timelines
4. Mention cost-benefit analysis when relevant
5. Suggest low-cost alternatives for resource-limited farmers
6. Use local measurement units when appropriate
7. Always cite sources when providing specific information

CRITICAL: Keep your response focused and concise (around 100-150 tokens).
Style: Be friendly, supportive, and encouraging. Farmers are your audience.
"""
        
        logger.info(f"Initialized OllamaLLMService (model={model_name}, temp={temperature}, max_tokens={max_tokens})")
    
    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict],
        conversation_id: Optional[str] = None,
        max_length: int = 1024,
        chat_history: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Alias for generate_response with extended parameters.
        
        Used by RAG orchestrator for compatibility.
        
        Args:
            query: User question
            context_chunks: Retrieved document chunks
            conversation_id: Conversation ID (for tracking)
            max_length: Not used, kept for compatibility
            chat_history: Previous conversation messages
            
        Returns:
            LLMResponse with generated answer
        """
        return await self.generate_response(
            query=query,
            context_chunks=context_chunks,
            chat_history=chat_history
        )
    
    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict],  # Changed to accept chunk objects with metadata
        chat_history: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Generate response using LLM with retrieved context
        
        Integrated from legacy rag_reasoning_service.py
        
        Builds prompt with:
        1. System instructions
        2. Retrieved context (with source attribution)
        3. Chat history (recent messages)
        4. User query
        
        Args:
            query: User question
            context_chunks: Retrieved document chunks (can be strings or dicts with score)
            chat_history: Previous messages in conversation
            
        Returns:
            LLMResponse with generated answer and metadata
        """
        # Build context with source attribution
        context_text, source_text = self._build_context(context_chunks)
        
        # Estimate confidence from chunk similarity
        confidence = self._estimate_confidence(context_chunks)
        
        # Build full prompt
        prompt = self._build_prompt(
            query=query,
            context=context_text,
            chat_history=chat_history
        )
        
        try:
            # Try Ollama first
            if self.ollama_service:
                response = await self._generate_answer_with_ollama_service(prompt)
            else:
                response = await self._generate_answer_with_llm(prompt)
            
            # Attach source information and confidence
            response.confidence = confidence
            response.context_chunks_used = [c.get("content", c) if isinstance(c, dict) else c for c in context_chunks[:3]]
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return await self._get_fallback_response(query, context_chunks, confidence)
    
    async def _generate_answer_with_ollama_service(self, prompt: str) -> LLMResponse:
        """
        Generate answer using ollama_service wrapper (legacy support).
        
        Args:
            prompt: Full prompt to LLM
            
        Returns:
            LLMResponse with generated text
        """
        try:
            start_time = datetime.now()
            
            # Use ollama_service.generate_text (correct method name)
            response_text = await self.ollama_service.generate_text(
                prompt=prompt,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            end_time = datetime.now()
            gen_time = (end_time - start_time).total_seconds()
            
            # Estimate tokens (rough: ~4 chars per token)
            tokens_used = len(response_text) // 4
            
            logger.info(f"LLM (ollama_service) generated ~{tokens_used} tokens in {gen_time:.2f}s")
            
            return LLMResponse(
                answer=response_text.strip(),
                model=self.model_name,
                tokens_used=tokens_used,
                generation_time_seconds=gen_time,
                context_chunks_used=[],
                confidence=0.8
            )
        except Exception as e:
            logger.error(f"ollama_service generation failed: {e}")
            raise
    
    async def _generate_answer_with_llm(self, prompt: str) -> LLMResponse:
        """
        Generate answer using Ollama HTTP API or HuggingFace fallback.
        
        Integrated from custom_llm_service.py
        
        Args:
            prompt: Full prompt to LLM
            
        Returns:
            LLMResponse with generated text
        """
        # Try Ollama HTTP API first
        try:
            return await self._call_ollama(prompt)
        except Exception as e:
            logger.warning(f"Ollama HTTP API failed: {e}, trying HuggingFace fallback")
            
        # Fallback to HuggingFace
        if self.hf_generator:
            try:
                return await self._generate_with_huggingface(prompt)
            except Exception as e:
                logger.error(f"HuggingFace generation also failed: {e}")
                raise
        
        raise Exception("No LLM backend available (Ollama and HuggingFace both unavailable)")
    
    async def _generate_with_huggingface(self, prompt: str) -> LLMResponse:
        """
        Generate response using HuggingFace GPT2 fallback.
        
        From legacy custom_llm_service.py
        
        Args:
            prompt: Prompt text
            
        Returns:
            LLMResponse
        """
        start_time = datetime.now()
        
        result = await asyncio.to_thread(
            self.hf_generator,
            prompt[:256],  # Limit input to avoid memory issues
            max_length=self.max_tokens + 256,
            do_sample=True,
            temperature=self.temperature
        )
        
        end_time = datetime.now()
        gen_time = (end_time - start_time).total_seconds()
        
        answer = result[0]["generated_text"].replace(prompt, "").strip()
        tokens_used = len(answer.split())
        
        logger.info(f"LLM (HuggingFace GPT2) generated {tokens_used} tokens in {gen_time:.2f}s")
        
        return LLMResponse(
            answer=answer,
            model="gpt2",
            tokens_used=tokens_used,
            generation_time_seconds=gen_time,
            context_chunks_used=[],
            confidence=0.6  # Lower confidence for fallback model
        )
    
    
    async def generate_response_streaming(
        self,
        query: str,
        context_chunks: List[Dict],
        chat_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming output
        
        Integrated from legacy rag_reasoning_service.py streaming support
        
        Yields tokens as they're generated for real-time feedback
        
        Args:
            query: User question
            context_chunks: Retrieved document chunks
            chat_history: Previous conversation messages
            
        Yields:
            Response text chunks
        """
        # Build context with source attribution
        context_text, source_text = self._build_context(context_chunks)
        
        prompt = self._build_prompt(query, context_text, chat_history)
        
        try:
            async for chunk in self._stream_answer_from_llm(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"[Error generating response: {str(e)}]"
    
    async def _stream_answer_from_llm(
        self,
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream answer from LLM
        
        Integrated from legacy rag_reasoning_service.py
        
        Args:
            prompt: Full prompt
            
        Yields:
            Text chunks
        """
        try:
            async for chunk in self._call_ollama_streaming(prompt):
                yield chunk
        except Exception as e:
            logger.warning(f"Streaming generation failed: {e}")
            # Fallback to non-streaming
            try:
                response = await self._generate_answer_with_llm(prompt)
                yield response.answer
            except Exception as e2:
                logger.error(f"Fallback generation also failed: {e2}")
                yield "[Error generating response]"
    
    async def _call_ollama(
        self,
        prompt: str
    ) -> LLMResponse:
        """
        Call Ollama API endpoint (updated version)
        
        Args:
            prompt: Full prompt to LLM
            
        Returns:
            LLMResponse with generated text
        """
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
            "stop": ["User:", "\n\nUser:", "\n\nSystem:"],  # Stop sequences
            "stream": False  # Get full response
        }
        
        try:
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"Ollama API error: {resp.status}")
                    
                    data = await resp.json()
                    answer = data.get("response", "").strip()
                    tokens_used = data.get("processed", len(answer.split()))
                    gen_time = data.get("eval_duration", 0) / 1e9  # ns to seconds
                    
                    end_time = datetime.now()
                    if gen_time == 0:
                        gen_time = (end_time - start_time).total_seconds()
                    
                    logger.info(f"LLM (Ollama) generated {tokens_used} tokens in {gen_time:.2f}s")
                    
                    return LLMResponse(
                        answer=answer,
                        model=self.model_name,
                        tokens_used=tokens_used,
                        generation_time_seconds=gen_time,
                        context_chunks_used=[],
                        confidence=0.8
                    )
        except asyncio.TimeoutError:
            logger.error("Ollama API timeout")
            raise
    
    async def _call_ollama_streaming(
        self,
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Call Ollama API with streaming
        
        Args:
            prompt: Full prompt to LLM
            
        Yields:
            Text chunks as they're generated
        """
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
            "stop": ["User:", "\n\nUser:", "\n\nSystem:"],
            "stream": True  # Streaming enabled
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        raise Exception(f"Ollama API error: {resp.status}")
                    
                    async for line in resp.content:
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line.decode())
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                        except json.JSONDecodeError:
                            continue
                        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
    
    def _build_context(
        self,
        context_chunks: List
    ) -> Tuple[str, str]:
        """
        Build context from retrieved chunks with source attribution.
        
        Integrated from legacy rag_reasoning_service.py
        
        Formats chunks with [Source N: document_name] prefix for proper citation
        
        Args:
            context_chunks: Retrieved chunks (RetrievedChunk objects, strings, or dicts)
            
        Returns:
            Tuple of (context_text, source_attribution_text)
        """
        if not context_chunks:
            return "", ""
        
        # Deduplicate chunks
        unique_chunks = {}
        for i, chunk in enumerate(context_chunks):
            # Handle RetrievedChunk objects
            if hasattr(chunk, 'content'):  # RetrievedChunk object
                content = chunk.content
                chunk_id = getattr(chunk, 'chunk_id', f"chunk_{i}")
            # Handle dict
            elif isinstance(chunk, dict):
                content = chunk.get("content", str(chunk))
                chunk_id = chunk.get("chunk_id", f"chunk_{i}")
            # Handle string
            else:
                content = str(chunk)
                chunk_id = f"chunk_{i}"
            
            # Use chunk_id as dict key instead of content object
            if chunk_id not in unique_chunks:
                unique_chunks[chunk_id] = {
                    "index": i,
                    "content": content,
                    "original": chunk
                }
        
        # Build context (BALANCED: 1200 chars - quality + speed)
        # Balanced approach: enough for 1-2 detailed chunks, fast processing
        context_parts = []
        source_parts = []
        total_length = 0
        max_context_length = 1200  # Sweet spot: quality context without excessive processing
        
        for i, (chunk_id, info) in enumerate(unique_chunks.items(), 1):
            content = info["content"]
            source_num = i
            
            # Extract source info if available
            source_name = "Document"
            original_chunk = info["original"]
            if hasattr(original_chunk, 'document_title'):  # RetrievedChunk
                source_name = original_chunk.document_title or f"Source {source_num}"
            elif isinstance(original_chunk, dict):
                source_name = original_chunk.get("document_title", f"Source {source_num}")
            
            # Add context with source marker
            chunk_with_source = f"[Source {source_num}: {source_name}]\n{content}"
            
            if total_length + len(chunk_with_source) <= max_context_length:
                context_parts.append(chunk_with_source)
                source_parts.append(f"[{source_num}] {source_name}")
                total_length += len(chunk_with_source)
            else:
                # Truncate if too long
                remaining = max_context_length - total_length
                if remaining > 100:
                    truncated = content[:remaining] + "...[truncated]"
                    context_parts.append(f"[Source {source_num}: {source_name}]\n{truncated}")
                break
        
        context_text = "\n\n".join(context_parts)
        source_text = "\n".join(source_parts)
        
        return context_text, source_text
    
    def _estimate_confidence(self, context_chunks: List) -> float:
        """
        Estimate answer confidence from chunk similarity scores.
        
        Integrated from legacy rag_reasoning_service.py
        
        Higher similarity = higher confidence
        
        Args:
            context_chunks: Retrieved chunks (may have relevance_score)
            
        Returns:
            Confidence score in [0, 1]
        """
        if not context_chunks:
            return 0.3  # Low confidence without context
        
        scores = []
        for chunk in context_chunks:
            if isinstance(chunk, dict):
                score = chunk.get("relevance_score", chunk.get("score", 0.5))
                scores.append(score)
            else:
                scores.append(0.5)  # Default confidence for string chunks
        
        # Average the scores, capped at 1.0
        avg_score = sum(scores) / len(scores) if scores else 0.3
        return min(1.0, max(0.0, avg_score))
    
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build complete prompt for LLM
        
        Updated from legacy - optimized for mistral:7b and speed
        
        Structure:
        1. System instructions (agricultural domain)
        2. Context (retrieved documents)
        3. Chat history (last 2 exchanges)
        4. Current query
        
        Args:
            query: User question
            context: Formatted context chunks with sources
            chat_history: Previous messages
            
        Returns:
            Complete prompt string
        """
        prompt_parts = []
        
        # System prompt (critical for agricultural context)
        prompt_parts.append(f"System: {self.system_prompt}\n")
        
        # Context from RAG (with source attribution)
        if context:
            prompt_parts.append("Knowledge Base:\n")
            prompt_parts.append(context)
            prompt_parts.append("\n\n")
        else:
            prompt_parts.append("[No relevant knowledge base entries found]\n\n")
        
        # Chat history (keep short for speed - last 2 exchanges)
        if chat_history and len(chat_history) > 0:
            prompt_parts.append("Previous Messages:\n")
            for msg in chat_history[-4:]:  # Last 2 rounds (user + assistant)
                role = msg.get("role", "unknown").title()
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}\n")
            prompt_parts.append("\n")
        
        # Current query
        prompt_parts.append(f"User: {query}\n")
        prompt_parts.append("Assistant: ")
        
        return "".join(prompt_parts)
    
    def _format_context(self, context_chunks: List[str]) -> str:
        """
        Format context chunks for inclusion in prompt (legacy method for compatibility)
        
        Args:
            context_chunks: List of document chunks
            
        Returns:
            Formatted context string
        """
        if not context_chunks:
            return ""
        
        # Deduplicate chunks
        unique_chunks = []
        seen = set()
        for chunk in context_chunks:
            content = chunk if isinstance(chunk, str) else str(chunk)
            if content not in seen:
                unique_chunks.append(content)
                seen.add(content)
        
        # Limit context to ~2000 chars to save space
        context_text = "\n\n".join(unique_chunks[:5])  # Top 5 chunks
        
        # Truncate if too long
        max_context_length = 2500
        if len(context_text) > max_context_length:
            context_text = context_text[:max_context_length] + "...[context truncated]"
        
        return context_text
    
    async def _get_fallback_response(
        self,
        query: str,
        context_chunks: List,
        confidence: float = 0.3
    ) -> LLMResponse:
        """
        Generate fallback response if LLM fails
        
        Integrated from legacy rag_reasoning_service.py
        
        Returns simple concatenation of context with note
        
        Args:
            query: Original query
            context_chunks: Retrieved context
            confidence: Confidence score
            
        Returns:
            LLMResponse with fallback content
        """
        fallback_parts = []
        fallback_parts.append("I encountered a temporary issue generating a detailed response. ")
        fallback_parts.append("Here's what I found related to your question:\n\n")
        
        for i, chunk in enumerate(context_chunks[:3], 1):
            content = chunk.get("content", chunk) if isinstance(chunk, dict) else chunk
            preview = content[:200] if isinstance(content, str) else str(content)[:200]
            fallback_parts.append(f"• [Source {i}] {preview}...\n\n")
        
        fallback_parts.append("Please try again or rephrase your question for a better response.")
        
        return LLMResponse(
            answer="".join(fallback_parts),
            model=self.model_name,
            tokens_used=0,
            generation_time_seconds=0,
            context_chunks_used=[c.get("content", c) if isinstance(c, dict) else c for c in context_chunks[:3]],
            confidence=confidence or 0.2  # Very low confidence for fallback
        )
    
    async def validate_connection(self) -> bool:
        """
        Validate that Ollama server is reachable
        
        Returns:
            True if server is accessible
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ollama_host}/api/tags"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = data.get("models", [])
                        logger.info(f"Ollama ✓ reachable, available models: {len(models)}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False
