# """
# Module de classification des requêtes pour déterminer si une question nécessite RAG simple 
# """

# import re
# import logging
# from typing import Dict, List, Tuple, Optional
# from mistralai.client import MistralClient
# from mistralai.models.chat_completion import ChatMessage

# from utils.config import MISTRAL_API_KEY, CHAT_MODEL, COMMUNE_NAME

# class QueryClassifier:
#     """
#     Classe pour classifier les requêtes et déterminer si elles nécessitent RAG
#     """
    
#     def __init__(self):
#         """
#         Initialise le classificateur de requêtes
#         """
#         self.mistral_client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
        
#         # Mots-clés liés à la commune qui suggèrent un besoin de RAG
#         self.commune_keywords = [
#     COMMUNE_NAME.lower(),
#     "écran",
#     "ligne",
#     "contrat",
#     "code",
#     "client",
#     "article",
#     "saisie",
#     "commande",
#     "entrée",
#     "stock",
#     "intervention",
#     "quantité",
#     "numéro",
#     "v1",
#     "validation",
#     "lignes",
#     "devis",
#     "appareil",
#     "m3",
#     "prix",
#     "oxypharm",
#     "raccourcis",
#     "produit",
#     "clique",
#     "ordre",
#     "cliquer",
#     "informations",
#     "statut",
#     "f4",
#     "lot",
#     "facturation",
#     "transaction",
#     "préparation",
#     "location",
#     "fiche",
#     "champ",
#     "matériel",
#     "emplacement",
#     "tarif",
#     "étiquette",
#     "patient",
#     "livraison",
#     "npi",
#     "fournisseur",
#     "dépôt",
#     "immo",
#     "réception",
#     "gestion",
#     "inventaire",
#     "module",
#     "accès",
#     "information",
#     "pulse",
#     "interventions",
#     "options",
#     "ensuite",
#     "bouton",
#     "visualisation",
#     "clic",
#     "rcpa",
#     "tournée",
#     "impression",
#     "inter",
#     "pda",
#     "facture",
#     "sans",
#     "prise",
#     "demande",
#     "autre",
#     "44",
#     "peut",
#     "réf",
#     "user",
#     "vue",
#     "reçu",
#     "audit",
#     "clavier",
#     "nouvelle",
#     "suivi",
#     "qté",
#     "ecran",
#     "cours",
#     "sélectionnez",
#     "f8",
#     "slide",
#     "mission",
#     "droite",
#     "chaque",
#     "modification",
#     "accueil",
#     "plusieurs",
#     "mvs",
#     "marchandise",
#     "besoin",
#     "remplir",
#     "site",
#     "edition",
#     "cases",
#     "motif",
#     "plateforme",
#     "commandes",
#     "20",
#     "installation",
#     "vérifier",
#     "automatiquement",
#     "ctrl",
#     "début",
#     "apres",
#     "traçabilité",
#     "lorsque",
#     "planning",
#     "2021",
#     "changer",
#     "contrats",
#     "stocks",
#     "page",
#     "notez",
#     "as400",
#     "temps",
#     "texte",
#     "directement",
#     "emplacements",
#     "devant",
#     "pouvoir",
#     "sélection",
#     "quantités",
#     "cliquant",
#     "outils",
#     "indiquez",
#     "mms100",
#     "visualiser",
#     "première",
#     "chez",
#     "arrivez",
#     "sortie",
#     "transferts",
#     "dossier",
#     "suspension",
#     "correction",
#     "connexion",
#     "afin",
#     "passage",
#     "emp",
#     "2024",
#     "faite",
#     "14",
#     "icone",
#     "revenez",
#     "procédure",
#     "fab",
#     "secteur",
#     "actif",
#     "ro140",
#     "note",
#     "période",
#     "dessous",
#     "clients",
#     "passe",
#     "tout",
#     "passant",
#     "édition",
#     "imprimante",
#     "imprimer",
#     "prescription",
#     "pharmacie",
#     "désignation",
#     "renseignez",
#     "destination",
#     "comme",
#     "conduite",
#     "nécessaire",
#     "bien",
#     "rto",
#     "installateur",
#     "trouvant",
#     "taper",
#     "terminer",
#     "mettant",
#     "achat",
#     "scannez",
#     "fonction",
#     "haut",
#     "permettre",
#     "actions",
#     "connaitre",
#     "préventives",
#     "différents",
#     "passer",
#     "copie",
#     "litige",
#     "colis",
#     "faisant",
#     "vers",
#     "activité",
#     "sinon",
#     "annuler",
#     "lvo",
#     "navigateur",
#     "zones",
#     "indiquant",
#     "état",
#     "nouvel",
#     "suivre",
#     "ouvre",
#     "corriger",
#     "dates",
#     "sortir",
#     "initiale",
#     "clôture",
#     "commentaire",
#     "nomenclature",
#     "face",
#     "toute",
#     "indique",
#     "tableau",
#     "st",
#     "agences",
#     "v2",
#     "lancer",
#     "paramétrage",
#     "enregistrer",
#     "ajouter",
#     "mobilité",
#     "sts100",
#     "paramètres",
#     "atelier",
#     "tarifs",
#     "incident",
#     "flux",
#     "sos100",
#     "afficher",
#     "étiquettes",
#     "bénéficiaire",
#     "bouteilles",
#     "sbv",
#     "expiration",
#     "etablissement",
#     "onglet",
#     "détail",
#     "prérequis",
#     "possibilité",
#     "traitement",
#     "correspond",
#     "voulue",
#     "prerequis",
#     "identité",
#     "oxygène",
#     "expédition",
#     "facturer",
#     "sme",
#     "rapport",
#     "plastique",
#     "niveau",
#     "reste",
#     "disponible",
#     "origine",
#     "manipulation",
#     "doivent",
#     "service",
#     "mws060",
#     "pharmacien",
#     "appareils",
#     "référencé",
#     "produits",
#     "défectueux",
#     "compte",
#     "fonctionnalités",
#     "automatique",
#     "échange",
#     "cur",
#     "rattaché",
#     "infos",
#     "amo",
#     "correspondant",
#     "papier",
#     "PDA"
#     "NPI",
#     "M3",
#     "MVS",
#     "oxypharm",
#     "oxygène",
# ]

        
#         # Questions générales qui ne nécessitent pas de RAG
#         self.general_patterns = [
#             r"^(bonjour|salut|hello|coucou|hey|bonsoir)[\s\.,!]*$",
#             r"^(merci|thanks|thank you|je te remercie)[\s\.,!]*$",
#             r"^(comment ça va|ça va|comment vas-tu|comment allez-vous)[\s\.,!?]*$",
#             r"^(au revoir|bye|à bientôt|à plus tard|à la prochaine)[\s\.,!]*$",
#             r"^(qui es[- ]tu|qu'es[- ]tu|que fais[- ]tu|comment fonctionnes[- ]tu|tu es quoi)[\s\?]*$",
#             r"^(aide|help|sos|besoin d'aide)[\s\.,!?]*$"
#         ]
    
