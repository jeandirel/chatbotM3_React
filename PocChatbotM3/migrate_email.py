import sqlite3
from utils.config import DATABASE_FILE

def migrate_db():
    print(f"Migrating database at {DATABASE_FILE}...")
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if email column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "email" not in columns:
            print("Adding 'email' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
            conn.commit()
            print("Migration successful.")
        else:
            print("'email' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
