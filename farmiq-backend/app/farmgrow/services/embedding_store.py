"""
FarmGrow Embedding Store - Local Storage Wrapper
Manages local in-memory embeddings storage for fast access.

This service provides embedding persistence and retrieval.
"""
import logging
from typing import Optional, Dict, List
import os
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class LocalEmbeddingStore:
    """
    Wrapper for local embedding storage using in-memory + file system.
    
    Features:
    - Save embeddings locally (JSON files)
    - In-memory cache for fast access
    - Fast similarity search
    - Batch operations for efficiency
    """
    
    def __init__(self, storage_dir: str = "./embeddings_cache"):
        """
        Initialize embedding store.
        
        Args:
            storage_dir: Directory for embedding storage
        """
        self.storage_dir = Path(storage_dir)
        self.embeddings = {}  # In-memory cache
        self.embeddings_dir = self.storage_dir / "embeddings"
        self.metadata_file = self.storage_dir / "metadata.json"
        
        # Create directory if it doesn't exist
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.embeddings_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing embeddings from disk
            self._load_embeddings_from_disk()
            
            total = len(self.embeddings)
            logger.info(f"✅ Initialized local embedding store at {storage_dir}")
            if total > 0:
                logger.info(f"   Loaded {total} existing embeddings from disk")
        except Exception as e:
            logger.error(f"Could not initialize embedding store: {e}")
            self.embeddings = {}
    
    def _load_embeddings_from_disk(self):
        """Load existing embeddings from disk (.npy files)"""
        try:
            import numpy as np
            
            if not self.embeddings_dir.exists():
                logger.debug(f"Embeddings directory not found: {self.embeddings_dir}")
                return
            
            # Load metadata if it exists
            metadata = {}
            if self.metadata_file.exists():
                try:
                    with open(self.metadata_file, 'r') as f:
                        metadata = json.load(f) or {}
                except Exception as e:
                    logger.warning(f"Could not load metadata.json: {e}")
            
            # Load all .npy files
            npy_files = list(self.embeddings_dir.glob("*.npy"))
            logger.debug(f"Found {len(npy_files)} embedding files to load")
            
            for npy_file in npy_files:
                try:
                    chunk_id = npy_file.stem  # filename without .npy extension
                    embedding = np.load(npy_file).tolist()
                    
                    # Get metadata if available
                    chunk_meta = metadata.get(chunk_id, {})
                    
                    self.embeddings[chunk_id] = {
                        "embedding": embedding,
                        "content": chunk_meta.get("content", ""),
                        "document_id": chunk_meta.get("document_id"),
                        "page_number": chunk_meta.get("page_number"),
                        "metadata": chunk_meta.get("metadata", {})
                    }
                except Exception as e:
                    logger.warning(f"Failed to load embedding {npy_file.name}: {e}")
                    continue
            
            logger.debug(f"Successfully loaded {len(self.embeddings)} embeddings from disk")
        except Exception as e:
            logger.error(f"Error loading embeddings from disk: {e}")
    
    async def save_embedding(self,
                            chunk_id: str,
                            content: str,
                            embedding,
                            document_id: str = None,
                            page_number: int = None,
                            metadata: dict = None) -> bool:
        """
        Save embedding to both local storage (disk) and in-memory cache.
        
        Saves to:
        1. Memory: self.embeddings dict
        2. Disk: ./embeddings_cache/embeddings/{chunk_id}.npy (NumPy binary)
        3. Metadata: ./embeddings_cache/metadata.json (chunk info)
        
        Args:
            chunk_id: Unique chunk identifier
            content: Chunk text content
            embedding: Embedding vector (numpy array or list)
            document_id: Document ID
            page_number: Page number
            metadata: Additional metadata
        
        Returns:
            True if successful
        """
        try:
            import numpy as np
            
            # Convert embedding to list if needed
            embedding_list = embedding if isinstance(embedding, list) else embedding.tolist()
            
            # Store in memory
            self.embeddings[chunk_id] = {
                "content": content,
                "embedding": embedding_list,
                "document_id": document_id,
                "page_number": page_number,
                "metadata": metadata or {}
            }
            
            # Save embedding to disk as .npy file
            npy_path = self.embeddings_dir / f"{chunk_id}.npy"
            np.save(npy_path, np.array(embedding_list))
            
            # Update metadata.json
            try:
                # Load existing metadata
                existing_metadata = {}
                if self.metadata_file.exists():
                    with open(self.metadata_file, 'r') as f:
                        existing_metadata = json.load(f) or {}
                
                # Add/update this chunk's metadata
                existing_metadata[chunk_id] = {
                    "content": content,
                    "document_id": document_id,
                    "page_number": page_number,
                    "metadata": metadata or {}
                }
                
                # Save back to metadata.json
                with open(self.metadata_file, 'w') as f:
                    json.dump(existing_metadata, f, indent=2)
            except Exception as e:
                logger.warning(f"Could not update metadata.json: {e}")
            
            logger.debug(f"Saved embedding for chunk {chunk_id} (to disk and memory)")
            return True
        except Exception as e:
            logger.error(f"Error saving embedding: {str(e)}")
            return False
    
    async def get_embedding(self, chunk_id: str) -> Optional[List]:
        """
        Retrieve embedding from local storage.
        
        Args:
            chunk_id: Chunk ID
        
        Returns:
            Embedding vector (as list) or None
        """
        try:
            if chunk_id in self.embeddings:
                return self.embeddings[chunk_id].get("embedding")
            return None
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return None
    
    async def search_similar(self, query_embedding, top_k: int = 5, threshold: float = 0.1) -> List[Dict]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            threshold: Similarity threshold
        
        Returns:
            List of similar chunks
        """
        try:
            import numpy as np
            
            query_vec = np.array(query_embedding)
            results = []
            
            for chunk_id, data in self.embeddings.items():
                emb = np.array(data["embedding"])
                # Cosine similarity
                similarity = np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-8)
                
                if similarity >= threshold:
                    results.append({
                        "chunk_id": chunk_id,
                        "content": data["content"],
                        "similarity": float(similarity),
                        "document_id": data.get("document_id")
                    })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get storage statistics.
        
        Returns:
            Statistics dict with total embeddings, chunks, etc.
        """
        try:
            return {
                "total_embeddings": len(self.embeddings),
                "total_chunks": len(self.embeddings),
                "storage_dir": str(self.storage_dir),
                "backend": "in-memory"
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {
                "total_embeddings": 0,
                "total_chunks": 0,
                "storage_dir": str(self.storage_dir),
                "error": str(e)
            }


# Backward compatibility alias
class EmbeddingStore(LocalEmbeddingStore):
    """Alias for LocalEmbeddingStore for backward compatibility"""
    pass
