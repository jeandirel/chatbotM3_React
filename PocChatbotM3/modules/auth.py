import logging
from datetime import timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from utils.database import get_db, User
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    """
    Service responsible for authentication and authorization.
    """

    def authenticate_user(self, db: Session, username: str, password: str):
        """Authenticates a user by username and password."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Authentication failed: User {username} not found.")
            return False
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user {username}.")
            return False
        logger.info(f"User {username} authenticated successfully.")
        return user

    def create_user_token(self, username: str) -> str:
        """Creates a JWT access token for a user."""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )

    def decode_access_token(self, token: str) -> Optional[dict]:
        """Decodes a JWT access token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """Dependency to get the current authenticated user."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        payload = self.decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
            
        return user

    def change_password(self, db: Session, username: str, old_password: str, new_password: str):
        """Changes the user's password."""
        user = self.authenticate_user(db, username, old_password)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True

    def register_user(self, db: Session, username: str, email: str, password: str):
        # 1. Check email domain
        if not email.endswith("@cerp-rouen.fr"):
            raise ValueError("L'email doit se terminer par @cerp-rouen.fr")
        
        # 2. Check if user exists
        existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            raise ValueError("Nom d'utilisateur ou email déjà utilisé")
            
        # 3. Create user
        hashed_password = get_password_hash(password)
        new_user = User(username=username, email=email, hashed_password=hashed_password, role="user")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
