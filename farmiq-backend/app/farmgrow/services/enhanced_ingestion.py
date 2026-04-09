"""
Enhanced Document Ingestion Service with Table Extraction
Integrates DocumentProcessor for comprehensive document handling
"""
import logging
import os
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Import our enhanced document processor
try:
    from app.farmgrow.services.document_processor import DocumentProcessor
except ImportError:
    DocumentProcessor = None
    logger.warning("DocumentProcessor not available")


class EnhancedDocumentIngestionService:
    """
    Enhanced document ingestion with:
    - Multi-format support (PDF, DOCX, XLSX, TXT, Images)
    - Table extraction and structure preservation
    - Intelligent chunking with context awareness
    - Section-based processing
    """
    
    def __init__(self,
                 libraries_path: str = None,
                 ocr_service=None,
                 embedding_service=None,
                 embedding_store=None,
                 chunk_size: int = 256,
                 chunk_overlap: int = 50):
        """
        Initialize enhanced document ingestion.
        
        Args:
            libraries_path: Path to documents folder
            ocr_service: OCR service for images/scanned documents
            embedding_service: Service to generate embeddings
            embedding_store: Store for embeddings
            chunk_size: Size of text chunks (words)
            chunk_overlap: Overlap between chunks
        """
        self.libraries_path = libraries_path or "./libraries"
        self.ocr_service = ocr_service
        self.embedding_service = embedding_service
        self.embedding_store = embedding_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize document processor
        self.doc_processor = DocumentProcessor(ocr_service=ocr_service)
        
        self.processed_documents: Dict[str, Dict] = {}
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_chunks': 0,
            'total_tables': 0,
            'start_time': datetime.now()
        }
        
        logger.info(f"🚀 Enhanced Document Ingestion Service initialized")
        logger.info(f"   Libraries path: {self.libraries_path}")
        logger.info(f"   Chunk size: {chunk_size} words, overlap: {chunk_overlap}")
    
    async def ingest_all_documents(self) -> Dict:
        """
        Ingest all documents from libraries folder.
        Supports multiple formats.
        
        Returns:
            Ingestion result summary
        """
        try:
            if not os.path.exists(self.libraries_path):
                logger.warning(f"Libraries path not found: {self.libraries_path}")
                return {
                    'status': 'error',
                    'message': f'Path not found: {self.libraries_path}',
                    'successfully_ingested': 0,
                    'failed': 0
                }
            
            logger.info(f"🔍 Scanning libraries folder: {self.libraries_path}")
            
            # Find all supported document files
            supported_exts = ['pdf', 'docx', 'xlsx', 'txt', 'png', 'jpg', 'jpeg']
            all_files = []
            
            for ext in supported_exts:
                all_files.extend(Path(self.libraries_path).glob(f'**/*.{ext}'))
            
            self.stats['total_files'] = len(all_files)
            logger.info(f"   Found {len(all_files)} supported documents")
            
            # Get already-embedded documents
            already_embedded = set()
            if self.embedding_store:
                try:
                    metadata_file = Path(self.embedding_store.storage_dir) / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f) or {}
                            for chunk_id, chunk_meta in metadata.items():
                                if 'metadata' in chunk_meta and 'document_name' in chunk_meta['metadata']:
                                    already_embedded.add(chunk_meta['metadata']['document_name'])
                        logger.info(f"   📋 Found {len(already_embedded)} embedded documents")
                except Exception as e:
                    logger.debug(f"Could not read metadata.json: {e}")
            
            # Check if all files already embedded
            if already_embedded and len(already_embedded) >= len(all_files):
                logger.info(f"   ⏭️  All {len(all_files)} documents already embedded")
                return {
                    'status': 'complete',
                    'successfully_ingested': 0,
                    'failed': 0,
                    'skipped': len(all_files),
                    'message': 'All documents already embedded'
                }
            
            # Ingest new files
            files_to_ingest = [f for f in all_files if f.name not in already_embedded]
            logger.info(f"   📄 Ingesting {len(files_to_ingest)} new documents")
            
            for file_path in files_to_ingest:
                try:
                    await self.ingest_document(str(file_path))
                    self.stats['successful'] += 1
                except Exception as e:
                    logger.error(f"   ❌ Failed to ingest {file_path.name}: {str(e)}")
                    self.stats['failed'] += 1
            
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            
            return {
                'status': 'complete',
                'successfully_ingested': self.stats['successful'],
                'failed': self.stats['failed'],
                'skipped': len(already_embedded),
                'total_chunks': self.stats['total_chunks'],
                'total_tables': self.stats['total_tables'],
                'elapsed_seconds': round(elapsed, 2),
                'documents': list(self.processed_documents.keys())
            }
        
        except Exception as e:
            logger.error(f"❌ Ingestion error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'successfully_ingested': self.stats['successful'],
                'failed': self.stats['failed']
            }
    
    async def ingest_document(self, file_path: str) -> Dict:
        """
        Ingest a single document with enhanced processing.
        
        Handles:
        - Text extraction and chunking
        - Table extraction and storage
        - Image/scanned page OCR
        - Metadata preservation
        """
        try:
            file_path = str(file_path)
            file_name = Path(file_path).name
            document_id = str(uuid.uuid4())
            
            logger.info(f"📄 Processing: {file_name}")
            
            # Process document with enhanced processor
            doc_content = await self.doc_processor.process_document(file_path)
            
            # Create text chunks
            chunks = self._chunk_document(
                doc_content['text'],
                document_id,
                file_name,
                doc_content.get('sections', [])
            )
            logger.info(f"   ✅ Created {len(chunks)} chunks")
            
            # Generate embeddings if available
            if self.embedding_service and self.embedding_store:
                logger.info(f"   Generating embeddings...")
                await self._generate_embeddings(chunks, document_id, file_name)
                logger.info(f"   ✅ Embeddings stored")
            
            # Store table data separately if tables found
            tables = doc_content.get('tables', [])
            if tables:
                self._store_table_metadata(document_id, file_name, tables)
                self.stats['total_tables'] += len(tables)
                logger.info(f"   📊 Stored {len(tables)} tables")
            
            # Track document
            self.processed_documents[document_id] = {
                'file': file_name,
                'path': file_path,
                'format': doc_content.get('format'),
                'chunks': len(chunks),
                'tables': len(tables),
                'metadata': doc_content.get('metadata', {}),
                'ingested_at': datetime.now().isoformat()
            }
            
            self.stats['total_chunks'] += len(chunks)
            logger.info(f"✅ Completed: {file_name}")
            
            return {
                'document_id': document_id,
                'file': file_name,
                'chunks': len(chunks),
                'tables': len(tables)
            }
        
        except Exception as e:
            logger.error(f"❌ Error ingesting {file_path}: {str(e)}")
            raise
    
    def _chunk_document(self, text: str, document_id: str, file_name: str, 
                        sections: List[Dict] = None) -> List[Dict]:
        """
        Chunk document text intelligently using sections.
        
        Args:
            text: Full document text
            document_id: Document UUID
            file_name: Original file name
            sections: Detected sections with boundaries
        
        Returns:
            List of chunks with metadata
        """
        chunks = []
        words = text.split()
        
        # If sections available, respect section boundaries
        if sections and len(sections) > 1:
            logger.debug(f"   Using {len(sections)} section boundaries for chunking")
            # Use simple section-based chunking
            for section_idx, section in enumerate(sections):
                start = section.get('start', 0)
                end = section.get('end', len(text))
                section_text = text[start:end]
                
                # Create chunks within this section
                section_chunks = self._create_chunks(
                    section_text, document_id, file_name, section_idx
                )
                chunks.extend(section_chunks)
        else:
            # Simple word-based chunking
            chunks = self._create_chunks(text, document_id, file_name)
        
        return chunks
    
    def _create_chunks(self, text: str, document_id: str, file_name: str, 
                      section_idx: int = 0) -> List[Dict]:
        """
        Create fixed-size chunks with overlap.
        
        Args:
            text: Text to chunk
            document_id: Document UUID
            file_name: Original file name
            section_idx: Section index for tracking
        
        Returns:
            List of chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 10:  # Minimum chunk size
                chunk = {
                    'id': f"{document_id}_chunk_{len(chunks)}",
                    'text': chunk_text,
                    'document_id': document_id,
                    'document_name': file_name,
                    'section': section_idx,
                    'chunk_index': len(chunks),
                    'created_at': datetime.now().isoformat()
                }
                chunks.append(chunk)
        
        return chunks
    
    def _store_table_metadata(self, document_id: str, file_name: str, 
                             tables: List[Dict]) -> None:
        """
        Store table metadata for later reference/retrieval.
        
        Tables are stored in a separate metadata file for efficient lookup.
        """
        try:
            if not self.embedding_store:
                return
            
            metadata_file = Path(self.embedding_store.storage_dir) / "tables_metadata.json"
            
            # Load existing table metadata
            tables_meta = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    tables_meta = json.load(f) or {}
            
            # Add new tables
            for table in tables:
                table_id = str(uuid.uuid4())
                tables_meta[table_id] = {
                    'document_id': document_id,
                    'document_name': file_name,
                    'page_or_sheet': table.get('page') or table.get('sheet_name'),
                    'row_count': len(table.get('rows', [])),
                    'col_count': len(table.get('rows', [None])[0]) if table.get('rows') else 0,
                    'markdown': table.get('markdown', ''),
                    'stored_at': datetime.now().isoformat()
                }
            
            # Save updated metadata
            with open(metadata_file, 'w') as f:
                json.dump(tables_meta, f, indent=2)
            
            logger.debug(f"Stored metadata for {len(tables)} tables")
        
        except Exception as e:
            logger.warning(f"Could not store table metadata: {e}")
    
    async def _generate_embeddings(self, chunks: List[Dict], document_id: str, 
                                   file_name: str) -> None:
        """
        Generate and store embeddings for chunks.
        
        Args:
            chunks: List of text chunks
            document_id: Document UUID
            file_name: Original file name
        """
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = await self.embedding_service.embed(chunk['text'])
                
                # Store embedding
                chunk_id = chunk['id']
                self.embedding_store.add_embedding(
                    chunk_id=chunk_id,
                    embedding=embedding,
                    content=chunk['text'],
                    metadata={
                        'document_id': document_id,
                        'document_name': file_name,
                        'chunk_index': chunk['chunk_index']
                    }
                )
            
            except Exception as e:
                logger.warning(f"Failed to generate embedding for chunk: {e}")
                continue
    
    def get_stats(self) -> Dict:
        """Get ingestion statistics."""
        return self.stats.copy()
