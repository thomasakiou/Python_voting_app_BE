import sys
sys.path.insert(0, ".")
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT column_name, data_type, character_maximum_length 
        FROM information_schema.columns 
        WHERE table_name = 'users';
    """)).fetchall()
    for col in res:
        print(f'{col[0]}: {col[1]}({col[2]})')
