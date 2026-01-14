'''
    Bulk Load Transactions CSV into Supabase PostgresSQL Database
    (because Supabase doesn't support 100MB+ files in the UI)
'''

import os
import csv
import psycopg2
from psycopg2.extras import execute_values
from psycopg2 import sql
from typing import List, Tuple
import sys
from datetime import datetime
import yaml


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'supabase_config.yaml')

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

PWD = config['pwd']
PROJECT_ID = config['project_id']

SUPABASE_DB_URL = os.getenv(
    "SUPABASE_DB_URL",
    f"postgresql://postgres:{PWD}@db.{PROJECT_ID}.supabase.co:5432/postgres"
)

# Get the synthetic data directory (sibling to scripts directory)
SYNTHETIC_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'synthetic')
TRANSACTIONS_CSV_PATH = os.path.join(SYNTHETIC_DIR, 'transactions.csv')
BATCH_SIZE = 1000 # Insert in batches of 1000 to avoid timeouts

def get_connection():
    '''
        Create a connection to the Supabase database
    '''
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL, connect_timeout=10)
        return conn

    except Exception as e:
        print (f"Error connecting to Supabase: {e}")
        sys.exit(1)

def verify_table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table_name,))
        exists = cur.fetchone()[0]
    
    return exists

def verify_accounts_exist(conn) -> bool:
    """Verify that accounts table has data (for foreign key validation)"""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM accounts;")
        count = cur.fetchone()[0]
        print(f"✓ Found {count:,} accounts in database")

        return count > 0

def create_transactions_table_if_not_exists(conn):
    """Create transactions table if it doesn't exist"""
    with conn.cursor() as cur:
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'transactions'
            );
        """)
        exists = cur.fetchone()[0]
        
        if not exists:
            print("📝 Creating transactions table...")
            cur.execute("""
                CREATE TABLE transactions (
                    transaction_id BIGSERIAL PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    merchant VARCHAR(255),
                    timestamp TIMESTAMP NOT NULL,
                    running_balance DECIMAL(15,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_account 
                        FOREIGN KEY (account_id) 
                        REFERENCES accounts(account_id) 
                        ON DELETE CASCADE
                );
            """)
            
            # Create indexes for performance
            cur.execute("""
                CREATE INDEX idx_transactions_account_id 
                ON transactions(account_id);
            """)
            
            cur.execute("""
                CREATE INDEX idx_transactions_timestamp 
                ON transactions(timestamp DESC);
            """)
            
            cur.execute("""
                CREATE INDEX idx_transactions_account_timestamp 
                ON transactions(account_id, timestamp DESC);
            """)
            
            conn.commit()
            print("✓ Transactions table created with indexes")
        else:
            print("✓ Transactions table already exists")


def parse_transaction_row(row: List[str]) -> Tuple:
    """Parse a CSV row into a tuple for database insertion"""
    try:
        transaction_id = int(row[0]) if row[0] else None
        account_id = int(row[1])
        amount = float(row[2])
        category = row[3].strip()
        merchant = row[4].strip() if row[4] else None
        timestamp_str = row[5].strip()
        running_balance = float(row[6]) if row[6] else None
        
        # Parse ISO timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        return (
            transaction_id,
            account_id,
            amount,
            category,
            merchant,
            timestamp,
            running_balance
        )
    except Exception as e:
        print(f"Error parsing row: {row[:3]}... Error: {e}")
        return None
    
def load_transactions_batch(conn, transactions: List[Tuple]):
    """Insert a batch of transactions using execute_values for speed"""
    if not transactions:
        return
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO transactions 
            (transaction_id, account_id, amount, category, merchant, timestamp, running_balance)
            VALUES %s
            ON CONFLICT (transaction_id) DO NOTHING
            """,
            transactions,
            template=None,
            page_size=1000
        )
    conn.commit()


