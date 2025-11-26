import sys
import os
# Add current dir to path to find modules
sys.path.append(os.getcwd())

from utils.database import SessionLocal
from sqlalchemy import text
from utils.config import DATABASE_FILE

print(f"Configured DB File: {DATABASE_FILE}")

try:
    if os.path.exists(DATABASE_FILE):
        print(f"DB File exists. Size: {os.path.getsize(DATABASE_FILE)} bytes")
    else:
        print("DB File does NOT exist!")

    db = SessionLocal()
    # Check if table exists first
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions'")).fetchone()
    if result:
        count = db.execute(text("SELECT COUNT(*) FROM interactions")).scalar()
        print(f"Number of interactions in DB: {count}")
        
        if count > 0:
            last = db.execute(text("SELECT * FROM interactions ORDER BY timestamp DESC LIMIT 1")).fetchone()
            print(f"Last interaction: {last}")
    else:
        print("Table 'interactions' does not exist.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
