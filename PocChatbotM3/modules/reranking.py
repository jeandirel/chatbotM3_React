import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RerankingService:
    """
    Service responsible for re-ordering retrieved documents to improve relevance and diversity.
    """

    def rerank(self, results: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks results using a heuristic approach (diversity of sources).
        """
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        final_results = []
        seen_sources = set()

        for result in results:
            if len(final_results) >= k:
                break

            source = result['metadata'].get('source')
            is_neighbor = result['metadata'].get('context_type') == 'neighbor'

            # Heuristic: Prioritize new sources, but allow neighbors (context)
            if source not in seen_sources or is_neighbor:
                final_results.append(result)
                if not is_neighbor:
                    seen_sources.add(source)
        
        logger.info(f"Reranked {len(results)} results to top {len(final_results)}.")
        return final_results
