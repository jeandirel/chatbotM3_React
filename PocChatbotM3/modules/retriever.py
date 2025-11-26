import logging
import numpy as np
import faiss
from typing import List, Dict, Any
from .embedding import EmbeddingService
from .vector_store import VectorStoreService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RetrieverService:
    """
    Service responsible for retrieving relevant documents based on a query.
    Handles embedding the query, searching the vector store, and expanding context.
    """

    def __init__(self, embedding_service: EmbeddingService, vector_store_service: VectorStoreService):
        self.embedding_service = embedding_service
        self.vector_store = vector_store_service
        self._chunk_map_by_source = {}
        self._build_chunk_map()

    def _build_chunk_map(self):
        """Builds a map of chunks by source for context expansion."""
        self._chunk_map_by_source = {}
        for i, chunk in enumerate(self.vector_store.document_chunks):
            source = chunk["metadata"].get("source")
            chunk_id_in_doc = chunk["metadata"].get("chunk_id_in_doc")
            
            if source and chunk_id_in_doc is not None:
                if source not in self._chunk_map_by_source:
                    self._chunk_map_by_source[source] = []
                
                self._chunk_map_by_source[source].append({
                    "global_index": i,
                    "local_id": chunk_id_in_doc,
                    "chunk": chunk
                })
        
        for source in self._chunk_map_by_source:
            self._chunk_map_by_source[source].sort(key=lambda x: x["local_id"])

    def retrieve(self, query_text: str, k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Retrieves relevant chunks for a given query.
        """
        if not query_text:
            return []

        # 1. Embed Query
        query_embedding = self.embedding_service.generate_embeddings([query_text])
        if query_embedding is None:
            return []
        
        faiss.normalize_L2(query_embedding)

        # 2. Search Vector Store (fetch more candidates for re-ranking)
        search_k = k * 4 
        scores, indices = self.vector_store.search(query_embedding, k=search_k)

        # 3. Process Results & Expand Context
        results_map = {}
        seen_ids = set()
        min_score_percent = min_score * 100

        if indices.size > 0:
            for i, idx in enumerate(indices[0]):
                if 0 <= idx < len(self.vector_store.document_chunks):
                    chunk = self.vector_store.get_chunk(idx)
                    chunk_id = chunk["id"]
                    raw_score = float(scores[0][i])
                    similarity = raw_score * 100

                    if similarity >= min_score_percent and chunk_id not in seen_ids:
                        # Add Main Chunk
                        results_map[chunk_id] = {
                            "score": similarity,
                            "raw_score": raw_score,
                            "text": chunk["text"],
                            "metadata": chunk["metadata"]
                        }
                        seen_ids.add(chunk_id)

                        # Add Adjacent Chunks (Context Expansion)
                        source = chunk["metadata"].get("source")
                        local_id = chunk["metadata"].get("chunk_id_in_doc")
                        if source and local_id is not None:
                            neighbors = self._get_adjacent_chunks(source, local_id)
                            for neighbor in neighbors:
                                n_id = neighbor["id"]
                                if n_id not in seen_ids:
                                    results_map[n_id] = {
                                        "score": similarity * 0.9, # Slightly lower score for neighbors
                                        "raw_score": raw_score * 0.9,
                                        "text": neighbor["text"],
                                        "metadata": {**neighbor["metadata"], "context_type": "neighbor"}
                                    }
                                    seen_ids.add(n_id)

        return list(results_map.values())

    def _get_adjacent_chunks(self, source_path: str, local_id: int, num_neighbors: int = 1) -> List[Dict[str, Any]]:
        """Retrieves chunks adjacent to the given chunk ID within the same document."""
        if source_path not in self._chunk_map_by_source:
            return []

        doc_chunks = self._chunk_map_by_source[source_path]
        main_idx = -1
        for i, meta in enumerate(doc_chunks):
            if meta["local_id"] == local_id:
                main_idx = i
                break
        
        if main_idx == -1:
            return []

        neighbors = []
        start = max(0, main_idx - num_neighbors)
        end = min(len(doc_chunks), main_idx + num_neighbors + 1)

        for i in range(start, end):
            if i != main_idx:
                neighbors.append(doc_chunks[i]["chunk"])
        
        return neighbors
