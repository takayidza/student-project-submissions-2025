CREATE DATABASE IF NOT EXISTS accident_detection;
USE accident_detection;

-- Users Table
CREATE TABLE Users (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accident_Prone_Areas Table
CREATE TABLE Accident_Prone_Areas (
    id CHAR(36) PRIMARY KEY,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    risk_level ENUM('Low', 'Medium', 'High') NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- History Table
CREATE TABLE History (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    area_id CHAR(36) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    speed DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES Accident_Prone_Areas(id) ON DELETE CASCADE
);

-- Alerts Table
CREATE TABLE Alerts (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    area_id CHAR(36) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES Accident_Prone_Areas(id) ON DELETE CASCADE
);

-- Settings Table
CREATE TABLE Settings (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    notification_enabled BOOLEAN DEFAULT TRUE,
    language VARCHAR(20) DEFAULT 'English',
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- Predictions Table
CREATE TABLE Predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    prediction_result ENUM('Safe', 'Accident Prone') NOT NULL,
    model_confidence FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
