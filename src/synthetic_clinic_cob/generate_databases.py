import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from clinic_data import gen_clinic_schedule
from cob_data import gen_products_manual, gen_marketing_schedule, gen_cob_customers


# Load environment variables
load_dotenv()

def generate_databases():
    # Generate data
    products_df = gen_products_manual()
    customers_df = gen_cob_customers(100, products_df)
    marketing_df = gen_marketing_schedule(7, 30, 9, 17)
    clinic_df = gen_clinic_schedule(5, 8, 14, 9, 17)

    # Get database paths from environment or use defaults
    clinic_db_path = os.getenv("CLINIC_DB_PATH", "clinic_appointments_2.db")
    cob_db_path = os.getenv("COB_DB_PATH", "cob_system_2.db")

    # Insert clinic data
    with sqlite3.connect(clinic_db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            clinic_id TEXT,
            doctor_id TEXT,
            doctor_name TEXT,
            specialty TEXT,
            clinic_name TEXT,
            slot_datetime DATETIME,
            available BOOLEAN DEFAULT 1,
            appointment_id TEXT,
            patient_name TEXT,
            contact_email TEXT,
            PRIMARY KEY (clinic_id, doctor_id, slot_datetime)
        )
        """)
        clinic_df.to_sql('appointments', conn, if_exists='replace', index=False)

    # Insert COB data
    with sqlite3.connect(cob_db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS marketing_availability (
            marketer_id TEXT,
            marketer_name TEXT,
            slot_datetime DATETIME,
            available BOOLEAN DEFAULT 1,
            appointment_id TEXT,
            customer_id TEXT,
            PRIMARY KEY (marketer_id, slot_datetime)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT,
            description TEXT,
            category TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            signup_date TEXT,
            status TEXT,
            product_id TEXT
        )
        """)
        marketing_df.to_sql('marketing_availability', conn, if_exists='replace', index=False)
        products_df.to_sql('products', conn, if_exists='replace', index=False)
        customers_df.to_sql('customers', conn, if_exists='replace', index=False)

    print("✅ SQLite databases created and populated successfully.")

if __name__ == '__main__':
    generate_databases()
