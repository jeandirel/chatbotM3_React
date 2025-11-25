# # utils/conversation_history.py
# import logging
# from datetime import datetime, timedelta
# from typing import List, Dict, Optional, Tuple
# import json

# from .database import get_all_interactions

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class ConversationHistory:
#     """
#     Gestionnaire d'historique des conversations multi-utilisateurs.
#     Permet de récupérer, grouper et charger les conversations précédentes d'un utilisateur.
#     """
    
#     def __init__(self):
#         self.session_gap_minutes = 30  # Gap de 30 minutes pour séparer les conversations
    
#     def get_user_conversations(self, user_session_id: str, limit: int = 10) -> List[Dict]:
#         """
#         Récupère les conversations distinctes d'un utilisateur spécifique.
        
#         Args:
#             user_session_id: ID de la session utilisateur
#             limit: Nombre maximum de conversations à retourner
        
#         Returns:
#             Liste de dictionnaires contenant les métadonnées des conversations
#         """
#         try:
#             # Récupérer toutes les interactions de l'utilisateur
#             all_interactions = get_all_interactions(limit=500)  # Limite élevée pour récupérer l'historique
            
#             if not all_interactions:
#                 logging.info(f"Aucune interaction trouvée pour l'utilisateur {user_session_id[:12]}")
#                 return []
            
#             # Filtrer les interactions de cet utilisateur
#             user_interactions = []
#             for interaction in all_interactions:
#                 metadata = interaction.get('metadata', {})
#                 if isinstance(metadata, dict):
#                     if metadata.get('user_session_id') == user_session_id:
#                         user_interactions.append(interaction)
            
#             if not user_interactions:
#                 logging.info(f"Aucune interaction trouvée pour l'utilisateur {user_session_id[:12]}")
#                 return []
            
#             # Grouper les interactions en conversations
#             conversations = self._group_interactions_into_conversations(user_interactions)
            
#             # Limiter le nombre de conversations et trier par date décroissante
#             conversations = sorted(conversations, key=lambda x: x['last_activity'], reverse=True)[:limit]
            
#             logging.info(f"Trouvé {len(conversations)} conversations pour l'utilisateur {user_session_id[:12]}")
#             return conversations
            
#         except Exception as e:
#             logging.error(f"Erreur lors de la récupération des conversations: {e}")
#             return []
    
#     def _group_interactions_into_conversations(self, interactions: List[Dict]) -> List[Dict]:
#         """
#         Groupe les interactions en conversations basées sur les gaps temporels.
        
#         Args:
#             interactions: Liste des interactions de l'utilisateur
        
#         Returns:
#             Liste des conversations groupées
#         """
#         if not interactions:
#             return []
        
#         # Trier les interactions par timestamp
#         sorted_interactions = sorted(interactions, key=lambda x: x['timestamp'])
        
#         conversations = []
#         current_conversation = []
#         last_timestamp = None
        
#         for interaction in sorted_interactions:
#             current_timestamp = datetime.fromisoformat(interaction['timestamp'].replace('Z', '+00:00'))
            
#             # Si c'est la première interaction ou si le gap est trop important
#             if (last_timestamp is None or 
#                 (current_timestamp - last_timestamp).total_seconds() > (self.session_gap_minutes * 60)):
                
#                 # Sauvegarder la conversation précédente si elle existe
#                 if current_conversation:
#                     conversations.append(self._create_conversation_metadata(current_conversation))
                
#                 # Commencer une nouvelle conversation
#                 current_conversation = [interaction]
#             else:
#                 # Ajouter à la conversation actuelle
#                 current_conversation.append(interaction)
            
#             last_timestamp = current_timestamp
        
#         # Ajouter la dernière conversation
#         if current_conversation:
#             conversations.append(self._create_conversation_metadata(current_conversation))
        
#         return conversations
    
#     def _create_conversation_metadata(self, interactions: List[Dict]) -> Dict:
#         """
#         Crée les métadonnées d'une conversation à partir de ses interactions.
        
#         Args:
#             interactions: Liste des interactions de la conversation
        
#         Returns:
#             Dictionnaire avec les métadonnées de la conversation
#         """
#         if not interactions:
#             return {}
        
#         first_interaction = interactions[0]
#         last_interaction = interactions[-1]
        
#         # Compter les types d'interactions
#         questions_count = len([i for i in interactions if i.get('query')])
        
