-- MySQL Database Schema for Crime Data Analytics and Visualization
-- Conforming to Official Local Government Directory (LGD) Standards (lgdirectory.gov.in)
-- Database Name: crime_analytics

CREATE DATABASE IF NOT EXISTS crime_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crime_analytics;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    is_active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    user_name VARCHAR(100) NULL,
    user_email VARCHAR(120) NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_act_user (user_id),
    INDEX idx_act_action (action),
    INDEX idx_act_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Login Security / Rate Limit Table
CREATE TABLE IF NOT EXISTS login_security (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    failed_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sec_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Normalized Geographic States Table (Exactly 28 Official States)
CREATE TABLE IF NOT EXISTS geo_states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_name VARCHAR(100) NOT NULL UNIQUE,
    state_code VARCHAR(10) NOT NULL UNIQUE,
    lgd_state_code INT NOT NULL UNIQUE,
    is_active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Normalized Geographic Districts Table
CREATE TABLE IF NOT EXISTS geo_districts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_id INT NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    lgd_district_code INT NULL,
    historical_name VARCHAR(100) NULL,
    is_active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_state_dist (state_id, district_name),
    FOREIGN KEY (state_id) REFERENCES geo_states(id) ON DELETE CASCADE,
    INDEX idx_geo_dist_state (state_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Normalized Geographic Sub-Districts Table (Tehsils / Taluks)
CREATE TABLE IF NOT EXISTS geo_areas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    district_id INT NOT NULL,
    state_id INT NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    area_name VARCHAR(100) NOT NULL,
    lgd_sub_district_code INT NULL,
    area_type VARCHAR(100) DEFAULT 'Sub-District / Taluk / Administrative Area',
    is_active TINYINT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_state_dist_area (district_id, area_name),
    FOREIGN KEY (district_id) REFERENCES geo_districts(id) ON DELETE CASCADE,
    FOREIGN KEY (state_id) REFERENCES geo_states(id) ON DELETE CASCADE,
    INDEX idx_geo_area_dist (district_id),
    INDEX idx_geo_area_state (state_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Master Locations Lookup Table
CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    area VARCHAR(100) NOT NULL,
    state_code VARCHAR(10) NULL,
    lgd_state_code INT NULL,
    lgd_district_code INT NULL,
    lgd_sub_district_code INT NULL,
    area_type VARCHAR(100) DEFAULT 'Sub-District / Taluk / Administrative Area',
    is_active TINYINT DEFAULT 1,
    UNIQUE KEY uq_locations (state, district, area),
    INDEX idx_loc_sd (state, district),
    INDEX idx_loc_state (state),
    INDEX idx_loc_dist (district),
    INDEX idx_loc_area (area)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Crime Incident Data Table
CREATE TABLE IF NOT EXISTS crime_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    area VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    crime_type VARCHAR(100) NOT NULL,
    cases_reported INT NOT NULL DEFAULT 0,
    chargesheeted INT NOT NULL DEFAULT 0,
    convictions INT NOT NULL DEFAULT 0,
    population INT NOT NULL DEFAULT 100000,
    crime_rate_per_100k DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_state (state),
    INDEX idx_district (district),
    INDEX idx_area (area),
    INDEX idx_year (year),
    INDEX idx_crime_type (crime_type),
    INDEX idx_crime_state_dist_area (state, district, area)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
