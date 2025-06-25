"""
Database utilities for Multi-Video Analysis Platform.

This module provides utility functions for:
- Database maintenance and cleanup
- Data migration helpers
- Database backup and restore
- Performance monitoring
- Data validation
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from .database import get_db_session, engine, config, logger
from ..models.video import Video
from ..models.section import Section
from ..models.frame import Frame


class DatabaseMaintenance:
    """Database maintenance utilities."""
    
    @staticmethod
    def vacuum_database() -> bool:
        """
        Vacuum the database to reclaim space and optimize performance.
        Only works with SQLite databases.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not config.is_sqlite:
            logger.warning("VACUUM operation is only supported for SQLite databases")
            return False
            
        try:
            with engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.commit()
            logger.info("Database vacuum completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False
    
    @staticmethod
    def analyze_database() -> bool:
        """
        Analyze database statistics for query optimization.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with engine.connect() as conn:
                if config.is_sqlite:
                    conn.execute(text("ANALYZE"))
                elif config.is_postgresql:
                    conn.execute(text("ANALYZE"))
                elif config.is_mysql:
                    conn.execute(text("ANALYZE TABLE videos, sections, frames"))
                conn.commit()
            logger.info("Database analysis completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            return False
    
    @staticmethod
    def get_database_size() -> Dict[str, Any]:
        """
        Get database size information.
        
        Returns:
            dict: Database size information
        """
        try:
            if config.is_sqlite:
                db_path = config.database_url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    size_bytes = os.path.getsize(db_path)
                    return {
                        "size_bytes": size_bytes,
                        "size_mb": round(size_bytes / (1024 * 1024), 2),
                        "path": db_path
                    }
            else:
                # For PostgreSQL/MySQL, would need specific queries
                logger.warning("Database size calculation not implemented for this database type")
                
            return {"size_bytes": 0, "size_mb": 0, "path": None}
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return {"size_bytes": 0, "size_mb": 0, "path": None}


class DatabaseBackup:
    """Database backup and restore utilities."""
    
    @staticmethod
    def create_backup(backup_dir: str = "backups") -> Optional[str]:
        """
        Create a backup of the database.
        
        Args:
            backup_dir: Directory to store backups
            
        Returns:
            str: Path to backup file if successful, None otherwise
        """
        try:
            # Create backup directory if it doesn't exist
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if config.is_sqlite:
                # For SQLite, copy the database file
                db_path = config.database_url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    backup_file = backup_path / f"video_analysis_backup_{timestamp}.db"
                    shutil.copy2(db_path, backup_file)
                    logger.info(f"SQLite backup created: {backup_file}")
                    return str(backup_file)
            else:
                # For other databases, export data as JSON
                backup_file = backup_path / f"video_analysis_backup_{timestamp}.json"
                DatabaseBackup._export_data_to_json(str(backup_file))
                logger.info(f"Data backup created: {backup_file}")
                return str(backup_file)
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None
    
    @staticmethod
    def _export_data_to_json(filepath: str) -> None:
        """Export database data to JSON format."""
        with get_db_session() as db:
            data = {
                "videos": [
                    {
                        "id": v.id,
                        "url": v.url,
                        "title": v.title,
                        "created_at": v.created_at.isoformat() if v.created_at else None,
                        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
                    }
                    for v in db.query(Video).all()
                ],
                "sections": [
                    {
                        "id": s.id,
                        "video_id": s.video_id,
                        "title": s.title,
                        "start_time": s.start_time,
                        "end_time": s.end_time,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    }
                    for s in db.query(Section).all()
                ],
                "frames": [
                    {
                        "id": f.id,
                        "video_id": f.video_id,
                        "timestamp": f.timestamp,
                        "path": f.path,
                        "created_at": f.created_at.isoformat() if f.created_at else None,
                        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                    }
                    for f in db.query(Frame).all()
                ],
                "backup_created": datetime.now().isoformat(),
                "database_type": "sqlite" if config.is_sqlite else "other"
            }
            
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def cleanup_old_backups(backup_dir: str = "backups", days_to_keep: int = 30) -> int:
        """
        Clean up old backup files.
        
        Args:
            backup_dir: Directory containing backups
            days_to_keep: Number of days to keep backups
            
        Returns:
            int: Number of files deleted
        """
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return 0
                
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for backup_file in backup_path.glob("video_analysis_backup_*"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file}")
            
            logger.info(f"Cleaned up {deleted_count} old backup files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return 0


class DatabaseStats:
    """Database statistics and monitoring utilities."""
    
    @staticmethod
    def get_table_stats() -> Dict[str, Any]:
        """
        Get statistics for all tables.
        
        Returns:
            dict: Table statistics
        """
        try:
            with get_db_session() as db:
                stats = {
                    "videos": {
                        "count": db.query(Video).count(),
                        "latest": db.query(Video).order_by(Video.created_at.desc()).first(),
                    },
                    "sections": {
                        "count": db.query(Section).count(),
                        "avg_duration": db.query(Section).filter(
                            Section.end_time.isnot(None),
                            Section.start_time.isnot(None)
                        ).with_entities(
                            text("AVG(end_time - start_time)")
                        ).scalar() or 0,
                    },
                    "frames": {
                        "count": db.query(Frame).count(),
                        "videos_with_frames": db.query(Frame.video_id).distinct().count(),
                    }
                }
                
                # Convert latest video to dict if exists
                if stats["videos"]["latest"]:
                    latest_video = stats["videos"]["latest"]
                    stats["videos"]["latest"] = {
                        "id": latest_video.id,
                        "title": latest_video.title,
                        "created_at": latest_video.created_at.isoformat() if latest_video.created_at else None,
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}
    
    @staticmethod
    def get_orphaned_records() -> Dict[str, List[int]]:
        """
        Find orphaned records (sections/frames without videos).
        
        Returns:
            dict: Lists of orphaned record IDs
        """
        try:
            with get_db_session() as db:
                # Find sections without videos
                orphaned_sections = db.query(Section.id).outerjoin(Video).filter(Video.id.is_(None)).all()
                
                # Find frames without videos
                orphaned_frames = db.query(Frame.id).outerjoin(Video).filter(Video.id.is_(None)).all()
                
                return {
                    "sections": [s[0] for s in orphaned_sections],
                    "frames": [f[0] for f in orphaned_frames],
                }
                
        except Exception as e:
            logger.error(f"Failed to find orphaned records: {e}")
            return {"sections": [], "frames": []}
    
    @staticmethod
    def cleanup_orphaned_records() -> Dict[str, int]:
        """
        Remove orphaned records from the database.
        
        Returns:
            dict: Count of deleted records by type
        """
        try:
            with get_db_session() as db:
                # Delete orphaned sections
                orphaned_sections = db.query(Section).outerjoin(Video).filter(Video.id.is_(None))
                sections_count = orphaned_sections.count()
                orphaned_sections.delete(synchronize_session=False)
                
                # Delete orphaned frames
                orphaned_frames = db.query(Frame).outerjoin(Video).filter(Video.id.is_(None))
                frames_count = orphaned_frames.count()
                orphaned_frames.delete(synchronize_session=False)
                
                db.commit()
                
                logger.info(f"Cleaned up {sections_count} orphaned sections and {frames_count} orphaned frames")
                return {"sections": sections_count, "frames": frames_count}
                
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned records: {e}")
            return {"sections": 0, "frames": 0}


class DatabaseMigration:
    """Database migration utilities."""
    
    @staticmethod
    def get_schema_version() -> str:
        """
        Get current database schema version.
        
        Returns:
            str: Schema version
        """
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Simple version based on table existence
            if all(table in tables for table in ["videos", "sections", "frames"]):
                return "1.0.0"
            else:
                return "0.0.0"
                
        except Exception as e:
            logger.error(f"Failed to get schema version: {e}")
            return "unknown"
    
    @staticmethod
    def validate_schema() -> Dict[str, Any]:
        """
        Validate database schema integrity.
        
        Returns:
            dict: Validation results
        """
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            required_tables = ["videos", "sections", "frames"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            validation_result = {
                "valid": len(missing_tables) == 0,
                "tables_found": tables,
                "missing_tables": missing_tables,
                "schema_version": DatabaseMigration.get_schema_version(),
            }
            
            if validation_result["valid"]:
                logger.info("Database schema validation passed")
            else:
                logger.warning(f"Database schema validation failed: missing tables {missing_tables}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return {"valid": False, "error": str(e)}


# Convenience functions for common operations
def quick_backup() -> Optional[str]:
    """Create a quick backup of the database."""
    return DatabaseBackup.create_backup()

def get_db_stats() -> Dict[str, Any]:
    """Get comprehensive database statistics."""
    return {
        "table_stats": DatabaseStats.get_table_stats(),
        "database_size": DatabaseMaintenance.get_database_size(),
        "schema_info": DatabaseMigration.validate_schema(),
        "orphaned_records": DatabaseStats.get_orphaned_records(),
    }

def maintenance_routine() -> Dict[str, Any]:
    """Run routine database maintenance tasks."""
    results = {}
    
    # Cleanup orphaned records
    results["orphaned_cleanup"] = DatabaseStats.cleanup_orphaned_records()
    
    # Analyze database
    results["analyze"] = DatabaseMaintenance.analyze_database()
    
    # Vacuum if SQLite
    if config.is_sqlite:
        results["vacuum"] = DatabaseMaintenance.vacuum_database()
    
    # Cleanup old backups
    results["backup_cleanup"] = DatabaseBackup.cleanup_old_backups()
    
    logger.info("Database maintenance routine completed")
    return results 