#         # Calculer les statistiques de feedback
#         feedbacks = [i.get('feedback') for i in interactions if i.get('feedback')]
#         positive_feedbacks = len([f for f in feedbacks if f == 'positif'])
#         negative_feedbacks = len([f for f in feedbacks if f == 'négatif'])
        
#         # Déterminer les modes utilisés
#         modes_used = set()
#         for interaction in interactions:
#             metadata = interaction.get('metadata', {})
#             if isinstance(metadata, dict):
#                 mode = metadata.get('mode')
#                 if mode:
#                     modes_used.add(mode)
        
#         # Générer un titre intelligent SEULEMENT pour les conversations RAG
#         first_query = first_interaction.get('query', '')
#         first_interaction_metadata = first_interaction.get('metadata', {})
        
#         # Vérifier si la première interaction utilise le mode RAG
#         if (isinstance(first_interaction_metadata, dict) and 
#             first_interaction_metadata.get('mode') == 'RAG'):
#             # Générer un titre intelligent pour les questions RAG
#             conversation_title = self._generate_conversation_title(first_query)
#         else:
#             # Pour les questions non-RAG, utiliser un titre générique
#             conversation_title = None
        
#         # Créer un aperçu de la première question (tronquée) comme fallback
#         preview_text = first_query[:60] + "..." if len(first_query) > 60 else first_query
        
#         return {
#             'conversation_id': f"conv_{first_interaction['id']}_{last_interaction['id']}",
#             'title': conversation_title,  # Titre généré automatiquement seulement pour RAG
#             'start_time': first_interaction['timestamp'],
#             'last_activity': last_interaction['timestamp'],
#             'interactions_count': len(interactions),
#             'questions_count': questions_count,
#             'preview_text': preview_text,  # Garder l'aperçu comme fallback
#             'positive_feedbacks': positive_feedbacks,
#             'negative_feedbacks': negative_feedbacks,
#             'total_feedbacks': len(feedbacks),
#             'modes_used': list(modes_used),
#             'interactions': interactions,  # Garder les interactions pour le chargement
#             'duration_minutes': self._calculate_conversation_duration(interactions),
#             'is_rag_conversation': 'RAG' in modes_used  # Indicateur pour le type de conversation
#         }
    
#     def _generate_conversation_title(self, first_query: str) -> str:
#         """
#         Génère un titre intelligent pour la conversation basé sur la première question.
#         Utilise des règles simples de transformation de la question en titre.
        
#         Args:
#             first_query: Première question de la conversation
        
#         Returns:
#             Titre formaté pour la conversation
#         """
#         if not first_query or len(first_query.strip()) == 0:
#             return "Nouvelle conversation"
        
#         # Nettoyer la question
#         query = first_query.strip()
        
#         # Règles de transformation simples
#         transformations = {
#             # Questions courantes sur M3
#             r'comment\s+(se\s+connecter|me\s+connecter)\s+(à|au|sur)\s+(.+?)[\?\.]?$': r'Connexion \3',
#             r'comment\s+(créer|faire|générer)\s+(une?\s+)?(.+?)[\?\.]?$': r'Créer \3',
#             r'comment\s+(utiliser|user)\s+(.+?)[\?\.]?$': r'Utiliser \2',
#             r'comment\s+(configurer|paramétrer)\s+(.+?)[\?\.]?$': r'Configuration \2',
#             r'comment\s+(installer|mettre en place)\s+(.+?)[\?\.]?$': r'Installation \2',
#             r'comment\s+(résoudre|corriger|réparer)\s+(.+?)[\?\.]?$': r'Résoudre \2',
#             r'comment\s+(accéder\s+à|aller\s+sur)\s+(.+?)[\?\.]?$': r'Accès \2',

#             # Questions "où" et "que"
#             r'où\s+(se\s+trouve|est|trouver)\s+(.+?)[\?\.]?$': r'Localiser \2',
#             r'qu\'?est-ce\s+que?\s+(.+?)[\?\.]?$': r'Définition \1',
#             r'que\s+fait\s+(.+?)[\?\.]?$': r'Fonction \1',

#             # Questions "pourquoi"
#             r'pourquoi\s+(.+?)[\?\.]?$': r'Raison \1',

