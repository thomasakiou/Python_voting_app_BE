"""
Script to import 279 voters from new.csv into the PostgreSQL users table.
Usage:
    python import_new_voters.py [--disambiguate | --skip-duplicates]
"""

import sys
import os
import csv
import psycopg2
from passlib.context import CryptContext

# Database configuration (defaults to local .env or fallback)
DB_HOST = os.getenv("DATABASE_HOSTNAME", "localhost")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_NAME = os.getenv("DATABASE_NAME", "voting")
DB_USER = os.getenv("DATABASE_USERNAME", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "ebimobowei81")

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "new.csv")
if not os.path.exists(CSV_PATH):
    # Try current directory
    CSV_PATH = "new.csv"

def run_import(disambiguate: bool = True):
    print(f"Connecting to database '{DB_NAME}' at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = False
    cur = conn.cursor()

    # Ensure schema columns exist
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_accredited BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accredited_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accredited_device_id VARCHAR(255);",
        "ALTER TYPE user_roles ADD VALUE IF NOT EXISTS 'agent';",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS device_info VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_session_id VARCHAR(255);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_login_count INTEGER DEFAULT 0;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_file_no VARCHAR(100);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_station VARCHAR(150);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_rank VARCHAR(150);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_conraiss VARCHAR(50);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_active BOOLEAN DEFAULT TRUE;",
    ]
    for stmt in statements:
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            conn.rollback()

    # Hash default password
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_pw = pwd_context.hash("voter123")

    # Read existing DB usernames
    cur.execute("SELECT lower(username) FROM users;")
    existing_db_usernames = {r[0] for r in cur.fetchall()}

    print(f"Reading CSV from: {CSV_PATH}")
    with open(CSV_PATH, 'r', encoding='utf-8-sig', errors='replace') as f:
        rows = list(csv.DictReader(f))

    print(f"Total rows found in CSV: {len(rows)}")

    seen_in_batch = {}
    inserted = 0
    skipped = 0

    insert_sql = """
        INSERT INTO users (
            username, full_name, phone, email, password, role,
            is_active, is_accredited, must_change_password,
            staff_file_no, staff_station, staff_rank, staff_conraiss, staff_active
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """

    for idx, r in enumerate(rows, start=1):
        raw_u = r['username'].strip()
        full_name = r['fullname'].strip()
        phone = r.get('phone', '').strip() or None
        email = r.get('email', '').strip().lower() or None
        file_no = r.get('file No', '').strip() or None
        station = r.get('station', '').strip() or None
        rank = r.get('rank', '').strip() or None
        conraiss = r.get('conraiss', '').strip() or None
        
        raw_active = r.get('active', '').strip().lower()
        staff_active = False if raw_active in ('no', 'false', '0', 'inactive') else True

        u_lower = raw_u.lower()
        
        if u_lower in seen_in_batch or u_lower in existing_db_usernames:
            if disambiguate:
                # Add suffix to make unique
                seen_in_batch[u_lower] = seen_in_batch.get(u_lower, 0) + 1
                final_username = f"{raw_u}-{seen_in_batch[u_lower]}"
                # Ensure even the suffixed name is not taken
                while final_username.lower() in existing_db_usernames:
                    seen_in_batch[u_lower] += 1
                    final_username = f"{raw_u}-{seen_in_batch[u_lower]}"
            else:
                print(f"  [SKIPPED] Duplicate username '{raw_u}' for '{full_name}'")
                skipped += 1
                continue
        else:
            seen_in_batch[u_lower] = 1
            final_username = raw_u

        try:
            cur.execute(insert_sql, (
                final_username, full_name, phone, email, hashed_pw, 'voter',
                True, False, True,
                file_no, station, rank, conraiss, staff_active
            ))
            existing_db_usernames.add(final_username.lower())
            inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"  [ERROR] Failed to insert '{final_username}': {e}")
            skipped += 1
            continue

    conn.commit()
    conn.close()

    print(f"\n==========================================")
    print(f"Import Summary:")
    print(f"  Successfully inserted: {inserted} voters")
    print(f"  Skipped:               {skipped} voters")
    print(f"==========================================")

if __name__ == "__main__":
    mode_disambiguate = "--skip-duplicates" not in sys.argv
    run_import(disambiguate=mode_disambiguate)
