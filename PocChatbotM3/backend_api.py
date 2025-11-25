import truststore
truststore.inject_into_ssl()
import logging
import datetime
import re
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Body, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from mistralai.exceptions import MistralAPIException

# Import local modules
from utils.config import (
    APP_TITLE, COMMUNE_NAME, MISTRAL_API_KEY, CHAT_MODEL, 
    SEARCH_K
)
from utils.vector_store import VectorStoreManager
from utils.database import (
    log_interaction, get_db, User, SessionLocal,
    create_conversation, get_user_conversations, get_conversation_messages, delete_conversation
)
from utils.query_classifier import QueryClassifier
from utils.conversation_history import conversation_manager
from utils.auth import (
    verify_password, get_password_hash, create_access_token, 
    get_current_active_user, get_current_admin_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES, User as AuthUser
)

# Initialize Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize FastAPI App
app = FastAPI(title=APP_TITLE)

# CORS Configuration
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # React default
    "*" # Allow all for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

from fastapi.staticfiles import StaticFiles
import os
# Mount static files
if not os.path.exists("inputs"):
    os.makedirs("inputs")
app.mount("/static", StaticFiles(directory="inputs"), name="static")

# Initialize Services
try:
    vs_manager = VectorStoreManager()
    query_classifier = QueryClassifier()
    mistral_client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
except Exception as e:
    logging.error(f"Failed to initialize services: {e}")
    vs_manager = None
    query_classifier = None
    mistral_client = None

# --- Helper Functions (Replicated from MistralChat.py) ---

SMALLTALK_PATTERNS = [
    r"^\s*bonjour\b",
    r"^\s*salut\b",
    r"^\s*bonsoir\b",
    r"^\s*(merci|thanks)\b",
    r"^\s*(coucou)\b",
    r"^\s*(hello)\b",
    r"\bcomment vas[- ]tu\b",
    r"\bcomment allez[- ]vous\b",
    r"\bbonne journ[eé]e\b",
    r"\bbonne soir[eé]e\b",
]

SMALLTALK_RESPONSES = [
    "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
    "Salut ! Je suis prêt à répondre à vos questions sur la documentation M3.",
    "Bonjour ! N'hésitez pas à me donner un sujet ou un besoin précis.",
    "Heureux de vous retrouver. Que souhaitez-vous explorer ?",
]

def is_smalltalk(query: str) -> bool:
    if not query:
        return False
    lowered = query.lower()
    return any(re.search(pattern, lowered) for pattern in SMALLTALK_PATTERNS)

def pick_smalltalk_response() -> str:
    idx = hash(datetime.datetime.now().isoformat()) % len(SMALLTALK_RESPONSES)
    return SMALLTALK_RESPONSES[idx]

def get_contextual_query(user_query: str, history_messages: list) -> tuple[str, list, bool]:
    """
    Rewrites the user query based on conversation history.
    """
    if not history_messages:
        return user_query, [], False
    
    system_prompt = """
Tu es un expert en réécriture de requêtes. Ton rôle est de réécrire la dernière question de l'utilisateur
pour qu'elle soit contextuellement complète et compréhensible par un système de recherche (RAG),
en utilisant l'historique de conversation fourni.

Si la dernière question est déjà autonome ou n'a pas besoin de contexte (par exemple, "Merci", "Bonjour", "Quelle est la procédure X"), retourne la question originale telle quelle.

Réponds UNIQUEMENT avec la requête réécrite et rien d'autre.
    """.strip()
    
    messages = [ChatMessage(role="system", content=system_prompt)]
    
    history_for_rewrite = history_messages[-4:] 
    
    for role, content in history_for_rewrite:
        if role in ('user', 'assistant'):
            messages.append(ChatMessage(role=role, content=content))
    
    messages.append(ChatMessage(role="user", content=f"Dernière question : {user_query}"))

    try:
        if not mistral_client:
            return user_query, [], False

        response = mistral_client.chat(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.0,
            max_tokens=150
        )
        
        rewritten_query = response.choices[0].message.content.strip()
        is_rewritten = (rewritten_query.lower().strip() != user_query.lower().strip())
        
        if is_rewritten:
            logging.info(f"Rewritten query: {user_query} -> {rewritten_query}")
        
        return rewritten_query, history_for_rewrite, is_rewritten

    except (MistralAPIException, Exception) as e:
        logging.error(f"Error rewriting query: {e}")
        return user_query, [], False

