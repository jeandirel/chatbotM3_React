from utils.database import SessionLocal, User
from utils.auth import get_password_hash

def reset_admin_password():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print(f"Resetting password for user: {admin.username}")
            admin.hashed_password = get_password_hash("admin123")
            db.commit()
            print("Password reset to 'admin123' successfully.")
        else:
            print("Admin user not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
