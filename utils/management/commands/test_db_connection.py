"""
Django management command to test database connectivity.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import DatabaseError
from psycopg2.errors import ReadOnlySqlTransaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test database connectivity and check for read-only mode'

    def handle(self, *args, **options):
        self.stdout.write('Testing database connectivity...')

        try:
            with connection.cursor() as cursor:
                # Test basic connectivity
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Database connection successful: {version[0]}')
                )

                # Test read-only mode
                try:
                    cursor.execute("CREATE TABLE IF NOT EXISTS test_readonly (id SERIAL PRIMARY KEY);")
                    cursor.execute("DROP TABLE IF EXISTS test_readonly;")
                    self.stdout.write(
                        self.style.SUCCESS('✓ Database is writable')
                    )
                except ReadOnlySqlTransaction:
                    self.stdout.write(
                        self.style.WARNING('⚠ Database is in read-only mode')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error testing write operations: {e}')
                    )

                # Test session table access
                try:
                    cursor.execute("SELECT COUNT(*) FROM django_session;")
                    session_count = cursor.fetchone()
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Session table accessible: {session_count[0]} sessions')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error accessing session table: {e}')
                    )

        except DatabaseError as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Database connection failed: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Unexpected error: {e}')
            )