#             # Procédures
#             r'procédure\s+(pour|de)\s+(.+?)[\?\.]?$': r'Procédure \2',
#             r'étapes\s+(pour|de)\s+(.+?)[\?\.]?$': r'Étapes \2',

#             # Erreurs et problèmes
#             r'erreur\s+(.+?)[\?\.]?$': r'Erreur \1',
#             r'problème\s+(avec|de)\s+(.+?)[\?\.]?$': r'Problème \2',
#             r'bug\s+(.+?)[\?\.]?$': r'Bug \1',
#         }
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
#         Utilise le titre généré seulement pour les conversations RAG.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
        
#         # Utiliser le titre généré seulement si c'est une conversation RAG et qu'un titre existe
#         if (conversation.get('is_rag_conversation', False) and 
#             conversation.get('title') and 
#             conversation.get('title') != "Nouvelle conversation"):
#             display_title = conversation['title']
#         else:
#             # Sinon utiliser l'aperçu de la question originale
#             display_title = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Indicateur du type de conversation
#         mode_indicator = ""
#         if conversation.get('is_rag_conversation', False):
#             mode_indicator = " 🔍"  # Icône pour les conversations RAG
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {display_title}{mode_indicator} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {display_title}{mode_indicator} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Connexion \3',
#             r'comment\s+(créer|faire|générer)\s+(une?\s+)?(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Créer \3',
#             r'comment\s+(utiliser|user)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Utiliser \2',
#             r'comment\s+(configurer|paramétrer)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Configuration \2',
#             r'comment\s+(installer|mettre en place)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Installation \2',
#             r'comment\s+(résoudre|corriger|réparer)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Résoudre \2',
#             r'comment\s+(accéder\s+à|aller\s+sur)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Accès \2',
            
#             # Questions "où" et "que"
#             r'où\s+(se\s+trouve|est|trouver)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Localiser \2',
#             r'qu\'?est-ce\s+que?\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Définition \1',
#             r'que\s+fait\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Fonction \1',
            
#             # Questions "pourquoi"
#             r'pourquoi\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Raison \1',
            
#             # Procédures
#             r'procédure\s+(pour|de)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Procédure \2',
#             r'étapes\s+(pour|de)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Étapes \2',
            
#             # Erreurs et problèmes
#             r'erreur\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Erreur \1',
#             r'problème\s+(avec|de)\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Problème \2',
#             r'bug\s+(.+?)[\?\.]?
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(): r'Bug \1',
#         }
        
#         import re
        
#         # Appliquer les transformations
#         for pattern, replacement in transformations.items():
#             match = re.search(pattern, query.lower())
#             if match:
#                 try:
#                     # Appliquer la transformation
#                     title = re.sub(pattern, replacement, query.lower(), flags=re.IGNORECASE)
#                     # Capitaliser les mots importants
#                     title = self._capitalize_title(title)
#                     return title
#                 except:
#                     continue
        
#         # Si aucune transformation ne correspond, créer un titre simple
#         # Garder les premiers mots et capitaliser
#         words = query.split()[:4]  # Garder max 4 mots
#         if words:
#             title = ' '.join(words)
#             # Supprimer les caractères de ponctuation de fin
#             title = re.sub(r'[?!.]+
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory(), '', title)
#             return self._capitalize_title(title)
        
#         return "Nouvelle conversation"
    
#     def _capitalize_title(self, title: str) -> str:
#         """
#         Capitalise correctement un titre en gardant les mots importants en majuscule.
        
#         Args:
#             title: Titre à capitaliser
        
#         Returns:
#             Titre capitalisé
#         """
#         # Mots à ne pas capitaliser (sauf en début de titre)
#         lowercase_words = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'à', 'au', 'aux', 
#                           'sur', 'dans', 'avec', 'pour', 'par', 'et', 'ou', 'mais', 'donc'}
        
#         words = title.split()
#         capitalized = []
        
#         for i, word in enumerate(words):
#             if i == 0:  # Premier mot toujours capitalisé
#                 capitalized.append(word.capitalize())
#             elif word.lower() in lowercase_words:
#                 capitalized.append(word.lower())
#             else:
#                 capitalized.append(word.capitalize())
        
#         return ' '.join(capitalized)
    
#     def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
#         """
#         Calcule la durée d'une conversation en minutes.
        
#         Args:
#             interactions: Liste des interactions
        
#         Returns:
#             Durée en minutes
#         """
#         if len(interactions) < 2:
#             return 0
        
