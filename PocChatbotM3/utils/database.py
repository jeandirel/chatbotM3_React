
# utils/database.py
import os
import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, JSON, inspect, text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError
import uuid

from .config import DATABASE_URL, DATABASE_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Crée le dossier de la base de données s'il n'existe pas
os.makedirs(DATABASE_DIR, exist_ok=True)

# Crée l'engine SQLAlchemy pour la base de données SQLite
# `check_same_thread=False` est nécessaire pour SQLite avec Streamlit/multithreading
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False) # echo=True pour voir les requêtes SQL

# Crée une base de déclaration pour les modèles ORM
Base = declarative_base()

# Définit le modèle ORM pour la table des sessions utilisateurs
class UserSession(Base):
    """Associe un identifiant humain à un identifiant numérique persistant."""
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


# Définit le modèle ORM pour la table des utilisateurs
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # "admin" ou "user"
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id")) # Optional: link to registered user
    session_id = Column(String, index=True) # Link to session_id (for anonymous or registered)
    title = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    interactions = relationship("Interaction", back_populates="conversation", cascade="all, delete-orphan")


# Définit le modèle ORM pour la table des interactions
class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    username = Column(String(255))
    query = Column(Text, nullable=False)
    response = Column(Text)
    sources = Column(JSON) # Stocke la liste des dictionnaires de sources en JSON
    query_metadata = Column(JSON) # Stocke les métadonnées (mode, confiance, user_session_id, rewritten_query, etc.)
    feedback = Column(String(20)) # ex: "👍", "👎"
    feedback_value = Column(Integer) # 1 pour positif, 0 pour négatif, NULL pour aucun
    feedback_comment = Column(Text) # Optionnel: commentaire de feedback
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    conversation = relationship("Conversation", back_populates="interactions")

# Crée la table dans la base de données si elle n'existe pas déjà
try:
    Base.metadata.create_all(engine)
    logging.info("Tables vérifiées/créées dans la base de données.")
    try:
        inspector = inspect(engine)
        # Check for username column in interactions
        interaction_columns = {col["name"] for col in inspector.get_columns("interactions")}
        if "username" not in interaction_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE interactions ADD COLUMN username VARCHAR(255)"))
            logging.info("Colonne 'username' ajoutée à la table 'interactions'.")
            
        # Check for conversation_id column in interactions
        if "conversation_id" not in interaction_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE interactions ADD COLUMN conversation_id VARCHAR"))
            logging.info("Colonne 'conversation_id' ajoutée à la table 'interactions'.")
            
    except SQLAlchemyError as column_error:
        logging.error("Impossible de vérifier/ajouter les colonnes dans 'interactions': %s", column_error)
except SQLAlchemyError as e:
    logging.error(f"Erreur lors de la création/vérification de la table: {e}")

# Crée une factory de session pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Fonction utilitaire pour obtenir une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_interaction(query: str, response: str, sources: list, metadata: dict = None, feedback: str = None, feedback_comment: str = None):
    """Enregistre une interaction dans la base de données."""
    db_session = SessionLocal()
    try:
        username = None
        conversation_id = None
        if metadata and isinstance(metadata, dict):
            username = metadata.get("username")
            conversation_id = metadata.get("conversation_id")

        interaction = Interaction(
            query=query,
            response=response,
            sources=sources, # SQLAlchemy gère la sérialisation JSON
            query_metadata=metadata, # Métadonnées
            username=username,
            feedback=feedback,
            feedback_comment=feedback_comment,
            conversation_id=conversation_id
        )
        db_session.add(interaction)
        db_session.commit()

        # Journaliser avec des informations sur le mode et l'ID utilisateur utilisé
        mode_info = ""
        user_info = ""
        username_info = ""
        if metadata:
            if "mode" in metadata:
                mode_info = f", Mode: {metadata['mode']}"
            if "user_session_id" in metadata:
                user_info = f", User: {metadata['user_session_id'][:8]}..."
            if username:
                username_info = f", Username: {username}"

        logging.info(f"Interaction enregistrée (Query: '{query[:50]}...'{mode_info}{user_info}{username_info}, Feedback: {feedback})")
        return interaction.id # Retourne l'ID de l'interaction enregistrée
    except SQLAlchemyError as e:
        logging.error(f"Erreur lors de l'enregistrement de l'interaction: {e}")
        db_session.rollback() # Annule les changements en cas d'erreur
        return None
    finally:
        db_session.close() # Ferme toujours la session

