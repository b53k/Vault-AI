import os
import psycopg2
from psycopg2 import pool
from typing import Optional
from contextlib import contextmanager
from dotenv import load_dotenv
from pathlib import Path

# Find .env file - look in service root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

class SupabaseConnection:
    def __init__(self):
        self.connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
    
    def initialize_pool(self):
        project_id = os.getenv('PROJECT_ID')
        pwd = os.getenv('PSWD')

        db_url = os.getenv(
            "SUPABASE_DB_URL",
            f"postgresql://postgres.{project_id}:{pwd}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
        )
        

        self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=db_url,
            connect_timeout=10,
        )

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        if not self.connection_pool:
            self.initialize_pool()
        
        conn = self.connection_pool.getconn()

        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)
        
    def close_all(self):
        """Close all connections -- need to only call this when the application shuts down"""
        if self.connection_pool:
            self.connection_pool.closeall()


db_connection = SupabaseConnection()

if __name__ == "__main__":
    try:
        db_connection.initialize_pool()
        print("✓ Database connection pool initialized successfully!")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")