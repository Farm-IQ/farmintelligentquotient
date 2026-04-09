"""
FarmIQ LLM Model Configuration
Manages local Ollama models for all operations:
- Text Generation: Llama 3.1 8B and Mistral 7B (⚡ Optimized for speed)
- Embeddings: BGE-M3 (384 dimensions, multilingual)
- OCR: DeepSeek-OCR (image text extraction)

Model Selection:
- DEFAULT_TEXT_MODEL: mistral:7b-instruct (5-6x faster than llama3.1:8b)
"""
import os
from typing import List, Dict, Optional


class ModelConfig:
    """Configuration for a single LLM model"""
    
    def __init__(self, 
                 name: str,
                 ollama_name: str,
                 parameters: int,
                 min_ram_gb: int,
                 speed: str,
                 description: str,
                 model_type: str = 'text'):
        """
        Initialize model configuration
        
        Args:
            name: Display name
            ollama_name: Ollama model identifier
            parameters: Model size in millions
            min_ram_gb: Minimum RAM required
            speed: 'fast', 'moderate', or 'very_fast'
            description: Model description
            model_type: 'text', 'embedding', or 'ocr'
        """
        self.name = name
        self.ollama_name = ollama_name
        self.parameters = parameters
        self.min_ram_gb = min_ram_gb
        self.speed = speed
        self.description = description
        self.model_type = model_type
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'ollama_name': self.ollama_name,
            'parameters': self.parameters,
            'min_ram_gb': self.min_ram_gb,
            'speed': self.speed,
            'description': self.description,
            'model_type': self.model_type
        }


# ============================================================================
# TEXT GENERATION MODELS
# ============================================================================

TEXT_MODELS = {
    'llama3.1:8b': ModelConfig(
        name='Llama 3.1 8B',
        ollama_name='llama3.1:8b',
        parameters=8000,
        min_ram_gb=16,
        speed='moderate',
        description='Strong reasoning and broad agricultural knowledge',
        model_type='text'
    ),
    
    'mistral:7b-instruct': ModelConfig(
        name='Mistral 7B Instruct',
        ollama_name='mistral:7b-instruct',
        parameters=7000,
        min_ram_gb=8,
        speed='fast',
        description='Very fast with low latency for quick responses (RECOMMENDED)',
        model_type='text'
    ),
    
    'neural-chat:7b': ModelConfig(
        name='Neural Chat 7B',
        ollama_name='neural-chat:7b',
        parameters=7000,
        min_ram_gb=8,
        speed='fast',
        description='Optimized for conversational AI with farming context',
        model_type='text'
    ),
    
    'phi:2.7b': ModelConfig(
        name='Phi 2.7B',
        ollama_name='phi:2.7b',
        parameters=2700,
        min_ram_gb=4,
        speed='very_fast',
        description='Ultra-fast lightweight model (for low-resource environments)',
        model_type='text'
    ),
}

# ============================================================================
# EMBEDDING MODEL
# ============================================================================

EMBEDDING_MODEL = ModelConfig(
    name='BGE-M3',
    ollama_name='bge-m3:latest',
    parameters=335,
    min_ram_gb=4,
    speed='fast',
    description='Multilingual embeddings to understand user questions (CRITICAL for RAG quality)',
    model_type='embedding'
)

# ============================================================================
# OCR MODEL
# ============================================================================

OCR_MODEL = ModelConfig(
    name='DeepSeek OCR',
    ollama_name='deepseek-ocr:latest',
    parameters=2000,
    min_ram_gb=6,
    speed='moderate',
    description='Extract text from images, diagrams, and documents',
    model_type='ocr'
)

# ============================================================================
# DEFAULT MODEL SELECTIONS
# ============================================================================

DEFAULT_TEXT_MODEL = 'mistral:7b-instruct'  # ⚡ OPTIMIZED: 5-6x faster than llama3.1:8b
EMBEDDING_MODEL_NAME = 'bge-m3:latest'
OCR_MODEL_NAME = 'deepseek-ocr:latest'


# ============================================================================
# MODEL SELECTOR
# ============================================================================

class ModelSelector:
    """
    Intelligently select the best text model for a given query
    
    Implements query-aware model selection to balance speed and quality
    """
    
    @staticmethod
    def select_text_model(query: str) -> str:
        """
        Select between Llama 3.1 or Mistral based on query
        
        Uses Mistral (faster) for simple queries, Llama 3.1 (higher quality)
        for complex queries.
        
        Args:
            query: User's question
            
        Returns:
            Selected model name (ollama format)
        """
        query_lower = query.lower()
        
        # Use Mistral for fast/simple queries
        fast_keywords = [
            'how much', 'when to', 'quick', 'fast', 'simple',
            'what is', 'how to plant', 'how many', 'what time'
        ]
        
        if any(kw in query_lower for kw in fast_keywords):
            return 'mistral:7b-instruct'  # Fast response
        
        # Use Llama 3.1 for everything else (better quality)
        return 'llama3.1:8b'
    
    @staticmethod
    def get_model_config(model_name: str) -> Dict:
        """Get configuration for a specific text model"""
        if model_name in TEXT_MODELS:
            return TEXT_MODELS[model_name].to_dict()
        return TEXT_MODELS[DEFAULT_TEXT_MODEL].to_dict()
    
    @staticmethod
    def get_embedding_config() -> Dict:
        """Get BGE-M3 embedding model configuration"""
        return EMBEDDING_MODEL.to_dict()
    
    @staticmethod
    def get_ocr_config() -> Dict:
        """Get DeepSeek OCR model configuration"""
        return OCR_MODEL.to_dict()
    
    @staticmethod
    def get_all_text_models() -> List[Dict]:
        """Get all available text models"""
        return [model.to_dict() for model in TEXT_MODELS.values()]
    
    @staticmethod
    def get_all_models() -> Dict:
        """Get all available models grouped by type"""
        return {
            'text_models': [model.to_dict() for model in TEXT_MODELS.values()],
            'embedding_model': EMBEDDING_MODEL.to_dict(),
            'ocr_model': OCR_MODEL.to_dict()
        }