def load_transactions_using_copy(conn, csv_path: str):
    """
    Load transactions using PostgreSQL COPY command (fastest method)
    This requires the CSV to be in the exact format PostgreSQL expects
    """
    print("🚀 Using PostgreSQL COPY command for maximum speed...")
    
    with conn.cursor() as cur:
        # Use COPY FROM with CSV format
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Skip header row
            next(f)
            
            # Use COPY with CSV format
            cur.copy_expert("""
                COPY transactions (
                    transaction_id, 
                    account_id, 
                    amount, 
                    category, 
                    merchant, 
                    timestamp, 
                    running_balance
                )
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    DELIMITER ',',
                    QUOTE '"',
                    ESCAPE '"',
                    HEADER false
                )
            """, f)
        
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM transactions;")
        count = cur.fetchone()[0]
        print(f"✓ Loaded {count:,} transactions using COPY")


def load_transactions_batched(conn, csv_path: str):
    """
    Load transactions in batches (slower but more memory-efficient)
    Use this if COPY command doesn't work due to format issues
    """
    print(f"📦 Loading transactions in batches of {BATCH_SIZE:,}...")
    
    total_rows = 0
    batch = []
    errors = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        for row_num, row in enumerate(reader, start=2):
            parsed = parse_transaction_row(row)
            
            if parsed is None:
                errors += 1
                continue
            
            batch.append(parsed)
            
            if len(batch) >= BATCH_SIZE:
                try:
                    load_transactions_batch(conn, batch)
                    total_rows += len(batch)
                    print(f"  ✓ Inserted {total_rows:,} transactions...", end='\r')
                    batch = []
                except Exception as e:
                    print(f"\n⚠️  Error inserting batch at row {row_num}: {e}")
                    errors += 1
                    batch = []
        
        # Insert remaining rows
        if batch:
            try:
                load_transactions_batch(conn, batch)
                total_rows += len(batch)
            except Exception as e:
                print(f"\n⚠️  Error inserting final batch: {e}")
                errors += 1
    
    print(f"\n✓ Completed! Inserted {total_rows:,} transactions")
    if errors > 0:
        print(f"⚠️  {errors} rows had errors and were skipped")


def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 Bulk Loading Transactions into Supabase")
    print("=" * 60)
    
    # Verify CSV file exists
    if not os.path.exists(TRANSACTIONS_CSV_PATH):
        print(f"❌ CSV file not found: {TRANSACTIONS_CSV_PATH}")
        sys.exit(1)
    
    file_size = os.path.getsize(TRANSACTIONS_CSV_PATH) / (1024 * 1024)
    print(f"📁 File size: {file_size:.2f} MB")
    
    # Connect to database
    print("\n🔌 Connecting to Supabase...")
    conn = get_connection()
    print("✓ Connected successfully")
    
    # Verify accounts table exists and has data
    if not verify_accounts_exist(conn):
        print("❌ Accounts table is empty! Load accounts.csv first.")
        conn.close()
        sys.exit(1)
    
    # Create transactions table if needed
    create_transactions_table_if_not_exists(conn)
    
    # Check if transactions already exist
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM transactions;")
        existing_count = cur.fetchone()[0]
        
        if existing_count > 0:
            response = input(
                f"\n⚠️  Transactions table already has {existing_count:,} rows. "
                "Continue and add more? (y/n): "
            )
            if response.lower() != 'y':
                print("Cancelled.")
                conn.close()
                return
    
    # Load transactions
    print("\n📥 Loading transactions...")
    try:
        # Try COPY method first (fastest)
        load_transactions_using_copy(conn, TRANSACTIONS_CSV_PATH)
    except Exception as e:
        print(f"\n⚠️  COPY method failed: {e}")
        print("🔄 Falling back to batched insert method...")
        load_transactions_batched(conn, TRANSACTIONS_CSV_PATH)
    
    # Verify final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM transactions;")
        final_count = cur.fetchone()[0]
        print(f"\n✅ Final transaction count: {final_count:,}")
    
    conn.close()
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()