"""
Robust script to import/append voters from new.csv into PostgreSQL users table.
Safely handles:
- Immediate per-row commit (so one error never rolls back other rows)
- Unique username constraints (disambiguates different people sharing an MCS number)
- Unique email constraints (blanks duplicate email instead of failing the insert)
- Unique file_no constraints (blanks duplicate file_no instead of failing the insert)
- Existing voter detection (updates staff details if already present)
"""

import sys
import os
import csv
import psycopg2
from passlib.context import CryptContext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    DB_HOST = settings.database_hostname
    DB_PORT = settings.database_port
    DB_NAME = settings.database_name
    DB_USER = settings.database_username
    DB_PASS = settings.database_password
except Exception:
    DB_HOST = os.getenv("DATABASE_HOSTNAME", "localhost")
    DB_PORT = os.getenv("DATABASE_PORT", "5432")
    DB_NAME = os.getenv("DATABASE_NAME", "voting")
    DB_USER = os.getenv("DATABASE_USERNAME", "postgres")
    DB_PASS = os.getenv("DATABASE_PASSWORD", "ebimobowei81")

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "new.csv")
if not os.path.exists(CSV_PATH):
    CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "new.csv")
if not os.path.exists(CSV_PATH):
    CSV_PATH = "new.csv"

def get_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
    except psycopg2.OperationalError as e:
        try:
            return psycopg2.connect(dbname=DB_NAME, user="postgres")
        except Exception:
            try:
                return psycopg2.connect(
                    host="127.0.0.1",
                    port=DB_PORT,
                    dbname=DB_NAME,
                    user=DB_USER,
                    password=DB_PASS
                )
            except Exception:
                raise e

def run_import():
    print(f"Connecting to database '{DB_NAME}'...")
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()
    print("Database connection established successfully.\n")

    # Hash default password
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_pw = pwd_context.hash("voter123")

    # Fetch existing DB users
    cur.execute("SELECT id, lower(username), lower(full_name), lower(coalesce(email, '')), lower(trim(coalesce(staff_file_no, ''))) FROM users;")
    all_users = cur.fetchall()
    
    db_by_username = {u[1]: u for u in all_users}
    existing_emails = {u[3] for u in all_users if u[3]}
    existing_file_nos = {u[4] for u in all_users if u[4]}

    print(f"Reading CSV from: {CSV_PATH}")
    with open(CSV_PATH, 'r', encoding='utf-8-sig', errors='replace') as f:
        rows = list(csv.DictReader(f))

    print(f"Total rows found in CSV: {len(rows)}")

    seen_in_batch = {}
    inserted = 0
    updated = 0
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

    update_sql = """
        UPDATE users
        SET staff_file_no = coalesce(users.staff_file_no, %s),
            staff_station = coalesce(%s, users.staff_station),
            staff_rank = coalesce(%s, users.staff_rank),
            staff_conraiss = coalesce(%s, users.staff_conraiss),
            phone = coalesce(%s, users.phone)
        WHERE id = %s
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
        f_lower = file_no.lower() if file_no else ""

        # Check if this person is ALREADY registered in the database
        if u_lower in db_by_username:
            existing_user = db_by_username[u_lower]
            ex_id, ex_user, ex_name, ex_email, ex_file = existing_user
            
            # Simple name similarity: check if last name or first name matches
            clean_curr_name = full_name.lower().replace("mr.", "").replace("mrs.", "").replace("miss", "").replace("dr.", "").strip()
            clean_ex_name = ex_name.replace("mr.", "").replace("mrs.", "").replace("miss", "").replace("dr.", "").strip()
            
            words_curr = set(clean_curr_name.split())
            words_ex = set(clean_ex_name.split())
            name_overlap = len(words_curr.intersection(words_ex)) > 0
            
            if name_overlap or (f_lower and f_lower == ex_file):
                # This voter is ALREADY in the database! Update details if needed
                try:
                    cur.execute(update_sql, (file_no, station, rank, conraiss, phone, ex_id))
                    conn.commit()
                    updated += 1
                except Exception as e:
                    conn.rollback()
                continue
            else:
                # DIFFERENT person sharing the same MCS number! Disambiguate username
                seen_in_batch[u_lower] = seen_in_batch.get(u_lower, 1) + 1
                final_username = f"{raw_u}-{seen_in_batch[u_lower]}"
                while final_username.lower() in db_by_username:
                    seen_in_batch[u_lower] += 1
                    final_username = f"{raw_u}-{seen_in_batch[u_lower]}"
        else:
            if u_lower in seen_in_batch:
                seen_in_batch[u_lower] += 1
                final_username = f"{raw_u}-{seen_in_batch[u_lower]}"
            else:
                seen_in_batch[u_lower] = 1
                final_username = raw_u

        # Handle Email uniqueness constraint
        final_email = email
        if email:
            if email in existing_emails:
                # Email already in use by another voter, leave blank to prevent DB constraint violation
                final_email = None
            else:
                existing_emails.add(email)

        # Handle Staff File No uniqueness constraint
        final_file_no = file_no
        if f_lower:
            if f_lower in existing_file_nos:
                # File number already in use by another voter, leave blank to prevent DB constraint violation
                final_file_no = None
            else:
                existing_file_nos.add(f_lower)

        try:
            cur.execute(insert_sql, (
                final_username, full_name, phone, final_email, hashed_pw, 'voter',
                True, False, True,
                final_file_no, station, rank, conraiss, staff_active
            ))
            # CRITICAL: Commit each row immediately so a rollback never affects other rows!
            conn.commit()
            db_by_username[final_username.lower()] = (None, final_username.lower(), full_name.lower(), final_email or '', final_file_no or '')
            inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"  [ERROR] Failed to insert '{final_username}' ({full_name}): {e}")
            skipped += 1
            continue

    conn.close()

    print(f"\n==========================================")
    print(f"Import Summary:")
    print(f"  Brand New Voters Inserted:  {inserted}")
    print(f"  Existing Voters Updated:    {updated}")
    print(f"  Skipped:                    {skipped}")
    print(f"  Total Processed:            {inserted + updated + skipped} / {len(rows)}")
    print(f"==========================================")

if __name__ == "__main__":
    run_import()
