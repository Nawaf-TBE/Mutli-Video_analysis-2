# Database Module

This module provides comprehensive database management for the Multi-Video Analysis Platform, including configuration, session management, utilities, and maintenance tools.

## 🏗️ Architecture

The database module is organized into several components:

- **`database.py`** - Core database configuration and session management
- **`utils.py`** - Database utilities for maintenance, backup, and statistics
- **`cli.py`** - Command-line interface for database management
- **`__init__.py`** - Module initialization and exports

## 📊 Database Schema

The application uses three main tables:

- **`videos`** - Stores video metadata and URLs
- **`sections`** - Stores video sections with timestamps
- **`frames`** - Stores extracted video frames with metadata

## 🚀 Features

### Core Database Features
- ✅ **Multi-database support** (SQLite, PostgreSQL, MySQL)
- ✅ **Connection pooling** with configurable settings
- ✅ **Health monitoring** and diagnostics
- ✅ **Transaction management** with context managers
- ✅ **Automatic schema validation**
- ✅ **SQLite optimization** with WAL mode and pragmas

### Maintenance & Utilities
- ✅ **Automated backups** with timestamp naming
- ✅ **Database vacuum** for SQLite optimization
- ✅ **Orphaned record cleanup**
- ✅ **Statistics and monitoring**
- ✅ **Schema migration support**
- ✅ **Database size tracking**

### CLI Management
- ✅ **Command-line interface** for all operations
- ✅ **JSON output** for scripting
- ✅ **Comprehensive help** and documentation

## 🔧 Configuration

The database module supports extensive configuration through environment variables:

```bash
# Database URL (required)
DATABASE_URL="sqlite:///./video_analysis.db"

# Optional configuration
DB_ECHO=false                    # Enable SQL query logging
DB_POOL_SIZE=5                   # Connection pool size
DB_MAX_OVERFLOW=10               # Maximum overflow connections
DB_POOL_TIMEOUT=30               # Pool timeout in seconds
DB_POOL_RECYCLE=1800            # Connection recycle time (30 minutes)
DB_CONNECT_TIMEOUT=10           # Connection timeout in seconds
```

### Database URL Examples

```bash
# SQLite (default)
DATABASE_URL="sqlite:///./video_analysis.db"

# PostgreSQL
DATABASE_URL="postgresql://user:password@localhost:5432/video_analysis"

# MySQL
DATABASE_URL="mysql://user:password@localhost:3306/video_analysis"
```

## 📚 Usage

### Python API

```python
from src.app.db import (
    get_db_session,
    init_db,
    check_db_health,
    get_db_stats,
    quick_backup
)

# Initialize database
init_db()

# Check health
if check_db_health():
    print("Database is healthy!")

# Use session context manager
with get_db_session() as db:
    videos = db.query(Video).all()

# Create backup
backup_path = quick_backup()

# Get statistics
stats = get_db_stats()
```

### FastAPI Integration

```python
from src.app.db import get_db

@app.get("/videos/")
async def get_videos(db: Session = Depends(get_db)):
    return db.query(Video).all()
```

### CLI Commands

```bash
# Show help
python -m src.app.db.cli --help

# Check database health
python -m src.app.db.cli health

# Show statistics
python -m src.app.db.cli stats

# Create backup
python -m src.app.db.cli backup

# Run maintenance
python -m src.app.db.cli maintenance

# Show database info
python -m src.app.db.cli info

# Clean orphaned records
python -m src.app.db.cli cleanup

# Vacuum database (SQLite only)
python -m src.app.db.cli vacuum
```

## 🛠️ Maintenance

### Automated Maintenance

The module includes a comprehensive maintenance routine that can be run periodically:

```python
from src.app.db import maintenance_routine

# Run all maintenance tasks
results = maintenance_routine()
```

This includes:
- Cleaning up orphaned records
- Analyzing database statistics
- Vacuuming SQLite databases
- Cleaning up old backups

### Manual Maintenance

```python
from src.app.db import DatabaseMaintenance, DatabaseStats

# Vacuum database
DatabaseMaintenance.vacuum_database()

# Analyze for query optimization
DatabaseMaintenance.analyze_database()

# Clean orphaned records
DatabaseStats.cleanup_orphaned_records()

# Get database size
size_info = DatabaseMaintenance.get_database_size()
```

## 💾 Backup & Restore

### Creating Backups