#     def needs_rag(self, query: str) -> Tuple[bool, float, str]:
#         """    
#         Détermine si une requête nécessite RAG
        
#         Args:
#             query: Requête de l'utilisateur
            
#         Returns:
#             Tuple (besoin_rag, confiance, raison)
#         """
#         # Convertir la requête en minuscules pour la comparaison
#         query_lower = query.lower()
        
#         # 1. Vérifier les patterns de questions générales (salutations, remerciements, etc.)
#         for pattern in self.general_patterns:
#             if re.match(pattern, query_lower):
#                 return False, 0.95, "Question générale ou salutation"
        
#         # 2. Vérifier la présence de mots-clés liés à la commune
#         commune_keywords_found = [kw for kw in self.commune_keywords if kw in query_lower]
#         if commune_keywords_found:
#             keywords_str = ", ".join(commune_keywords_found)
#             return True, 0.9, f"Contient des mots-clés liés à la commune: {keywords_str}"
        
#         # 3. Utiliser le LLM pour les cas ambigus
#         if self.mistral_client:
#             return self._classify_with_llm(query)
        
#         # Par défaut, utiliser RAG pour les questions longues (plus de 5 mots)
#         words = query.split()
#         if len(words) > 5:
#             return True, 0.6, "Question complexe (plus de 5 mots)"
        
