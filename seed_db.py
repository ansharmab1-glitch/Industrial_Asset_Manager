import mysql.connector
import random
import os
import certifi
from dotenv import load_dotenv

# Load environment variables for secure access
load_dotenv()

def seed_enterprise_database():
    print("Connecting to TiDB Cloud...")
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 4000),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="industrial_asset_tracker",
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        ssl_ca=certifi.where(),
        # --- NEW: Aggressive Cloud Timeouts ---
        connection_timeout=10,
        read_timeout=10,
        write_timeout=10
    )
    cursor = conn.cursor()

    print("Dropping old tables...")
    tables_to_drop = ["tickets", "motors", "transformers", "pumps", "generators", "fans", "boilers", "compressors", "machinery", "assets", "plants", "users"]
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
    print("Building Security & Plant Architecture...")
    # 1. Build Security Table
    cursor.execute('''CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL
    )''')
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (os.getenv("MANAGER_USER"), os.getenv("MANAGER_PASS"), 'Manager'))
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (os.getenv("ENGINEER_USER"), os.getenv("ENGINEER_PASS"), 'Engineer'))

    # 2. Build Core Plant and Asset Tables
    cursor.execute('''CREATE TABLE plants (
        plant_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        fire_status VARCHAR(50) DEFAULT 'Normal',
        gas_leakage_status VARCHAR(50) DEFAULT 'Normal'
    )''')

    cursor.execute('''CREATE TABLE assets (
        asset_id INT AUTO_INCREMENT PRIMARY KEY,
        plant_id INT,
        name VARCHAR(255) NOT NULL,
        asset_type VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE
    )''')

    cursor.execute('''CREATE TABLE tickets (
        ticket_id INT AUTO_INCREMENT PRIMARY KEY,
        asset_id INT,
        issue_description TEXT NOT NULL,
        urgency_level INT NOT NULL,
        status VARCHAR(50) DEFAULT 'Open',
        date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
    )''')

    print("Building Table-per-Type (TPT) Sub-tables...")
    # 3. Build Specialized Engineering Sub-Tables
    cursor.execute('''CREATE TABLE motors (asset_id INT PRIMARY KEY, v_input INT, output_power_kw FLOAT, power_factor FLOAT, phases INT, rpm INT, frequency INT, insulation_class VARCHAR(50), fire_protection VARCHAR(50), FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE transformers (asset_id INT PRIMARY KEY, kva_rating FLOAT, voltage_rating VARCHAR(50), frequency INT, phases INT, insulation_class VARCHAR(50), vector_group VARCHAR(50), FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE pumps (asset_id INT PRIMARY KEY, flow_rate_m3h FLOAT, head_pressure_bar FLOAT, FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE generators (asset_id INT PRIMARY KEY, power_output_mw FLOAT, voltage_kv FLOAT, FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE fans (asset_id INT PRIMARY KEY, airflow_cfm FLOAT, static_pressure_pa FLOAT, FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE boilers (asset_id INT PRIMARY KEY, pressure_capacity_bar FLOAT, max_temp_c FLOAT, FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE compressors (asset_id INT PRIMARY KEY, max_pressure_bar FLOAT, flow_rate_m3h FLOAT, FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE machinery (asset_id INT PRIMARY KEY, operating_hours INT, maintenance_interval_days INT, FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE)''')

    # 4. Insert 10 Industrial Plants
    plants_data = [("CPP",), ("CCPP",), ("PTA",), ("Cracker",), ("Central Workshop",), ("Substation Alpha",), ("Substation Beta",), ("Cooling Tower Unit",), ("Water Treatment Plant",), ("Packaging Unit",)]
    cursor.executemany("INSERT INTO plants (name) VALUES (%s)", plants_data)

    print("Populating 5,000 Randomized Assets... (This will take 15-30 seconds over the cloud)")
    # 5. Generate 5,000 Unevenly Distributed, Non-Consecutive Assets
    plant_weights = {1: 1200, 2: 950, 3: 850, 4: 1100, 5: 150, 6: 100, 7: 100, 8: 250, 9: 200, 10: 100}
    asset_types = ["Motor", "Transformer", "Pump", "Generator", "Fan", "Boiler", "Compressor", "Machinery"]
    mock_assets = []

    for p_id, count in plant_weights.items():
        id_pool = random.sample(range(1000, 99999), count)
        for unit_num in id_pool:
            a_type = random.choice(asset_types)
            name = f"{a_type} Unit-{unit_num}"
            mock_assets.append((p_id, name, a_type, "Operational"))

    # Scramble the arrival order
    random.shuffle(mock_assets)
    
    print("Initiating Cloud Sync... (This may take 1-3 minutes depending on network speed)")
    
    # 6. Insert Assets row-by-row and micro-batch to prevent cloud timeouts
    count = 0
    for asset in mock_assets:
        try:
            cursor.execute("INSERT INTO assets (plant_id, name, asset_type, status) VALUES (%s, %s, %s, %s)", asset)
            new_asset_id = cursor.lastrowid
            a_type = asset[2]
            
            # Inject standard mock engineering values based on the equipment type
            if a_type == "Motor":
                cursor.execute("INSERT INTO motors (asset_id, v_input, output_power_kw, power_factor, phases, rpm, frequency, insulation_class, fire_protection) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (new_asset_id, 415, 75.0, 0.85, 3, 1500, 50, "Class F", "Ex d"))
            elif a_type == "Transformer":
                cursor.execute("INSERT INTO transformers (asset_id, kva_rating, voltage_rating, frequency, phases, insulation_class, vector_group) VALUES (%s, %s, %s, %s, %s, %s, %s)", (new_asset_id, 500.0, "11kV/415V", 50, 3, "Class A", "Dyn11"))
            elif a_type == "Pump":
                cursor.execute("INSERT INTO pumps (asset_id, flow_rate_m3h, head_pressure_bar) VALUES (%s, %s, %s)", (new_asset_id, 120.5, 15.0))
            elif a_type == "Generator":
                cursor.execute("INSERT INTO generators (asset_id, power_output_mw, voltage_kv) VALUES (%s, %s, %s)", (new_asset_id, 2.5, 11.0))
            elif a_type == "Fan":
                cursor.execute("INSERT INTO fans (asset_id, airflow_cfm, static_pressure_pa) VALUES (%s, %s, %s)", (new_asset_id, 5000.0, 250.0))
            elif a_type == "Boiler":
                cursor.execute("INSERT INTO boilers (asset_id, pressure_capacity_bar, max_temp_c) VALUES (%s, %s, %s)", (new_asset_id, 45.0, 450.0))
            elif a_type == "Compressor":
                cursor.execute("INSERT INTO compressors (asset_id, max_pressure_bar, flow_rate_m3h) VALUES (%s, %s, %s)", (new_asset_id, 10.0, 350.0))
            elif a_type == "Machinery":
                cursor.execute("INSERT INTO machinery (asset_id, operating_hours, maintenance_interval_days) VALUES (%s, %s, %s)", (new_asset_id, 1200, 180))
            
            count += 1
            
            # Save to the cloud every 50 rows to prevent pipe clogging
            if count % 50 == 0:
                conn.commit()
                print(f"[{count}/5000] assets successfully synced to TiDB...", flush=True)

        except Exception as e:
            print(f"Network error at asset {count}. Error: {e}")
            conn.rollback() 
            break 

    # Final commit for any remaining rows
    conn.commit()
    print("SUCCESS: Database fully populated!")

if __name__ == "__main__":
    seed_enterprise_database()