def process_query_logic(user_query: str, user_id: str, username: str, conversation_messages: list, current_conversation_id: str):
    """
    Core logic to process the query, perform RAG, and generate response.
    """
    if not mistral_client:
        return "Error: Mistral Client not initialized.", [], {}, None

    # 1. Rewrite Query
    rewritten_query, history_for_rewrite, is_rewritten = get_contextual_query(
        user_query, 
        conversation_messages
    )
    
    # 2. Classify Query
    needs_rag, confidence, reason = query_classifier.needs_rag(rewritten_query) if query_classifier else (False, 0.0, "Classifier not init")
    
    user_label = username or user_id[:8]
    logging.info(f"[{user_label}] Classification: RAG={needs_rag} (Confidence: {confidence:.2f}, Reason: {reason})")
    
    retrieved_docs = []
    sources_for_log = []
    
    # 3. Retrieve Documents
    if needs_rag and vs_manager and vs_manager.index is not None:
        try:
            retrieved_docs = vs_manager.search(
                query_text=rewritten_query, 
                k=SEARCH_K
            )
        except Exception as e:
            logging.error(f"Vector search error: {e}")
            needs_rag = False
            reason = f"Vector search failed: {e}"
    
    # 4. Prepare Context and Prompt
    llm_history = [ChatMessage(role=msg['role'], content=msg['content']) 
                   for msg in conversation_messages[-8:] 
                   if msg['role'] in ('user', 'assistant')]
        
    llm_history.append(ChatMessage(role="user", content=user_query))

    if is_smalltalk(user_query):
        friendly = pick_smalltalk_response()
        metadata = {
            "mode": "DIRECT",
            "confidence": 1.0,
            "reason": "Smalltalk detected",
            "conversation_id": current_conversation_id,
            "user_session_id": user_id,
            "username": username,
        }
        interaction_id = log_interaction(
            query=user_query,
            response=friendly,
            sources=[],
            metadata=metadata
        )
        return friendly, [], metadata, interaction_id
    
    
    # --- RAG Mode (Docs found) ---
    if needs_rag and retrieved_docs:
        logging.info(f"[{user_id[:8]}] RAG Active : {len(retrieved_docs)} docs retrieved.")
        
        context_str = "\n\n---\n\n".join(
            [
                f"Source: {doc['metadata'].get('source', 'Unknown')} (Score: {doc['score']:.4f}, Type: {doc['metadata'].get('context_type', 'principal')})\nContent: {doc['text']}"
                for doc in retrieved_docs
            ]
        )
        
        sources_for_log = [ 
            {
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": doc["score"],
                "raw_score": doc.get("raw_score", 0.0)
            }
            for doc in retrieved_docs
        ]

        system_prompt_template = """
Vous êtes un assistant virtuel pour {commune_name}.
Répondez à la question de l'utilisateur en vous basant **UNIQUEMENT** sur la documentation fournie dans le contexte ci-dessous.
Synthétisez toujours l'information avec vos propres mots et évitez le copier-coller.
Si l'information n'est **PAS** dans le contexte, dites poliment que vous ne savez pas ou que l'information n'est pas disponible dans votre base de connaissances.
Adoptez un ton cordial et professionnel, et **citez vos sources** (nom de fichier ou catégorie).

Contexte fourni pour la recherche:
---
{context_str}
---
""".strip()
        system_prompt = system_prompt_template.format(
            commune_name=COMMUNE_NAME,
            context_str=context_str
        ).strip()
        
    # --- RAG Mode (Retrieval Failed) ---
    elif needs_rag and not retrieved_docs:
        logging.warning(f"[{user_id[:8]}] RAG Failed : No docs found.")
        sources_for_log = []
        
        system_prompt_template = """
Vous êtes un assistant virtuel pour {commune_name}.
L'utilisateur a posé une question qui semble concerner des informations spécifiques à la documentation, mais aucune information pertinente n'a été trouvée dans notre base de connaissances.
Indiquez poliment que vous n'avez pas cette information spécifique et proposez-lui de reformuler la question ou de contacter directement le service desk ou le pôle IA (Myriana).
N'inventez pas d'informations sur {commune_name} et gardez un ton empathique.
""".strip()
        system_prompt = system_prompt_template.format(
            commune_name=COMMUNE_NAME
        ).strip()
        
    # --- Direct Mode ---
    else:
        sources_for_log = []
        
        system_prompt_template = """
Vous êtes un assistant virtuel pour {commune_name}.
Répondez à la question de l'utilisateur en utilisant vos connaissances générales avec un ton chaleureux.
Soyez concis, précis, utile et reformulez avec vos propres mots.
Si la question concerne des informations spécifiques à {commune_name} que vous ne connaissez pas, indiquez clairement que vous n'avez pas cette information spécifique.
N'inventez pas d'informations sur {commune_name}.
""".strip()
        system_prompt = system_prompt_template.format(
            commune_name=COMMUNE_NAME
        ).strip()
        
    # 5. Call Model
    final_messages = [ChatMessage(role="system", content=system_prompt)] + llm_history
    
    try:
        response = mistral_client.chat(
            model=CHAT_MODEL,
            messages=final_messages,
            temperature=0.2,
            max_tokens=2048
        )
        llm_response = response.choices[0].message.content
        
    except (MistralAPIException, Exception) as e:
        llm_response = f"❌ Mistral API Error: {e}"
        logging.error(f"Mistral API Error: {e}")
    
    # 6. Log Interaction
    metadata = {
        "user_session_id": user_id,
        "username": username,
        "conversation_id": current_conversation_id,
        "mode": "RAG" if needs_rag else "DIRECT",
        "confidence": confidence,
        "reason": reason,
        "rewritten_query": rewritten_query,
        "rewrite_history_used": is_rewritten,
        "llm_model": CHAT_MODEL
    }
    
    interaction_id = log_interaction(
        query=user_query,
        response=llm_response,
        sources=sources_for_log,
        metadata=metadata
    )
    
    return llm_response, sources_for_log, metadata, interaction_id


