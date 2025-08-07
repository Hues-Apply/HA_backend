#!/usr/bin/env python
"""
Standalone script to test database connectivity and diagnose read-only issues.
Run this script to check if the database is accessible and writable.
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.db.utils import DatabaseError
from psycopg2.errors import ReadOnlySqlTransaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connectivity and check for read-only mode."""
    print("Testing database connectivity...")

    try:
        with connection.cursor() as cursor:
            # Test basic connectivity
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✓ Database connection successful: {version[0]}")

            # Test read-only mode
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS test_readonly (id SERIAL PRIMARY KEY);")
                cursor.execute("DROP TABLE IF EXISTS test_readonly;")
                print("✓ Database is writable")
            except ReadOnlySqlTransaction:
                print("⚠ Database is in read-only mode")
                print("This is likely the cause of the admin login error.")
                print("Solutions:")
                print("1. Check if your database provider has put the database in read-only mode")
                print("2. Verify your database credentials have write permissions")
                print("3. Check if there are any maintenance windows or backups running")
            except Exception as e:
                print(f"✗ Error testing write operations: {e}")

            # Test session table access
            try:
                cursor.execute("SELECT COUNT(*) FROM django_session;")
                session_count = cursor.fetchone()
                print(f"✓ Session table accessible: {session_count[0]} sessions")
            except Exception as e:
                print(f"✗ Error accessing session table: {e}")

            # Test admin user table access
            try:
                cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                user_count = cursor.fetchone()
                print(f"✓ User table accessible: {user_count[0]} users")
            except Exception as e:
                print(f"✗ Error accessing user table: {e}")

    except DatabaseError as e:
        print(f"✗ Database connection failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    test_database_connection()
