import mysql.connector
import os
import certifi
from dotenv import load_dotenv

# Load the hidden environment variables
load_dotenv()

def get_db_connection():
    """Establishes a secure connection to the live TiDB Cloud database server."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 4000),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="industrial_asset_tracker",
        # TiDB Serverless requires secure SSL connections
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        ssl_ca=certifi.where()
    )
    return conn

# Centralized Schema Mapping for Table-per-Type (TPT) Data Processing
EQUIPMENT_SCHEMA = {
    "Motor": {"v_input": int, "output_power_kw": float, "power_factor": float, "phases": int, "rpm": int, "frequency": int, "insulation_class": str, "fire_protection": str},
    "Transformer": {"kva_rating": float, "voltage_rating": str, "frequency": int, "phases": int, "insulation_class": str, "vector_group": str},
    "Pump": {"flow_rate_m3h": float, "head_pressure_bar": float},
    "Generator": {"power_output_mw": float, "voltage_kv": float},
    "Fan": {"airflow_cfm": float, "static_pressure_pa": float},
    "Boiler": {"pressure_capacity_bar": float, "max_temp_c": float},
    "Compressor": {"max_pressure_bar": float, "flow_rate_m3h": float},
    "Machinery": {"operating_hours": int, "maintenance_interval_days": int}
}

TABLE_MAPPING = {
    "Motor": "motors", "Transformer": "transformers", "Pump": "pumps",
    "Generator": "generators", "Fan": "fans", "Boiler": "boilers",
    "Compressor": "compressors", "Machinery": "machinery"
}