import logging
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PreprocessingService:
    """
    Service responsible for cleaning and splitting text into chunks.
    """

    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            add_start_index=True,
        )

    def split_documents(self, documents: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Splits a list of document dictionaries into chunks.
        """
        logger.info(f"Splitting {len(documents)} documents into chunks (size={self.chunk_size}, overlap={self.chunk_overlap})...")
        
        all_chunks = []
        doc_counter = 0
        
        for doc in documents:
            langchain_doc = Document(page_content=doc["page_content"], metadata=doc["metadata"])
            chunks = self.text_splitter.split_documents([langchain_doc])
            
            logger.debug(f"Document '{doc['metadata'].get('filename', 'N/A')}' split into {len(chunks)} chunks.")

            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "id": f"{doc_counter}_{i}",
                    "text": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_id_in_doc": i,
                        "start_index": chunk.metadata.get("start_index", -1)
                    }
                }
                all_chunks.append(chunk_dict)
            doc_counter += 1

        logger.info(f"Total of {len(all_chunks)} chunks created.")
        return all_chunks
