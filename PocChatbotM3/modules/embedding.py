import logging
import numpy as np
from typing import List, Optional
from mistralai.client import MistralClient
from mistralai.exceptions import MistralAPIException
from utils.config import MISTRAL_API_KEY, EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service responsible for generating embeddings using Mistral API.
    """

    def __init__(self):
        self.client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
        if not self.client:
            logger.warning("Mistral Client not initialized. Embeddings cannot be generated.")

    def generate_embeddings(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Generates embeddings for a list of texts in batches.
        """
        if not self.client:
            logger.error("Cannot generate embeddings: MISTRAL_API_KEY missing.")
            return None
        
        if not texts:
            logger.warning("No text provided for embedding generation.")
            return None

        logger.info(f"Generating embeddings for {len(texts)} chunks (model: {EMBEDDING_MODEL})...")
        all_embeddings = []
        total_batches = (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
            batch_texts = texts[i:i + EMBEDDING_BATCH_SIZE]

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")
            try:
                response = self.client.embeddings(
                    model=EMBEDDING_MODEL,
                    input=batch_texts
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            except MistralAPIException as e:
                logger.error(f"Mistral API Error during embedding generation (batch {batch_num}): {e}")
                self._handle_failed_batch(all_embeddings, len(batch_texts))
            except Exception as e:
                logger.error(f"Unexpected error during embedding generation (batch {batch_num}): {e}")
                self._handle_failed_batch(all_embeddings, len(batch_texts))

        if not all_embeddings:
            logger.error("No embeddings could be generated.")
            return None

        embeddings_array = np.array(all_embeddings).astype('float32')
        logger.info(f"Embeddings generated successfully. Shape: {embeddings_array.shape}")
        return embeddings_array

    def _handle_failed_batch(self, all_embeddings: List, batch_size: int):
        """Adds zero vectors for failed batches to maintain alignment."""
        dim = len(all_embeddings[0]) if all_embeddings else 1024
        logger.warning(f"Adding {batch_size} zero vectors of dimension {dim} for failed batch.")
        all_embeddings.extend([np.zeros(dim, dtype='float32')] * batch_size)