#         # Par défaut, ne pas utiliser RAG
#         return False, 0.5, "Aucun critère spécifique détecté"
    
#     def _classify_with_llm(self, query: str) -> Tuple[bool, float, str]:
#         """
#         Utilise le LLM pour classifier la requête
        
#         Args:
#             query: Requête de l'utilisateur
            
#         Returns:
#             Tuple (besoin_rag, confiance, raison)
#         """
#         try:
#             system_prompt = f"""
# Vous êtes un classificateur de requêtes pour un assistant virtuel interne de {COMMUNE_NAME}.
# Votre tâche est de déterminer si une question nécessite une recherche dans la documentation interne? qui n'est rien d'autre que les documents PDF du dossier Oxypharm de ce projet.

# Répondez UNIQUEMENT par "RAG" ou "DIRECT" suivi d'une brève explication :
# - "RAG" si la question porte sur des informations spécifiques à la base de données(documentation M3)par exemple(procédures internes, etc.).
# - "DIRECT" si c'est une question générale, une salutation ou une demande qui ne nécessite pas la documentation interne.

# Exemples :
# Question : "Bonjour, comment ça va ?"
# Réponse : DIRECT - Simple salutation

# Question : "Quelle est la procedure de litige lors de la réception de marchandise ?"
# Réponse : RAG - Demande d’informations spécifiques à la documentation

# Question : "c'est quoi M3 ?"
# Réponse : RAG - Demande d’informations spécifiques à la documentation

# Question : "Qu’est-ce que l’intelligence artificielle ?"
# Réponse : DIRECT - Question générale de connaissance
# """

            
#             messages = [
#                 ChatMessage(role="system", content=system_prompt),
#                 ChatMessage(role="user", content=query)
#             ]
            
#             response = self.mistral_client.chat(
#                 model=CHAT_MODEL,
#                 messages=messages,
#                 temperature=0.1,  # Température basse pour des réponses cohérentes
#                 max_tokens=50  # Réponse courte suffisante
#             )
            
#             result = response.choices[0].message.content.strip()
#             logging.info(f"Classification LLM pour '{query}': {result}")
            
#             # Analyser la réponse
#             if result.startswith("RAG"):
#                 confidence = 0.85  # Confiance élevée dans la décision du LLM
#                 reason = result.replace("RAG - ", "").replace("RAG-", "").replace("RAG:", "").strip()
#                 return True, confidence, reason
#             elif result.startswith("DIRECT"):
#                 confidence = 0.85
#                 reason = result.replace("DIRECT - ", "").replace("DIRECT-", "").replace("DIRECT:", "").strip()
#                 return False, confidence, reason
#             else:
#                 # Réponse ambiguë, utiliser RAG par défaut
#                 return True, 0.6, "Classification ambiguë, utilisation de RAG par précaution"
                
#         except Exception as e:
#             logging.error(f"Erreur lors de la classification avec LLM: {e}")
#             # En cas d'erreur, utiliser RAG par défaut
#             return True, 0.5, f"Erreur de classification: {str(e)}"
        
        
        

# """
# Module de classification des requêtes pour déterminer si une question nécessite RAG.
# Logique :
#   1) Small-talk/général -> DIRECT
#   2) Garde sémantique via FAISS (VectorStoreManager.search)
#        - si similarité OK -> RAG
#        - si très faible -> DIRECT
#        - sinon -> on laisse le LLM trancher
#   3) Fallback LLM -> "RAG" ou "DIRECT" + raison courte
# """

# import re
# import logging
# from typing import Tuple, Optional

# from mistralai.client import MistralClient
# from mistralai.models.chat_completion import ChatMessage

