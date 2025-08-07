"""
Custom database backend to handle read-only transactions gracefully.
"""
import logging
from django.db.backends.postgresql.base import DatabaseWrapper as PostgresDatabaseWrapper
from django.db.utils import DatabaseError
from psycopg2.errors import ReadOnlySqlTransaction

logger = logging.getLogger(__name__)


class DatabaseWrapper(PostgresDatabaseWrapper):
    """
    Custom database wrapper that handles read-only transaction errors gracefully.
    """

    def _execute(self, sql, params=None):
        """
        Override _execute to handle read-only transaction errors.
        """
        try:
            return super()._execute(sql, params)
        except ReadOnlySqlTransaction as e:
            logger.warning(f"Read-only transaction error: {e}")
            # For read-only errors, we can't do much but log and re-raise
            # The application should handle this at a higher level
            raise DatabaseError(f"Database is in read-only mode: {e}") from e
        except Exception as e:
            logger.error(f"Database execution error: {e}")
            raise

    def ensure_connection(self):
        """
        Override ensure_connection to add retry logic for read-only errors.
        """
        try:
            return super().ensure_connection()
        except ReadOnlySqlTransaction as e:
            logger.warning(f"Connection failed due to read-only mode: {e}")
            # Try to reconnect without read-only mode
            self.close()
            return super().ensure_connection()


def get_database_connection_options():
    """
    Get database connection options that work better with read-only databases.
    """
    return {
        'sslmode': 'require',
        'connect_timeout': 10,
        'application_name': 'huesapply_backend',
        'options': '',
    }
