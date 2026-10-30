import os
import sqlite3
import logging
from werkzeug.security import generate_password_hash
from config import Config

# Configure proper logging instead of silent failures
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


# ==============================================================================
# EMBEDDED SQLITE SCHEMA  (no file dependency — works on Render/Railway/Heroku)
# ==============================================================================
_SQLITE_SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'USER',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        user_email TEXT,
        action TEXT NOT NULL,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS login_security (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        failed_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP NULL,
        last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    # geo_states WITHOUT lgd_state_code NOT NULL (was causing insert failures)
    """CREATE TABLE IF NOT EXISTS geo_states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_name TEXT NOT NULL UNIQUE,
        state_code TEXT NOT NULL UNIQUE,
        lgd_state_code INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS geo_districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_id INTEGER NOT NULL,
        state_name TEXT NOT NULL,
        district_name TEXT NOT NULL,
        lgd_district_code INTEGER,
        historical_name TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(state_id, district_name),
        FOREIGN KEY(state_id) REFERENCES geo_states(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS geo_areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        district_id INTEGER NOT NULL,
        state_id INTEGER,
        state_name TEXT NOT NULL,
        district_name TEXT NOT NULL,
        area_name TEXT NOT NULL,
        lgd_sub_district_code INTEGER,
        area_type TEXT DEFAULT 'Sub-District / Taluk / Administrative Area',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(district_id, area_name),
        FOREIGN KEY(district_id) REFERENCES geo_districts(id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        area TEXT NOT NULL,
        state_code TEXT,
        lgd_state_code INTEGER,
        lgd_district_code INTEGER,
        lgd_sub_district_code INTEGER,
        area_type TEXT DEFAULT 'Sub-District / Taluk / Administrative Area',
        is_active INTEGER DEFAULT 1,
        UNIQUE(state, district, area)
    )""",
    """CREATE TABLE IF NOT EXISTS crime_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT NOT NULL,
        district TEXT NOT NULL,
        area TEXT NOT NULL,
        year INTEGER NOT NULL,
        crime_type TEXT NOT NULL,
        cases_reported INTEGER NOT NULL DEFAULT 0,
        chargesheeted INTEGER NOT NULL DEFAULT 0,
        convictions INTEGER NOT NULL DEFAULT 0,
        population INTEGER NOT NULL DEFAULT 100000,
        crime_rate_per_100k REAL NOT NULL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_state ON crime_data(state)",
    "CREATE INDEX IF NOT EXISTS idx_district ON crime_data(district)",
    "CREATE INDEX IF NOT EXISTS idx_area ON crime_data(area)",
    "CREATE INDEX IF NOT EXISTS idx_year ON crime_data(year)",
    "CREATE INDEX IF NOT EXISTS idx_crime_type ON crime_data(crime_type)",
    "CREATE INDEX IF NOT EXISTS idx_crime_state_dist_area ON crime_data(state, district, area)",
    "CREATE INDEX IF NOT EXISTS idx_geo_dist_state ON geo_districts(state_id)",
    "CREATE INDEX IF NOT EXISTS idx_geo_area_dist ON geo_areas(district_id)",
    "CREATE INDEX IF NOT EXISTS idx_locations_lookup ON locations(state, district, area)",
]

# ==============================================================================
# MINIMAL FALLBACK CRIME SEED DATA
# Used ONLY when CSV file is missing (Render fresh deploy)
# 10 states × 3 districts × 2 areas × 5 crime types × 5 years = 1500 records
# ==============================================================================
def _build_fallback_seed_records():
    import random
    random.seed(42)  # Reproducible seed

    STATES = [
        ("Maharashtra", "MH"), ("Uttar Pradesh", "UP"), ("Delhi", "DL"),
        ("Karnataka", "KA"), ("Tamil Nadu", "TN"), ("West Bengal", "WB"),
        ("Rajasthan", "RJ"), ("Gujarat", "GJ"), ("Madhya Pradesh", "MP"),
        ("Telangana", "TS"),
    ]
    DISTRICTS = {
        "Maharashtra":   [("Mumbai",        "Andheri", "Bandra"),
                          ("Pune",           "Shivajinagar", "Hadapsar"),
                          ("Nagpur",         "Sitabuldi", "Dharampeth")],
        "Uttar Pradesh": [("Lucknow",        "Hazratganj", "Aliganj"),
                          ("Kanpur Nagar",   "Civil Lines", "Govind Nagar"),
                          ("Prayagraj",      "Civil Lines", "Naini")],
        "Delhi":         [("New Delhi",      "Connaught Place", "Karol Bagh"),
                          ("South Delhi",    "Hauz Khas", "Greater Kailash"),
                          ("North Delhi",    "Rohini", "Pitampura")],
        "Karnataka":     [("Bengaluru Urban","Koramangala", "Whitefield"),
                          ("Mysuru",         "Nazarbad", "Hebbal"),
                          ("Belagavi",       "Camp Area", "Tilakwadi")],
        "Tamil Nadu":    [("Chennai",        "Egmore", "Anna Nagar"),
                          ("Coimbatore",     "RS Puram", "Saibaba Colony"),
                          ("Madurai",        "Goripalayam", "KK Nagar")],
        "West Bengal":   [("Kolkata",        "Park Street", "Howrah"),
                          ("Burdwan",        "Asansol", "Durgapur"),
                          ("North 24 Parganas", "Barasat", "Kalyani")],
        "Rajasthan":     [("Jaipur",         "Malviya Nagar", "Mansarovar"),
                          ("Jodhpur",        "Ratanada", "Shastri Nagar"),
                          ("Udaipur",        "Hiran Magri", "Pratap Nagar")],
        "Gujarat":       [("Ahmedabad",      "Navrangpura", "Maninagar"),
                          ("Surat",          "Varachha", "Katargam"),
                          ("Vadodara",       "Sayajigunj", "Fatehgunj")],
        "Madhya Pradesh":[("Bhopal",         "MP Nagar", "Arera Colony"),
                          ("Indore",         "Vijay Nagar", "Rau"),
                          ("Gwalior",        "Lashkar", "Morar")],
        "Telangana":     [("Hyderabad",      "Banjara Hills", "Jubilee Hills"),
                          ("Warangal",       "Hanamkonda", "Kazipet"),
                          ("Rangareddy",     "LB Nagar", "Vanasthalipuram")],
    }
    CRIME_TYPES = ["Theft", "Assault", "Robbery", "Fraud", "Cybercrime"]
    YEARS = [2021, 2022, 2023, 2024, 2025]
    POP_BASE = {
        "Maharashtra": 1200000, "Uttar Pradesh": 900000, "Delhi": 1500000,
        "Karnataka": 800000, "Tamil Nadu": 750000, "West Bengal": 700000,
        "Rajasthan": 600000, "Gujarat": 850000, "Madhya Pradesh": 650000,
        "Telangana": 900000,
    }

    records = []
    for state, _ in STATES:
        pop = POP_BASE.get(state, 700000)
        for district, area1, area2 in DISTRICTS[state]:
            for area in [area1, area2]:
                for crime_type in CRIME_TYPES:
                    for year in YEARS:
                        cases = random.randint(50, 2500)
                        chargesheeted = int(cases * random.uniform(0.55, 0.90))
                        convictions = int(chargesheeted * random.uniform(0.40, 0.75))
                        rate = round((cases / max(pop, 1)) * 100000, 2)
                        records.append((
                            state, district, area, year, crime_type,
                            cases, chargesheeted, convictions, pop, rate
                        ))
    return records


class DatabaseService:
    _mysql_pool = None
    _active_db_type = None

    @classmethod
    def get_db_type(cls):
        if cls._active_db_type:
            return cls._active_db_type

        if Config.DB_TYPE == "mysql" and HAS_MYSQL:
            try:
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
                logger.warning(f"[DB Notice] MySQL connection failed ({e}). Falling back to SQLite.")
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
                logger.warning(f"[DB Warning] MySQL connect error: {e}. Switching to SQLite.")
                cls._active_db_type = "sqlite"
                return cls.get_sqlite_connection()
        else:
            return cls.get_sqlite_connection()

    @classmethod
    def get_sqlite_connection(cls):
        db_dir = os.path.dirname(Config.SQLITE_PATH)
        os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(Config.SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @classmethod
    def _normalize_query(cls, query, db_type):
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
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch_one:
                row = cursor.fetchone()
                if row and db_type == "mysql":
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                elif row:
                    return dict(row)
                return None
            elif fetch_all:
                rows = cursor.fetchall()
                if db_type == "mysql":
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return [dict(row) for row in rows]
            else:
                if db_type == "sqlite":
                    conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"[DB Query Error] {e} | Query: {query[:120]}")
            raise
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
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"[DB Insert Error] {e} | Query: {query[:120]}")
            raise
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
        except Exception as e:
            logger.error(f"[DB Batch Error] {e} | Query: {query[:120]}")
            raise
        finally:
            conn.close()

    # ==========================================================================
    # CORE INIT — self-contained, no external file dependencies
    # ==========================================================================
    @classmethod
    def init_db(cls):
        db_type = cls.get_db_type()
        logger.info(f"[Database Initialization] Using database engine: {db_type.upper()}")

        if db_type == "mysql":
            try:
                conn = mysql.connector.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD
                )
                cursor = conn.cursor()
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
                conn.close()
            except Exception as e:
                logger.error(f"[MySQL Init Error] {e}")

        # ------------------------------------------------------------------
        # 1. Create all tables using embedded schema (no file dependency)
        # ------------------------------------------------------------------
        cls._apply_embedded_schema()

        # ------------------------------------------------------------------
        # 2. Migration: add is_active column if missing (for old DBs)
        # ------------------------------------------------------------------
        try:
            if db_type == "sqlite":
                cols = [c.get("name") for c in (cls.execute_query("PRAGMA table_info(users)") or [])]
                if cols and "is_active" not in cols:
                    cls.execute_query("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1", fetch_all=False)
            elif db_type == "mysql":
                try:
                    cls.execute_query("ALTER TABLE users ADD COLUMN is_active INT DEFAULT 1", fetch_all=False)
                except Exception:
                    pass
        except Exception:
            pass

        # ------------------------------------------------------------------
        # 3. Seed default users if table is empty
        # ------------------------------------------------------------------
        cls._seed_users()

        # ------------------------------------------------------------------
        # 4. Seed crime_data — try CSV first, fallback to built-in data
        # ------------------------------------------------------------------
        cls._seed_crime_data()

        # ------------------------------------------------------------------
        # 5. Seed geographic master tables from crime_data
        # ------------------------------------------------------------------
        cls.seed_master_geo_tables()

        logger.info("[Database Initialization] Complete. All tables ready.")

    @classmethod
    def _apply_embedded_schema(cls):
        """Run embedded CREATE TABLE IF NOT EXISTS statements. No file I/O needed."""
        db_type = cls.get_db_type()
        conn = cls.get_connection()
        try:
            cursor = conn.cursor()
            for stmt in _SQLITE_SCHEMA_STATEMENTS:
                normalized = cls._normalize_query(stmt, db_type)
                try:
                    cursor.execute(normalized)
                except Exception as e:
                    logger.warning(f"[Schema Stmt Warning] {e} | stmt={normalized[:80]}")
            if db_type == "sqlite":
                conn.commit()
            logger.info("[Schema] All tables created / verified successfully.")
        except Exception as e:
            logger.error(f"[Schema Apply Error] {e}")
        finally:
            conn.close()

        # Also try to run the SQL file for any extra constraints (optional, best-effort)
        schema_file = "schema.sql" if cls.get_db_type() == "mysql" else "schema_sqlite.sql"
        schema_path = os.path.join(Config.BASE_DIR, "database", schema_file)
        if os.path.exists(schema_path):
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn2 = cls.get_connection()
                cursor2 = conn2.cursor()
                for statement in schema_sql.split(";"):
                    stmt = statement.strip()
                    if stmt and not stmt.startswith("--"):
                        try:
                            cursor2.execute(cls._normalize_query(stmt, cls.get_db_type()))
                        except Exception:
                            pass  # IF NOT EXISTS handles most; ignore rest
                if cls.get_db_type() == "sqlite":
                    conn2.commit()
                conn2.close()
            except Exception as e:
                logger.warning(f"[Schema File Warning] {e}")

    @classmethod
    def _seed_users(cls):
        """Create default admin/user accounts if users table is empty."""
        try:
            result = cls.execute_query("SELECT COUNT(*) as cnt FROM users", fetch_one=True)
            count = result.get("cnt", 0) if result else 0
        except Exception as e:
            logger.error(f"[Seed Users] Could not read users table: {e}")
            return

        if count == 0:
            logger.info("[Seeding Users] Creating default admin and user credentials...")
            try:
                admin_pwd = generate_password_hash("Admin#Safe2026")
                user_pwd = generate_password_hash("User#Safe2026")
                cls.execute_insert(
                    "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s)",
                    ("System Administrator", "admin@gmail.com", admin_pwd, "ADMIN", 1)
                )
                cls.execute_insert(
                    "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s)",
                    ("Standard User", "user@gmail.com", user_pwd, "USER", 1)
                )
                logger.info("[Seeding Users] Default accounts created.")
            except Exception as e:
                logger.error(f"[Seed Users Error] {e}")

        # Seed primary admin from environment variables (Render env vars)
        primary_admin_email = os.getenv("ADMIN_EMAIL", "").strip()
        primary_admin_name = os.getenv("ADMIN_NAME", "System Admin").strip()
        primary_admin_pwd = os.getenv("ADMIN_PASSWORD", "").strip()
        if primary_admin_email and primary_admin_pwd:
            try:
                existing = cls.execute_query(
                    "SELECT id FROM users WHERE email = %s",
                    (primary_admin_email,), fetch_one=True
                )
                if not existing:
                    hashed = generate_password_hash(primary_admin_pwd)
                    cls.execute_insert(
                        "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s)",
                        (primary_admin_name, primary_admin_email, hashed, "ADMIN", 1)
                    )
                    logger.info(f"[Seeding Users] Env-configured admin '{primary_admin_email}' created.")
            except Exception as e:
                logger.error(f"[Seed Admin Error] {e}")

    @classmethod
    def _seed_crime_data(cls):
        """Seed crime_data — try CSV file first, then use built-in fallback data."""
        try:
            result = cls.execute_query("SELECT COUNT(*) as cnt FROM crime_data", fetch_one=True)
            count = result.get("cnt", 0) if result else 0
        except Exception as e:
            logger.error(f"[Seed Crime] Could not read crime_data table: {e}")
            return

        if count >= 1000:
            logger.info(f"[Seed Crime] {count} records already exist. Skipping seed.")
            return

        logger.info("[Seeding Crime Data] Attempting to load from CSV...")

        # Try CSV first
        csv_loaded = False
        csv_path = Config.SAMPLE_CSV_PATH
        if os.path.exists(csv_path):
            try:
                csv_loaded = cls._load_crime_csv(csv_path)
            except Exception as e:
                logger.warning(f"[CSV Load Warning] {e}")

        # Fallback: built-in seed data (works on Render with no CSV)
        if not csv_loaded:
            logger.info("[Seeding Crime Data] CSV not found or empty. Using built-in fallback seed data...")
            try:
                if count > 0:
                    cls.execute_query("DELETE FROM crime_data", fetch_all=False)
                records = _build_fallback_seed_records()
                insert_query = """
                    INSERT INTO crime_data
                    (state, district, area, year, crime_type, cases_reported,
                     chargesheeted, convictions, population, crime_rate_per_100k)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cls.execute_batch(insert_query, records)
                logger.info(f"[Seeding Crime Data] Inserted {len(records)} fallback records.")
            except Exception as e:
                logger.error(f"[Seed Crime Fallback Error] {e}")

    @classmethod
    def _load_crime_csv(cls, csv_path):
        """Load crime data from CSV. Returns True on success."""
        try:
            import pandas as pd
        except ImportError:
            logger.warning("[CSV Load] pandas not available.")
            return False

        df = pd.read_csv(csv_path)
        df.columns = [str(c).strip().lower() for c in df.columns]

        if df.empty:
            return False

        insert_query = """
            INSERT INTO crime_data
            (state, district, area, year, crime_type, cases_reported,
             chargesheeted, convictions, population, crime_rate_per_100k)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        records = []
        for _, row in df.iterrows():
            pop = int(row.get('population', 100000))
            cases = int(row.get('cases_reported', 0))
            chargesheeted = int(row.get('chargesheeted', 0))
            convictions = int(row.get('convictions', 0))
            if 'crime_rate_per_100k' in row and pd.notna(row['crime_rate_per_100k']):
                rate = float(row['crime_rate_per_100k'])
            else:
                rate = round((cases / max(pop, 1)) * 100000, 2)
            records.append((
                str(row.get('state', '')).strip(),
                str(row.get('district', '')).strip(),
                str(row.get('area', '')).strip(),
                int(row.get('year', 2024)),
                str(row.get('crime_type', 'Theft')).strip(),
                cases, chargesheeted, convictions, pop, rate
            ))

        if not records:
            return False

        cls.execute_batch(insert_query, records)
        logger.info(f"[CSV Load] Inserted {len(records)} records from CSV.")
        return True

    # Kept for backward compat (called externally in some places)
    @classmethod
    def seed_sample_csv_data(cls):
        csv_path = Config.SAMPLE_CSV_PATH
        if not os.path.exists(csv_path):
            logger.warning(f"[CSV Warning] {csv_path} not found.")
            return
        cls._load_crime_csv(csv_path)

    @classmethod
    def seed_master_geo_tables(cls):
        """Populate geo_states, geo_districts, geo_areas, locations from crime_data."""
        try:
            geo_count = cls.execute_query("SELECT COUNT(*) as cnt FROM geo_states", fetch_one=True)
            if geo_count and geo_count.get("cnt", 0) > 0:
                return  # Already populated

            logger.info("[Seeding Geo Master] Populating normalized geographic master tables...")

            STATE_CODES = {
                "Andhra Pradesh": "AP", "Arunachal Pradesh": "AR", "Assam": "AS",
                "Bihar": "BR", "Chhattisgarh": "CG", "Delhi": "DL", "Goa": "GA",
                "Gujarat": "GJ", "Haryana": "HR", "Himachal Pradesh": "HP",
                "Jharkhand": "JH", "Karnataka": "KA", "Kerala": "KL",
                "Madhya Pradesh": "MP", "Maharashtra": "MH", "Manipur": "MN",
                "Meghalaya": "ML", "Mizoram": "MZ", "Nagaland": "NL",
                "Odisha": "OD", "Punjab": "PB", "Rajasthan": "RJ",
                "Sikkim": "SK", "Tamil Nadu": "TN", "Telangana": "TS",
                "Tripura": "TR", "Uttar Pradesh": "UP", "Uttarakhand": "UK",
                "West Bengal": "WB",
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
                ("Delhi", "New Delhi"): "Central / New Delhi",
            }

            # Insert states
            states = cls.execute_query("SELECT DISTINCT state FROM crime_data ORDER BY state ASC")
            for s in states:
                s_name = s['state']
                code = STATE_CODES.get(s_name, s_name[:2].upper())
                try:
                    cls.execute_query(
                        "INSERT OR IGNORE INTO geo_states (state_name, state_code) VALUES (%s, %s)",
                        (s_name, code), fetch_all=False
                    )
                except Exception as e:
                    logger.warning(f"[Geo State Insert] {s_name}: {e}")

            # Insert districts
            dists = cls.execute_query("""
                SELECT DISTINCT cd.state, cd.district, gs.id as state_id
                FROM crime_data cd
                JOIN geo_states gs ON cd.state = gs.state_name
                ORDER BY cd.state, cd.district
            """)
            for d in dists:
                hist = HISTORICAL_DISTRICTS.get((d['state'], d['district']), None)
                try:
                    cls.execute_query(
                        "INSERT OR IGNORE INTO geo_districts (state_id, state_name, district_name, historical_name) VALUES (%s, %s, %s, %s)",
                        (d['state_id'], d['state'], d['district'], hist), fetch_all=False
                    )
                except Exception as e:
                    logger.warning(f"[Geo District Insert] {d['district']}: {e}")

            # Insert areas
            areas = cls.execute_query("""
                SELECT DISTINCT cd.state, cd.district, cd.area, gd.id as district_id
                FROM crime_data cd
                JOIN geo_districts gd ON cd.state = gd.state_name AND cd.district = gd.district_name
                ORDER BY cd.state, cd.district, cd.area
            """)
            for a in areas:
                try:
                    cls.execute_query(
                        "INSERT OR IGNORE INTO geo_areas (district_id, state_name, district_name, area_name) VALUES (%s, %s, %s, %s)",
                        (a['district_id'], a['state'], a['district'], a['area']), fetch_all=False
                    )
                except Exception as e:
                    logger.warning(f"[Geo Area Insert] {a['area']}: {e}")
                try:
                    cls.execute_query(
                        "INSERT OR IGNORE INTO locations (state, district, area) VALUES (%s, %s, %s)",
                        (a['state'], a['district'], a['area']), fetch_all=False
                    )
                except Exception as e:
                    logger.warning(f"[Location Insert] {a['area']}: {e}")

            logger.info("[Seeding Geo Master] Complete.")
        except Exception as e:
            logger.error(f"[Geo Master Init Error] {e}")
