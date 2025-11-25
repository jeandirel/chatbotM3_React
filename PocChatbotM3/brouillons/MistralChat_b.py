# # app.py
# import streamlit as st
# from mistralai.client import MistralClient
# from mistralai.models.chat_completion import ChatMessage
# import logging
# import datetime
# from streamlit_feedback import streamlit_feedback  # Importez le composant
# import os
# import base64


# # Importer nos modules locaux
# from utils.config import APP_TITLE, COMMUNE_NAME, MISTRAL_API_KEY
# from utils.vector_store import VectorStoreManager
# from utils.database import log_interaction, update_feedback  # Importez update_feedback
# from utils.query_classifier import QueryClassifier

# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )

# # --- Configuration de la page Streamlit ---
# st.set_page_config(page_title=APP_TITLE, page_icon="📚", layout="wide")

# # --- Initialisation (avec mise en cache Streamlit) ---


# # Met en cache le VectorStoreManager pour éviter de recharger l'index à chaque interaction
# @st.cache_resource
# def get_vector_store():
#     logging.info("Chargement du VectorStoreManager...")
#     return VectorStoreManager()


# # Met en cache le client Mistral
# @st.cache_resource
# def get_mistral_client():
#     if not MISTRAL_API_KEY:
#         st.error("Erreur: La clé API Mistral (MISTRAL_API_KEY) n'est pas configurée.")
#         st.stop()
#     logging.info("Initialisation du client Mistral...")
#     return MistralClient(api_key=MISTRAL_API_KEY)


# # Met en cache le classificateur de requêtes
# @st.cache_resource
# def get_query_classifier():
#     logging.info("Initialisation du classificateur de requêtes...")
#     return QueryClassifier()


# # Charge le Vector Store, le client Mistral et le classificateur de requêtes
# vector_store = get_vector_store()
# client = get_mistral_client()
# query_classifier = get_query_classifier()

# # Initialise l'historique du chat dans l'état de la session s'il n'existe pas


# if "messages" not in st.session_state:
#     st.session_state.messages = []
# # Initialise l'ID de la dernière interaction pour le feedback
# if "last_interaction_id" not in st.session_state:
#     st.session_state.last_interaction_id = None

# # --- Interface Utilisateur ---

# # Barre latérale (sidebar)
# with st.sidebar:
#     st.title(f"📚 {COMMUNE_NAME}")
#     st.caption(f"Assistant virtuel ASTERA")

#     # Bouton pour lancer une nouvelle conversation
#     if st.button("🔄 Nouvelle conversation", use_container_width=True):
#         # Réinitialiser l'historique des messages
#         st.session_state.messages = []
#         st.session_state.last_interaction_id = None
#         st.rerun()  # Recharger l'application pour afficher la nouvelle conversation

#     st.divider()

#     # Paramètres de l'application
#     st.subheader("⚙️ Paramètres")

#     # Sélecteur de modèle Mistral
#     model_options = {
#         "mistral-small-latest": "Mistral Small (rapide)",
#         "mistral-large-latest": "Mistral Large (précis)",
#     }
#     selected_model = st.selectbox(
#         "Modèle LLM",
#         options=list(model_options.keys()),
#         format_func=lambda x: model_options[x],
#         index=0,  # Small par défaut
#     )

#     # Slider pour le nombre de documents
#     num_docs = st.slider(
#         "Nombre de documents à récupérer",
#         min_value=1,
#         max_value=20,
#         value=5,  # 5 par défaut
#         step=1,
#     )

#     # Slider pour le score minimum (en pourcentage)
#     min_score_percent = st.slider(
#         "Score minimum (filtrer les résultats faibles)",
#         min_value=0,
#         max_value=100,
#         value=75,  # 75% par défaut
#         step=5,
#         format="%d%%",
#     )
#     # Convertir le pourcentage en valeur décimale (0-1)
#     min_score = min_score_percent / 100.0

#     st.divider()

#     # Informations sur l'application
#     st.subheader("📝 Informations")
#     st.markdown(f"**Modèle sélectionné**: {model_options[selected_model]}")
#     st.markdown(
#         f"**Documents indexés**: {vector_store.index.ntotal if vector_store.index else 0}"
#     )

#     # Informations sur la conversation actuelle
#     if st.session_state.messages:
#         st.info(
#             f"{len(st.session_state.messages) // 2} échanges dans cette conversation"
#         )

#         # Bouton pour télécharger la conversation
#         # Préparer le contenu de la conversation au format texte
#         conversation_text = "\n\n".join(
#             [
#                 f"{'Utilisateur' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
#                 for msg in st.session_state.messages
#             ]
#         )

#         # Ajouter un en-tête avec la date et le titre
#         header = f"Conversation avec l'assistant virtuel de {COMMUNE_NAME}\n"
#         header += f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
#         conversation_text = header + conversation_text

#         # Bouton de téléchargement
#         st.download_button(
#             label="💾 Télécharger la conversation",
#             data=conversation_text,
#             file_name=f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
#             mime="text/plain",
#             use_container_width=True,
#         )

# # Titre principal
# st.title(f"📚 {APP_TITLE}")
# st.caption(f"Posez vos questions sur {COMMUNE_NAME}")

# # Affichage de l'historique du chat
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#         # Afficher les sources si elles existent pour les messages de l'assistant
#         if message["role"] == "assistant" and "sources" in message and message["sources"]:
#             with st.expander("Sources utilisées"):
#                 for i, source in enumerate(message["sources"]):
#                     # Accès sécurisé aux métadonnées
#                     meta = source.get("metadata", {})
#                     st.markdown(f"**Source {i+1}:** `{meta.get('source', 'N/A')}`")
#                     st.markdown(f"*Score de similarité:* {source.get('score', 0.0):.2f}%")
#                     if 'raw_score' in source:
#                         st.markdown(f"*Score brut:* {source.get('raw_score', 0.0):.4f}")
#                     st.markdown(f"*Catégorie:* `{meta.get('category', 'N/A')}`")
#                     st.text_area(f"Extrait {i+1}", value=source.get("text", "")[:500]+"...", height=100, disabled=True, key=f"src_{message['timestamp']}_{i}") # Clé unique pour éviter les conflits