#         first_time = datetime.fromisoformat(interactions[0]['timestamp'].replace('Z', '+00:00'))
#         last_time = datetime.fromisoformat(interactions[-1]['timestamp'].replace('Z', '+00:00'))
        
#         duration = (last_time - first_time).total_seconds() / 60
#         return int(duration)
    
#     def format_conversation_preview(self, conversation: Dict) -> str:
#         """
#         Formate l'aperçu d'une conversation pour le menu déroulant.
        
#         Args:
#             conversation: Métadonnées de la conversation
        
#         Returns:
#             Chaîne formatée pour l'affichage
#         """
#         if not conversation:
#             return "Conversation vide"
        
#         # Formatage de la date
#         start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
#         date_str = start_time.strftime('%d/%m/%Y %H:%M')
        
#         # Informations sur la conversation
#         interactions_count = conversation.get('interactions_count', 0)
#         duration = conversation.get('duration_minutes', 0)
#         preview = conversation.get('preview_text', 'Sans titre')
        
#         # Indicateurs de feedback
#         feedback_indicator = ""
#         total_feedbacks = conversation.get('total_feedbacks', 0)
#         if total_feedbacks > 0:
#             positive = conversation.get('positive_feedbacks', 0)
#             if positive > 0:
#                 feedback_indicator = f" 👍{positive}"
#             if conversation.get('negative_feedbacks', 0) > 0:
#                 feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
#         # Format final
#         if duration > 0:
#             return f"{date_str} - {preview} ({interactions_count} échanges, {duration}min{feedback_indicator})"
#         else:
#             return f"{date_str} - {preview} ({interactions_count} échanges{feedback_indicator})"
    
#     def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
#         """
#         Convertit les interactions d'une conversation au format messages de Streamlit.
        
#         Args:
#             conversation: Métadonnées de la conversation avec interactions
        
#         Returns:
#             Liste de messages au format Streamlit
#         """
#         if not conversation or 'interactions' not in conversation:
#             return []
        
#         messages = []
#         interactions = conversation['interactions']
        
#         for interaction in interactions:
#             # Message utilisateur
#             if interaction.get('query'):
#                 messages.append({
#                     'role': 'user',
#                     'content': interaction['query'],
#                     'timestamp': interaction['timestamp']
#                 })
            
#             # Message assistant
#             if interaction.get('response'):
#                 # Préparer les sources pour l'affichage
#                 sources = interaction.get('sources', [])
#                 formatted_sources = []
#                 if sources and isinstance(sources, list):
#                     formatted_sources = [
#                         {
#                             'text': src.get('text', ''),
#                             'metadata': src.get('metadata', {}),
#                             'score': src.get('score', 0.0)
#                         }
#                         for src in sources
#                     ]
                
#                 messages.append({
#                     'role': 'assistant',
#                     'content': interaction['response'],
#                     'sources': formatted_sources,
#                     'timestamp': interaction['timestamp'],
#                     'interaction_id': interaction['id']
#                 })
        
#         return messages
    
#     def get_conversation_summary(self, user_session_id: str) -> Dict:
#         """
#         Génère un résumé de l'activité conversationnelle de l'utilisateur.
        
#         Args:
#             user_session_id: ID de la session utilisateur
        
#         Returns:
#             Dictionnaire avec les statistiques de l'utilisateur
#         """
#         try:
#             conversations = self.get_user_conversations(user_session_id, limit=50)
            
#             if not conversations:
#                 return {
#                     'total_conversations': 0,
#                     'total_interactions': 0,
#                     'total_feedbacks': 0,
#                     'average_conversation_length': 0
#                 }
            
#             total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
#             total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
#             total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
#             return {
#                 'total_conversations': len(conversations),
#                 'total_interactions': total_interactions,
#                 'total_feedbacks': total_feedbacks,
#                 'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
#                 'total_duration_minutes': total_duration,
#                 'most_recent_activity': conversations[0].get('last_activity') if conversations else None
#             }
            
#         except Exception as e:
#             logging.error(f"Erreur lors du calcul du résumé: {e}")
#             return {}

# # Instance globale du gestionnaire d'historique
# conversation_manager = ConversationHistory()



####################################### mise à jour 24/06/2024 #########################################
######### code generer par gemini2.5 pro
# utils/conversation_history.py
# utils/conversation_history.py