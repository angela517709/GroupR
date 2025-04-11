import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="6267",
        database="iamsmart_db"
    )
    return connection

def init_db():
    # Connect without database first to create it
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="6267"
    )
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS iamsmart_db")
    conn.close()
    
    # Connect to the database and create tables
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create clinics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(200) NOT NULL,
            quota INT DEFAULT 0,
            location VARCHAR(50) NOT NULL
        )
    """)
    
    # Insert sample data
    sample_clinics = [
        ('Central Clinic', 'Central', 5, 'hong_kong'),
        ('Wan Chai Medical', 'Wan Chai', 0, 'hong_kong'),
        ('TST Medical Center', 'TST', 3, 'kowloon'),
        ('MK Clinic', 'Mong Kok', 2, 'kowloon'),
        ('Sha Tin Clinic', 'Sha Tin', 4, 'new_territories'),
        ('Tsuen Wan Medical', 'Tsuen Wan', 1, 'new_territories')
    ]
    
    cursor.execute("TRUNCATE TABLE clinics")
    cursor.executemany("""
        INSERT INTO clinics (name, address, quota, location) 
        VALUES (%s, %s, %s, %s)
    """, sample_clinics)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()