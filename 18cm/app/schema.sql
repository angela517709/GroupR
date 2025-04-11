CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clinic_id INT NOT NULL,
    clinic_name VARCHAR(100) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    datetime DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'upcoming',
    doctor VARCHAR(100),
    room_number VARCHAR(20),
    notes TEXT,
    address VARCHAR(200),
    contact VARCHAR(50)
);

CREATE INDEX idx_clinic_datetime ON appointments(clinic_id, datetime);