# --- API Models ---

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    username: Optional[str] = "API_User"
    history: Optional[List[Dict[str, str]]] = [] # [{'role': 'user', 'content': '...'}]

class SourceModel(BaseModel):
    text: str
    metadata: Dict[str, Any]
    score: float

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceModel] = []
    session_id: str
    conversation_id: Optional[str] = None
    interaction_id: Optional[int] = None
    metadata: Dict[str, Any] = {}

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: str = "Nouvelle discussion"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime.datetime
    session_id: str

    class Config:
        from_attributes = True

# --- API Endpoints ---

class FeedbackRequest(BaseModel):
    feedback: str
    feedback_value: Optional[int] = None
    feedback_comment: Optional[str] = None

class InteractionResponse(BaseModel):
    id: int
    timestamp: datetime.datetime
    query: str
    response: str
    username: Optional[str]
    feedback: Optional[str]
    feedback_comment: Optional[str]
    metadata: Optional[Dict[str, Any]]
    sources: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None

    class Config:
        from_attributes = True

# --- API Endpoints ---

@app.on_event("startup")
def startup_event():
    # Create default admin if not exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            hashed_pw = get_password_hash("admin123")
            new_admin = User(username="admin", hashed_password=hashed_pw, role="admin")
            db.add(new_admin)
            db.commit()
            logging.info("Default admin user created (admin/admin123)")
    finally:
        db.close()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: AuthUser = Depends(get_current_active_user)):
    return current_user

@app.get("/api/users", response_model=List[UserResponse])
async def read_users(current_user: AuthUser = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: AuthUser = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/feedback/{interaction_id}")
async def submit_feedback(interaction_id: int, feedback: FeedbackRequest, current_user: AuthUser = Depends(get_current_active_user)):
    from utils.database import update_feedback
    success = update_feedback(
        interaction_id=interaction_id,
        feedback=feedback.feedback,
        feedback_value=feedback.feedback_value,
        feedback_comment=feedback.feedback_comment
    )
    if not success:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return {"status": "success"}

@app.get("/api/interactions", response_model=List[InteractionResponse])
async def get_interactions(current_user: AuthUser = Depends(get_current_admin_user)):
    from utils.database import get_all_interactions
    interactions = get_all_interactions(limit=200)
    return interactions

# --- Conversation Endpoints ---

@app.get("/api/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: AuthUser = Depends(get_current_active_user)):
    # Use username as session_id for now, or a separate session ID if we had one
    # For simplicity, we'll use the username as the session identifier for registered users
    return get_user_conversations(current_user.username)

@app.post("/api/conversations", response_model=ConversationResponse)
async def create_new_conversation(conversation: ConversationCreate, current_user: AuthUser = Depends(get_current_active_user)):
    new_conv = create_conversation(session_id=current_user.username, title=conversation.title)
    if not new_conv:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return new_conv

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, current_user: AuthUser = Depends(get_current_active_user)):
    # In a real app, verify user owns conversation
    messages = get_conversation_messages(conversation_id)
    return messages

@app.delete("/api/conversations/{conversation_id}")
async def delete_conv(conversation_id: str, current_user: AuthUser = Depends(get_current_active_user)):
    success = delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success"}


@app.get("/health")
def health_check():
    return {"status": "ok", "services": {
        "vector_store": vs_manager is not None,
        "query_classifier": query_classifier is not None,
        "mistral_client": mistral_client is not None
    }}

@app.get("/")
def root():
    return {"message": "Chatbot API is running. Use the React interface to interact."}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, current_user: AuthUser = Depends(get_current_active_user)):
    try:
        # Generate or use session ID
        session_id = request.session_id or current_user.username
        
        # Override username with authenticated user
        username = current_user.username

        # Handle conversation ID
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create new conversation if not provided
            # But usually frontend should create it or we create it on first message
            # Let's create one if missing and it's the first message? 
            # Or just create one implicitly?
            # Better: If no conversation_id, create one.
            new_conv = create_conversation(session_id=username, title=request.message[:30] + "...")
            conversation_id = new_conv.id

        # Format history for internal logic
        # The internal logic expects a list of dicts or objects with 'role' and 'content'
        # We passed request.history which is List[Dict]
        
        response_text, sources, metadata, interaction_id = process_query_logic(
            user_query=request.message,
            user_id=session_id,
            username=username,
            conversation_messages=request.history,
            current_conversation_id=conversation_id
        )
        
        return ChatResponse(
            response=response_text,
            sources=sources,
            session_id=session_id,
            conversation_id=conversation_id,
            interaction_id=interaction_id,
            metadata=metadata
        )

    except Exception as e:
        logging.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
