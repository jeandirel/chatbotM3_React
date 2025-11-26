import truststore
truststore.inject_into_ssl()
import logging
import time
import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os

# Import new modules
from modules.ingestion import IngestionService
from modules.preprocessing import PreprocessingService
from modules.embedding import EmbeddingService
from modules.vector_store import VectorStoreService
from modules.retriever import RetrieverService
from modules.reranking import RerankingService
from modules.generation import GenerationService
from modules.cache import CacheService
from modules.session import SessionService
from modules.auth import AuthService
from modules.monitoring import MonitoringService

# Import config and database utils (still used for DB session)
from utils.config import APP_TITLE, SEARCH_K, CHUNK_SIZE, CHUNK_OVERLAP, DATABASE_FILE
print(f"🚀 DEBUG: Database path is: {DATABASE_FILE}")
from utils.database import get_db, SessionLocal, User, FAQ

# Initialize Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI App
app = FastAPI(title=APP_TITLE)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if not os.path.exists("inputs"):
    os.makedirs("inputs")
app.mount("/static", StaticFiles(directory="inputs"), name="static")

# --- Initialize Services ---
try:
    monitoring_service = MonitoringService()
    auth_service = AuthService()
    session_service = SessionService()
    cache_service = CacheService()
    
    ingestion_service = IngestionService()
    preprocessing_service = PreprocessingService(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    embedding_service = EmbeddingService()
    vector_store_service = VectorStoreService()
    
    retriever_service = RetrieverService(embedding_service, vector_store_service)
    reranking_service = RerankingService()
    generation_service = GenerationService()
    
    logging.info("All modules initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize services: {e}")
    raise e

# --- Helper Logic ---

def process_query_logic(user_query: str, user_id: str, username: str, conversation_messages: list, current_conversation_id: str):
    """
    Orchestrates the RAG pipeline using the new modular architecture.
    """
    start_time = time.time()
    
    # 1. Check Cache
    cache_key = f"{user_query}_{current_conversation_id}" # Simple cache key
    cached_response = cache_service.get(cache_key)
    if cached_response:
        monitoring_service.log_event("Cache Hit", {"query": user_query})
        return cached_response['response'], cached_response['sources'], cached_response['metadata'], None

    # 2. Rewrite Query
    rewritten_query, is_rewritten = generation_service.rewrite_query(user_query, conversation_messages)
    
    # 3. Check for Smalltalk
    if generation_service.is_smalltalk(user_query):
        friendly_response = generation_service.get_smalltalk_response()
        metadata = {
            "mode": "DIRECT",
            "confidence": 1.0,
            "reason": "Smalltalk detected",
            "conversation_id": current_conversation_id,
            "user_session_id": user_id,
            "username": username,
        }
        interaction_id = session_service.log_interaction(user_query, friendly_response, [], metadata)
        return friendly_response, [], metadata, interaction_id

    # 4. Retrieve Documents
    retrieved_docs = retriever_service.retrieve(rewritten_query, k=SEARCH_K)
    
    # 5. Rerank Results
    reranked_docs = reranking_service.rerank(retrieved_docs, k=SEARCH_K)
    
    sources_for_log = [
        {
            "text": doc["text"],
            "metadata": doc["metadata"],
            "score": doc["score"],
            "raw_score": doc.get("raw_score", 0.0)
        }
        for doc in reranked_docs
    ]

    # 6. Generate Response
    if reranked_docs:
        llm_response = generation_service.generate_rag_response(user_query, reranked_docs, conversation_messages)
        mode = "RAG"
    else:
        llm_response = generation_service.generate_direct_response(user_query, conversation_messages)
        mode = "DIRECT"

    # 7. Log Interaction & Metrics
    metadata = {
        "user_session_id": user_id,
        "username": username,
        "conversation_id": current_conversation_id,
        "mode": mode,
        "rewritten_query": rewritten_query,
        "rewrite_history_used": is_rewritten,
    }
    
    interaction_id = session_service.log_interaction(user_query, llm_response, sources_for_log, metadata)
    monitoring_service.log_performance("process_query_logic", start_time)
    
    # 8. Update Cache
    cache_service.set(cache_key, {
        'response': llm_response,
        'sources': sources_for_log,
        'metadata': metadata
    })

    return llm_response, sources_for_log, metadata, interaction_id


# --- API Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    username: Optional[str] = "API_User"
    history: Optional[List[Dict[str, str]]] = []

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
    # created_at: datetime.datetime # Simplified for now

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class ConversationCreate(BaseModel):
    title: str = "Nouvelle discussion"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime.datetime
    session_id: str

    class Config:
        from_attributes = True

class FeedbackRequest(BaseModel):
    feedback: str
    feedback_value: Optional[int] = None
    feedback_comment: Optional[str] = None

class InteractionResponse(BaseModel):
    id: int
    # timestamp: datetime.datetime
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


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class FAQCreate(BaseModel):
    question: str
    category: str = "Général"

class FAQResponse(BaseModel):
    id: int
    question: str
    category: str
    
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
            from utils.auth import get_password_hash
            hashed_pw = get_password_hash("admin123")
            new_admin = User(username="admin", hashed_password=hashed_pw, role="admin")
            db.add(new_admin)
            db.commit()
            logging.info("Default admin user created (admin/admin123)")
        
        # Create default FAQs if not exists
        try:
            faq_count = db.query(FAQ).count()
            if faq_count == 0:
                default_faqs = [
                    {"question": "Comment consulter un document ?", "category": "Utilisation"},
                    {"question": "Comment envoyer un document ?", "category": "Utilisation"},
                    {"question": "La sécurité des données est-elle garantie ?", "category": "Sécurité"},
                    {"question": "Comment changer mon mot de passe ?", "category": "Compte"},
                    {"question": "Qui contacter en cas de problème ?", "category": "Support"},
                    {"question": "Quels sont les formats supportés ?", "category": "Technique"},
                    {"question": "Puis-je supprimer une conversation ?", "category": "Utilisation"},
                    {"question": "Comment fonctionne la recherche ?", "category": "Technique"},
                ]
                for item in default_faqs:
                    db.add(FAQ(question=item["question"], category=item["category"]))
                db.commit()
                logging.info("Default FAQs created")
        except Exception as e:
            logging.warning(f"Could not check/create FAQs (table might not exist yet): {e}")

    finally:
        db.close()

@app.get("/api/faq", response_model=List[FAQResponse])
async def get_faqs(db: Session = Depends(get_db)):
    return db.query(FAQ).all()

@app.post("/api/faq", response_model=FAQResponse)
async def create_faq(faq: FAQCreate, current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    new_faq = FAQ(question=faq.question, category=faq.category)
    db.add(new_faq)
    db.commit()
    db.refresh(new_faq)
    return new_faq

@app.delete("/api/faq/{faq_id}")
async def delete_faq(faq_id: int, current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(faq)
    db.commit()
    return {"status": "success"}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_user_token(user.username)
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "username": user.username}

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    try:
        new_user = auth_service.register_user(db, user.username, user.email, user.password)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user

@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest, current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    success = auth_service.change_password(db, current_user.username, request.old_password, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect old password")
    return {"status": "success"}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, current_user: User = Depends(auth_service.get_current_user)):
    try:
        session_id = request.session_id or current_user.username
        username = current_user.username
        conversation_id = request.conversation_id

        if not conversation_id:
            new_conv = session_service.create_conversation(user_id=username, title=request.message[:30] + "...")
            conversation_id = new_conv.id

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
        monitoring_service.log_error("chat_endpoint", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: User = Depends(auth_service.get_current_user)):
    return session_service.get_user_conversations(current_user.username)

@app.post("/api/conversations", response_model=ConversationResponse)
async def create_new_conversation(conversation: ConversationCreate, current_user: User = Depends(auth_service.get_current_user)):
    new_conv = session_service.create_conversation(user_id=current_user.username, title=conversation.title)
    if not new_conv:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return new_conv

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, current_user: User = Depends(auth_service.get_current_user)):
    return session_service.get_conversation_history(conversation_id)

@app.delete("/api/conversations/{conversation_id}")
async def delete_conv(conversation_id: str, current_user: User = Depends(auth_service.get_current_user)):
    success = session_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success"}

@app.get("/api/interactions")
async def get_interactions(limit: int = 100, current_user: User = Depends(auth_service.get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return session_service.get_all_interactions(limit=limit)

@app.post("/api/feedback/{interaction_id}")
async def submit_feedback(interaction_id: int, feedback: FeedbackRequest, current_user: User = Depends(auth_service.get_current_user)):
    # Use session_service for feedback updates
    success = session_service.update_feedback(
        interaction_id=interaction_id,
        feedback=feedback.feedback,
        feedback_value=feedback.feedback_value,
        feedback_comment=feedback.feedback_comment
    )
    if not success:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return {"status": "success"}