# # Imports projet
# from utils.config import MISTRAL_API_KEY, CHAT_MODEL, COMMUNE_NAME  # :contentReference[oaicite:0]{index=0}
# from utils.vector_store import VectorStoreManager  # :contentReference[oaicite:1]{index=1}

# # --- Seuils de routage RAG (on essaie d'abord depuis config.py, sinon valeurs par défaut) ---
# try:
#     from utils.config import RAG_TOPK, RAG_MIN_SIMILARITY, RAG_MIN_COVERAGE  # optionnel
# except Exception:
#     RAG_TOPK = 5               # on regarde les 5 meilleurs chunks
#     RAG_MIN_SIMILARITY = 0.40  # échelle 0..1 (nos scores FAISS sont % -> reconvertis en 0..1)
#     RAG_MIN_COVERAGE = 2       # au moins 2 chunks >= seuil

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# class QueryClassifier:
#     """
#     Classe pour classifier les requêtes et déterminer si elles nécessitent RAG.
#     Dépendances :
#       - utils.vector_store.VectorStoreManager.search(query_text, k, min_score)  # :contentReference[oaicite:2]{index=2}
#       - config CHAT_MODEL / MISTRAL_API_KEY / COMMUNE_NAME                      # :contentReference[oaicite:3]{index=3}
#     """

#     def __init__(self):
#         self.mistral_client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
#         self.vs = VectorStoreManager()  # accès à l’index FAISS (chargé si présent)  # :contentReference[oaicite:4]{index=4}

#         # Questions générales (salutations, remerciements, aide générique, etc.) = pas de RAG
#         self.general_patterns = [
#             r"^(bonjour|salut|hello|coucou|hey|bonsoir)[\s\.,!]*$",
#             r"^(merci|thanks|thank you|je te remercie)[\s\.,!]*$",
#             r"^(comment ça va|ça va|comment vas-tu|comment allez-vous)[\s\.,!?]*$",
#             r"^(au revoir|bye|à bientôt|à plus tard|à la prochaine)[\s\.,!]*$",
#             r"^(qui es[- ]tu|qu'es[- ]tu|que fais[- ]tu|comment fonctionnes[- ]tu|tu es quoi)[\s\?]*$",
#             r"^(aide|help|sos|besoin d'aide)[\s\.,!?]*$",
#         ]

#     def needs_rag(self, query: str) -> Tuple[bool, float, str]:
#         """
#         Détermine si une requête nécessite RAG.

#         Args:
#             query: texte de l'utilisateur
#         Returns:
#             (need_rag: bool, confidence: float 0..1, reason: str)
#         """
#         ql = query.lower().strip()

#         # 1) Small-talk ou général -> DIRECT
#         for pattern in self.general_patterns:
#             if re.match(pattern, ql):
#                 return False, 0.95, "Question générale ou salutation"

#         # 2) Garde sémantique via FAISS
#         decision, conf, reason = self._semantic_gate(query)
#         if decision is not None:
#             return decision, conf, reason

#         # 3) Fallback LLM si disponible
#         if self.mistral_client:
#             return self._classify_with_llm(query)

#         # 4) Défaut prudent si pas de LLM
#         return False, 0.5, "Pas de signal sémantique suffisant → DIRECT"

#     # ----------------------------- Garde sémantique -----------------------------

#     def _semantic_gate(self, query: str) -> Tuple[Optional[bool], float, str]:
#         """
#         Essaye de décider RAG/DIRECT via la similarité FAISS.
#         Règles :
#           - On récupère top-k résultats (scores en % dans VectorStoreManager.search)
#           - coverage = nb de chunks avec sim >= RAG_MIN_SIMILARITY
#           - si coverage >= RAG_MIN_COVERAGE ET max_sim >= RAG_MIN_SIMILARITY -> RAG
#           - si max_sim < (RAG_MIN_SIMILARITY - 0.10) -> DIRECT
#           - sinon -> None (zone grise : laisser le LLM trancher)
#         """
#         try:
#             # On ne met PAS de min_score ici : on veut lire toute la distribution et décider nous-mêmes
#             results = self.vs.search(query_text=query, k=RAG_TOPK, min_score=None)  # :contentReference[oaicite:5]{index=5}
#             if not results:
#                 # Index absent/vide ou pas d'embedding possible : on laisse l'étape suivante décider
#                 return None, 0.0, ""

