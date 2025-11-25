

# utils/query_classifier.py

import re
import logging
from typing import Dict, List, Tuple, Optional
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Import de la configuration
from utils.config import MISTRAL_API_KEY, CHAT_MODEL, COMMUNE_NAME, RAG_TOPK, RAG_MIN_SIMILARITY, RAG_MIN_COVERAGE
from utils.vector_store import VectorStoreManager # NOUVEAU: Import pour la garde sémantique

# Configuration du logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class QueryClassifier:
    """
    Classe pour classifier les requêtes et déterminer si elles nécessitent RAG.
    Implémente la Garde Sémantique et le Fallback LLM-as-a-Judge.
    """
    
    def __init__(self):
        """Initialise le classificateur de requêtes."""
        self.mistral_client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
        
        # EXPERTISE RAG: Accès au VectorStore pour la garde sémantique
        # On ne charge l'index que pour l'interrogation (pas pour la recherche de chunks)
        try:
            # On crée une instance du VectorStoreManager pour accéder à l'index et aux méthodes d'embedding.
            self.vs = VectorStoreManager() 
        except Exception as e:
            logger.error(f"Impossible d'initialiser VectorStoreManager dans QueryClassifier: {e}")
            self.vs = None
        
        # Questions générales (small-talk) = DIRECT
        self.general_patterns = [
            r"^(bonjour|salut|hello|coucou|hey|bonsoir)[\s\.,!]*$",
            r"^(merci|thanks|thank you|je te remercie)[\s\.,!]*$",
            r"^(comment ça va|ça va|comment vas-tu|comment allez-vous)[\s\.,!?]*$",
            r"^(au revoir|bye|à bientôt|à plus tard|à la prochaine)[\s\.,!]*$",
            r"^(qui es[- ]tu|qu'es[- ]tu|que fais[- ]tu|comment fonctionnes[- ]tu|tu es quoi)[\s\?]*$",
            r"^(aide|help|sos|besoin d'aide)[\s\.,!?]*$",
        ]
        
        # Mots-clés qui FORCENT le RAG (basés sur votre liste fournie)
        # Utilisé comme première couche de filtrage rapide (non-sémantique)
        self.hard_rag_keywords = [
            "procédure", "raccourcis", "m3", "oxypharm", "as400", "sos100", "sts100", 
            "écran", "code", "champ", "validation", "commande", "litige", "inventaire"
        ]
    
    def needs_rag(self, query: str) -> Tuple[bool, float, str]:
        """    
        Détermine si une requête nécessite RAG en utilisant une logique multi-étapes.
        
        Args:
            query: Requête de l'utilisateur (peut être réécrite par le module de chat)
            
        Returns:
            Tuple (besoin_rag, confiance, raison)
        """
        ql = query.lower().strip()
        
        # 1. Vérification Small-Talk / Général -> DIRECT (Confiance très élevée)
        for pattern in self.general_patterns:
            if re.match(pattern, ql):
                return False, 0.95, "Question générale ou salutation"
        
        # 2. Vérification Mots-Clés Durs -> RAG (Confiance moyenne)
        commune_keywords_found = [kw for kw in self.hard_rag_keywords if kw in ql]
        if commune_keywords_found:
            keywords_str = ", ".join(commune_keywords_found)
            return True, 0.75, f"Contient un mot-clé fort pour RAG: {keywords_str}"

        # 3. Garde Sémantique via FAISS (Recherche réelle)
        decision, conf, reason = self._semantic_gate(query)
        if decision is not None:
            return decision, conf, reason # Décision tranchée par la similarité

        # 4. Fallback LLM si disponible (Zone grise)
        if self.mistral_client:
            return self._classify_with_llm(query)
        
        # 5. Défaut Prudent
        return False, 0.5, "Aucun critère de RAG détecté (défaut DIRECT)"
        
    # ----------------------------- Garde sémantique -----------------------------

    def _semantic_gate(self, query: str) -> Tuple[Optional[bool], float, str]:
        """
        Essaye de décider RAG/DIRECT via la similarité FAISS pour les cas ambigus.
        """
        if not self.vs or self.vs.index is None:
            logger.warning("Index Faiss non disponible pour la garde sémantique.")
            return None, 0.0, "Index Faiss non disponible"
            
        try:
            # On ne met PAS de min_score pour la recherche initiale: on veut voir la distribution.
            # On regarde 2*RAG_TOPK pour avoir plus de données que le simple Top-K
            results = self.vs.search(query_text=query, k=RAG_TOPK * 2, min_score=None) 
            if not results:
                return None, 0.0, ""

            # Convertir les scores en [0..1] (ils sont en %)
            sims = [r["score"] / 100.0 for r in results] 
            
            # Nombre de chunks dont la similarité dépasse le seuil
            coverage = sum(1 for s in sims if s >= RAG_MIN_SIMILARITY)
            max_sim = max(sims)

            # Règle 1: Signal Fort -> RAG
            if coverage >= RAG_MIN_COVERAGE and max_sim >= RAG_MIN_SIMILARITY:
                # Confiance bornée par la similarité max
                conf = min(0.90, max(0.70, max_sim)) # Minimum 0.70 si les critères sont remplis
                src = results[0].get("metadata", {}).get("source", "doc")
                return True, conf, f"Garde Sémantique: Similarité élevée (max={max_sim:.2f}, cover={coverage}) via {src}"

            # Règle 2: Signal Très Faible -> DIRECT
            if max_sim < (RAG_MIN_SIMILARITY - 0.20): # Si la meilleure similarité est très basse
                conf = min(0.90, 0.6 + (1 - max_sim) * 0.3)
                return False, conf, f"Garde Sémantique: Similarité doc trop faible (max={max_sim:.2f}) → DIRECT"

            # Règle 3: Zone Grise
            return None, 0.0, "Zone grise sémantique, renvoi au LLM"

        except Exception as e:
            logger.error(f"[SemanticGate] Erreur lors de la recherche sémantique: {e}")
            return None, 0.0, "Erreur lors de l'évaluation sémantique"

    # ------------------------------- Fallback LLM -------------------------------

    def _classify_with_llm(self, query: str) -> Tuple[bool, float, str]:
        """
        Utilise le LLM pour trancher entre 'RAG' et 'DIRECT' dans les cas ambigus.
        """
        if not self.mistral_client:
            return False, 0.5, "LLM indisponible pour la classification"
            
        try:
            system_prompt = f"""
Vous êtes un classificateur de requêtes pour un assistant interne de {COMMUNE_NAME}.
Votre rôle est de déterminer si la question nécessite la documentation interne (PDF Oxypharm / M3).
Ceci est une étape de dernier recours pour les questions ambiguës.

Répondez UNIQUEMENT par "RAG" ou "DIRECT" suivi d'une brève explication :
- "RAG" si la question porte sur des informations spécifiques à la documentation interne (procédures, écrans, champs, codes, workflows, etc.).
- "DIRECT" si c'est une question générale ou sans lien clair avec la documentation.

Exemples :
Question : "Quelle est la procédure de litige lors de la réception de marchandise ?"
Réponse : RAG - Demande d’informations spécifiques à la doc M3

Question : "c'est quoi M3 ?"
Réponse : RAG - Question sur un concept interne

Question : "Qu’est-ce que l’intelligence artificielle ?"
Réponse : DIRECT - Question générale
""".strip()

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=query),
            ]

            resp = self.mistral_client.chat(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=50,
            )

            result = resp.choices[0].message.content.strip()
            logger.info(f"Classification LLM pour '{query}': {result}")

            if result.upper().startswith("RAG"):
                reason = result.replace("RAG -", "").replace("RAG:", "").replace("RAG", "").strip()
                return True, 0.85, reason or "LLM: Nécessite la doc interne"
            if result.upper().startswith("DIRECT"):
                reason = result.replace("DIRECT -", "").replace("DIRECT:", "").replace("DIRECT", "").strip()
                return False, 0.85, reason or "LLM: Question générale"

            # Réponse ambiguë -> prudence, on force le RAG pour ne pas manquer d'information
            return True, 0.60, "LLM ambigu → RAG par précaution"

        except Exception as e:
            logger.error(f"Erreur classification LLM: {e}")
            # En cas d'erreur API, rester prudent (DIRECT) pour éviter du RAG hors-sujet
            return False, 0.50, f"Erreur LLM : {e}"