# # Zone de saisie utilisateur en bas
# if prompt := st.chat_input("Posez votre question ici..."):
#     # Ajouter le message utilisateur à l'historique et l'afficher
#     st.session_state.messages.append(
#         {
#             "role": "user",
#             "content": prompt,
#             "timestamp": datetime.datetime.now().isoformat(),
#         }
#     )
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Afficher un message d'attente
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         message_placeholder.markdown(
#             "🧠 Recherche d'informations et génération de la réponse..."
#         )

#         # --- Logique de traitement de la requête ---
#         try:
#             # 1. Classifier la requête pour déterminer si elle nécessite RAG
#             needs_rag, confidence, reason = query_classifier.needs_rag(prompt)

#             # Afficher le résultat de la classification
#             mode_str = "RAG" if needs_rag else "DIRECT"
#             logging.info(
#                 f"Classification de la requête: {mode_str} (confiance: {confidence:.2f}) - Raison: {reason}"
#             )

#             # Afficher un message indiquant le mode utilisé
#             mode_info = st.empty()
#             if needs_rag:
#                 mode_info.info(
#                     f"Mode RAG: Recherche d'informations spécifiques dans la base de connaissances (confiance: {confidence:.2f})"
#                 )
#                 # 2. Recherche dans le Vector Store si nécessaire
#                 logging.info(
#                     f"Recherche de documents pour: '{prompt}' (max: {num_docs}, score min: {min_score})"
#                 )
#                 retrieved_docs = vector_store.search(
#                     prompt, k=num_docs, min_score=min_score
#                 )
#             else:
#                 mode_info.info(
#                     f"Mode Direct: Réponse basée sur les connaissances générales du modèle (confiance: {confidence:.2f})"
#                 )
#                 # Pas de recherche dans le Vector Store
#                 retrieved_docs = []

#             # 2. Préparer les données en fonction du mode
#             if needs_rag and retrieved_docs:
#                 # Mode RAG avec documents trouvés
#                 logging.info(f"{len(retrieved_docs)} documents récupérés.")
#                 # Préparer le contexte pour le LLM
#                 context_str = "\n\n---\n\n".join(
#                     [
#                         f"Source: {doc['metadata'].get('source', 'Inconnue')} (Score: {doc['score']:.4f})\nContenu: {doc['text']}"
#                         for doc in retrieved_docs
#                     ]
#                 )
#                 sources_for_log = [  # Version simplifiée pour le log et l'affichage
#                     {
#                         "text": doc["text"],
#                         "metadata": doc["metadata"],
#                         "score": doc["score"],
#                     }
#                     for doc in retrieved_docs
#                 ]

#                 # Prompt système pour le mode RAG
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# Répondez à la question de l'utilisateur en vous basant UNIQUEMENT sur la documentation fourni du contexte ci-dessous.
# Si l'information n'est pas dans le contexte, dites que vous ne savez pas ou que l'information n'est pas disponible dans les documents fournis.
# Soyez concis et précis. Citez vos sources si possible (par exemple, en mentionnant le nom du fichier ou la catégorie trouvée dans les métadonnées).

# Contexte fourni:
# ---
# {context_str}
# ---
# """
#             elif needs_rag and not retrieved_docs:
#                 # Mode RAG mais aucun document trouvé
#                 logging.warning("Aucun document pertinent trouvé.")
#                 context_str = (
#                     "Aucune information pertinente trouvée dans les documents."
#                 )
#                 sources_for_log = []

#                 # Prompt système pour le mode RAG sans résultats
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# L'utilisateur a posé une question qui semble concerner des informations spécifiques à la documentation, mais aucune information pertinente n'a été trouvée dans notre base de connaissances.
# Indiquez poliment que vous n'avez pas cette information spécifique et suggérez à l'utilisateur de reformuler sa question ou de contacter directement le service desk ou le pole IA (Myriana).
# N'inventez pas d'informations sur {COMMUNE_NAME}.
# """
#             else:
#                 # Mode Direct (sans RAG)
#                 context_str = "Mode direct: réponse basée sur les connaissances générales du modèle."
#                 sources_for_log = []

#                 # Prompt système pour le mode Direct
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# Répondez à la question de l'utilisateur en utilisant vos connaissances générales.
# Soyez concis, précis et utile.
# Si la question concerne des informations spécifiques à {COMMUNE_NAME} que vous ne connaissez pas, indiquez clairement que vous n'avez pas cette information spécifique.
# N'inventez pas d'informations sur {COMMUNE_NAME}.
# """
#             user_message = ChatMessage(role="user", content=prompt)
#             system_message = ChatMessage(role="system", content=system_prompt)
#             messages_for_api = [system_message, user_message]

#             # 3. Appel à l'API Mistral Chat
#             logging.info(
#                 f"Appel de l'API Mistral Chat avec le modèle {selected_model}..."
#             )
#             chat_response = client.chat(model=selected_model, messages=messages_for_api)
#             response_text = chat_response.choices[0].message.content
#             logging.info("Réponse générée par Mistral.")

#             # 4. Afficher la réponse et les sources
#             message_placeholder.markdown(response_text)

#             # Afficher les sources si disponibles (mode RAG avec résultats)
#             if sources_for_log:
#                 with st.expander("Sources utilisées"):
#                     for i, source in enumerate(sources_for_log):
#                         meta = source.get("metadata", {})
#                         st.markdown(f"**Source {i+1}:** `{meta.get('source', 'N/A')}`")
#                         st.markdown(
#                             f"*Score de similarité:* {source.get('score', 0.0):.2f}%"
#                         )
#                         if "raw_score" in source:
#                             st.markdown(
#                                 f"*Score brut:* {source.get('raw_score', 0.0):.4f}"
#                             )
#                         st.markdown(f"*Catégorie:* `{meta.get('category', 'N/A')}`")
#                         st.text_area(
#                             f"Extrait {i+1}",
#                             value=source.get("text", "")[:500] + "...",
#                             height=100,
#                             disabled=True,
#                             key=f"src_new_{i}",
#                         )  # Clé unique
#                         # Affichage du PDF associé si le chemin existe
#                         pdf_file_path = meta.get("source", "")
                        
#             elif needs_rag:
#                 # Mode RAG sans résultats
#                 st.info(
#                     "Aucune source pertinente n'a été trouvée dans la base de connaissances pour cette question."
#                 )
#             else:
#                 # Mode Direct
#                 st.info(
#                     "Réponse générée en mode direct, sans consultation de la base de connaissances."
#                 )
            

#             # 5. Enregistrer l'interaction dans la base de données (sans feedback initial)
#             # Ajouter des métadonnées sur le mode utilisé
#             metadata = {
#                 "mode": "RAG" if needs_rag else "DIRECT",
#                 "confidence": confidence,
#                 "reason": reason,
#             }

#             interaction_id = log_interaction(
#                 query=prompt,
#                 response=response_text,
#                 sources=sources_for_log,  # Stocke la liste de dicts
#                 metadata=metadata,  # Ajouter les métadonnées sur le mode
#             )
#             st.session_state.last_interaction_id = (
#                 interaction_id  # Garde l'ID pour le feedback
#             )
#             logging.info(f"Interaction enregistrée avec ID: {interaction_id}")

#             # Ajouter la réponse de l'assistant à l'historique pour affichage permanent
#             st.session_state.messages.append(
#                 {
#                     "role": "assistant",
#                     "content": response_text,
#                     "sources": sources_for_log,  # Garder les sources pour réaffichage
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "interaction_id": interaction_id,  # Lier le message à l'ID BDD
#                 }
#             )

#         except Exception as e:
#             # Vérifier si c'est une erreur API Mistral
#             if hasattr(e, "status_code") and hasattr(e, "message"):
#                 logging.error(f"Erreur API Mistral: {e}")
#                 message_placeholder.error(
#                     f"Une erreur s'est produite lors de la communication avec l'API Mistral: {e}"
#                 )
#             else:
#                 logging.error(f"Erreur inattendue: {e}", exc_info=True)
#                 message_placeholder.error(f"Une erreur s'est produite: {e}")

#             st.session_state.messages.append(
#                 {
#                     "role": "assistant",
#                     "content": f"Erreur: {e}",
#                     "sources": [],
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "interaction_id": None,
#                 }
#             )
#             st.session_state.last_interaction_id = None  # Pas d'ID si erreur avant log

# # --- Section Feedback ---
# # Placer le feedback après la boucle d'affichage et la zone de chat input
# # On cible la *dernière* réponse de l'assistant pour le feedback
# last_assistant_message = next(
#     (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None
# )

# # Vérifie si la dernière réponse a un ID d'interaction associé
# current_interaction_id = (
#     last_assistant_message.get("interaction_id") if last_assistant_message else None
# )

# if current_interaction_id:
#     # Utilisation de streamlit-feedback
#     feedback = streamlit_feedback(
#         feedback_type="thumbs",  # "thumbs" ou "faces"
#         optional_text_label="[Optionnel] Commentaires :",
#         key=f"feedback_{current_interaction_id}",  # Clé unique liée à l'interaction
#         align="flex-start",  # Aligner à gauche
#         on_submit=lambda x: logging.info(f"Feedback soumis: {x}"),  # Log pour débogage
#     )

#     # Traitement du feedback s'il est donné
#     if feedback:
#         # Convertir le feedback en valeur numérique et texte
                # raw_score = feedback.get("score")
                # normalized_score = None

                # if isinstance(raw_score, str):
                #     stripped_score = raw_score.strip()
                #     score_lower = stripped_score.lower()
                #     if score_lower in {"positive", "thumbs_up", "thumbsup", "up"}:
                #         normalized_score = "positive"
                #     elif score_lower in {"negative", "thumbs_down", "thumbsdown", "down"}:
                #         normalized_score = "negative"
                #     elif score_lower in {"1", "true"}:
                #         normalized_score = "positive"
                #     elif score_lower in {"-1", "0", "false"}:
                #         normalized_score = "negative"
                #     elif stripped_score in ("\U0001F44D", "\U0001F44E"):
                #         normalized_score = "positive" if stripped_score == "\U0001F44D" else "negative"
                # elif isinstance(raw_score, bool):
                #     normalized_score = "positive" if raw_score else "negative"
                # elif isinstance(raw_score, (int, float)):
                #     if raw_score > 0:
                #         normalized_score = "positive"
                #     elif raw_score < 0:
                #         normalized_score = "negative"

                # if normalized_score is None and raw_score is not None:
                #     logging.warning("Feedback score non reconnu: %r", raw_score)

                # feedback_value = 1 if normalized_score == "positive" else 0 if normalized_score == "negative" else None
                # feedback_text = ("positif" if normalized_score == "positive" else "négatif" if normalized_score == "negative" else "N/A")

                # feedback_emoji = ("\U0001F44D" if normalized_score == "positive" else "\U0001F44E" if normalized_score == "negative" else "N/A")
                # comment = feedback.get("text", None)

#         # Mettre à jour l'interaction dans la base de données
#         success = update_feedback(
#             current_interaction_id, feedback_text, comment, feedback_value
#         )
#         if success:
#             st.toast(f"Merci pour votre retour ({feedback_emoji}) !", icon="✅")
#             # Optionnel: Désactiver les boutons après le premier clic pour éviter les soumissions multiples
#             # Ceci est plus complexe à gérer avec la nature stateless de Streamlit sans callbacks avancés.
#             # Pour la simplicité, on se contente de l'enregistrer. L'utilisateur peut re-cliquer mais seule la dernière valeur compte.
#         else:
#             st.toast("Erreur lors de l'enregistrement de votre retour.", icon="❌")

#         # Optionnel : Effacer le feedback de l'état pour éviter re-soumission au re-run
#         # st.session_state[f"feedback_{current_interaction_id}"] = None # Peut causer des pbs si mal géré

# else:
#     st.write("Posez une question pour pouvoir donner votre avis sur la réponse.")
# custom_css = """
# <style>
# /* Couleurs générales */T
# body {
#     background-color: #fff9f3;
#     color: #333333;
#     font-family: 'Segoe UI', sans-serif;
# }

# /* Header, boutons orange */
# header, .st-emotion-cache-18ni7ap, .st-emotion-cache-6qob1r {
#     background-color: #ffa94d !important;
#     color: white !important;
# }

# .stButton>button {
#     background-color: #ffa94d;
#     color: white;
#     border-radius: 8px;
#     font-weight: bold;
#     border: none;
#     padding: 6px 14px;
# }

# .stButton>button:hover {
#     background-color: #ff922b;
#     color: white;
# }

# /* Input et zone texte */
# input, textarea {
#     border-radius: 6px !important;
#     border: 1px solid #ffa94d !important;
#     padding: 6px;
# }

# /* Expander titre */
# .stExpanderHeader {
#     background-color: #ffe8cc !important;
#     color: #ff6600 !important;
#     font-weight: bold;
#     border-radius: 5px;
# }

# /* Chat bubbles */
# .stChatMessage {
#     background-color: #fff3e0 !important;
#     border-radius: 10px;
#     padding: 10px;
#     margin-bottom: 10px;
# }

# /* Barre latérale */
# section[data-testid="stSidebar"] {
#     background-color: #fff3e0;
# }

# /* Download button */
# [data-testid="baseButton-secondary"] {
#     border: 1px solid #ffa94d !important;
#     color: #ff6600 !important;
#     background: white;
# }

# [data-testid="baseButton-secondary"]:hover {
#     background: #ffe8cc;
# }
# </style>
# """
# st.markdown(custom_css, unsafe_allow_html=True)



###################################################################################################
###############################################################################################  Version actuelle du fichier MistralChat.py du chatbot

# app.py
# import streamlit as st
# from mistralai.client import MistralClient
# from mistralai.models.chat_completion import ChatMessage
# import logging
# import datetime
# from streamlit_feedback import streamlit_feedback  # Importez le composant
# import os
# import base64


# # Importer nos modules locaux
# from utils.config import APP_TITLE, COMMUNE_NAME, MISTRAL_API_KEY
# from utils.vector_store import VectorStoreManager
# from utils.database import log_interaction, update_feedback  # Importez update_feedback
# from utils.query_classifier import QueryClassifier

# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )

# # --- Configuration de la page Streamlit ---
# st.set_page_config(page_title=APP_TITLE, page_icon="📚", layout="wide")


# custom_css = """
# <style>
# /* Couleurs générales */
# body {
#     background-color: #fff9f3;
#     color: #333333;
#     font-family: 'Segoe UI', sans-serif;
# }

# /* Header, boutons orange */
# header, .st-emotion-cache-18ni7ap, .st-emotion-cache-6qob1r {
#     background-color: #ffa94d !important;
#     color: white !important;
# }

# .stButton>button {
#     background-color: #ffa94d;
#     color: white;
#     border-radius: 8px;
#     font-weight: bold;
#     border: none;
#     padding: 6px 14px;
#     transition: background-color 0.3s ease;
# }

# .stButton>button:hover {
#     background-color: #ff922b;
#     color: white;
# }

# /* Boutons PDF spéciaux */
# .stButton>button[title*="Voir PDF"] {
#     background-color: #FF6B35;
#     color: white;
#     border: 2px solid #FF6B35;
# }

# .stButton>button[title*="Fermer PDF"] {
#     background-color: #dc3545;
#     color: white;
#     border: 2px solid #dc3545;
# }

# .stButton>button[title*="Voir PDF"]:hover {
#     background-color: #E55A2B;
#     border-color: #E55A2B;
# }

# .stButton>button[title*="Fermer PDF"]:hover {
#     background-color: #c82333;
#     border-color: #c82333;
# }

# /* Input et zone texte */
# input, textarea {
#     border-radius: 6px !important;
#     border: 1px solid #ffa94d !important;
#     padding: 6px;
# }

# /* Zone de chat input */
# .stChatInputContainer {
#     border: 2px solid #ffa94d !important;
#     border-radius: 10px !important;
#     background-color: #fff !important;
# }

# /* Expander titre */
# .stExpanderHeader {
#     background-color: #ffe8cc !important;
#     color: #ff6600 !important;
#     font-weight: bold;
#     border-radius: 5px;
# }

# /* Chat bubbles */
# .stChatMessage {
#     background-color: #fff3e0 !important;
#     border-radius: 10px;
#     padding: 10px;
#     margin-bottom: 10px;
#     border: 1px solid #ffe8cc;
# }

# /* Messages utilisateur */
# [data-testid="user-message"] {
#     background-color: #e3f2fd !important;
#     border-left: 4px solid #2196f3 !important;
# }

# /* Messages assistant */
# [data-testid="assistant-message"] {
#     background-color: #fff3e0 !important;
#     border-left: 4px solid #ffa94d !important;
# }

# /* Barre latérale */
# section[data-testid="stSidebar"] {
#     background-color: #fff3e0;
#     border-right: 2px solid #ffa94d;
# }

# .css-1d391kg {
#     background-color: #fff3e0;
# }

# /* Download button */
# [data-testid="baseButton-secondary"] {
#     border: 1px solid #ffa94d !important;
#     color: #ff6600 !important;
#     background: white;
# }

# [data-testid="baseButton-secondary"]:hover {
#     background: #ffe8cc;
# }

# /* Styles pour les containers PDF */
# .pdf-container {
#     border: 3px solid #FF6B35;
#     border-radius: 10px;
#     padding: 15px;
#     margin: 15px 0;
#     background-color: #FFF8F0;
#     box-shadow: 0 4px 6px rgba(255, 107, 53, 0.1);
# }

# .pdf-header {
#     color: #FF6B35;
#     margin-top: 0;
#     font-size: 1.2em;
#     font-weight: bold;
# }

# /* Titre principal */
# .main-title {
#     color: #ff6600;
#     text-align: center;
#     padding: 20px 0;
# }

# /* Messages d'info */
# .stInfo {
#     background-color: #e8f4fd !important;
#     border-left: 4px solid #2196f3 !important;
#     color: #0c5aa6 !important;
# }

# /* Messages de succès */
# .stSuccess {
#     background-color: #e8f5e8 !important;
#     border-left: 4px solid #4caf50 !important;
#     color: #2e7d32 !important;
# }

# /* Spinner/Loading */
# .stSpinner {
#     color: #ffa94d !important;
# }

# /* Sliders */
# .stSlider > div > div > div {
#     background-color: #ffa94d !important;
# }

# /* Select boxes */
# .stSelectbox > div > div {
#     border: 1px solid #ffa94d !important;
#     border-radius: 6px !important;
# }
# </style>
# """

# # Appliquer le CSS immédiatement après la configuration de la page
# st.markdown(custom_css, unsafe_allow_html=True)

# # --- Fonctions pour l'aperçu PDF ---

# def display_pdf_preview(pdf_path, unique_key):
#     """Affiche l'aperçu PDF dans un iframe avec gestion d'état"""
    
#     # Vérifier si le fichier existe
#     if not os.path.exists(pdf_path):
#         st.error(f"❌ Fichier PDF introuvable : {pdf_path}")
#         return
    
#     # Clé d'état unique pour ce PDF
#     state_key = f"show_pdf_{unique_key}"
    
#     # Initialiser l'état si nécessaire
#     if state_key not in st.session_state:
#         st.session_state[state_key] = False
    
#     # Bouton pour afficher/masquer le PDF
#     if not st.session_state[state_key]:
#         if st.button("👁️ Voir PDF", key=f"btn_show_{unique_key}"):
#             st.session_state[state_key] = True
#             st.rerun()
#     else:
#         if st.button("❌ Fermer PDF", key=f"btn_close_{unique_key}"):
#             st.session_state[state_key] = False
#             st.rerun()
        
#         # Afficher le PDF dans un iframe
#         try:
#             with open(pdf_path, "rb") as pdf_file:
#                 pdf_data = pdf_file.read()
#                 pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
            
#             # Container stylisé avec bordure orange
#             st.markdown("""
#             <div style="
#                 border: 3px solid #FF6B35;
#                 border-radius: 10px;
#                 padding: 15px;
#                 margin: 15px 0;
#                 background-color: #FFF8F0;
#                 box-shadow: 0 4px 6px rgba(255, 107, 53, 0.1);
#             ">
#                 <h4 style="color: #FF6B35; margin-top: 0;">📄 Aperçu du document PDF</h4>
#             </div>
#             """, unsafe_allow_html=True)
            
#             # Iframe pour afficher le PDF
#             pdf_display = f'''
#             <div style="
#                 border: 3px solid #FF6B35;
#                 border-radius: 10px;
#                 padding: 0;
#                 margin: 10px 0;
#                 background-color: #FFF8F0;
#                 overflow: hidden;
#             ">
#                 <iframe src="data:application/pdf;base64,{pdf_b64}" 
#                         width="100%" 
#                         height="600" 
#                         style="border: none; border-radius: 7px;">
#                     <p>Votre navigateur ne supporte pas l'affichage des PDF. 
#                     <a href="data:application/pdf;base64,{pdf_b64}" target="_blank">Cliquez ici pour télécharger le PDF</a></p>
#                 </iframe>
#             </div>
#             '''
#             st.markdown(pdf_display, unsafe_allow_html=True)
            
#         except Exception as e:
#             st.error(f"❌ Erreur lors de l'affichage du PDF : {str(e)}")

# def get_absolute_pdf_path(relative_path):
#     base_path = os.path.join(os.getcwd(), "inputs")
#     full_path = os.path.join(base_path, relative_path)
    
#     # Vérifier si le fichier existe
#     if os.path.exists(full_path):
#         return full_path
#     else:
#         print(f"❌ Fichier non trouvé: {full_path}")
#         # Essayer sans duplication Oxypharm
#         if "Oxypharm" in relative_path:
#             clean_path = relative_path.replace("Oxypharm\\", "", 1).replace("Oxypharm/", "", 1)
#             alternative_path = os.path.join(os.getcwd(), "inputs", "Oxypharm", clean_path)
#             if os.path.exists(alternative_path):
#                 print(f"✅ Fichier trouvé à: {alternative_path}")
#                 return alternative_path
        
#         return full_path  # Retourne le chemin même s'il n'existe pas

# def display_sources_with_pdf_preview(sources, message_timestamp):
#     """Affiche les sources avec aperçu PDF intégré"""
    
#     if not sources:
#         return
    
#     with st.expander("Sources utilisées"):
#         for i, source in enumerate(sources):
#             # Accès sécurisé aux métadonnées
#             meta = source.get("metadata", {})
#             relative_path = meta.get("source", "")
            
#             # Affichage des informations de la source
#             st.markdown(f"**Source {i+1}:** `{relative_path}`")
#             st.markdown(f"*Score de similarité:* {source.get('score', 0.0):.2f}%")
#             if 'raw_score' in source:
#                 st.markdown(f"*Score brut:* {source.get('raw_score', 0.0):.4f}")
#             st.markdown(f"*Catégorie:* `{meta.get('category', 'N/A')}`")
            
#             # Zone de texte pour l'extrait
#             st.text_area(
#                 f"Extrait {i+1}", 
#                 value=source.get("text", "")[:500]+"...", 
#                 height=100, 
#                 disabled=True, 
#                 key=f"src_{message_timestamp}_{i}"
#             )
            
#             # Bouton pour afficher le PDF si le fichier existe
#             if relative_path and relative_path.lower().endswith('.pdf'):
#                 absolute_path = get_absolute_pdf_path(relative_path)
#                 unique_key = f"{message_timestamp}_{i}_{hash(relative_path)}"
#                 display_pdf_preview(absolute_path, unique_key)
                
#             st.divider()  # Séparateur entre les sources

# # --- Initialisation (avec mise en cache Streamlit) ---


# # Met en cache le VectorStoreManager pour éviter de recharger l'index à chaque interaction
# @st.cache_resource
# def get_vector_store():
#     logging.info("Chargement du VectorStoreManager...")
#     return VectorStoreManager()


# # Met en cache le client Mistral
# @st.cache_resource
# def get_mistral_client():
#     if not MISTRAL_API_KEY:
#         st.error("Erreur: La clé API Mistral (MISTRAL_API_KEY) n'est pas configurée.")
#         st.stop()
#     logging.info("Initialisation du client Mistral...")
#     return MistralClient(api_key=MISTRAL_API_KEY)


# # Met en cache le classificateur de requêtes
# @st.cache_resource
# def get_query_classifier():
#     logging.info("Initialisation du classificateur de requêtes...")
#     return QueryClassifier()


# # Charge le Vector Store, le client Mistral et le classificateur de requêtes
# vector_store = get_vector_store()
# client = get_mistral_client()
# query_classifier = get_query_classifier()

# # Initialise l'historique du chat dans l'état de la session s'il n'existe pas


# if "messages" not in st.session_state:
#     st.session_state.messages = []
# # Initialise l'ID de la dernière interaction pour le feedback
# if "last_interaction_id" not in st.session_state:
#     st.session_state.last_interaction_id = None

# # --- Interface Utilisateur ---

# # Barre latérale (sidebar)
# with st.sidebar:
#     st.title(f"📚 {COMMUNE_NAME}")
#     st.caption(f"Assistant virtuel ASTERA")

#     # Bouton pour lancer une nouvelle conversation
#     if st.button("🔄 Nouvelle conversation", use_container_width=True):
#         # Réinitialiser l'historique des messages
#         st.session_state.messages = []
#         st.session_state.last_interaction_id = None
#         # Réinitialiser tous les états d'aperçu PDF
#         keys_to_remove = [key for key in st.session_state.keys() if key.startswith("show_pdf_")]
#         for key in keys_to_remove:
#             del st.session_state[key]
#         st.rerun()  # Recharger l'application pour afficher la nouvelle conversation

#     st.divider()

#     # Paramètres de l'application
#     st.subheader("⚙️ Paramètres")

#     # Sélecteur de modèle Mistral
#     model_options = {
#         "mistral-small-latest": "Mistral Small (rapide)",
#         "mistral-large-latest": "Mistral Large (précis)",
#     }
#     selected_model = st.selectbox(
#         "Modèle LLM",
#         options=list(model_options.keys()),
#         format_func=lambda x: model_options[x],
#         index=0,  # Small par défaut
#     )

#     # Slider pour le nombre de documents
#     num_docs = st.slider(
#         "Nombre de documents à récupérer",
#         min_value=1,
#         max_value=20,
#         value=5,  # 5 par défaut
#         step=1,
#     )

#     # Slider pour le score minimum (en pourcentage)
#     min_score_percent = st.slider(
#         "Score minimum (filtrer les résultats faibles)",
#         min_value=0,
#         max_value=100,
#         value=75,  # 75% par défaut
#         step=5,
#         format="%d%%",
#     )
#     # Convertir le pourcentage en valeur décimale (0-1)
#     min_score = min_score_percent / 100.0

#     st.divider()

#     # Informations sur l'application
#     st.subheader("📝 Informations")
#     st.markdown(f"**Modèle sélectionné**: {model_options[selected_model]}")
#     st.markdown(
#         f"**Documents indexés**: {vector_store.index.ntotal if vector_store.index else 0}"
#     )

#     # Informations sur la conversation actuelle
#     if st.session_state.messages:
#         st.info(
#             f"{len(st.session_state.messages) // 2} échanges dans cette conversation"
#         )

#         # Bouton pour télécharger la conversation
#         # Préparer le contenu de la conversation au format texte
#         conversation_text = "\n\n".join(
#             [
#                 f"{'Utilisateur' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
#                 for msg in st.session_state.messages
#             ]
#         )

#         # Ajouter un en-tête avec la date et le titre
#         header = f"Conversation avec l'assistant virtuel de {COMMUNE_NAME}\n"
#         header += f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
#         conversation_text = header + conversation_text

#         # Bouton de téléchargement
#         st.download_button(
#             label="💾 Télécharger la conversation",
#             data=conversation_text,
#             file_name=f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
#             mime="text/plain",
#             use_container_width=True,
#         )

# # Titre principal
# st.title(f"📚 {APP_TITLE}")
# st.caption(f"Posez vos questions sur {COMMUNE_NAME}")

# # Affichage de l'historique du chat
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#         # Afficher les sources si elles existent pour les messages de l'assistant
#         if message["role"] == "assistant" and "sources" in message and message["sources"]:
#             display_sources_with_pdf_preview(message["sources"], message["timestamp"])


# # Zone de saisie utilisateur en bas
# if prompt := st.chat_input("Posez votre question ici..."):
#     # Ajouter le message utilisateur à l'historique et l'afficher
#     st.session_state.messages.append(
#         {
#             "role": "user",
#             "content": prompt,
#             "timestamp": datetime.datetime.now().isoformat(),
#         }
#     )
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Afficher un message d'attente
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         message_placeholder.markdown(
#             "🧠 Recherche d'informations et génération de la réponse..."
#         )

#         # --- Logique de traitement de la requête ---
#         try:
#             # 1. Classifier la requête pour déterminer si elle nécessite RAG
#             needs_rag, confidence, reason = query_classifier.needs_rag(prompt)

#             # Afficher le résultat de la classification
#             mode_str = "RAG" if needs_rag else "DIRECT"
#             logging.info(
#                 f"Classification de la requête: {mode_str} (confiance: {confidence:.2f}) - Raison: {reason}"
#             )

#             # Afficher un message indiquant le mode utilisé
#             mode_info = st.empty()
#             if needs_rag:
#                 mode_info.info(
#                     f"Mode RAG: Recherche d'informations spécifiques dans la base de connaissances (confiance: {confidence:.2f})"
#                 )
#                 # 2. Recherche dans le Vector Store si nécessaire
#                 logging.info(
#                     f"Recherche de documents pour: '{prompt}' (max: {num_docs}, score min: {min_score})"
#                 )
#                 retrieved_docs = vector_store.search(
#                     prompt, k=num_docs, min_score=min_score
#                 )
#             else:
#                 mode_info.info(
#                     f"Mode Direct: Réponse basée sur les connaissances générales du modèle (confiance: {confidence:.2f})"
#                 )
#                 # Pas de recherche dans le Vector Store
#                 retrieved_docs = []

#             # 2. Préparer les données en fonction du mode
#             if needs_rag and retrieved_docs:
#                 # Mode RAG avec documents trouvés
#                 logging.info(f"{len(retrieved_docs)} documents récupérés.")
#                 # Préparer le contexte pour le LLM
#                 context_str = "\n\n---\n\n".join(
#                     [
#                         f"Source: {doc['metadata'].get('source', 'Inconnue')} (Score: {doc['score']:.4f})\nContenu: {doc['text']}"
#                         for doc in retrieved_docs
#                     ]
#                 )
#                 sources_for_log = [  # Version simplifiée pour le log et l'affichage
#                     {
#                         "text": doc["text"],
#                         "metadata": doc["metadata"],
#                         "score": doc["score"],
#                     }
#                     for doc in retrieved_docs
#                 ]

#                 # Prompt système pour le mode RAG
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# Répondez à la question de l'utilisateur en vous basant UNIQUEMENT sur la documentation fourni du contexte ci-dessous.
# Si l'information n'est pas dans le contexte, dites que vous ne savez pas ou que l'information n'est pas disponible dans les documents fournis.
# Soyez concis et précis. Citez vos sources si possible (par exemple, en mentionnant le nom du fichier ou la catégorie trouvée dans les métadonnées).

# Contexte fourni:
# ---
# {context_str}
# ---
# """
#             elif needs_rag and not retrieved_docs:
#                 # Mode RAG mais aucun document trouvé
#                 logging.warning("Aucun document pertinent trouvé.")
#                 context_str = (
#                     "Aucune information pertinente trouvée dans les documents."
#                 )
#                 sources_for_log = []

#                 # Prompt système pour le mode RAG sans résultats
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# L'utilisateur a posé une question qui semble concerner des informations spécifiques à la documentation, mais aucune information pertinente n'a été trouvée dans notre base de connaissances.
# Indiquez poliment que vous n'avez pas cette information spécifique et suggérez à l'utilisateur de reformuler sa question ou de contacter directement le service desk ou le pole IA (Myriana).
# N'inventez pas d'informations sur {COMMUNE_NAME}.
# """
#             else:
#                 # Mode Direct (sans RAG)
#                 context_str = "Mode direct: réponse basée sur les connaissances générales du modèle."
#                 sources_for_log = []

#                 # Prompt système pour le mode Direct
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# Répondez à la question de l'utilisateur en utilisant vos connaissances générales.
# Soyez concis, précis et utile.
# Si la question concerne des informations spécifiques à {COMMUNE_NAME} que vous ne connaissez pas, indiquez clairement que vous n'avez pas cette information spécifique.
# N'inventez pas d'informations sur {COMMUNE_NAME}.
# """
#             user_message = ChatMessage(role="user", content=prompt)
#             system_message = ChatMessage(role="system", content=system_prompt)
#             messages_for_api = [system_message, user_message]

#             # 3. Appel à l'API Mistral Chat
#             logging.info(
#                 f"Appel de l'API Mistral Chat avec le modèle {selected_model}..."
#             )
#             chat_response = client.chat(model=selected_model, messages=messages_for_api)
#             response_text = chat_response.choices[0].message.content
#             logging.info("Réponse générée par Mistral.")

#             # 4. Afficher la réponse et les sources
#             message_placeholder.markdown(response_text)

#             # Afficher les sources si disponibles (mode RAG avec résultats)
#             if sources_for_log:
#                 display_sources_with_pdf_preview(sources_for_log, datetime.datetime.now().isoformat())
                        
#             elif needs_rag:
#                 # Mode RAG sans résultats
#                 st.info(
#                     "Aucune source pertinente n'a été trouvée dans la base de connaissances pour cette question."
#                 )
#             else:
#                 # Mode Direct
#                 st.info(
#                     "Réponse générée en mode direct, sans consultation de la base de connaissances."
#                 )
            

#             # 5. Enregistrer l'interaction dans la base de données (sans feedback initial)
#             # Ajouter des métadonnées sur le mode utilisé
#             metadata = {
#                 "mode": "RAG" if needs_rag else "DIRECT",
#                 "confidence": confidence,
#                 "reason": reason,
#             }

#             interaction_id = log_interaction(
#                 query=prompt,
#                 response=response_text,
#                 sources=sources_for_log,  # Stocke la liste de dicts
#                 metadata=metadata,  # Ajouter les métadonnées sur le mode
#             )
#             st.session_state.last_interaction_id = (
#                 interaction_id  # Garde l'ID pour le feedback
#             )
#             logging.info(f"Interaction enregistrée avec ID: {interaction_id}")

#             # Ajouter la réponse de l'assistant à l'historique pour affichage permanent
#             st.session_state.messages.append(
#                 {
#                     "role": "assistant",
#                     "content": response_text,
#                     "sources": sources_for_log,  # Garder les sources pour réaffichage
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "interaction_id": interaction_id,  # Lier le message à l'ID BDD
#                 }
#             )

#         except Exception as e:
#             # Vérifier si c'est une erreur API Mistral
#             if hasattr(e, "status_code") and hasattr(e, "message"):
#                 logging.error(f"Erreur API Mistral: {e}")
#                 message_placeholder.error(
#                     f"Une erreur s'est produite lors de la communication avec l'API Mistral: {e}"
#                 )
#             else:
#                 logging.error(f"Erreur inattendue: {e}", exc_info=True)
#                 message_placeholder.error(f"Une erreur s'est produite: {e}")

#             st.session_state.messages.append(
#                 {
#                     "role": "assistant",
#                     "content": f"Erreur: {e}",
#                     "sources": [],
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "interaction_id": None,
#                 }
#             )
#             st.session_state.last_interaction_id = None  # Pas d'ID si erreur avant log

# # --- Section Feedback ---
# # Placer le feedback après la boucle d'affichage et la zone de chat input
# # On cible la *dernière* réponse de l'assistant pour le feedback
# last_assistant_message = next(
#     (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None
# )

# # Vérifie si la dernière réponse a un ID d'interaction associé
# current_interaction_id = (
#     last_assistant_message.get("interaction_id") if last_assistant_message else None
# )

# if current_interaction_id:
#     # Utilisation de streamlit-feedback
#     feedback = streamlit_feedback(
#         feedback_type="thumbs",  # "thumbs" ou "faces"
#         optional_text_label="[Optionnel] Commentaires :",
#         key=f"feedback_{current_interaction_id}",  # Clé unique liée à l'interaction
#         align="flex-start",  # Aligner à gauche
#         on_submit=lambda x: logging.info(f"Feedback soumis: {x}"),  # Log pour débogage
#     )

#     # Traitement du feedback s'il est donné
#     if feedback:
#         # Convertir le feedback en valeur numérique et texte
#         feedback_score = feedback.get("score")

#         # Vérifier si le score est valide
#         # Le composant streamlit_feedback peut renvoyer des emojis au lieu de "thumbs_up"/"thumbs_down"
#         if feedback_score == "👍" or feedback_score == "thumbs_up":
#             feedback_score = "positive"
#         elif feedback_score == "👎" or feedback_score == "thumbs_down":
#             feedback_score = "negative"
#         else:
#             logging.warning(f"Score de feedback invalide: {feedback_score}")
#             feedback_score = None

#         # 1 pour positif, 0 pour négatif
#         feedback_value = (
#             1
#             if feedback_score == "positive"
#             else 0 if feedback_score == "negative" else None
#         )

#         # Texte pour la base de données ("positif" ou "négatif")
#         feedback_text = (
#             "positif"
#             if feedback_score == "positive"
#             else "négatif" if feedback_score == "negative" else "N/A"
#         )

#         # Emoji pour l'affichage dans l'interface
#         feedback_emoji = (
#             "👍"
#             if feedback_score == "positive"
#             else "👎" if feedback_score == "negative" else "N/A"
#         )
#         comment = feedback.get("text", None)

#         # Mettre à jour l'interaction dans la base de données
#         success = update_feedback(
#             current_interaction_id, feedback_text, comment, feedback_value
#         )
#         if success:
#             st.toast(f"Merci pour votre retour ({feedback_emoji}) !", icon="✅")
#             # Optionnel: Désactiver les boutons après le premier clic pour éviter les soumissions multiples
#             # Ceci est plus complexe à gérer avec la nature stateless de Streamlit sans callbacks avancés.
#             # Pour la simplicité, on se contente de l'enregistrer. L'utilisateur peut re-cliquer mais seule la dernière valeur compte.
#         else:
#             st.toast("Erreur lors de l'enregistrement de votre retour.", icon="❌")

#         # Optionnel : Effacer le feedback de l'état pour éviter re-soumission au re-run
#         # st.session_state[f"feedback_{current_interaction_id}"] = None # Peut causer des pbs si mal géré

# else:
#     st.write("Posez une question pour pouvoir donner votre avis sur la réponse.")






################################################################################################################################################
########################################################################################################################################" Test de version multi-utilisateur du fichier MistralChat.py du chatbot"

# import streamlit as st
# from mistralai.client import MistralClient
# from mistralai.models.chat_completion import ChatMessage
# import logging
# import datetime
# from streamlit_feedback import streamlit_feedback
# import os
# import base64
# import hashlib
# import uuid
# import sys

# # Importer nos modules locaux
# from utils.config import APP_TITLE, COMMUNE_NAME, MISTRAL_API_KEY
# from utils.vector_store import VectorStoreManager
# from utils.database import log_interaction, update_feedback
# from utils.query_classifier import QueryClassifier

# # -----------------------------
# # Fonction utilisant conversation_manager
# # -----------------------------
# def traiter_conversation(*args, **kwargs):
#     # Import "lazy" pour éviter l'import circulaire
#     from utils.conversation_history import conversation_manager

#     # Exemple d'utilisation
#     conversation_manager.do_something(*args, **kwargs)

# # Configuration du logging
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )

# # --- Configuration de la page Streamlit ---
# st.set_page_config(page_title=APP_TITLE, page_icon="📚", layout="wide")

# # =============================================================================
# # GESTION MULTI-UTILISATEURS
# # =============================================================================

# def get_user_session_id():
#     """
#     Génère ou récupère un identifiant unique pour la session utilisateur.
#     Chaque utilisateur aura son propre ID de session persistant.
#     """
#     if 'user_session_id' not in st.session_state:
#         # Générer un ID unique basé sur l'adresse IP et un UUID
#         user_ip = st.context.headers.get("X-Forwarded-For", "unknown")
#         unique_id = f"{user_ip}_{uuid.uuid4().hex[:8]}"
#         st.session_state.user_session_id = unique_id
#         logging.info(f"Nouvel utilisateur créé: {unique_id}")
    
#     return st.session_state.user_session_id

# def get_user_messages():
#     """
#     Récupère l'historique des messages pour l'utilisateur actuel.
#     Chaque utilisateur a son propre historique isolé.
#     """
#     user_id = get_user_session_id()
#     messages_key = f"messages_{user_id}"
    
#     if messages_key not in st.session_state:
#         st.session_state[messages_key] = []
#         logging.info(f"Initialisation de l'historique pour l'utilisateur {user_id}")
    
#     return st.session_state[messages_key]

# def get_user_last_interaction_id():
#     """
#     Récupère l'ID de la dernière interaction pour l'utilisateur actuel.
#     Utilisé pour gérer le feedback de manière isolée par utilisateur.
#     """
#     user_id = get_user_session_id()
#     interaction_key = f"last_interaction_id_{user_id}"
    
#     if interaction_key not in st.session_state:
#         st.session_state[interaction_key] = None
    
#     return st.session_state[interaction_key]

# def set_user_last_interaction_id(interaction_id):
#     """
#     Définit l'ID de la dernière interaction pour l'utilisateur actuel.
#     """
#     user_id = get_user_session_id()
#     interaction_key = f"last_interaction_id_{user_id}"
#     st.session_state[interaction_key] = interaction_id

# def reset_user_session():
#     """
#     Réinitialise complètement la session utilisateur :
#     - Historique des messages
#     - États d'aperçu PDF
#     - États des expanders de sources
#     - ID de la dernière interaction
#     - Feedback déjà soumis
#     - Sélecteur de conversation
#     """
#     user_id = get_user_session_id()
    
#     # Nettoyer l'historique des messages
#     messages_key = f"messages_{user_id}"
#     if messages_key in st.session_state:
#         del st.session_state[messages_key]
    
#     # Nettoyer l'ID de la dernière interaction
#     interaction_key = f"last_interaction_id_{user_id}"
#     if interaction_key in st.session_state:
#         del st.session_state[interaction_key]
    
#     # Nettoyer tous les états PDF pour cet utilisateur
#     pdf_keys_to_remove = [key for key in st.session_state.keys() 
#                          if key.startswith(f"show_pdf_{user_id}_")]
#     for key in pdf_keys_to_remove:
#         del st.session_state[key]
    
#     # Nettoyer tous les états d'expander pour cet utilisateur
#     expander_keys_to_remove = [key for key in st.session_state.keys() 
#                               if key.startswith(f"expander_sources_{user_id}_")]
#     for key in expander_keys_to_remove:
#         del st.session_state[key]
    
#     # Nettoyer les feedbacks soumis pour cet utilisateur
#     feedback_keys_to_remove = [key for key in st.session_state.keys() 
#                               if key.startswith(f"feedback_submitted_{user_id}_")]
#     for key in feedback_keys_to_remove:
#         del st.session_state[key]
    
#     # Réinitialiser le sélecteur de conversation
#     if "conversation_selector" in st.session_state:
#         st.session_state["conversation_selector"] = None
    
#     logging.info(f"Session réinitialisée pour l'utilisateur {user_id}")

# # =============================================================================
# # CSS PERSONNALISÉ (CONSERVÉ INTÉGRALEMENT)
# # =============================================================================

# custom_css = """
# <style>
# /* Couleurs générales */
# body {
#     background-color: #fff9f3;
#     color: #333333;
#     font-family: 'Segoe UI', sans-serif;
# }

# /* Header, boutons orange */
# header, .st-emotion-cache-18ni7ap, .st-emotion-cache-6qob1r {
#     background-color: #ffa94d !important;
#     color: white !important;
# }

# .stButton>button {
#     background-color: #ffa94d;
#     color: white;
#     border-radius: 8px;
#     font-weight: bold;
#     border: none;
#     padding: 6px 14px;
#     transition: background-color 0.3s ease;
# }

# .stButton>button:hover {
#     background-color: #ff922b;
#     color: white;
# }

# /* Boutons PDF spéciaux */
# .stButton>button[title*="Voir PDF"] {
#     background-color: #FF6B35;
#     color: white;
#     border: 2px solid #FF6B35;
# }

# .stButton>button[title*="Fermer PDF"] {
#     background-color: #dc3545;
#     color: white;
#     border: 2px solid #dc3545;
# }

# .stButton>button[title*="Voir PDF"]:hover {
#     background-color: #E55A2B;
#     border-color: #E55A2B;
# }

# .stButton>button[title*="Fermer PDF"]:hover {
#     background-color: #c82333;
#     border-color: #c82333;
# }

# /* Input et zone texte */
# input, textarea {
#     border-radius: 6px !important;
#     border: 1px solid #ffa94d !important;
#     padding: 6px;
# }

# /* Zone de chat input */
# .stChatInputContainer {
#     border: 2px solid #ffa94d !important;
#     border-radius: 10px !important;
#     background-color: #fff !important;
# }

# /* Expander titre */
# .stExpanderHeader {
#     background-color: #ffe8cc !important;
#     color: #ff6600 !important;
#     font-weight: bold;
#     border-radius: 5px;
# }

# /* Chat bubbles */
# .stChatMessage {
#     background-color: #fff3e0 !important;
#     border-radius: 10px;
#     padding: 10px;
#     margin-bottom: 10px;
#     border: 1px solid #ffe8cc;
# }

# /* Messages utilisateur */
# [data-testid="user-message"] {
#     background-color: #e3f2fd !important;
#     border-left: 4px solid #2196f3 !important;
# }

# /* Messages assistant */
# [data-testid="assistant-message"] {
#     background-color: #fff3e0 !important;
#     border-left: 4px solid #ffa94d !important;
# }

# /* Barre latérale */
# section[data-testid="stSidebar"] {
#     background-color: #fff3e0;
#     border-right: 2px solid #ffa94d;
# }

# .css-1d391kg {
#     background-color: #fff3e0;
# }

# /* Download button */
# [data-testid="baseButton-secondary"] {
#     border: 1px solid #ffa94d !important;
#     color: #ff6600 !important;
#     background: white;
# }

# [data-testid="baseButton-secondary"]:hover {
#     background: #ffe8cc;
# }

# /* Styles pour les containers PDF */
# .pdf-container {
#     border: 3px solid #FF6B35;
#     border-radius: 10px;
#     padding: 15px;
#     margin: 15px 0;
#     background-color: #FFF8F0;
#     box-shadow: 0 4px 6px rgba(255, 107, 53, 0.1);
# }

# .pdf-header {
#     color: #FF6B35;
#     margin-top: 0;
#     font-size: 1.2em;
#     font-weight: bold;
# }

# /* Titre principal */
# .main-title {
#     color: #ff6600;
#     text-align: center;
#     padding: 20px 0;
# }

# /* Messages d'info */
# .stInfo {
#     background-color: #e8f4fd !important;
#     border-left: 4px solid #2196f3 !important;
#     color: #0c5aa6 !important;
# }

# /* Messages de succès */
# .stSuccess {
#     background-color: #e8f5e8 !important;
#     border-left: 4px solid #4caf50 !important;
#     color: #2e7d32 !important;
# }

# /* Spinner/Loading */
# .stSpinner {
#     color: #ffa94d !important;
# }

# /* Sliders */
# .stSlider > div > div > div {
#     background-color: #ffa94d !important;
# }

# /* Select boxes */
# .stSelectbox > div > div {
#     border: 1px solid #ffa94d !important;
#     border-radius: 6px !important;
# }
# </style>
# """

# # Appliquer le CSS immédiatement après la configuration de la page
# st.markdown(custom_css, unsafe_allow_html=True)

# # =============================================================================
# # FONCTIONS POUR L'APERÇU PDF (ADAPTÉES MULTI-UTILISATEURS)
# # =============================================================================

# def display_pdf_preview(pdf_path, unique_key, container=None):
#     """
#     Affiche l'aperçu PDF dans un iframe avec gestion d'état multi-utilisateurs.
#     Utilise un container optionnel pour éviter les problèmes de re-render.
#     """
    
#     # Vérifier si le fichier existe
#     if not os.path.exists(pdf_path):
#         st.error(f"❌ Fichier PDF introuvable : {pdf_path}")
#         return
    
#     # Clé d'état unique pour ce PDF et cet utilisateur
#     user_id = get_user_session_id()
#     state_key = f"show_pdf_{user_id}_{unique_key}"
    
#     # Initialiser l'état si nécessaire
#     if state_key not in st.session_state:
#         st.session_state[state_key] = False
    
#     # Utiliser le container fourni ou créer un nouveau
#     display_container = container if container else st
    
#     # Bouton pour afficher/masquer le PDF
#     button_col1, button_col2 = display_container.columns([1, 1])
    
#     with button_col1:
#         if not st.session_state[state_key]:
#             if st.button("👁️ Voir PDF", key=f"btn_show_{user_id}_{unique_key}"):
#                 st.session_state[state_key] = True
    
#     with button_col2:
#         if st.session_state[state_key]:
#             if st.button("❌ Fermer PDF", key=f"btn_close_{user_id}_{unique_key}"):
#                 st.session_state[state_key] = False
    
#     # Afficher le PDF si l'état est actif
#     if st.session_state[state_key]:
#         try:
#             with open(pdf_path, "rb") as pdf_file:
#                 pdf_data = pdf_file.read()
#                 pdf_b64 = base64.b64encode(pdf_data).decode('utf-8')
            
#             # Container stylisé avec bordure orange
#             display_container.markdown("""
#             <div style="
#                 border: 3px solid #FF6B35;
#                 border-radius: 10px;
#                 padding: 15px;
#                 margin: 15px 0;
#                 background-color: #FFF8F0;
#                 box-shadow: 0 4px 6px rgba(255, 107, 53, 0.1);
#             ">
#                 <h4 style="color: #FF6B35; margin-top: 0;">📄 Aperçu du document PDF</h4>
#             </div>
#             """, unsafe_allow_html=True)
            
#             # Iframe pour afficher le PDF
#             pdf_display = f'''
#             <div style="
#                 border: 3px solid #FF6B35;
#                 border-radius: 10px;
#                 padding: 0;
#                 margin: 10px 0;
#                 background-color: #FFF8F0;
#                 overflow: hidden;
#             ">
#                 <iframe src="data:application/pdf;base64,{pdf_b64}" 
#                         width="100%" 
#                         height="600" 
#                         style="border: none; border-radius: 7px;">
#                     <p>Votre navigateur ne supporte pas l'affichage des PDF. 
#                     <a href="data:application/pdf;base64,{pdf_b64}" target="_blank">Cliquez ici pour télécharger le PDF</a></p>
#                 </iframe>
#             </div>
#             '''
#             display_container.markdown(pdf_display, unsafe_allow_html=True)
            
#         except Exception as e:
#             display_container.error(f"❌ Erreur lors de l'affichage du PDF : {str(e)}")

# def get_absolute_pdf_path(relative_path):
#     """
#     Convertit un chemin relatif en chemin absolu pour les fichiers PDF.
#     Gère les chemins dupliqués et les erreurs de structure de dossiers.
#     """
#     base_path = os.path.join(os.getcwd(), "inputs")
#     full_path = os.path.join(base_path, relative_path)
    
#     # Vérifier si le fichier existe
#     if os.path.exists(full_path):
#         return full_path
#     else:
#         logging.warning(f"Fichier non trouvé: {full_path}")
#         # Essayer sans duplication Oxypharm
#         if "Oxypharm" in relative_path:
#             clean_path = relative_path.replace("Oxypharm\\", "", 1).replace("Oxypharm/", "", 1)
#             alternative_path = os.path.join(os.getcwd(), "inputs", "Oxypharm", clean_path)
#             if os.path.exists(alternative_path):
#                 logging.info(f"Fichier trouvé à: {alternative_path}")
#                 return alternative_path
        
#         return full_path  # Retourne le chemin même s'il n'existe pas

# def display_sources_with_pdf_preview(sources, message_timestamp):
#     """
#     Affiche les sources avec aperçu PDF intégré, adapté pour multi-utilisateurs.
#     Version simplifiée sans gestion complexe d'expander pour éviter les bugs.
#     """
    
#     if not sources:
#         return
    
#     user_id = get_user_session_id()
    
#     # Créer un container permanent pour les sources
#     sources_container = st.container()
    
#     with sources_container:
#         # Utiliser un expander simple sans gestion d'état complexe
#         with st.expander("📚 Sources utilisées", expanded=True):
#             for i, source in enumerate(sources):
#                 # Créer un container pour chaque source
#                 source_container = st.container()
                
#                 with source_container:
#                     # Accès sécurisé aux métadonnées
#                     meta = source.get("metadata", {})
#                     relative_path = meta.get("source", "")
                    
#                     # Affichage des informations de la source
#                     st.markdown(f"**Source {i+1}:** `{relative_path}`")
#                     st.markdown(f"*Score de similarité:* {source.get('score', 0.0):.2f}%")
#                     if 'raw_score' in source:
#                         st.markdown(f"*Score brut:* {source.get('raw_score', 0.0):.4f}")
#                     st.markdown(f"*Catégorie:* `{meta.get('category', 'N/A')}`")
                    
#                     # Zone de texte pour l'extrait
#                     st.text_area(
#                         f"Extrait {i+1}", 
#                         value=source.get("text", "")[:500]+"...", 
#                         height=100, 
#                         disabled=True, 
#                         key=f"src_{user_id}_{message_timestamp}_{i}"
#                     )
                    
#                     # Bouton pour afficher le PDF si le fichier existe
#                     if relative_path and relative_path.lower().endswith('.pdf'):
#                         absolute_path = get_absolute_pdf_path(relative_path)
#                         unique_key = f"{message_timestamp}_{i}_{hash(relative_path)}"
                        
#                         # Passer le container de la source à la fonction PDF
#                         display_pdf_preview(absolute_path, unique_key, source_container)
                        
#                     st.divider()  # Séparateur entre les sources

# # =============================================================================
# # INITIALISATION AVEC CACHE STREAMLIT
# # =============================================================================

# @st.cache_resource
# def get_vector_store():
#     """
#     Met en cache le VectorStoreManager pour éviter de recharger l'index à chaque interaction.
#     Partagé entre tous les utilisateurs pour optimiser les performances.
#     """
#     logging.info("Chargement du VectorStoreManager...")
#     return VectorStoreManager()

# @st.cache_resource
# def get_mistral_client():
#     """
#     Met en cache le client Mistral pour éviter les reconnexions.
#     Partagé entre tous les utilisateurs.
#     """
#     if not MISTRAL_API_KEY:
#         st.error("Erreur: La clé API Mistral (MISTRAL_API_KEY) n'est pas configurée.")
#         st.stop()
#     logging.info("Initialisation du client Mistral...")
#     return MistralClient(api_key=MISTRAL_API_KEY)

# @st.cache_resource
# def get_query_classifier():
#     """
#     Met en cache le classificateur de requêtes.
#     Partagé entre tous les utilisateurs pour optimiser les performances.
#     """
#     logging.info("Initialisation du classificateur de requêtes...")
#     return QueryClassifier()

# # Charger les ressources partagées
# vector_store = get_vector_store()
# client = get_mistral_client()
# query_classifier = get_query_classifier()

# # =============================================================================
# # INTERFACE UTILISATEUR - SIDEBAR
# # =============================================================================

# with st.sidebar:
#     st.title(f"📚 {COMMUNE_NAME}")
#     st.caption(f"Assistant virtuel ASTERA")

#     # Affichage de l'ID utilisateur (pour debug/support)
#     user_id = get_user_session_id()
#     st.caption(f"🆔 Session: {user_id[:12]}...")

#     # Bouton pour lancer une nouvelle conversation
#     if st.button("🔄 Nouvelle conversation", use_container_width=True):
#         reset_user_session()
#         st.rerun()

#     st.divider()

#     # =============================================================================
#     # HISTORIQUE DES CONVERSATIONS
#     # =============================================================================
    
#     st.subheader("📋 Conversations précédentes")
    
#     try:
#         # Récupérer les conversations de l'utilisateur
#         user_conversations = conversation_manager.get_user_conversations(user_id, limit=15)
        
#         if user_conversations:
#             st.caption(f"💬 {len(user_conversations)} conversations trouvées")
            
#             # Menu déroulant pour sélectionner une conversation
#             conversation_options = [None] + user_conversations
#             selected_conversation = st.selectbox(
#                 "Sélectionner une conversation :",
#                 options=conversation_options,
#                 format_func=lambda x: "-- Sélectionner une conversation --" if x is None 
#                                     else conversation_manager.format_conversation_preview(x),
#                 key="conversation_selector"
#             )
            
#             # Boutons d'action pour la conversation sélectionnée
#             if selected_conversation:
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     if st.button("📂 Charger", key="load_conversation_btn", use_container_width=True):
#                         # Charger les messages de la conversation
#                         conversation_messages = conversation_manager.load_conversation_messages(selected_conversation)
                        
#                         if conversation_messages:
#                             # Réinitialiser la session actuelle
#                             reset_user_session()
                            
#                             # Charger les messages dans la session
#                             user_messages = get_user_messages()
#                             user_messages.extend(conversation_messages)
                            
#                             st.success(f"✅ Conversation chargée ({len(conversation_messages)} messages)")
#                             st.rerun()
#                         else:
#                             st.error("❌ Impossible de charger la conversation")
                
#                 with col2:
#                     # Bouton d'information sur la conversation
#                     if st.button("ℹ️ Info", key="info_conversation_btn", use_container_width=True):
#                         # Afficher les détails dans un expander
#                         with st.expander("📊 Détails de la conversation", expanded=True):
#                             st.write(f"**🕐 Début:** {selected_conversation['start_time']}")
#                             st.write(f"**🕐 Fin:** {selected_conversation['last_activity']}")
#                             st.write(f"**💬 Échanges:** {selected_conversation['interactions_count']}")
#                             st.write(f"**⏱️ Durée:** {selected_conversation['duration_minutes']} min")
                            
#                             # Feedbacks
#                             total_fb = selected_conversation.get('total_feedbacks', 0)
#                             if total_fb > 0:
#                                 pos_fb = selected_conversation.get('positive_feedbacks', 0)
#                                 neg_fb = selected_conversation.get('negative_feedbacks', 0)
#                                 st.write(f"**👍 Feedbacks:** {pos_fb} positifs, {neg_fb} négatifs")
                            
#                             # Modes utilisés
#                             modes = selected_conversation.get('modes_used', [])
#                             if modes:
#                                 st.write(f"**🔧 Modes:** {', '.join(modes)}")
            
#             # Statistiques rapides de l'utilisateur
#             with st.expander("📊 Mes statistiques", expanded=False):
#                 user_summary = conversation_manager.get_conversation_summary(user_id)
#                 if user_summary:
#                     st.metric("Total conversations", user_summary.get('total_conversations', 0))
#                     st.metric("Total échanges", user_summary.get('total_interactions', 0))
#                     st.metric("Total feedbacks", user_summary.get('total_feedbacks', 0))
                    
#                     avg_length = user_summary.get('average_conversation_length', 0)
#                     if avg_length > 0:
#                         st.metric("Longueur moyenne", f"{avg_length:.1f} échanges/conv")
#         else:
#             st.info("💭 Aucune conversation précédente trouvée")
#             st.caption("Commencez une nouvelle conversation ci-dessus !")
            
#     except Exception as e:
#         st.error(f"❌ Erreur lors du chargement de l'historique: {str(e)}")
#         logging.error(f"Erreur historique conversations pour {user_id[:8]}: {e}")

#     st.divider()

#     # Paramètres de l'application
#     st.subheader("⚙️ Paramètres")

#     # Sélecteur de modèle Mistral
#     model_options = {
#         "mistral-small-latest": "Mistral Small (rapide)",
#         "mistral-large-latest": "Mistral Large (précis)",
#     }
#     selected_model = st.selectbox(
#         "Modèle LLM",
#         options=list(model_options.keys()),
#         format_func=lambda x: model_options[x],
#         index=0,  # Small par défaut
#     )

#     # Slider pour le nombre de documents
#     num_docs = st.slider(
#         "Nombre de documents à récupérer",
#         min_value=1,
#         max_value=20,
#         value=5,  # 5 par défaut
#         step=1,
#     )

#     # Slider pour le score minimum (en pourcentage)
#     min_score_percent = st.slider(
#         "Score minimum (filtrer les résultats faibles)",
#         min_value=0,
#         max_value=100,
#         value=75,  # 75% par défaut
#         step=5,
#         format="%d%%",
#     )
#     # Convertir le pourcentage en valeur décimale (0-1)
#     min_score = min_score_percent / 100.0

#     st.divider()

#     # Informations sur l'application
#     st.subheader("📝 Informations")
#     st.markdown(f"**Modèle sélectionné**: {model_options[selected_model]}")
#     st.markdown(
#         f"**Documents indexés**: {vector_store.index.ntotal if vector_store.index else 0}"
#     )

#     # Informations sur la conversation actuelle de l'utilisateur
#     user_messages = get_user_messages()
#     if user_messages:
#         st.info(
#             f"{len(user_messages) // 2} échanges dans cette conversation"
#         )

#         # Bouton pour télécharger la conversation de l'utilisateur
#         conversation_text = "\n\n".join(
#             [
#                 f"{'Utilisateur' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
#                 for msg in user_messages
#             ]
#         )

#         # Ajouter un en-tête avec la date et le titre
#         header = f"Conversation avec l'assistant virtuel de {COMMUNE_NAME}\n"
#         header += f"Date: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
#         header += f"Session: {user_id}\n\n"
#         conversation_text = header + conversation_text

#         # Bouton de téléchargement
#         st.download_button(
#             label="💾 Télécharger la conversation",
#             data=conversation_text,
#             file_name=f"conversation_{user_id[:8]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
#             mime="text/plain",
#             use_container_width=True,
#         )

# # =============================================================================
# # INTERFACE UTILISATEUR - CONTENU PRINCIPAL
# # =============================================================================

# # Titre principal
# st.title(f"📚 {APP_TITLE}")
# st.caption(f"Posez vos questions sur {COMMUNE_NAME}")

# # Affichage de l'historique du chat pour l'utilisateur actuel
# user_messages = get_user_messages()
# for message in user_messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#         # Afficher les sources si elles existent pour les messages de l'assistant
#         if message["role"] == "assistant" and "sources" in message and message["sources"]:
#             display_sources_with_pdf_preview(message["sources"], message["timestamp"])

# # =============================================================================
# # LOGIQUE DE TRAITEMENT DES REQUÊTES
# # =============================================================================

# # Zone de saisie utilisateur en bas
# if prompt := st.chat_input("Posez votre question ici..."):
#     user_id = get_user_session_id()
    
#     # Ajouter le message utilisateur à l'historique et l'afficher
#     user_messages = get_user_messages()
#     user_messages.append(
#         {
#             "role": "user",
#             "content": prompt,
#             "timestamp": datetime.datetime.now().isoformat(),
#         }
#     )
    
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Afficher un message d'attente
#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         message_placeholder.markdown(
#             "🧠 Recherche d'informations et génération de la réponse..."
#         )

#         # Logique de traitement de la requête
#         try:
#             # 1. Classifier la requête pour déterminer si elle nécessite RAG
#             needs_rag, confidence, reason = query_classifier.needs_rag(prompt)

#             # Afficher le résultat de la classification
#             mode_str = "RAG" if needs_rag else "DIRECT"
#             logging.info(
#                 f"[{user_id[:8]}] Classification de la requête: {mode_str} (confiance: {confidence:.2f}) - Raison: {reason}"
#             )

#             # Afficher un message indiquant le mode utilisé
#             mode_info = st.empty()
#             if needs_rag:
#                 mode_info.info(
#                     f"🔍 Mode RAG: Recherche d'informations spécifiques dans la base de connaissances (confiance: {confidence:.2f})"
#                 )
#                 logging.info(
#                     f"[{user_id[:8]}] Recherche de documents pour: '{prompt}' (max: {num_docs}, score min: {min_score})"
#                 )
#                 retrieved_docs = vector_store.search(
#                     prompt, k=num_docs, min_score=min_score
#                 )
#             else:
#                 mode_info.info(
#                     f"💡 Mode Direct: Réponse basée sur les connaissances générales du modèle (confiance: {confidence:.2f})"
#                 )
#                 # Pas de recherche dans le Vector Store
#                 retrieved_docs = []

#             # 3. Préparer les données en fonction du mode
#             if needs_rag and retrieved_docs:
#                 # Mode RAG avec documents trouvés
#                 logging.info(f"[{user_id[:8]}] {len(retrieved_docs)} documents récupérés.")
#                 # Préparer le contexte pour le LLM
#                 context_str = "\n\n---\n\n".join(
#                     [
#                         f"Source: {doc['metadata'].get('source', 'Inconnue')} (Score: {doc['score']:.4f})\nContenu: {doc['text']}"
#                         for doc in retrieved_docs
#                     ]
#                 )
#                 sources_for_log = [  # Version simplifiée pour le log et l'affichage
#                     {
#                         "text": doc["text"],
#                         "metadata": doc["metadata"],
#                         "score": doc["score"],
#                     }
#                     for doc in retrieved_docs
#                 ]

#                 # Prompt système pour le mode RAG
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# Répondez à la question de l'utilisateur en vous basant UNIQUEMENT sur la documentation fournie du contexte ci-dessous.
# Si l'information n'est pas dans le contexte, dites que vous ne savez pas ou que l'information n'est pas disponible dans les documents fournis.
# Soyez concis et précis. Citez vos sources si possible (par exemple, en mentionnant le nom du fichier ou la catégorie trouvée dans les métadonnées).

# Contexte fourni:
# ---
# {context_str}
# ---
# """
#             elif needs_rag and not retrieved_docs:
#                 # Mode RAG mais aucun document trouvé
#                 logging.warning(f"[{user_id[:8]}] Aucun document pertinent trouvé.")
#                 context_str = (
#                     "Aucune information pertinente trouvée dans les documents."
#                 )
#                 sources_for_log = []

#                 # Prompt système pour le mode RAG sans résultats
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# L'utilisateur a posé une question qui semble concerner des informations spécifiques à la documentation, mais aucune information pertinente n'a été trouvée dans notre base de connaissances.
# Indiquez poliment que vous n'avez pas cette information spécifique et suggérez à l'utilisateur de reformuler sa question ou de contacter directement le service desk ou le pôle IA (Myriana).
# N'inventez pas d'informations sur {COMMUNE_NAME}.
# """
#             else:
#                 # Mode Direct (sans RAG)
#                 context_str = "Mode direct: réponse basée sur les connaissances générales du modèle."
#                 sources_for_log = []

#                 # Prompt système pour le mode Direct
#                 system_prompt = f"""Vous êtes un assistant virtuel pour {COMMUNE_NAME}.
# Répondez à la question de l'utilisateur en utilisant vos connaissances générales.
# Soyez concis, précis et utile.
# Si la question concerne des informations spécifiques à {COMMUNE_NAME} que vous ne connaissez pas, indiquez clairement que vous n'avez pas cette information spécifique.
# N'inventez pas d'informations sur {COMMUNE_NAME}.
# """

#             user_message = ChatMessage(role="user", content=prompt)
#             system_message = ChatMessage(role="system", content=system_prompt)
#             messages_for_api = [system_message, user_message]

#             # 4. Appel à l'API Mistral Chat
#             logging.info(
#                 f"[{user_id[:8]}] Appel de l'API Mistral Chat avec le modèle {selected_model}..."
#             )
#             chat_response = client.chat(model=selected_model, messages=messages_for_api)
#             response_text = chat_response.choices[0].message.content
#             logging.info(f"[{user_id[:8]}] Réponse générée par Mistral.")

#             # 5. Afficher la réponse et les sources
#             message_placeholder.markdown(response_text)

#             # Afficher les sources si disponibles (mode RAG avec résultats)
#             if sources_for_log:
#                 display_sources_with_pdf_preview(sources_for_log, datetime.datetime.now().isoformat())
                        
#             elif needs_rag:
#                 # Mode RAG sans résultats
#                 st.info(
#                     "📭 Aucune source pertinente n'a été trouvée dans la base de connaissances pour cette question."
#                 )
#             else:
#                 # Mode Direct
#                 st.info(
#                     "🎯 Réponse générée en mode direct, sans consultation de la base de connaissances."
#                 )
            
#             # 6. Enregistrer l'interaction dans la base de données (sans feedback initial)
#             # Ajouter des métadonnées sur le mode utilisé et l'utilisateur
#             metadata = {
#                 "mode": "RAG" if needs_rag else "DIRECT",
#                 "confidence": confidence,
#                 "reason": reason,
#                 "user_session_id": user_id,
#             }

#             interaction_id = log_interaction(
#                 query=prompt,
#                 response=response_text,
#                 sources=sources_for_log,  # Stocke la liste de dicts
#                 metadata=metadata,  # Ajouter les métadonnées sur le mode et l'utilisateur
#             )
#             set_user_last_interaction_id(interaction_id)
#             logging.info(f"[{user_id[:8]}] Interaction enregistrée avec ID: {interaction_id}")

#             # Ajouter la réponse de l'assistant à l'historique pour affichage permanent
#             user_messages.append(
#                 {
#                     "role": "assistant",
#                     "content": response_text,
#                     "sources": sources_for_log,  # Garder les sources pour réaffichage
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "interaction_id": interaction_id,  # Lier le message à l'ID BDD
#                 }
#             )

#         except Exception as e:
#             # Vérifier si c'est une erreur API Mistral
#             if hasattr(e, "status_code") and hasattr(e, "message"):
#                 logging.error(f"[{user_id[:8]}] Erreur API Mistral: {e}")
#                 message_placeholder.error(
#                     f"❌ Une erreur s'est produite lors de la communication avec l'API Mistral: {e}"
#                 )
#             else:
#                 logging.error(f"[{user_id[:8]}] Erreur inattendue: {e}", exc_info=True)
#                 message_placeholder.error(f"❌ Une erreur s'est produite: {e}")

#             user_messages.append(
#                 {
#                     "role": "assistant",
#                     "content": f"Erreur: {e}",
#                     "sources": [],
#                     "timestamp": datetime.datetime.now().isoformat(),
#                     "interaction_id": None,
#                 }
#             )
#             set_user_last_interaction_id(None)  # Pas d'ID si erreur avant log

# # =============================================================================
# # SECTION FEEDBACK UTILISATEUR (ADAPTÉE MULTI-UTILISATEURS)
# # =============================================================================

# def handle_user_feedback():
#     """
#     Gère le système de feedback utilisateur avec isolation par utilisateur.
#     Chaque utilisateur peut donner un feedback sur sa dernière réponse uniquement.
#     """
#     user_id = get_user_session_id()
#     user_messages = get_user_messages()
    
#     # On cible la *dernière* réponse de l'assistant pour le feedback
#     last_assistant_message = next(
#         (m for m in reversed(user_messages) if m["role"] == "assistant"), None
#     )

#     # Vérifie si la dernière réponse a un ID d'interaction associé
#     current_interaction_id = (
#         last_assistant_message.get("interaction_id") if last_assistant_message else None
#     )

#     if current_interaction_id:
#         # Clé unique pour ce feedback (utilisateur + interaction)
#         feedback_key = f"feedback_{user_id}_{current_interaction_id}"
#         feedback_submitted_key = f"feedback_submitted_{user_id}_{current_interaction_id}"
        
#         # Vérifier si le feedback a déjà été soumis
#         feedback_already_submitted = st.session_state.get(feedback_submitted_key, False)
        
#         if not feedback_already_submitted:
#             # Utilisation de streamlit-feedback
#             feedback = streamlit_feedback(
#                 feedback_type="thumbs",  # "thumbs" ou "faces"
#                 optional_text_label="[Optionnel] Commentaires :",
#                 key=feedback_key,  # Clé unique liée à l'utilisateur et l'interaction
#                 align="flex-start",  # Aligner à gauche
#                 on_submit=lambda x: logging.info(f"[{user_id[:8]}] Feedback soumis: {x}"),  # Log pour débogage
#             )

#             # Traitement du feedback s'il est donné
#             if feedback:
#                 # Convertir le feedback en valeur numérique et texte
#                 feedback_score = feedback.get("score")

#                 # Vérifier si le score est valide
#                 # Le composant streamlit_feedback peut renvoyer des emojis au lieu de "thumbs_up"/"thumbs_down"
#                 if feedback_score == "👍" or feedback_score == "thumbs_up":
#                     feedback_score = "positive"
#                 elif feedback_score == "👎" or feedback_score == "thumbs_down":
#                     feedback_score = "negative"
#                 else:
#                     logging.warning(f"[{user_id[:8]}] Score de feedback invalide: {feedback_score}")
#                     feedback_score = None

#                 # 1 pour positif, 0 pour négatif
#                 feedback_value = (
#                     1
#                     if feedback_score == "positive"
#                     else 0 if feedback_score == "negative" else None
#                 )

#                 # Texte pour la base de données ("positif" ou "négatif")
#                 feedback_text = (
#                     "positif"
#                     if feedback_score == "positive"
#                     else "négatif" if feedback_score == "negative" else "N/A"
#                 )

#                 # Emoji pour l'affichage dans l'interface
#                 feedback_emoji = (
#                     "👍"
#                     if feedback_score == "positive"
#                     else "👎" if feedback_score == "negative" else "N/A"
#                 )
#                 comment = feedback.get("text", None)

#                 # Mettre à jour l'interaction dans la base de données
#                 success = update_feedback(
#                     current_interaction_id, feedback_text, comment, feedback_value
#                 )
#                 if success:
#                     st.toast(f"✅ Merci pour votre retour ({feedback_emoji}) !", icon="✅")
#                     # Marquer le feedback comme soumis pour cet utilisateur
#                     st.session_state[feedback_submitted_key] = True
#                     logging.info(f"[{user_id[:8]}] Feedback enregistré pour interaction {current_interaction_id}")
#                     st.rerun()  # Actualiser pour masquer les boutons de feedback
#                 else:
#                     st.toast("❌ Erreur lors de l'enregistrement de votre retour.", icon="❌")
#         else:
#             # Feedback déjà soumis, afficher un message informatif
#             st.success("✅ Merci ! Votre feedback a été pris en compte.")
#     else:
#         st.info("💬 Posez une question pour pouvoir donner votre avis sur la réponse.")

# # Appeler la fonction de gestion du feedback
# handle_user_feedback()

