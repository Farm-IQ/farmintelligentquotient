"""
Ollama Service - Unified Interface for Local LLMs
Handles:
- Text generation (mistral:7b-instruct, llama3.1:8b)
- Embeddings (bge-m3:latest)
- OCR (deepseek-ocr:latest)
All models run locally via Ollama
"""
import logging
import os
from typing import List, Dict, Optional, AsyncGenerator, Tuple
import asyncio
import json

try:
    import ollama
except ImportError:
    ollama = None

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Unified service for all Ollama operations
    Ensures models are available before use
    Provides fallback and error handling
    """
    
    def __init__(self, 
                 ollama_host: str = None,
                 text_model: str = None,  # ⚡ Uses config default
                 embedding_model: str = None,  # ⚡ Uses config default
                 ocr_model: str = None):  # ⚡ Uses config default
        """
        Initialize Ollama service with performance-optimized defaults
        
        Args:
            ollama_host: Ollama server URL (default: http://localhost:11434)
            text_model: Text generation model (default: from config.models.DEFAULT_TEXT_MODEL)
            embedding_model: Embedding model (default: from config.models.EMBEDDING_MODEL_NAME)
            ocr_model: OCR model (default: from config.models.OCR_MODEL_NAME)
        """
        # ⚡ Import config defaults for performance optimization
        from config.models import DEFAULT_TEXT_MODEL, EMBEDDING_MODEL_NAME, OCR_MODEL_NAME
        
        # Use config defaults if not specified
        text_model = text_model or DEFAULT_TEXT_MODEL
        embedding_model = embedding_model or EMBEDDING_MODEL_NAME
        ocr_model = ocr_model or OCR_MODEL_NAME
        self.ollama_host = ollama_host or os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.text_model = text_model
        self.embedding_model = embedding_model
        self.ocr_model = ocr_model
        self.client = None
        self.http_client = None
        self.available_models = []
        self.model_status = {}
        
        logger.info(f"🤖 Ollama Service Configuration:")
        logger.info(f"   🔌 Host: {self.ollama_host}")
        logger.info(f"   📝 Text Model: {self.text_model}")
        logger.info(f"   🔍 Embedding Model: {self.embedding_model}")
        logger.info(f"   📸 OCR Model: {self.ocr_model}")
        
        self._initialize()
    
    def _initialize(self):
        """Initialize Ollama client and check model availability"""
        try:
            if not ollama:
                logger.error("❌ Ollama library not installed. Install: pip install ollama")
                return
            
            self.client = ollama.Client(host=self.ollama_host)
            logger.info(f"🔌 Initializing Ollama service at {self.ollama_host}")
            
            # List available models
            self._sync_list_models()
            
            # Check required models
            self._check_models_availability()
            
        except Exception as e:
            logger.error(f"❌ Error initializing Ollama service: {str(e)}")
            self.client = None
    
    def _sync_list_models(self):
        """Synchronously list available models"""
        models_response = None
        try:
            if not self.client:
                logger.warning("⚠️ Ollama client not initialized - cannot list models")
                return
            
            logger.debug("🔍 Attempting to list models from Ollama...")
            models_response = self.client.list()
            logger.debug(f"📋 Raw response type: {type(models_response)}")
            
            # The ollama library returns a ListResponse object with a .models attribute
            # where each model has a .model attribute with the model name
            if hasattr(models_response, 'models'):
                # ✅ Primary path: ollama.ListResponse object with .models attribute
                # Each item in .models has a .model attribute with the name
                self.available_models = [m.model for m in models_response.models]
                logger.debug(f"📋 Extracted {len(self.available_models)} models from ListResponse.models")
            elif isinstance(models_response, dict) and 'models' in models_response:
                # Fallback: Format: {"models": [{"name": "...", ...}, ...]}
                models_list = models_response.get('models', [])
                self.available_models = [
                    m.get('name', str(m)) if isinstance(m, dict) else str(m) 
                    for m in models_list
                ]
                logger.debug(f"📋 Extracted {len(self.available_models)} models from dict format")
            elif isinstance(models_response, list):
                # Fallback: Format: [{"name": "...", ...}, ...]
                self.available_models = [
                    m.get('name', str(m)) if isinstance(m, dict) else str(m) 
                    for m in models_response
                ]
                logger.debug(f"📋 Extracted {len(self.available_models)} models from list format")
            else:
                # Unknown format
                logger.warning(f"⚠️ Unknown response format from Ollama: {type(models_response)}")
                logger.warning(f"   Has 'models' attr: {hasattr(models_response, 'models')}")
                logger.warning(f"   Is dict: {isinstance(models_response, dict)}")
                logger.warning(f"   Is list: {isinstance(models_response, list)}")
                self.available_models = []
            
            logger.info(f"📦 Found {len(self.available_models)} available models")
            for model in self.available_models:
                logger.info(f"   ✅ {model}")
        
        except Exception as e:
            logger.error(f"❌ Could not list Ollama models: {str(e)}")
            if models_response is not None:
                logger.error(f"   Response type: {type(models_response)}")
            self.available_models = []
    
    def _check_models_availability(self):
        """Check if required models are available"""
        models_to_check = {
            'text': self.text_model,
            'embedding': self.embedding_model,
            'ocr': self.ocr_model
        }
        
        for model_type, model_name in models_to_check.items():
            is_available = any(model_name.lower() in m.lower() for m in self.available_models)
            self.model_status[model_type] = {
                'name': model_name,
                'available': is_available
            }
            
            status = "✅" if is_available else "❌"
            logger.info(f"{status} {model_type.upper()} model '{model_name}': {'available' if is_available else 'NOT FOUND'}")
            
            if not is_available:
                logger.warning(f"   To install: ollama pull {model_name}")
    
    def is_ready(self) -> bool:
        """Check if Ollama service is ready with all required models"""
        if not self.client:
            return False
        
        all_ready = all(
            self.model_status.get(mtype, {}).get('available', False)
            for mtype in ['text', 'embedding', 'ocr']
        )
        return all_ready
    
    def get_status(self) -> Dict:
        """Get service status and model availability"""
        return {
            'ollama_host': self.ollama_host,
            'connected': self.client is not None,
            'total_models': len(self.available_models),
            'models': self.model_status,
            'ready': self.is_ready()
        }
    
    # ==================== TEXT GENERATION ====================
    
    async def generate_text(self, 
                          prompt: str,
                          model: str = None,
                          temperature: float = 0.7,
                          top_p: float = 0.9,
                          top_k: int = 40,
                          max_tokens: int = 1000) -> str:
        """
        Generate text response using LLM
        ⚡ Optimized: Supports mistral:7b for fast inference
        
        Args:
            prompt: Input prompt
            model: Model to use (default: self.text_model = 'mistral:7b')
            temperature: Creativity (0.0-1.0, higher = more creative)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
        """
        if not self.client:
            logger.error("❌ Ollama client not initialized")
            raise RuntimeError("Ollama service not available")
        
        model = model or self.text_model
        
        try:
            # Verify model is available
            if model not in self.available_models:
                logger.warning(f"⚠️  Model '{model}' not in available models: {self.available_models}")
                logger.warning(f"   Available models: {self.available_models}")
                logger.warning(f"   Attempting to use {model} anyway...")
            
            logger.debug(f"🤖 Generating text with {model}...")
            logger.debug(f"   Params: temp={temperature}, top_p={top_p}, max_tokens={max_tokens}")
            
            response = await asyncio.to_thread(
                self._sync_generate_text,
                prompt, model, temperature, top_p, top_k, max_tokens
            )
            
            logger.debug(f"✅ Text generation completed with {model}")
            return response
        
        except Exception as e:
            logger.error(f"❌ Text generation error with {model}: {str(e)}")
            raise
    
    def _sync_generate_text(self, prompt: str, model: str, 
                           temperature: float, top_p: float, 
                           top_k: int, max_tokens: int) -> str:
        """Synchronous text generation (for threading)"""
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt,
                stream=False,
                options={
                    'temperature': temperature,
                    'top_p': top_p,
                    'top_k': top_k,
                    'num_predict': max_tokens,
                }
            )
            
            return response.get('response', '').strip()
        
        except Exception as e:
            logger.error(f"Error in sync text generation: {str(e)}")
            raise
    
    async def generate_text_stream(self,
                                  prompt: str,
                                  model: str = None,
                                  temperature: float = 0.7,
                                  top_p: float = 0.9,
                                  top_k: int = 40,
                                  max_tokens: int = 1000) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming response
        
        Args:
            prompt: Input prompt
            model: Model to use
            temperature: Creativity level
            top_p: Nucleus sampling
            top_k: Top-k sampling
            max_tokens: Max response length
            
        Yields:
            Text chunks as they're generated
        """
        if not self.client:
            raise RuntimeError("Ollama service not available")
        
        model = model or self.text_model
        
        try:
            logger.debug(f"🤖 Streaming text with {model}...")
            
            response = self.client.generate(
                model=model,
                prompt=prompt,
                stream=True,
                options={
                    'temperature': temperature,
                    'top_p': top_p,
                    'top_k': top_k,
                    'num_predict': max_tokens,
                }
            )
            
            for chunk in response:
                text = chunk.get('response', '')
                if text:
                    yield text
        
        except Exception as e:
            logger.error(f"❌ Streaming error: {str(e)}")
            raise
    
    # ==================== EMBEDDINGS ====================
    
    async def generate_embedding(self, text: str, 
                                model: str = None) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            model: Embedding model (default: bge-m3)
            
        Returns:
            Embedding vector as list of floats
        """
        if not self.client:
            raise RuntimeError("Ollama service not available")
        
        model = model or self.embedding_model
        
        try:
            text = text.strip()
            if not text:
                raise ValueError("Empty text provided")
            
            logger.debug(f"📊 Generating embedding with {model}...")
            
            embedding = await asyncio.to_thread(
                self._sync_generate_embedding,
                text, model
            )
            
            return embedding
        
        except Exception as e:
            logger.error(f"❌ Embedding generation error: {str(e)}")
            raise
    
    def _sync_generate_embedding(self, text: str, model: str) -> List[float]:
        """Synchronous embedding generation (for threading)"""
        try:
            response = self.client.embeddings(
                model=model,
                prompt=text
            )
            
            embedding = response.get('embedding', [])
            if not embedding:
                logger.warning(f"Empty embedding returned from {model}")
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error in sync embedding: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str],
                                       model: str = None,
                                       batch_size: int = 10) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Embedding model
            batch_size: Process batch size (for memory efficiency)
            
        Returns:
            List of embedding vectors
        """
        if not self.client:
            raise RuntimeError("Ollama service not available")
        
        model = model or self.embedding_model
        texts = [t.strip() for t in texts if t.strip()]
        
        if not texts:
            return []
        
        try:
            embeddings = []
            
            # Process in batches to avoid memory issues
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.debug(f"Processing embedding batch {i//batch_size + 1}...")
                
                for text in batch:
                    embedding = await self.generate_embedding(text, model)
                    embeddings.append(embedding)
            
            logger.info(f"✅ Generated embeddings for {len(embeddings)} texts")
            return embeddings
        
        except Exception as e:
            logger.error(f"❌ Batch embedding error: {str(e)}")
            raise
    
    # ==================== OCR ====================
    
    async def extract_text_from_image(self, 
                                     image_path: str,
                                     model: str = None) -> str:
        """
        Extract text from image using OCR model
        
        Args:
            image_path: Path to image file
            model: OCR model (default: deepseek-ocr)
            
        Returns:
            Extracted text
        """
        if not self.client:
            raise RuntimeError("Ollama service not available")
        
        model = model or self.ocr_model
        
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            logger.info(f"🔍 Extracting text from {image_path} using {model}...")
            
            # Read image as base64
            import base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Use vision API
            response = await asyncio.to_thread(
                self._sync_extract_ocr,
                image_data, model
            )
            
            logger.info(f"✅ OCR extraction complete ({len(response)} chars)")
            return response
        
        except Exception as e:
            logger.error(f"❌ OCR extraction error: {str(e)}")
            raise
    
    def _sync_extract_ocr(self, image_base64: str, model: str) -> str:
        """Synchronous OCR (for threading)"""
        try:
            # For vision models in Ollama, we use generate with image
            response = self.client.generate(
                model=model,
                prompt="Extract all text from this image. Return only the extracted text.",
                images=[image_base64],
                stream=False
            )
            
            return response.get('response', '').strip()
        
        except Exception as e:
            logger.error(f"Error in sync OCR: {str(e)}")
            raise
    
    async def extract_text_from_images_batch(self,
                                            image_paths: List[str],
                                            model: str = None) -> Dict[str, str]:
        """
        Extract text from multiple images
        
        Args:
            image_paths: List of image paths
            model: OCR model
            
        Returns:
            Dictionary mapping image path to extracted text
        """
        if not self.client:
            raise RuntimeError("Ollama service not available")
        
        model = model or self.ocr_model
        results = {}
        
        try:
            for image_path in image_paths:
                try:
                    text = await self.extract_text_from_image(image_path, model)
                    results[image_path] = text
                except Exception as e:
                    logger.error(f"Failed to extract text from {image_path}: {str(e)}")
                    results[image_path] = f"[ERROR: {str(e)}]"
            
            logger.info(f"✅ Batch OCR complete for {len(results)} images")
            return results
        
        except Exception as e:
            logger.error(f"❌ Batch OCR error: {str(e)}")
            raise
    
    # ==================== UTILITY METHODS ====================
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry
        Note: This is synchronous and blocks until download completes
        
        Args:
            model_name: Name of model to pull (e.g., 'llama3.1:8b')
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Ollama client not available")
            return False
        
        try:
            logger.info(f"⬇️ Pulling model: {model_name}")
            logger.info("This may take several minutes depending on model size...")
            
            # Pull model - this blocks until complete
            self.client.pull(model_name)
            
            logger.info(f"✅ Model {model_name} pulled successfully")
            
            # Refresh model list
            self._sync_list_models()
            self._check_models_availability()
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error pulling model {model_name}: {str(e)}")
            return False
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model"""
        try:
            if not self.client:
                return None
            
            info = self.client.show(model_name)
            return info
        
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return None
    
    def list_all_models(self) -> List[str]:
        """Get list of all available models"""
        return self.available_models.copy()
    
    def get_model_details(self) -> Dict:
        """Get detailed information about configured models"""
        return {
            'text_model': {
                'name': self.text_model,
                'status': self.model_status.get('text', {}).get('available', False)
            },
            'embedding_model': {
                'name': self.embedding_model,
                'status': self.model_status.get('embedding', {}).get('available', False)
            },
            'ocr_model': {
                'name': self.ocr_model,
                'status': self.model_status.get('ocr', {}).get('available', False)
            }
        }


# Global instance (optional, for singleton pattern)
_ollama_instance: Optional[OllamaService] = None


def get_ollama_service(
    ollama_host: str = None,
    text_model: str = "mistral:7b-instruct",
    embedding_model: str = "bge-m3:latest",
    ocr_model: str = "deepseek-ocr:latest"
) -> OllamaService:
    """
    Get or create Ollama service instance
    
    Args:
        ollama_host: Ollama server URL
        text_model: Text generation model name
        embedding_model: Embedding model name
        ocr_model: OCR model name
        
    Returns:
        OllamaService instance
    """
    global _ollama_instance
    
    if _ollama_instance is None:
        _ollama_instance = OllamaService(
            ollama_host=ollama_host,
            text_model=text_model,
            embedding_model=embedding_model,
            ocr_model=ocr_model
        )
    
    return _ollama_instance
