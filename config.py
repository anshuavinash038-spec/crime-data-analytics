import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "crime_analytics_secret_key_prod_2026_secure")
    
    # Cloud Database URL support (Render, Railway, Heroku, Supabase, PlanetScale)
    DB_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    
    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()  # 'sqlite' (zero-config) or 'mysql'
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "crime_analytics")
    
    # SQLite Path — default to database/crime_analytics.db, or allow SQLITE_PATH override
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    _default_sqlite_path = os.path.join(BASE_DIR, "database", "crime_analytics.db")
    SQLITE_PATH = os.getenv("SQLITE_PATH", _default_sqlite_path)

    # Auto-parse cloud DATABASE_URL if provided
    if DB_URL:
        try:
            parsed = urllib.parse.urlparse(DB_URL)
            if parsed.scheme.startswith("mysql"):
                DB_TYPE = "mysql"
                DB_HOST = parsed.hostname or "localhost"
                DB_PORT = parsed.port or 3306
                DB_USER = parsed.username or "root"
                DB_PASSWORD = urllib.parse.unquote(parsed.password or "")
                DB_NAME = (parsed.path or "/crime_analytics").lstrip("/")
            elif parsed.scheme.startswith("sqlite"):
                DB_TYPE = "sqlite"
                if parsed.path and parsed.path != "/":
                    SQLITE_PATH = os.path.abspath(parsed.path.lstrip("/"))
        except Exception as e:
            print(f"[Config Notice] DB_URL parse notice: {e}")
    
    # Power BI Configuration
    POWERBI_EMBED_URL = os.getenv("POWERBI_EMBED_URL", "")
    
    # Uploads & Reports directory
    REPORTS_DIR = os.path.join(BASE_DIR, "data", "reports")
    SAMPLE_CSV_PATH = os.path.join(BASE_DIR, "data", "sample_crime_data.csv")

    # Production Session & Security Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max payload

    @classmethod
    def init_app(cls, app):
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
        os.makedirs(os.path.join(cls.BASE_DIR, "database"), exist_ok=True)
        os.makedirs(os.path.join(cls.BASE_DIR, "data"), exist_ok=True)
