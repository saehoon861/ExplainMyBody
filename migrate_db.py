import sys
import os

# Create a temporary script to alter the table
sys.path.append(os.path.join(os.getcwd(), "backend"))

from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists first to be safe (postgres specific query, but standard SQL mostly)
            # Or just try to add it and ignore "duplicate column" error
            conn.execute(text("ALTER TABLE user_details ADD COLUMN target_weight FLOAT"))
            conn.commit()
            print("Successfully added target_weight column.")
        except Exception as e:
            print(f"Migration failed (maybe column exists?): {e}")

if __name__ == "__main__":
    migrate()
