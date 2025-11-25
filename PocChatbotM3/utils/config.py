# utils/config.py
import os
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
load_dotenv()

# --- Clé API ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print("⚠️ Attention: La clé API Mistral (MISTRAL_API_KEY) n'est pas définie dans le fichier .env")
    # Vous pouvez choisir de lever une exception ici ou de continuer avec des fonctionnalités limitées
    # raise ValueError("Clé API Mistral manquante. Veuillez la définir dans le fichier .env")

# --- Modèles Mistral ---
EMBEDDING_MODEL = "mistral-embed"
CHAT_MODEL = "mistral-small-latest" # Ou un autre modèle comme mistral-large-latest

# --- Configuration de l'Indexation ---
# INPUT_DATA_URL = os.getenv("INPUT_DATA_URL") # Décommentez si vous utilisez une URL
INPUT_DIR = "inputs"                # Dossier pour les données sources après extraction
VECTOR_DB_DIR = "vector_db"         # Dossier pour stocker l'index Faiss et les chunks
FAISS_INDEX_FILE = os.path.join(VECTOR_DB_DIR, "faiss_index.idx")
DOCUMENT_CHUNKS_FILE = os.path.join(VECTOR_DB_DIR, "document_chunks.pkl")

CHUNK_SIZE = 1500                   # Taille des chunks en *caractères* (vise ~512 tokens)
CHUNK_OVERLAP = 150                 # Chevauchement en *caractères*
EMBEDDING_BATCH_SIZE = 32           # Taille des lots pour l'API d'embedding

# --- Configuration de la Recherche ---
SEARCH_K = 5                        # Nombre de documents à récupérer par défaut

# --- Configuration de la Base de Données ---
RUNTIME_DATA_DIR = os.getenv("CHATBOT_RUNTIME_DIR", "runtime_data")
DATABASE_DIR = os.path.join(RUNTIME_DATA_DIR, "database")
DATABASE_FILE = os.path.join(DATABASE_DIR, "interactions.db")
DATABASE_URL = f"sqlite:///{DATABASE_FILE}" # URL pour SQLAlchemy

# --- Configuration de l'Application ---
APP_TITLE = "ChatbotM3 "
COMMUNE_NAME = "Documentation M3" # Nom à personnaliser dans l'interface


#mise à jours 08/09/2025 à 11h15
# --- RAG Routing (seuils) ---
RAG_TOPK = 5               # on regarde les 5 meilleurs chunks
RAG_MIN_SIMILARITY = 0.40  # 0..1 (ex: 0.40 = 40% si scores*100)
RAG_MIN_COVERAGE = 2       # au moins 2 chunks >= seuil
