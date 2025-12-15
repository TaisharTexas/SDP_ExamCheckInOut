import pymysql
import time
import os
from django.db import connection

def wait_for_db():
    """Wait for database to be available through SSH tunnel"""
    db_conn = None
    retries = 30
    
    while retries > 0:
        try:
            db_conn = connection.cursor()
            print("Database connection established")
            break
        except Exception as e:
            print(f"Database unavailable, waiting 2 seconds... ({retries} attempts left)")
            print(f"Error: {e}")
            retries -= 1
            time.sleep(2)
    
    if retries == 0:
        raise Exception("Could not establish database connection")
    

pymysql.install_as_MySQLdb()

# if os.environ.get('DATABASE_HOST') == 'localhost':  # This means we're using the tunnel
#     wait_for_db()