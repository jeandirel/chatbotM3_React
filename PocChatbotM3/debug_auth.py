from utils.database import SessionLocal, User
from utils.auth import get_password_hash, verify_password
import logging

logging.basicConfig(level=logging.INFO)

def reset_admin():
    db = SessionLocal()
    try:
        username = "admin"
        password = "admin123"
        
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            logging.info(f"User '{username}' found.")
            # Verify current password
            if verify_password(password, user.hashed_password):
                logging.info("Current password is VALID.")
            else:
                logging.warning("Current password is INVALID. Resetting...")
                user.hashed_password = get_password_hash(password)
                db.commit()
                logging.info("Password reset successfully.")
        else:
            logging.warning(f"User '{username}' NOT found. Creating...")
            hashed_pw = get_password_hash(password)
            new_user = User(username=username, hashed_password=hashed_pw, role="admin")
            db.add(new_user)
            db.commit()
            logging.info(f"User '{username}' created successfully.")
            
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