#             sims = [r["score"] / 100.0 for r in results]  # convertit % -> [0..1]
#             coverage = sum(1 for s in sims if s >= RAG_MIN_SIMILARITY)
#             max_sim = max(sims)

#             if coverage >= RAG_MIN_COVERAGE and max_sim >= RAG_MIN_SIMILARITY:
#                 # Confiance bornée par la similarité max
#                 conf = min(0.95, max(0.70, max_sim))
#                 src = results[0].get("metadata", {}).get("source", "doc")
#                 return True, conf, f"Similarité doc élevée (max={max_sim:.2f}, cover={coverage}) via {src}"

#             # Signal très faible → éviter RAG inutile
#             if max_sim < (RAG_MIN_SIMILARITY - 0.10):
#                 conf = min(0.9, 0.6 + 0.4 * (1 - max_sim))
#                 return False, conf, f"Similarité doc faible (max={max_sim:.2f}) → DIRECT"

#             # Zone grise → laisser le LLM décider
#             return None, 0.0, ""

#         except Exception as e:
#             logger.error(f"[SemanticGate] erreur: {e}")
#             return None, 0.0, ""

#     # ------------------------------- Fallback LLM -------------------------------

#     def _classify_with_llm(self, query: str) -> Tuple[bool, float, str]:
#         """
#         Utilise le LLM pour trancher entre 'RAG' et 'DIRECT' dans les cas ambigus.
#         Le prompt mentionne explicitement que la doc interne = PDF d'Oxypharm/M3.
#         """
#         try:
#             system_prompt = f"""
# Vous êtes un classificateur de requêtes pour un assistant interne de {COMMUNE_NAME}.
# Décidez si la question nécessite la documentation interne (PDF Oxypharm / M3).

# Répondez UNIQUEMENT par "RAG" ou "DIRECT" suivi d'une brève explication :
# - "RAG" si la question porte sur des infos spécifiques à la documentation interne (procédures, écrans, champs, codes, workflows, etc.).
# - "DIRECT" si c'est une question générale, small-talk, ou sans lien avec la documentation.

# Exemples :
# Question : "Bonjour, comment ça va ?"
# Réponse : DIRECT - Simple salutation

# Question : "Quelle est la procédure de litige lors de la réception de marchandise ?"
# Réponse : RAG - Demande d’informations spécifiques à la doc M3

# Question : "c'est quoi M3 ?"
# Réponse : RAG - Question sur un concept/documentation interne

# Question : "Qu’est-ce que l’intelligence artificielle ?"
# Réponse : DIRECT - Question générale
# """.strip()

#             messages = [
#                 ChatMessage(role="system", content=system_prompt),
#                 ChatMessage(role="user", content=query),
#             ]

#             resp = self.mistral_client.chat(
#                 model=CHAT_MODEL,
#                 messages=messages,
#                 temperature=0.1,
#                 max_tokens=50,
#             )

#             result = resp.choices[0].message.content.strip()
#             logger.info(f"Classification LLM pour '{query}': {result}")

#             if result.upper().startswith("RAG"):
#                 reason = result.replace("RAG -", "").replace("RAG:", "").replace("RAG", "").strip()
#                 return True, 0.85, reason or "LLM: nécessite la doc interne"
#             if result.upper().startswith("DIRECT"):
#                 reason = result.replace("DIRECT -", "").replace("DIRECT:", "").replace("DIRECT", "").strip()
#                 return False, 0.85, reason or "LLM: question générale"

#             # Réponse ambiguë → prudence
#             return True, 0.60, "LLM ambigu → RAG par précaution"

#         except Exception as e:
#             logger.error(f"Erreur classification LLM: {e}")
#             # En cas d'erreur réseau/API, rester prudent (DIRECT) pour éviter du RAG hors-sujet
#             return False, 0.50, f"Erreur LLM : {e}"