def get_all_interactions(limit: int = 100):
    """Récupère les dernières interactions de la base de données."""
    db_session = SessionLocal()
    try:
        interactions = db_session.query(Interaction).order_by(Interaction.timestamp.desc()).limit(limit).all()
        logging.info(f"{len(interactions)} interactions récupérées.")
        # Convertit les objets Interaction en dictionnaires pour une manipulation plus facile (ex: Pandas)
        return [
            {
                "id": inter.id,
                "timestamp": inter.timestamp,
                "query": inter.query,
                "response": inter.response,
                "username": inter.username,
                "sources": inter.sources, # Déjà une liste de dicts (ou None)
                "query_metadata": inter.query_metadata, # Changement de nom de clé pour la cohérence
                "metadata": inter.query_metadata, # Garder 'metadata' pour la rétrocompatibilité (utile pour le viewer)
                "feedback": inter.feedback,
                "feedback_value": inter.feedback_value,
                "feedback_comment": inter.feedback_comment,
                "conversation_id": inter.conversation_id
            }
            for inter in interactions
        ]
    except SQLAlchemyError as e:
        logging.error(f"Erreur lors de la récupération des interactions: {e}")
        return []
    finally:
        db_session.close()

def update_feedback(interaction_id: int, feedback: str, feedback_comment: str = None, feedback_value: int = None):
    """Met à jour le feedback pour une interaction spécifique (Logique conservée)."""
    db_session = SessionLocal()
    try:
        interaction = db_session.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
            # Mise à jour des valeurs
            interaction.feedback = feedback
            interaction.feedback_value = feedback_value
            interaction.feedback_comment = feedback_comment

            # Enregistrer les modifications
            db_session.commit()
            logging.info(f"Feedback mis à jour pour l'interaction ID {interaction_id}")
            return True
        else:
            logging.warning(f"Interaction ID {interaction_id} non trouvée pour la mise à jour du feedback.")
            return False
    except SQLAlchemyError as e:
        logging.error(f"Erreur lors de la mise à jour du feedback pour l'interaction {interaction_id}: {e}")
        db_session.rollback()
        return False
    finally:
        db_session.close()


def get_or_create_user_session(username: str) -> str:
    """Retourne un identifiant numérique formaté pour un utilisateur donné.

    Crée automatiquement l'entrée si elle n'existe pas encore.
    """
    if not username:
        raise ValueError("username must not be empty")

    normalized_username = username.strip().lower()
    if not normalized_username:
        raise ValueError("username must contain non-whitespace characters")

    db_session = SessionLocal()
    try:
        record = db_session.query(UserSession).filter(UserSession.username == normalized_username).first()
        if record is None:
            record = UserSession(username=normalized_username)
            db_session.add(record)
            db_session.commit()
            db_session.refresh(record)

        return f"{record.id:03d}"
    except SQLAlchemyError as e:
        logging.error("Erreur lors de la récupération/creation de la session utilisateur '%s': %s", normalized_username, e)
        db_session.rollback()
        raise
    finally:
        db_session.close()

# --- Conversation Management Functions ---

def create_conversation(session_id: str, title: str = "Nouvelle discussion"):
    db = SessionLocal()
    try:
        conversation = Conversation(session_id=session_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception as e:
        logging.error(f"Error creating conversation: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def get_user_conversations(session_id: str):
    db = SessionLocal()
    try:
        conversations = db.query(Conversation).filter(Conversation.session_id == session_id).order_by(Conversation.created_at.desc()).all()
        return conversations
    finally:
        db.close()

def get_conversation_messages(conversation_id: str):
    db = SessionLocal()
    try:
        interactions = db.query(Interaction).filter(Interaction.conversation_id == conversation_id).order_by(Interaction.timestamp.asc()).all()
        messages = []
        for i in interactions:
            messages.append({"role": "user", "content": i.query, "id": f"{i.id}_user"})
            messages.append({
                "role": "assistant", 
                "content": i.response, 
                "id": f"{i.id}_bot", 
                "sources": i.sources,
                "interaction_id": i.id,
                "feedback": i.feedback
            })
        return messages
    finally:
        db.close()

def delete_conversation(conversation_id: str):
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    except Exception as e:
        logging.error(f"Error deleting conversation: {e}")
        db.rollback()
        return False
    finally:
        db.close()
