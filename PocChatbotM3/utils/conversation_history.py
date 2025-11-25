
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import re # Import pour la gestion des expressions régulières

from .database import get_all_interactions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConversationHistory:
    """
    Gestionnaire d'historique des conversations multi-utilisateurs.
    Permet de récupérer, grouper et charger les conversations précédentes d'un utilisateur.
    """
    
    def __init__(self):
        # Durée maximale (en minutes) entre deux interactions pour les considérer dans la même conversation
        self.session_gap_minutes = 30  
    
    def get_current_conversation_key(self, user_session_id: str, current_time: datetime) -> str:
        """
        Calcule une clé unique pour la conversation en cours basée sur le gap temporel (30 minutes).
        Utilisée par MistralChat.py pour grouper les interactions dans la base de données.
        """
        # 1. Calculer le début de l'intervalle actuel
        total_minutes = current_time.hour * 60 + current_time.minute
        session_interval_start_minutes = (total_minutes // self.session_gap_minutes) * self.session_gap_minutes
        
        # 2. Reconstruire l'horodatage tronqué
        start_hour = session_interval_start_minutes // 60
        start_minute = session_interval_start_minutes % 60
        
        # Conserver la date, mais ajuster l'heure et les secondes/microsecondes à zéro
        truncated_time = current_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        # 3. Générer la clé
        # Format: [user_id]_[YYYYMMDD]_[HHMM]
        date_part = truncated_time.strftime('%Y%m%d_%H%M')
        
        return f"{user_session_id}_{date_part}"

    def get_user_conversations(self, user_session_id: str, limit: int = 10) -> List[Dict]:
        """
        Récupère les conversations distinctes d'un utilisateur spécifique.
        """
        try:
            # Récupérer plus d'interactions pour s'assurer d'avoir assez d'historique pour grouper
            all_interactions = get_all_interactions(limit=500) 
            
            if not all_interactions:
                logging.info(f"Aucune interaction trouvée pour l'utilisateur {user_session_id[:12]}")
                return []
            
            # Filtrer les interactions de cet utilisateur
            user_interactions = []
            for interaction in all_interactions:
                # Vérification de sécurité des métadonnées (utilise 'query_metadata' qui est le champ JSON)
                metadata = interaction.get('query_metadata') or interaction.get('metadata', {}) 
                if isinstance(metadata, dict):
                    if metadata.get('user_session_id') == user_session_id:
                        user_interactions.append(interaction)
            
            if not user_interactions:
                logging.info(f"Aucune interaction trouvée pour l'utilisateur {user_session_id[:12]}")
                return []
            
            # Grouper les interactions en conversations
            conversations = self._group_interactions_into_conversations(user_interactions)
            
            # Limiter le nombre de conversations et trier par date décroissante
            conversations = sorted(conversations, key=lambda x: x['last_activity'], reverse=True)[:limit]
            
            logging.info(f"Trouvé {len(conversations)} conversations pour l'utilisateur {user_session_id[:12]}")
            return conversations
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des conversations: {e}")
            return []
    
    def _group_interactions_into_conversations(self, interactions: List[Dict]) -> List[Dict]:
        """
        Groupe les interactions en conversations basées sur les gaps temporels.
        """
        if not interactions:
            return []
        
        # Trier les interactions par timestamp
        sorted_interactions = sorted(interactions, key=lambda x: x['timestamp'])
        
        conversations = []
        current_conversation = []
        last_timestamp = None
        
        for interaction in sorted_interactions:
            # Correction pour gérer les formats d'horodatage JSON/SQLAlchemy
            timestamp_str = interaction['timestamp'].isoformat() if isinstance(interaction['timestamp'], datetime) else interaction['timestamp']
            
            try:
                current_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                logging.warning(f"Timestamp invalide: {timestamp_str}")
                continue
            
            if last_timestamp is None or (current_timestamp - last_timestamp).total_seconds() > (self.session_gap_minutes * 60):
                if current_conversation:
                    conversations.append(self._create_conversation_metadata(current_conversation))
                
                current_conversation = [interaction]
            else:
                current_conversation.append(interaction)
            
            last_timestamp = current_timestamp
        
        if current_conversation:
            conversations.append(self._create_conversation_metadata(current_conversation))
        
        return conversations
    
    def _create_conversation_metadata(self, interactions: List[Dict]) -> Dict:
        """
        Crée les métadonnées d'une conversation à partir de ses interactions.
        """
        if not interactions:
            return {}
        
        first_interaction = interactions[0]
        last_interaction = interactions[-1]
        
        # S'assurer que les timestamps sont des chaînes pour fromisoformat
        first_ts = first_interaction['timestamp'].isoformat() if isinstance(first_interaction['timestamp'], datetime) else first_interaction['timestamp']
        last_ts = last_interaction['timestamp'].isoformat() if isinstance(last_interaction['timestamp'], datetime) else last_interaction['timestamp']
        
        # Compter les types d'interactions
        questions_count = len([i for i in interactions if i.get('query')])
        
        # Calculer les statistiques de feedback
        feedbacks = [i.get('feedback') for i in interactions if i.get('feedback')]
        positive_feedbacks = len([f for f in feedbacks if f == 'positif'])
        negative_feedbacks = len([f for f in feedbacks if f == 'négatif'])
        
        # Déterminer les modes utilisés
        modes_used = set()
        for interaction in interactions:
            metadata = interaction.get('query_metadata') or interaction.get('metadata', {})
            if isinstance(metadata, dict):
                mode = metadata.get('mode')
                if mode:
                    modes_used.add(mode)
        
        first_query = first_interaction.get('query', '')
        
        # GÉNÉRATION DU TITRE AVANCÉ
        conversation_title = self._generate_conversation_title(first_query)
        
        preview_text = first_query[:60] + "..." if len(first_query) > 60 else first_query
        
        return {
            'conversation_id': f"conv_{first_interaction['id']}_{last_interaction['id']}",
            'title': conversation_title, # Titre généré automatiquement
            'start_time': first_ts,
            'last_activity': last_ts,
            'interactions_count': len(interactions),
            'questions_count': questions_count,
            'preview_text': preview_text,
            'positive_feedbacks': positive_feedbacks,
            'negative_feedbacks': negative_feedbacks,
            'total_feedbacks': len(feedbacks),
            'modes_used': list(modes_used),
            'interactions': interactions, # Garder les interactions pour le chargement
            'duration_minutes': self._calculate_conversation_duration(interactions),
            'is_rag_conversation': 'RAG' in modes_used
        }
    
    def _generate_conversation_title(self, first_query: str) -> str:
        """
        Génère un titre intelligent pour la conversation basé sur la première question.
        """
        if not first_query or len(first_query.strip()) == 0:
            return "Nouvelle conversation"
        
        query = first_query.strip().lower() # Traiter en minuscule
        
        # Règles de transformation: (Pattern Regex, Replacement String)
        transformations = {
            r'^comment\s+(se\s+connecter|me\s+connecter)\s+(à|au|sur)\s+(.+?)[\?\.]*$': r'Connexion \4',
            r'^comment\s+(créer|faire|générer)\s+(une?\s+)?(.+?)[\?\.]*$': r'Création \4',
            r'^comment\s+(utiliser|user)\s+(.+?)[\?\.]*$': r'Utilisation \2',
            r'^comment\s+(configurer|paramétrer)\s+(.+?)[\?\.]*$': r'Configuration \2',
            r'^comment\s+(résoudre|corriger|réparer)\s+(.+?)[\?\.]*$': r'Résolution \2',
            r'^comment\s+(accéder\s+à|aller\s+sur)\s+(.+?)[\?\.]*$': r'Accès \2',
            r'^où\s+(se\s+trouve|est|trouver)\s+(.+?)[\?\.]*$': r'Localisation \2',
            r'^qu\'?est-ce\s+que?\s+(.+?)[\?\.]*$': r'Définition \1',
            r'^que\s+fait\s+(.+?)[\?\.]*$': r'Fonction \1',
            r'^pourquoi\s+(.+?)[\?\.]*$': r'Raison \1',
            r'^(procédure|étapes)\s+(pour|de)\s+(.+?)[\?\.]*$': r'Procédure \3',
            r'^(erreur|problème|bug)\s+(.+?)[\?\.]*$': r'\1 \2',
            r'^c\'est\s+quoi\s+(.+?)[\?\.]*$': r'Définition \1', # Ajout pour M3
            r'(.+?)\s+dans\s+m3[\?\.]*$': r'\1 M3', # Ajout pour M3
        }
        
        # Appliquer les transformations
        for pattern, replacement in transformations.items():
            match = re.search(pattern, query)
            if match:
                try:
                    title = re.sub(pattern, replacement, query)
                    return self._capitalize_title(title)
                except Exception as e:
                    logging.warning(f"Erreur lors de la création du titre via regex: {e}")
                    continue
        
        # Fallback: Garder les premiers mots et capitaliser
        words = query.split()[:5]  
        if words:
            title = ' '.join(words)
            title = re.sub(r'[?!.]+$', '', title) # Supprimer la ponctuation de fin
            return self._capitalize_title(title)
        
        return "Nouvelle conversation"
    
    def _capitalize_title(self, title: str) -> str:
        """
        Capitalise correctement un titre.
        """
        lowercase_words = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'à', 'au', 'aux', 
                          'sur', 'dans', 'avec', 'pour', 'par', 'et', 'ou', 'mais', 'donc', 'un', 'une'}
        
        words = title.split()
        capitalized = []
        
        for i, word in enumerate(words):
            if i == 0:
                capitalized.append(word.capitalize())
            elif word.lower() in lowercase_words:
                capitalized.append(word.lower())
            else:
                capitalized.append(word.capitalize())
        
        return ' '.join(capitalized)
    
    def _calculate_conversation_duration(self, interactions: List[Dict]) -> int:
        """
        Calcule la durée d'une conversation en minutes.
        """
        if len(interactions) < 2:
            return 0
        
        try:
            first_ts_str = interactions[0]['timestamp'].isoformat() if isinstance(interactions[0]['timestamp'], datetime) else interactions[0]['timestamp']
            last_ts_str = interactions[-1]['timestamp'].isoformat() if isinstance(interactions[-1]['timestamp'], datetime) else interactions[-1]['timestamp']
            
            first_time = datetime.fromisoformat(first_ts_str.replace('Z', '+00:00'))
            last_time = datetime.fromisoformat(last_ts_str.replace('Z', '+00:00'))
            
            duration = (last_time - first_time).total_seconds() / 60
            return int(duration)
        except Exception:
            return 0
    
    def format_conversation_preview(self, conversation: Dict) -> str:
        """
        Formate l'aperçu d'une conversation pour le menu déroulant.
        """
        if not conversation:
            return "Conversation vide"
        
        # Conversion sûre de la date
        try:
            start_time = datetime.fromisoformat(conversation['start_time'].replace('Z', '+00:00'))
            date_str = start_time.strftime('%d/%m/%Y %H:%M')
        except Exception:
            date_str = "Date inconnue"
        
        # Informations sur la conversation
        interactions_count = conversation.get('interactions_count', 0)
        duration = conversation.get('duration_minutes', 0)
        display_title = conversation.get('title', conversation.get('preview_text', 'Sans titre'))
        
        # Indicateurs de feedback
        feedback_indicator = ""
        total_feedbacks = conversation.get('total_feedbacks', 0)
        if total_feedbacks > 0:
            positive = conversation.get('positive_feedbacks', 0)
            if positive > 0:
                feedback_indicator = f" 👍{positive}"
            if conversation.get('negative_feedbacks', 0) > 0:
                feedback_indicator += f" 👎{conversation.get('negative_feedbacks', 0)}"
        
        # Indicateur du type de conversation
        mode_indicator = " 🔍" if conversation.get('is_rag_conversation', False) else " 💡"
        
        # Format final
        if duration > 0:
            return f"{date_str} - {display_title}{mode_indicator} ({interactions_count} échanges, {duration}min{feedback_indicator})"
        else:
            return f"{date_str} - {display_title}{mode_indicator} ({interactions_count} échanges{feedback_indicator})"
    
    def load_conversation_messages(self, conversation: Dict) -> List[Dict]:
        """
        Convertit les interactions d'une conversation au format messages de Streamlit.
        """
        if not conversation or 'interactions' not in conversation:
            return []
        
        messages = []
        interactions = conversation['interactions']
        
        for interaction in interactions:
            # Message utilisateur
            if interaction.get('query'):
                messages.append({
                    'role': 'user',
                    'content': interaction['query'],
                    'timestamp': interaction['timestamp'],
                    'metadata': interaction.get('query_metadata') 
                })
            
            # Message assistant
            if interaction.get('response'):
                sources = interaction.get('sources', [])
                formatted_sources = []
                if sources and isinstance(sources, list):
                    formatted_sources = [
                        {
                            'text': src.get('text', ''),
                            'metadata': src.get('metadata', {}),
                            'score': src.get('score', 0.0),
                            'raw_score': src.get('raw_score', 0.0)
                        }
                        for src in sources
                    ]
                
                messages.append({
                    'role': 'assistant',
                    'content': interaction['response'],
                    'sources': formatted_sources,
                    'timestamp': interaction['timestamp'],
                    'interaction_id': interaction['id']
                })
        
        return messages
    
    def get_conversation_summary(self, user_session_id: str) -> Dict:
        """
        Génère un résumé de l'activité conversationnelle de l'utilisateur.
        """
        try:
            conversations = self.get_user_conversations(user_session_id, limit=100)
            
            if not conversations:
                return {
                    'total_conversations': 0,
                    'total_interactions': 0,
                    'total_feedbacks': 0,
                    'average_conversation_length': 0
                }
            
            total_interactions = sum(conv.get('interactions_count', 0) for conv in conversations)
            total_feedbacks = sum(conv.get('total_feedbacks', 0) for conv in conversations)
            total_duration = sum(conv.get('duration_minutes', 0) for conv in conversations)
            
            return {
                'total_conversations': len(conversations),
                'total_interactions': total_interactions,
                'total_feedbacks': total_feedbacks,
                'average_conversation_length': total_interactions / len(conversations) if conversations else 0,
                'total_duration_minutes': total_duration,
                'most_recent_activity': conversations[0].get('last_activity') if conversations else None
            }
            
        except Exception as e:
            logging.error(f"Erreur lors du calcul du résumé: {e}")
            return {}

# Instance globale du gestionnaire d'historique
conversation_manager = ConversationHistory()
