"""
Database module for Multi-Video Analysis Platform.

This module provides database configuration, session management, 
and utility functions for the application.
"""

from .database import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_db,
    check_db_health,
    get_db_info,
    close_db_connections,
    execute_in_transaction,
    parse_database_url,
    config,
)

from .utils import (
    DatabaseMaintenance,
    DatabaseBackup,
    DatabaseStats,
    DatabaseMigration,
    quick_backup,
    get_db_stats,
    maintenance_routine,
)

__all__ = [
    # Core database components
    "Base",
    "engine", 
    "SessionLocal",
    "get_db",
    "get_db_session",
    "config",
    
    # Database operations
    "init_db",
    "check_db_health",
    "get_db_info",
    "close_db_connections",
    "execute_in_transaction",
    "parse_database_url",
    
    # Utility classes
    "DatabaseMaintenance",
    "DatabaseBackup", 
    "DatabaseStats",
    "DatabaseMigration",
    
    # Convenience functions
    "quick_backup",
    "get_db_stats",
    "maintenance_routine",
] 