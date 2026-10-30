-- SQLite Schema for Crime Data Analytics and Visualization
-- Conforming to Official Local Government Directory (LGD) Standards (lgdirectory.gov.in)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT,
    user_email TEXT,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_security (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Master Geography: Indian States (with optional LGD State Code)
CREATE TABLE IF NOT EXISTS geo_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_name TEXT NOT NULL UNIQUE,
    state_code TEXT NOT NULL UNIQUE,
    lgd_state_code INTEGER,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Master Geography: Official Districts mapped to parent State (with LGD District Code)
CREATE TABLE IF NOT EXISTS geo_districts (
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
);

-- Master Geography: Official Sub-Districts / Tehsils / Taluks
CREATE TABLE IF NOT EXISTS geo_areas (
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
);

-- Synchronized Fast Lookup Table
CREATE TABLE IF NOT EXISTS locations (
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
);

-- Crime Incident / Transaction Data
CREATE TABLE IF NOT EXISTS crime_data (
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
);

CREATE INDEX IF NOT EXISTS idx_state ON crime_data(state);
CREATE INDEX IF NOT EXISTS idx_district ON crime_data(district);
CREATE INDEX IF NOT EXISTS idx_area ON crime_data(area);
CREATE INDEX IF NOT EXISTS idx_year ON crime_data(year);
CREATE INDEX IF NOT EXISTS idx_crime_type ON crime_data(crime_type);
CREATE INDEX IF NOT EXISTS idx_crime_state_dist_area ON crime_data(state, district, area);
CREATE INDEX IF NOT EXISTS idx_geo_dist_state ON geo_districts(state_id);
CREATE INDEX IF NOT EXISTS idx_geo_area_dist ON geo_areas(district_id);
CREATE INDEX IF NOT EXISTS idx_geo_area_state ON geo_areas(state_id);
CREATE INDEX IF NOT EXISTS idx_locations_lookup ON locations(state, district, area);
