import os
import sqlite3
from werkzeug.security import generate_password_hash
from config import Config

try:
    import mysql.connector
    from mysql.connector import pooling
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

class DatabaseService:
    _mysql_pool = None
    _active_db_type = None

    @classmethod
    def get_db_type(cls):
        if cls._active_db_type:
            return cls._active_db_type
            
        if Config.DB_TYPE == "mysql" and HAS_MYSQL:
            try:
                # Test connection to MySQL
                conn = mysql.connector.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    connect_timeout=3
                )
                conn.close()
                cls._active_db_type = "mysql"
                return "mysql"
            except Exception as e:
                print(f"[DB Notice] MySQL connection failed ({e}). Falling back to SQLite database.")
                cls._active_db_type = "sqlite"
                return "sqlite"
        else:
            cls._active_db_type = "sqlite"
            return "sqlite"

    @classmethod
    def get_connection(cls):
        db_type = cls.get_db_type()
        if db_type == "mysql":
            try:
                return mysql.connector.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    autocommit=True
                )
            except Exception as e:
                print(f"[DB Warning] MySQL DB connect error: {e}. Switching to SQLite.")
                cls._active_db_type = "sqlite"
                return cls.get_sqlite_connection()
        else:
            return cls.get_sqlite_connection()

    @classmethod
    def get_sqlite_connection(cls):
        os.makedirs(os.path.dirname(Config.SQLITE_PATH), exist_ok=True)
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def _normalize_query(cls, query, db_type):
        """Standardize MySQL vs SQLite syntax differences."""
        if db_type == "sqlite":
            query = query.replace("%s", "?")
            query = query.replace("INSERT IGNORE INTO", "INSERT OR IGNORE INTO")
            query = query.replace("insert ignore into", "insert or ignore into")
            query = query.replace("AUTO_INCREMENT", "AUTOINCREMENT")
            query = query.replace("auto_increment", "autoincrement")
        elif db_type == "mysql":
            query = query.replace("INSERT OR IGNORE INTO", "INSERT IGNORE INTO")
            query = query.replace("insert or ignore into", "insert ignore into")
            query = query.replace("AUTOINCREMENT", "AUTO_INCREMENT")
            query = query.replace("autoincrement", "auto_increment")
        return query

    @classmethod
    def execute_query(cls, query, params=(), fetch_all=True, fetch_one=False):
        db_type = cls.get_db_type()
        conn = cls.get_connection()
        query = cls._normalize_query(query, db_type)
            
        try:
            cursor = conn.cursor() if db_type == "mysql" else conn.cursor()
            cursor.execute(query, params)
            
            if fetch_one:
                row = cursor.fetchone()
                if row and db_type == "mysql":
                    columns = [col[0] for col in cursor.description]
                    result = dict(zip(columns, row))
                elif row:
                    result = dict(row)
                else:
                    result = None
                return result
            elif fetch_all:
                rows = cursor.fetchall()
                if db_type == "mysql":
                    columns = [col[0] for col in cursor.description]
                    result = [dict(zip(columns, row)) for row in rows]
                else:
                    result = [dict(row) for row in rows]
                return result
            else:
                if db_type == "sqlite":
                    conn.commit()
                return cursor.rowcount
        finally:
            conn.close()

    @classmethod
    def execute_insert(cls, query, params=()):
        db_type = cls.get_db_type()
        conn = cls.get_connection()
        query = cls._normalize_query(query, db_type)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if db_type == "sqlite":
                conn.commit()
            last_id = cursor.lastrowid
            return last_id
        finally:
            conn.close()

    @classmethod
    def execute_batch(cls, query, params_list):
        db_type = cls.get_db_type()
        conn = cls.get_connection()
        query = cls._normalize_query(query, db_type)
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            if db_type == "sqlite":
                conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        db_type = cls.get_db_type()
        print(f"[Database Initialization] Using database engine: {db_type.upper()}")
        
        if db_type == "mysql":
            # Ensure DB exists
            try:
                conn = mysql.connector.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                conn.close()
            except Exception as e:
                print(f"[MySQL Init Error] {e}")

        # Run Schema SQL
        schema_file = "schema.sql" if db_type == "mysql" else "schema_sqlite.sql"
        schema_path = os.path.join(Config.BASE_DIR, "database", schema_file)
        
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
                
            conn = cls.get_connection()
            try:
                cursor = conn.cursor()
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
                if db_type == "sqlite":
                    conn.commit()
            except Exception as e:
                print(f"[Schema Execution Error] {e}")
            finally:
                conn.close()

        # Schema Migrations / Fixes for existing DBs
        try:
            # 1. Ensure is_active exists on users table
            cls.execute_query("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1", fetch_all=False)
        except Exception:
            pass  # Already exists

        try:
            # 2. Ensure activity_logs table exists
            cls.execute_query("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_name TEXT,
                    user_email TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """, fetch_all=False)
        except Exception:
            pass

        # Seed Default Users if empty
        users_count = cls.execute_query("SELECT COUNT(*) as cnt FROM users", fetch_one=True)
        if not users_count or users_count.get("cnt", 0) == 0:
            print("[Seeding Users] Creating default admin and user credentials...")
            admin_pwd = generate_password_hash("admin123")
            user_pwd = generate_password_hash("user123")
            
            cls.execute_insert(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ("System Administrator", "admin@crime.local", admin_pwd, "ADMIN")
            )
            cls.execute_insert(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ("Standard User", "user@crime.local", user_pwd, "USER")
            )

        # Primary admin account from environment variables (never hardcoded in production)
        primary_admin_email = os.getenv("ADMIN_EMAIL", "")
        primary_admin_name = os.getenv("ADMIN_NAME", "System Admin")
        primary_admin_pwd = os.getenv("ADMIN_PASSWORD", "")
        if primary_admin_email and primary_admin_pwd:
            existing_admin = cls.execute_query("SELECT id FROM users WHERE email = %s", (primary_admin_email,), fetch_one=True)
            if not existing_admin:
                hashed = generate_password_hash(primary_admin_pwd)
                cls.execute_insert(
                    "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s)",
                    (primary_admin_name, primary_admin_email, hashed, "ADMIN", 1)
                )

        # Seed Sample Crime Records if missing or old small dataset
        crime_count = cls.execute_query("SELECT COUNT(*) as cnt FROM crime_data", fetch_one=True)
        if not crime_count or crime_count.get("cnt", 0) < 1000:
            print("[Seeding Crime Data] Importing rich expanded Indian crime records with Area hierarchy...")
            cls.execute_query("DELETE FROM crime_data", fetch_all=False)
            cls.seed_sample_csv_data()

        # Seed Normalized Master Geo Tables if missing
        cls.seed_master_geo_tables()

    @classmethod
    def seed_master_geo_tables(cls):
        """Populate geo_states, geo_districts, geo_areas, and locations from crime_data if empty."""
        try:
            geo_count = cls.execute_query("SELECT COUNT(*) as cnt FROM geo_states", fetch_one=True)
            if geo_count and geo_count.get("cnt", 0) > 0:
                return

            print("[Seeding Geo Master] Populating normalized geographic master tables...")
            STATE_CODES = {
                "Delhi": "DL", "Gujarat": "GJ", "Karnataka": "KA", "Maharashtra": "MH",
                "Tamil Nadu": "TN", "Telangana": "TS", "Uttar Pradesh": "UP", "West Bengal": "WB"
            }
            HISTORICAL_DISTRICTS = {
                ("Uttar Pradesh", "Prayagraj"): "Allahabad",
                ("Uttar Pradesh", "Kanpur Nagar"): "Cawnpore",
                ("Uttar Pradesh", "Varanasi"): "Benares",
                ("Karnataka", "Bengaluru Urban"): "Bangalore Urban",
                ("Karnataka", "Mysuru"): "Mysore",
                ("Karnataka", "Belagavi"): "Belgaum",
                ("Karnataka", "Shivamogga"): "Shimoga",
                ("Karnataka", "Mangaluru"): "Mangalore",
                ("Maharashtra", "Mumbai Suburban"): "Bombay Suburban",
                ("Maharashtra", "Aurangabad"): "Chhatrapati Sambhajinagar",
                ("Tamil Nadu", "Chennai"): "Madras",
                ("West Bengal", "Kolkata"): "Calcutta",
                ("West Bengal", "Burdwan"): "Purba Bardhaman",
                ("Delhi", "Dwarka"): "South West Delhi (Dwarka Sub-City)",
                ("Delhi", "New Delhi"): "Central / New Delhi"
            }

            states = cls.execute_query("SELECT DISTINCT state FROM crime_data ORDER BY state ASC")
            for s in states:
                s_name = s['state']
                code = STATE_CODES.get(s_name, s_name[:2].upper())
                cls.execute_query("INSERT OR IGNORE INTO geo_states (state_name, state_code) VALUES (%s, %s)", (s_name, code), fetch_all=False)

            dists = cls.execute_query("""
                SELECT DISTINCT cd.state, cd.district, gs.id as state_id
                FROM crime_data cd
                JOIN geo_states gs ON cd.state = gs.state_name
                ORDER BY cd.state, cd.district
            """)
            for d in dists:
                s_id = d['state_id']
                s_name = d['state']
                d_name = d['district']
                hist = HISTORICAL_DISTRICTS.get((s_name, d_name), None)
                cls.execute_query(
                    "INSERT OR IGNORE INTO geo_districts (state_id, state_name, district_name, historical_name) VALUES (%s, %s, %s, %s)",
                    (s_id, s_name, d_name, hist), fetch_all=False
                )

            areas = cls.execute_query("""
                SELECT DISTINCT cd.state, cd.district, cd.area, gd.id as district_id
                FROM crime_data cd
                JOIN geo_districts gd ON cd.state = gd.state_name AND cd.district = gd.district_name
                ORDER BY cd.state, cd.district, cd.area
            """)
            for a in areas:
                d_id = a['district_id']
                s_name = a['state']
                d_name = a['district']
                a_name = a['area']
                cls.execute_query(
                    "INSERT OR IGNORE INTO geo_areas (district_id, state_name, district_name, area_name) VALUES (%s, %s, %s, %s)",
                    (d_id, s_name, d_name, a_name), fetch_all=False
                )
                cls.execute_query(
                    "INSERT OR IGNORE INTO locations (state, district, area) VALUES (%s, %s, %s)",
                    (s_name, d_name, a_name), fetch_all=False
                )
            print("[Seeding Geo Master Complete] Master geographic tables initialized.")
        except Exception as e:
            print(f"[Geo Master Init Warning] {e}")


    @classmethod
    def seed_sample_csv_data(cls):
        csv_path = Config.SAMPLE_CSV_PATH
        if not os.path.exists(csv_path):
            print(f"[CSV Warning] {csv_path} not found.")
            return

        import pandas as pd
        df = pd.read_csv(csv_path)
        
        insert_query = """
        INSERT INTO crime_data 
        (state, district, area, year, crime_type, cases_reported, chargesheeted, convictions, population, crime_rate_per_100k)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        records = []
        for _, row in df.iterrows():
            pop = int(row['Population'])
            cases = int(row['Cases_Reported'])
            rate = float(row['Crime_Rate_per_100k']) if 'Crime_Rate_per_100k' in row and pd.notna(row['Crime_Rate_per_100k']) else round((cases / pop) * 100000, 2)
            
            records.append((
                str(row['State']).strip(),
                str(row['District']).strip(),
                str(row['Area']).strip(),
                int(row['Year']),
                str(row['Crime_Type']).strip(),
                cases,
                int(row['Chargesheeted']),
                int(row['Convictions']),
                pop,
                rate
            ))
            
        cls.execute_batch(insert_query, records)
        print(f"[Seeding Complete] Successfully inserted {len(records)} crime records into database.")
