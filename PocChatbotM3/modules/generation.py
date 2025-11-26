import logging
import datetime
import re
from typing import List, Dict, Tuple, Any
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from mistralai.exceptions import MistralAPIException
from utils.config import MISTRAL_API_KEY, CHAT_MODEL, COMMUNE_NAME

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GenerationService:
    """
    Service responsible for generating responses using the LLM (Mistral).
    Handles query rewriting, smalltalk detection, and RAG prompt construction.
    """

    SMALLTALK_PATTERNS = [
        r"^\s*bonjour\b", r"^\s*salut\b", r"^\s*bonsoir\b",
        r"^\s*(merci|thanks)\b", r"^\s*(coucou)\b", r"^\s*(hello)\b",
        r"\bcomment vas[- ]tu\b", r"\bcomment allez[- ]vous\b",
        r"\bbonne journ[eé]e\b", r"\bbonne soir[eé]e\b",
    ]

    SMALLTALK_RESPONSES = [
        "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
        "Salut ! Je suis prêt à répondre à vos questions sur la documentation M3.",
        "Bonjour ! N'hésitez pas à me donner un sujet ou un besoin précis.",
        "Heureux de vous retrouver. Que souhaitez-vous explorer ?",
    ]

    def __init__(self):
        self.client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
        if not self.client:
            logger.warning("Mistral Client not initialized. Generation will fail.")

    def is_smalltalk(self, query: str) -> bool:
        if not query: return False
        lowered = query.lower()
        return any(re.search(pattern, lowered) for pattern in self.SMALLTALK_PATTERNS)

    def get_smalltalk_response(self) -> str:
        idx = hash(datetime.datetime.now().isoformat()) % len(self.SMALLTALK_RESPONSES)
        return self.SMALLTALK_RESPONSES[idx]

    def rewrite_query(self, user_query: str, history_messages: List[Dict[str, str]]) -> Tuple[str, bool]:
        """Rewrites the query based on conversation history."""
        if not history_messages or not self.client:
            return user_query, False

        system_prompt = """
        Tu es un expert en réécriture de requêtes. Ton rôle est de réécrire la dernière question de l'utilisateur
        pour qu'elle soit contextuellement complète et compréhensible par un système de recherche (RAG),
        en utilisant l'historique de conversation fourni.
        Si la question est déjà autonome, retourne-la telle quelle.
        Réponds UNIQUEMENT avec la requête réécrite.
        """.strip()

        messages = [ChatMessage(role="system", content=system_prompt)]
        
        # Use last 4 messages for context
        for msg in history_messages[-4:]:
            if msg['role'] in ('user', 'assistant'):
                messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        
        messages.append(ChatMessage(role="user", content=f"Dernière question : {user_query}"))

        try:
            response = self.client.chat(model=CHAT_MODEL, messages=messages, temperature=0.0, max_tokens=150)
            rewritten = response.choices[0].message.content.strip()
            is_rewritten = rewritten.lower().strip() != user_query.lower().strip()
            if is_rewritten:
                logger.info(f"Query rewritten: {user_query} -> {rewritten}")
            return rewritten, is_rewritten
        except Exception as e:
            logger.error(f"Error rewriting query: {e}")
            return user_query, False

    def generate_rag_response(self, user_query: str, retrieved_docs: List[Dict[str, Any]], history: List[Dict[str, str]]) -> str:
        """Generates a response based on retrieved documents."""
        if not self.client:
            return "Error: LLM client not initialized."

        context_str = "\n\n---\n\n".join([
            f"Source: {doc['metadata'].get('source', 'Unknown')}\nContent: {doc['text']}"
            for doc in retrieved_docs
        ])

        system_prompt = f"""
        Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
        Répondez à la question de l'utilisateur en vous basant **UNIQUEMENT** sur la documentation fournie ci-dessous.
        Synthétisez l'information avec vos propres mots.
        Si l'information n'est pas dans le contexte, dites poliment que vous ne savez pas.
        Citez vos sources.

        Contexte:
        ---
        {context_str}
        ---
        """.strip()

        messages = [ChatMessage(role="system", content=system_prompt)]
        for msg in history[-8:]: # Include recent history
             messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        messages.append(ChatMessage(role="user", content=user_query))

        try:
            response = self.client.chat(model=CHAT_MODEL, messages=messages, temperature=0.2, max_tokens=2048)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return f"Error generating response: {e}"

    def generate_direct_response(self, user_query: str, history: List[Dict[str, str]]) -> str:
        """Generates a response without RAG (Direct mode)."""
        if not self.client: return "Error: LLM client not initialized."

        system_prompt = f"""
        Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
        Répondez à la question de l'utilisateur en utilisant vos connaissances générales.
        Soyez concis et utile.
        """.strip()

        messages = [ChatMessage(role="system", content=system_prompt)]
        for msg in history[-8:]:
             messages.append(ChatMessage(role=msg['role'], content=msg['content']))
        messages.append(ChatMessage(role="user", content=user_query))

        try:
            response = self.client.chat(model=CHAT_MODEL, messages=messages, temperature=0.2, max_tokens=2048)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating direct response: {e}")
            return f"Error generating response: {e}"
