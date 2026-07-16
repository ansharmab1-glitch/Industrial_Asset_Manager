import mysql.connector
import random
import os
from dotenv import load_dotenv
from database import get_db_connection

# Load environment variables for secure access
load_dotenv()

def seed_enterprise_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Wipe existing tables for a clean slate
    tables_to_drop = ["tickets", "motors", "transformers", "pumps", "generators", "fans", "boilers", "compressors", "machinery", "assets", "plants", "users"]
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
    # 2. Build Security and Role-Based Tables
    cursor.execute('''
    CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL
    )''')
    
    # Securely fetch application credentials from the .env file
    m_user = os.getenv("MANAGER_USER")
    m_pass = os.getenv("MANAGER_PASS")
    e_user = os.getenv("ENGINEER_USER")
    e_pass = os.getenv("ENGINEER_PASS")

    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (m_user, m_pass, 'Manager'))
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (e_user, e_pass, 'Engineer'))

    # 3. Build Core Plant and Asset Architecture
    cursor.execute('''
    CREATE TABLE plants (
        plant_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        fire_status VARCHAR(50) DEFAULT 'Normal',
        gas_leakage_status VARCHAR(50) DEFAULT 'Normal'
    )''')

    cursor.execute('''
    CREATE TABLE assets (
        asset_id INT AUTO_INCREMENT PRIMARY KEY,
        plant_id INT,
        name VARCHAR(255) NOT NULL,
        asset_type VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
    )''')

    cursor.execute('''
    CREATE TABLE tickets (
        ticket_id INT AUTO_INCREMENT PRIMARY KEY,
        asset_id INT,
        issue_description TEXT NOT NULL,
        urgency_level INT NOT NULL,
        status VARCHAR(50) DEFAULT 'Open',
        date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
    )''')

    # 4. Insert 10 Industrial Plants
    plants_data = [
        ("CPP",), ("CCPP",), ("PTA",), ("Cracker",), ("Central Workshop",),
        ("Substation Alpha",), ("Substation Beta",), ("Cooling Tower Unit",), 
        ("Water Treatment Plant",), ("Packaging Unit",)
    ]
    cursor.executemany("INSERT INTO plants (name) VALUES (%s)", plants_data)

    # 5. Generate 5,000 Unevenly Distributed, Non-Consecutive Assets
    plant_weights = {
        1: 1200, 2: 950, 3: 850, 4: 1100, 5: 150, 
        6: 100, 7: 100, 8: 250, 9: 200, 10: 100
    }
    
    asset_types = ["Motor", "Transformer", "Pump", "Generator", "Fan", "Boiler", "Compressor", "Machinery"]
    mock_assets = []

    for p_id, count in plant_weights.items():
        # Dynamically sample a unique, scrambled pool of identification numbers from a wide range
        id_pool = random.sample(range(1000, 99999), count)
        for unit_num in id_pool:
            a_type = random.choice(asset_types)
            name = f"{a_type} Unit-{unit_num}"
            mock_assets.append((p_id, name, a_type, "Operational"))

    # Completely scramble the arrival order across your infrastructure
    random.shuffle(mock_assets)
    cursor.executemany("INSERT INTO assets (plant_id, name, asset_type, status) VALUES (%s, %s, %s, %s)", mock_assets)

    conn.commit()
    cursor.close()
    conn.close()
    print("TiDB Cloud Database successfully seeded with 5,000 randomized assets!")

if __name__ == "__main__":
    seed_enterprise_database()