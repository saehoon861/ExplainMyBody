from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('user_details')]
print(f"Columns in user_details: {columns}")
missing = []
if 'preferences' not in columns:
    missing.append('preferences')
if 'health_specifics' not in columns:
    missing.append('health_specifics')

if missing:
    print(f"Missing columns: {missing}")
else:
    print("All columns present.")