```python
from src.app.db import DatabaseBackup

# Create backup with default settings
backup_path = DatabaseBackup.create_backup()

# Create backup in custom directory
backup_path = DatabaseBackup.create_backup("my_backups")
```

### Backup Types

- **SQLite**: Direct file copy with timestamp
- **PostgreSQL/MySQL**: JSON export with all data

### Automatic Cleanup

Old backups are automatically cleaned up during maintenance:

```python
# Clean backups older than 30 days
deleted_count = DatabaseBackup.cleanup_old_backups(days_to_keep=30)
```

## 📈 Monitoring & Statistics

### Health Monitoring

```python
from src.app.db import check_db_health, get_db_info

# Simple health check
healthy = check_db_health()

# Detailed database information
info = get_db_info()
```

### Statistics

```python
from src.app.db import get_db_stats, DatabaseStats

# Comprehensive statistics
stats = get_db_stats()

# Table-specific statistics
table_stats = DatabaseStats.get_table_stats()

# Find orphaned records
orphaned = DatabaseStats.get_orphaned_records()
```

## 🔧 Advanced Configuration

### SQLite Optimizations

The module automatically applies SQLite optimizations:

```sql
PRAGMA foreign_keys=ON;          -- Enable foreign key constraints
PRAGMA journal_mode=WAL;         -- Write-Ahead Logging for concurrency
PRAGMA synchronous=NORMAL;       -- Balance performance and durability
```

### Connection Pool Settings

For PostgreSQL and MySQL, connection pooling is automatically configured:

- **Pool size**: 5 connections (configurable)
- **Max overflow**: 10 additional connections
- **Pool timeout**: 30 seconds
- **Connection recycle**: 30 minutes
- **Pre-ping**: Verify connections before use

## 🚨 Error Handling

The module includes comprehensive error handling:

- **Connection failures**: Automatic retry with exponential backoff
- **Transaction rollback**: Automatic rollback on errors
- **Health monitoring**: Continuous health checks
- **Logging**: Detailed logging for debugging

## 🔒 Security

### Best Practices

- Database URLs with credentials are masked in logs
- Connection timeouts prevent hanging connections
- Foreign key constraints ensure data integrity
- Transaction isolation prevents data corruption

### Environment Variables

Sensitive information should be stored in environment variables:

```bash
# Use environment variables for credentials
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
```

## 🧪 Testing

The module includes utilities for testing:

```python
from src.app.db import get_db_session, init_db

# Test database initialization
def test_db_init():
    init_db()
    assert check_db_health()

# Test with session
def test_with_session():
    with get_db_session() as db:
        # Your test code here
        pass
```

## 📝 Migration Support

The module includes basic migration utilities:

```python
from src.app.db import DatabaseMigration

# Get current schema version
version = DatabaseMigration.get_schema_version()

# Validate schema
validation = DatabaseMigration.validate_schema()
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection refused**: Check if database server is running
2. **Permission denied**: Verify database credentials and permissions
3. **Table not found**: Run `init_db()` to create tables
4. **Lock timeout**: Check for long-running transactions

### Debug Mode

Enable SQL logging for debugging:

```bash
export DB_ECHO=true
```

### Health Check Endpoint

The API includes a comprehensive health check:

```bash
curl http://localhost:8000/health
```

## 📖 API Reference

### Core Functions

- `init_db()` - Initialize database and create tables
- `check_db_health()` - Check database connectivity
- `get_db()` - FastAPI dependency for database sessions
- `get_db_session()` - Context manager for database sessions
- `get_db_info()` - Get database configuration information
- `get_db_stats()` - Get comprehensive database statistics

### Utility Classes

- `DatabaseConfig` - Configuration management
- `DatabaseMaintenance` - Maintenance operations
- `DatabaseBackup` - Backup and restore operations
- `DatabaseStats` - Statistics and monitoring
- `DatabaseMigration` - Schema migration utilities

### CLI Commands

- `health` - Check database health
- `stats` - Show database statistics
- `info` - Show database information
- `backup` - Create database backup
- `maintenance` - Run maintenance routine
- `cleanup` - Clean orphaned records
- `vacuum` - Vacuum database (SQLite only)

---

## 🤝 Contributing

When contributing to the database module:

1. Follow the existing code style and patterns
2. Add comprehensive error handling
3. Include logging for important operations
4. Write tests for new functionality
5. Update documentation for new features

## 📄 License

This database module is part of the Multi-Video Analysis Platform. 