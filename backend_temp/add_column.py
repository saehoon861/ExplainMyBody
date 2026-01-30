import sqlite3
import os

db_path = "/home/roh/myworkspace/ExplainMyBody/backend_temp/explainmybody.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN daily_records JSON DEFAULT '{}'")
        conn.commit()
        print("✅ daily_records column added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️ daily_records column already exists.")
        else:
            print(f"❌ Error adding column: {e}")
    finally:
        conn.close()
else:
    print("❌ Database file not found.")
