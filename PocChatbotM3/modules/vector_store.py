import os
import pickle
import faiss
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from utils.config import FAISS_INDEX_FILE, DOCUMENT_CHUNKS_FILE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Service responsible for managing the FAISS vector index and document chunks.
    """

    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.document_chunks: List[Dict[str, any]] = []
        self._load_index_and_chunks()

    def _load_index_and_chunks(self):
        """Loads FAISS index and chunks from disk."""
        if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE):
            try:
                logger.info(f"Loading FAISS index from {FAISS_INDEX_FILE}...")
                self.index = faiss.read_index(FAISS_INDEX_FILE)
                logger.info(f"Loading chunks from {DOCUMENT_CHUNKS_FILE}...")
                with open(DOCUMENT_CHUNKS_FILE, 'rb') as f:
                    self.document_chunks = pickle.load(f)
                logger.info(f"Index ({self.index.ntotal} vectors) and {len(self.document_chunks)} chunks loaded.")
            except Exception as e:
                logger.error(f"Error loading index/chunks: {e}")
                self.index = None
                self.document_chunks = []
        else:
            logger.warning("FAISS index or chunks file not found. Index is empty.")

    def save_index_and_chunks(self):
        """Saves FAISS index and chunks to disk."""
        if self.index is None or not self.document_chunks:
            logger.warning("Attempting to save empty index or chunks.")
            return

        os.makedirs(os.path.dirname(FAISS_INDEX_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(DOCUMENT_CHUNKS_FILE), exist_ok=True)

        try:
            faiss.write_index(self.index, FAISS_INDEX_FILE)
            with open(DOCUMENT_CHUNKS_FILE, 'wb') as f:
                pickle.dump(self.document_chunks, f)
            logger.info("Index and chunks saved successfully.")
        except Exception as e:
            logger.error(f"Error saving index/chunks: {e}")

    def create_index(self, embeddings: np.ndarray, chunks: List[Dict[str, any]]):
        """Creates a new FAISS index from embeddings and chunks."""
        if embeddings is None or len(chunks) == 0:
            logger.error("Cannot create index: No embeddings or chunks provided.")
            return

        if embeddings.shape[0] != len(chunks):
            logger.error(f"Mismatch: {embeddings.shape[0]} embeddings vs {len(chunks)} chunks.")
            return

        dimension = embeddings.shape[1]
        logger.info(f"Creating FAISS index (dim={dimension})...")
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.document_chunks = chunks
        
        logger.info(f"FAISS index created with {self.index.ntotal} vectors.")
        self.save_index_and_chunks()

    def search(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Searches the index for the k nearest neighbors.
        Returns distances (scores) and indices.
        """
        if self.index is None:
            logger.warning("Search failed: Index is empty.")
            return np.array([]), np.array([])

        return self.index.search(query_embedding, k)

    def get_chunk(self, index: int) -> Optional[Dict[str, any]]:
        """Retrieves a chunk by its index."""
        if 0 <= index < len(self.document_chunks):
            return self.document_chunks[index]
        return None
