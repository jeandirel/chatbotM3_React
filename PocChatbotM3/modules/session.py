import logging
import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from utils.database import SessionLocal, Conversation, Interaction, UserSession

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SessionService:
    """
    Service responsible for managing user sessions, conversation history, and interactions.
    Directly handles database operations for these entities.
    """

    def __init__(self):
        pass

    def _get_db(self) -> Session:
        return SessionLocal()

    def create_conversation(self, user_id: str, title: str = "Nouvelle discussion") -> Optional[Conversation]:
        """Creates a new conversation for a user."""
        db = self._get_db()
        try:
            conversation = Conversation(session_id=user_id, title=title)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation for user {user_id}: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Retrieves all conversations for a user."""
        db = self._get_db()
        try:
            conversations = db.query(Conversation).filter(Conversation.session_id == user_id).order_by(Conversation.created_at.desc()).all()
            return conversations
        except Exception as e:
            logger.error(f"Error fetching conversations for user {user_id}: {e}")
            return []
        finally:
            db.close()

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Retrieves message history for a conversation, formatted for the frontend."""
        db = self._get_db()
        try:
            interactions = db.query(Interaction).filter(Interaction.conversation_id == conversation_id).order_by(Interaction.timestamp.asc()).all()
            messages = []
            for i in interactions:
                # User message
                messages.append({
                    "role": "user", 
                    "content": i.query, 
                    "id": f"{i.id}_user"
                })
                # Assistant message
                messages.append({
                    "role": "assistant", 
                    "content": i.response, 
                    "id": f"{i.id}_bot", 
                    "sources": i.sources,
                    "interaction_id": i.id,
                    "feedback": i.feedback,
                    "feedback_comment": i.feedback_comment
                })
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages for conversation {conversation_id}: {e}")
            return []
        finally:
            db.close()

    def delete_conversation(self, conversation_id: str) -> bool:
        """Deletes a conversation and its interactions."""
        db = self._get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                db.delete(conversation)
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def log_interaction(self, query: str, response: str, sources: List[Dict], metadata: Dict) -> Optional[int]:
        """Logs a chat interaction into the database."""
        db = self._get_db()
        try:
            username = metadata.get("username") if metadata else None
            conversation_id = metadata.get("conversation_id") if metadata else None
            
            interaction = Interaction(
                query=query,
                response=response,
                sources=sources,
                query_metadata=metadata,
                username=username,
                conversation_id=conversation_id
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            
            logger.info(f"Interaction logged. ID: {interaction.id}")
            return interaction.id
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def update_feedback(self, interaction_id: int, feedback: str, feedback_comment: str = None, feedback_value: int = None) -> bool:
        """Updates feedback for a specific interaction."""
        db = self._get_db()
        try:
            interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
            if interaction:
                interaction.feedback = feedback
                interaction.feedback_value = feedback_value
                interaction.feedback_comment = feedback_comment
                db.commit()
                logger.info(f"Feedback updated for interaction {interaction_id}")
                return True
            else:
                logger.warning(f"Interaction {interaction_id} not found for feedback update.")
                return False
        except Exception as e:
            logger.error(f"Error updating feedback for interaction {interaction_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_or_create_user_session(self, username: str) -> str:
        """Gets or creates a persistent numeric session ID for a username."""
        if not username:
            raise ValueError("username must not be empty")
        
        normalized_username = username.strip().lower()
        db = self._get_db()
        try:
            record = db.query(UserSession).filter(UserSession.username == normalized_username).first()
            if record is None:
                record = UserSession(username=normalized_username)
                db.add(record)
                db.commit()
                db.refresh(record)
            
            return f"{record.id:03d}"
        except Exception as e:
            logger.error(f"Error managing user session for {normalized_username}: {e}")
            db.rollback()
            raise e
        finally:
            db.close()

    def get_all_interactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves the latest interactions from the database."""
        db = self._get_db()
        try:
            interactions = db.query(Interaction).order_by(Interaction.timestamp.desc()).limit(limit).all()
            logger.info(f"{len(interactions)} interactions retrieved.")
            return [
                {
                    "id": inter.id,
                    "timestamp": inter.timestamp,
                    "query": inter.query,
                    "response": inter.response,
                    "username": inter.username,
                    "sources": inter.sources,
                    "query_metadata": inter.query_metadata,
                    "metadata": inter.query_metadata, # Backward compatibility
                    "feedback": inter.feedback,
                    "feedback_value": inter.feedback_value,
                    "feedback_comment": inter.feedback_comment,
                    "conversation_id": inter.conversation_id
                }
                for inter in interactions
            ]
        except Exception as e:
            logger.error(f"Error retrieving interactions: {e}")
            return []
        finally:
            db.close()
