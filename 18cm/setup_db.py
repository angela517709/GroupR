import mysql.connector

def setup_database():
    # Create initial connection without database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="6267"
    )
    cursor = conn.cursor()
    
    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS iamsmart_db")
    cursor.close()
    conn.close()
    
    # Connect to the new database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="6267",
        database="iamsmart_db"
    )
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(200) NOT NULL,
            quota INT DEFAULT 0,
            location VARCHAR(50) NOT NULL
        )
    """)
    
    # Add sample data
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
    cursor.close()
    conn.close()

if __name__ == '__main__':
    setup_database()
    print("Database setup completed successfully!")