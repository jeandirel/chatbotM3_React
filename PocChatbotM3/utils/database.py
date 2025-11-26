
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
    email = Column(String, unique=True, index=True, nullable=True)
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

class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    category = Column(String, default="Général")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

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


