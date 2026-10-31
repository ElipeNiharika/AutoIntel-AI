-- =======================================================================
-- AI Vehicle Service, Repair & Insurance Intelligence System
-- MySQL Enterprise Normalized Relational Database Schema
-- =======================================================================

CREATE DATABASE IF NOT EXISTS ai_vehicle_service;
USE ai_vehicle_service;

-- 1. Users Table (Authentication & Role-Based Access Control)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Vehicles Table (Vehicle Specs & Catalog References)
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(200) NOT NULL,
    vehicle_type VARCHAR(100) NOT NULL,
    fuel_type VARCHAR(50) DEFAULT 'Petrol',
    transmission VARCHAR(50) DEFAULT 'Automatic',
    manufacturing_year INT DEFAULT 2020,
    mileage INT DEFAULT 25000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Service Requests Table (Service Workorders & Operational Specs)
CREATE TABLE IF NOT EXISTS service_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    vehicle_id INT NULL,
    service_type VARCHAR(200) NOT NULL,
    service_description TEXT,
    parts_used TEXT,
    estimated_cost DECIMAL(12,2) DEFAULT 0.00,
    total_cost DECIMAL(12,2) DEFAULT 0.00,
    duration_hours FLOAT DEFAULT 0.0,
    technician_rating FLOAT DEFAULT 4.5,
    warranty_info VARCHAR(255) DEFAULT 'Standard Factory Warranty',
    insurance_claim_used TINYINT(1) DEFAULT 0,
    urgency_level VARCHAR(50) DEFAULT 'Normal',
    tow_distance FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'Completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Master Predictions Table (Unified Prediction Audit Log)
CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    service_id INT NULL,
    vehicle_info VARCHAR(255) NOT NULL,
    service_type VARCHAR(200) NOT NULL,
    predicted_cost DECIMAL(12,2) DEFAULT 0.00,
    predicted_time FLOAT DEFAULT 0.0,
    predicted_insurance_claim TINYINT(1) DEFAULT 0,
    insurance_probability FLOAT DEFAULT 0.0,
    diagnosis_category VARCHAR(100) DEFAULT 'General',
    severity VARCHAR(50) DEFAULT 'Normal',
    recommended_action TEXT,
    parts_recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (service_id) REFERENCES service_requests(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Dedicated Insurance Predictions & Fraud Table
CREATE TABLE IF NOT EXISTS insurance_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_id INT NULL,
    user_id INT NULL,
    policy_type VARCHAR(100) DEFAULT 'Sedan - All Perils',
    deductible DECIMAL(10,2) DEFAULT 500.00,
    driver_rating INT DEFAULT 3,
    claim_covered_pred TINYINT(1) DEFAULT 0,
    claim_covered_prob FLOAT DEFAULT 0.0,
    fraud_detected_pred TINYINT(1) DEFAULT 0,
    fraud_risk_prob FLOAT DEFAULT 0.0,
    risk_level VARCHAR(50) DEFAULT 'Low',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Dedicated Diagnosis Results Table
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_id INT NULL,
    user_id INT NULL,
    symptom_text TEXT,
    ecu_code VARCHAR(50),
    classified_category VARCHAR(100) NOT NULL,
    severity VARCHAR(50) DEFAULT 'Normal',
    confidence_score FLOAT DEFAULT 0.90,
    root_cause TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Dedicated Parts Recommendations Table
CREATE TABLE IF NOT EXISTS parts_recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    diagnosis_id INT NULL,
    prediction_id INT NULL,
    action_type ENUM('REPLACE', 'REPAIR', 'INSPECT') DEFAULT 'REPLACE',
    part_name VARCHAR(255) NOT NULL,
    estimated_part_cost DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (diagnosis_id) REFERENCES diagnosis_results(id) ON DELETE CASCADE,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed Default Admin & Demo Technician Users
INSERT IGNORE INTO users (id, name, email, password_hash, role) VALUES 
(1, 'Lead Fleet Admin', 'admin@autointel.ai', 'pbkdf2:sha256:600000$demo$c4ca4238a0b923820dcc509a6f75849b', 'admin'),
(2, 'Service Technician', 'technician@autointel.ai', 'pbkdf2:sha256:600000$demo$c4ca4238a0b923820dcc509a6f75849b', 'user');
