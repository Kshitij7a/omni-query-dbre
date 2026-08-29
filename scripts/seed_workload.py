import psycopg2
import os
import random
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "omniquery")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def seed_data():
    print("Connecting to database...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print("Creating orders table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_id INT,
            amount DECIMAL(10, 2),
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Check if table already has data
    cursor.execute("SELECT COUNT(*) FROM orders;")
    count = cursor.fetchone()[0]
    
    if count < 50000:
        print("Populating orders with heavy unindexed data...")
        cursor.execute("""
            INSERT INTO orders (customer_id, amount, status)
            SELECT 
                (random() * 1000)::int,
                (random() * 500)::decimal(10, 2),
                CASE WHEN random() < 0.5 THEN 'PENDING' ELSE 'COMPLETED' END
            FROM generate_series(1, 50000);
        """)

    print("Running repetitive unindexed queries to populate pg_stat_statements...")
    for _ in range(150):
        cust_id = random.randint(1, 1000)
        cursor.execute(f"SELECT COUNT(*) FROM orders WHERE customer_id = {cust_id};")
        cursor.fetchall()
        
    for _ in range(100):
        cursor.execute("SELECT * FROM orders WHERE status = 'PENDING' ORDER BY created_at DESC LIMIT 10;")
        cursor.fetchall()

    print("Workload seeded successfully.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    seed_data()
