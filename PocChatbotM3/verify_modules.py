import sys
import os
import logging

# Add current directory to path
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

def verify_modules():
    try:
        logger.info("Importing modules...")
        from modules.ingestion import IngestionService
        from modules.preprocessing import PreprocessingService
        from modules.embedding import EmbeddingService
        from modules.vector_store import VectorStoreService
        from modules.retriever import RetrieverService
        from modules.reranking import RerankingService
        from modules.generation import GenerationService
        from modules.cache import CacheService
        from modules.session import SessionService
        from modules.auth import AuthService
        from modules.monitoring import MonitoringService
        
        logger.info("Initializing services...")
        ingestion = IngestionService()
        preprocessing = PreprocessingService()
        vector_store = VectorStoreService()
        reranking = RerankingService()
        cache = CacheService()
        session = SessionService()
        auth = AuthService()
        monitoring = MonitoringService()
        
        logger.info("All modules imported and initialized.")
        return True
    except Exception as e:
        with open("verify_log.txt", "w") as f:
            f.write(str(e))
            import traceback
            traceback.print_exc(file=f)
        return False

if __name__ == "__main__":
    if verify_modules():
        print("✅ Module verification SUCCESS")
    else:
        print("❌ Module verification FAILED")
