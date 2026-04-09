"""
FarmGrow Document Ingestion Service
Processes documents from libraries folder:
- Extracts text from PDFs
- Handles image OCR
- Chunks documents intelligently
- Generates and stores embeddings locally

Stores: NumPy embeddings + JSON metadata for fast retrieval
"""
import logging
import os
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    logger.warning("PyPDF2 not installed. PDF parsing disabled.")


class DocumentIngestionService:
    """
    Ingest and process documents from libraries folder.
    
    Features:
    - Scan for PDF documents
    - Extract text from PDFs
    - Handle scanned documents with OCR
    - Chunk documents intelligently
    - Generate embeddings for chunks
    - Store embeddings locally (NumPy + JSON) AND in-memory cache
    
    Storage Architecture:
    ✅ Local File-Based:
       - Embeddings: ./embeddings_cache/embeddings/*.npy (NumPy binary files)
       - Metadata: ./embeddings_cache/metadata.json (chunk info)
       - Fast access, persistent across sessions
    
    ✅ In-Memory Cache (LocalEmbeddingStore):
       - Dict of {chunk_id -> embedding_vector, content, metadata}
       - Loaded from disk on initialization
       - Used for fast retrieval during RAG queries
       - No separate database required for MVP
    """
    
    def __init__(self,
                 libraries_path: str = None,
                 ocr_service=None,
                 embedding_service=None,
                 embedding_store=None,
                 chunk_size: int = 256,
                 chunk_overlap: int = 50):
        """
        Initialize document ingestion service.
        
        Args:
            libraries_path: Path to libraries folder containing documents
            ocr_service: OCR service for image text extraction
            embedding_service: Embedding service for generating embeddings
            embedding_store: Local embedding store (NumPy + JSON)
            chunk_size: Size of text chunks (words)
            chunk_overlap: Overlap between consecutive chunks
        """
        self.libraries_path = libraries_path or "./libraries"
        self.ocr_service = ocr_service
        self.embedding_service = embedding_service
        self.embedding_store = embedding_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Keep track of processed documents
        self.processed_documents: Dict[str, Dict] = {}
        self.ingestion_stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_chunks': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"📚 Initializing Document Ingestion Service")
        logger.info(f"   Libraries path: {self.libraries_path}")
        logger.info(f"   Chunk size: {chunk_size} words, overlap: {chunk_overlap} words")
    
    async def ingest_all_documents(self) -> Dict:
        """
        Ingest all documents from libraries folder.
        
        Skips documents that have already been embedded.
        
        Returns:
            Ingestion result with file counts and status
        """
        try:
            if not os.path.exists(self.libraries_path):
                logger.warning(f"Libraries path not found: {self.libraries_path}")
                return {
                    'status': 'error',
                    'message': f'Path not found: {self.libraries_path}',
                    'successfully_ingested': 0,
                    'failed': 0,
                    'total_chunks': 0
                }
            
            logger.info(f"🔍 Scanning libraries folder: {self.libraries_path}")
            
            # Find all PDF files
            pdf_files = list(Path(self.libraries_path).glob('**/*.pdf'))
            self.ingestion_stats['total_files'] = len(pdf_files)
            
            logger.info(f"   Found {len(pdf_files)} PDF files")
            
            # Get already-embedded document names from metadata.json
            already_embedded_docs = set()
            if self.embedding_store:
                try:
                    metadata_file = Path(self.embedding_store.storage_dir) / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f) or {}
                            # Extract unique document names from metadata
                            for chunk_id, chunk_meta in metadata.items():
                                if 'metadata' in chunk_meta and 'document_name' in chunk_meta['metadata']:
                                    doc_name = chunk_meta['metadata']['document_name']
                                    already_embedded_docs.add(doc_name)
                        logger.info(f"   📋 Found {len(already_embedded_docs)} unique documents in metadata.json")
                except Exception as e:
                    logger.debug(f"Could not read metadata.json for skip detection: {e}")
            
            # If no documents in metadata but embeddings exist, assume all are embedded
            if not already_embedded_docs and self.embedding_store and len(self.embedding_store.embeddings) > 0:
                logger.info(f"   ℹ️  {len(self.embedding_store.embeddings)} embeddings exist but no metadata - assuming all PDFs are embedded")
                logger.info(f"   ⏭️  Skipping all {len(pdf_files)} files (embeddings already cached)")
                return {
                    'status': 'complete',
                    'successfully_ingested': 0,
                    'failed': 0,
                    'total_chunks': 0,
                    'skipped_already_embedded': len(pdf_files),
                    'elapsed_seconds': 0,
                    'message': 'All documents already in embedding cache',
                    'documents': []
                }
            
            # Check which PDFs need embedding
            files_to_ingest = []
            skipped_count = 0
            for pdf_path in pdf_files:
                file_name = pdf_path.name
                if file_name in already_embedded_docs:
                    logger.info(f"⏭️  Skipping already embedded: {file_name}")
                    skipped_count += 1
                else:
                    files_to_ingest.append(pdf_path)
            
            logger.info(f"   ⏭️  Skipped {skipped_count} already-embedded files")
            logger.info(f"   📄 Will ingest {len(files_to_ingest)} new files")
            
            # Process each file
            for pdf_path in files_to_ingest:
                try:
                    await self.ingest_document(str(pdf_path))
                    self.ingestion_stats['successful'] += 1
                except Exception as e:
                    logger.error(f"   ❌ Failed to ingest {pdf_path.name}: {str(e)}")
                    self.ingestion_stats['failed'] += 1
            
            elapsed = (datetime.now() - self.ingestion_stats['start_time']).total_seconds()
            
            return {
                'status': 'complete',
                'successfully_ingested': self.ingestion_stats['successful'],
                'failed': self.ingestion_stats['failed'],
                'total_chunks': self.ingestion_stats['total_chunks'],
                'skipped_already_embedded': skipped_count,
                'elapsed_seconds': elapsed,
                'documents': list(self.processed_documents.keys())
            }
        
        except Exception as e:
            logger.error(f"❌ Ingestion error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'successfully_ingested': self.ingestion_stats['successful'],
                'failed': self.ingestion_stats['failed'],
                'total_chunks': self.ingestion_stats['total_chunks']
            }
    
    async def ingest_document(self, file_path: str) -> Dict:
        """
        Ingest a single document.
        
        Args:
            file_path: Path to document
        
        Returns:
            Ingestion result with chunk count
        """
        try:
            file_path = str(file_path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_name = Path(file_path).name
            document_id = str(uuid.uuid4())
            
            logger.info(f"📄 Ingesting: {file_name}")
            
            # Extract text from PDF
            logger.info(f"   Extracting text...")
            text, metadata = await self._extract_text_from_pdf(file_path)
            
            if not text:
                raise ValueError(f"No text extracted from {file_name}")
            
            logger.info(f"   ✅ Extracted {len(text)} characters")
            
            # Chunk document
            logger.info(f"   Chunking document...")
            chunks = self._chunk_text(text, document_id, file_name)
            logger.info(f"   ✅ Created {len(chunks)} chunks")
            
            # Generate embeddings if service available
            if self.embedding_service and self.embedding_store:
                logger.info(f"   Generating embeddings...")
                await self._generate_and_store_embeddings(chunks, document_id, file_name)
                logger.info(f"   ✅ Stored embeddings locally")
            
            # Track document
            self.processed_documents[document_id] = {
                'file': file_name,
                'path': file_path,
                'chunks': chunks,
                'metadata': metadata,
                'ingested_at': datetime.now().isoformat(),
                'chunk_count': len(chunks)
            }
            
            self.ingestion_stats['total_chunks'] += len(chunks)
            
            logger.info(f"✅ Ingestion complete: {file_name}")
            return {
                'document_id': document_id,
                'file': file_name,
                'chunks_created': len(chunks)
            }
        
        except Exception as e:
            logger.error(f"❌ Error ingesting document: {str(e)}")
            raise
    
    async def _extract_text_from_pdf(self, file_path: str) -> Tuple[str, Dict]:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF
        
        Returns:
            Tuple of (text, metadata)
        """
        try:
            if not PyPDF2:
                raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
            
            text_parts = []
            metadata = {'pages': 0, 'has_images': False}
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata['pages'] = len(reader.pages)
                
                for page_num, page in enumerate(reader.pages, 1):
                    # Extract text
                    page_text = page.extract_text()
                    text_parts.append(f"[Page {page_num}]\n{page_text}")
                    
                    # Check for images (simple heuristic)
                    if '/Image' in str(page):
                        metadata['has_images'] = True
                        logger.info(f"   🖼️ Found images on page {page_num}")
                        
                        # Try OCR if available
                        if self.ocr_service:
                            try:
                                image_text = await self.ocr_service.extract_text_from_page(file_path, page_num)
                                if image_text:
                                    text_parts.append(f"[OCR Page {page_num}]\n{image_text}")
                            except Exception as e:
                                logger.debug(f"OCR failed for page {page_num}: {str(e)}")
            
            full_text = "\n".join(text_parts)
            return full_text, metadata
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _chunk_text(self, text: str, document_id: str, file_name: str) -> List[Dict]:
        """
        Chunk text into overlapping segments.
        
        Args:
            text: Full document text
            document_id: Document ID
            file_name: Original file name
        
        Returns:
            List of chunks with metadata
        """
        try:
            words = text.split()
            chunks = []
            
            stride = self.chunk_size - self.chunk_overlap
            
            for i in range(0, len(words), stride):
                chunk_words = words[i:i + self.chunk_size]
                chunk_text = " ".join(chunk_words)
                
                chunk = {
                    'chunk_id': f"{document_id}_chunk_{len(chunks)}",
                    'document_id': document_id,
                    'document_name': file_name,
                    'content': chunk_text,
                    'start_word_idx': i,
                    'end_word_idx': min(i + self.chunk_size, len(words)),
                    'word_count': len(chunk_words),
                    'page_number': self._estimate_page_number(i, len(words), text.count('[Page'))
                }
                
                chunks.append(chunk)
            
            return chunks
        
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            return []
    
    async def _generate_and_store_embeddings(self,
                                            chunks: List[Dict],
                                            document_id: str,
                                            file_name: str) -> bool:
        """
        Generate and store embeddings for chunks.
        
        Args:
            chunks: List of chunks
            document_id: Document ID
            file_name: File name
        
        Returns:
            True if successful
        """
        try:
            # Extract just the text content for embedding
            chunk_texts = [chunk['content'] for chunk in chunks]
            
            # Generate embeddings in batch
            logger.info(f"   🪡 Generating embeddings for {len(chunks)} chunks...")
            embeddings = await self.embedding_service.embed_batch(chunk_texts)
            
            # Store embeddings
            logger.info(f"   💾 Storing embeddings...")
            for chunk, embedding in zip(chunks, embeddings):
                await self.embedding_store.save_embedding(
                    chunk_id=chunk['chunk_id'],
                    content=chunk['content'],
                    embedding=embedding,
                    document_id=document_id,
                    page_number=chunk.get('page_number'),
                    metadata={
                        'document_name': file_name,
                        'word_count': chunk['word_count']
                    }
                )
            
            logger.info(f"   ✅ Stored {len(embeddings)} embeddings")
            return True
        
        except Exception as e:
            logger.error(f"Error generating/storing embeddings: {str(e)}")
            return False
    
    def _estimate_page_number(self, word_idx: int, total_words: int, page_count: int) -> int:
        """Estimate page number based on word position."""
        if page_count == 0:
            return 1
        return min(int((word_idx / total_words) * page_count) + 1, page_count)
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID."""
        return self.processed_documents.get(document_id)
    
    def get_all_documents(self) -> List[Dict]:
        """Get all ingested documents."""
        return list(self.processed_documents.values())
    
    def get_ingestion_stats(self) -> Dict:
        """Get ingestion statistics."""
        return {
            'total_files_processed': self.ingestion_stats['total_files'],
            'successfully_ingested': self.ingestion_stats['successful'],
            'failed': self.ingestion_stats['failed'],
            'total_chunks': self.ingestion_stats['total_chunks'],
            'documents_in_memory': len(self.processed_documents)
        }
    
    def get_ingested_files(self) -> List[str]:
        """Get list of already-ingested file names."""
        return [doc['file'] for doc in self.processed_documents.values()]
    
    def has_ingested_documents(self) -> bool:
        """Check if any documents have been ingested."""
        return len(self.processed_documents) > 0


# Global instance
_ingestion_service_instance: Optional[DocumentIngestionService] = None


def get_ingestion_service(
    libraries_path: str = None,
    ocr_service=None,
    embedding_service=None,
    embedding_store=None
) -> DocumentIngestionService:
    """Get or create ingestion service instance."""
    global _ingestion_service_instance
    
    if _ingestion_service_instance is None:
        _ingestion_service_instance = DocumentIngestionService(
            libraries_path=libraries_path,
            ocr_service=ocr_service,
            embedding_service=embedding_service,
            embedding_store=embedding_store
        )
    
    return _ingestion_service_instance
