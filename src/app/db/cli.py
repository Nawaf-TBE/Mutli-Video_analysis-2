#!/usr/bin/env python3
"""
Database CLI management tool for Multi-Video Analysis Platform.

Usage:
    python -m src.app.db.cli [command] [options]

Commands:
    backup          Create a database backup
    stats           Show database statistics
    maintenance     Run maintenance routine
    health          Check database health
    info            Show database information
    cleanup         Clean up orphaned records
    vacuum          Vacuum the database (SQLite only)
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.app.db import (
    check_db_health,
    get_db_info,
    get_db_stats,
    maintenance_routine,
    quick_backup,
    DatabaseMaintenance,
    DatabaseStats,
    DatabaseBackup,
)


def cmd_backup(args):
    """Create a database backup."""
    print("Creating database backup...")
    backup_path = DatabaseBackup.create_backup(args.dir)
    if backup_path:
        print(f"✅ Backup created successfully: {backup_path}")
        return 0
    else:
        print("❌ Backup creation failed")
        return 1


def cmd_stats(args):
    """Show database statistics."""
    print("Gathering database statistics...")
    stats = get_db_stats()
    
    if args.json:
        print(json.dumps(stats, indent=2, default=str))
    else:
        print("\n📊 Database Statistics")
        print("=" * 50)
        
        # Table stats
        table_stats = stats.get("table_stats", {})
        print(f"\n📹 Videos: {table_stats.get('videos', {}).get('count', 0)}")
        print(f"📝 Sections: {table_stats.get('sections', {}).get('count', 0)}")
        print(f"🖼️  Frames: {table_stats.get('frames', {}).get('count', 0)}")
        
        # Database size
        db_size = stats.get("database_size", {})
        if db_size.get("size_mb", 0) > 0:
            print(f"💾 Database size: {db_size['size_mb']} MB")
        
        # Schema info
        schema_info = stats.get("schema_info", {})
        print(f"🔧 Schema version: {schema_info.get('schema_version', 'unknown')}")
        print(f"✅ Schema valid: {schema_info.get('valid', False)}")
        
        # Orphaned records
        orphaned = stats.get("orphaned_records", {})
        orphaned_sections = len(orphaned.get("sections", []))
        orphaned_frames = len(orphaned.get("frames", []))
        if orphaned_sections > 0 or orphaned_frames > 0:
            print(f"⚠️  Orphaned records: {orphaned_sections} sections, {orphaned_frames} frames")
    
    return 0


def cmd_maintenance(args):
    """Run database maintenance routine."""
    print("Running database maintenance routine...")
    results = maintenance_routine()
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("\n🔧 Maintenance Results")
        print("=" * 50)
        
        for task, result in results.items():
            if isinstance(result, dict):
                if task == "orphaned_cleanup":
                    sections = result.get("sections", 0)
                    frames = result.get("frames", 0)
                    print(f"🧹 {task}: Cleaned {sections} sections, {frames} frames")
                else:
                    print(f"🔧 {task}: {result}")
            else:
                status = "✅" if result else "❌"
                print(f"{status} {task}: {'Success' if result else 'Failed'}")
    
    return 0


def cmd_health(args):
    """Check database health."""
    print("Checking database health...")
    healthy = check_db_health()
    
    if healthy:
        print("✅ Database is healthy")
        return 0
    else:
        print("❌ Database health check failed")
        return 1


def cmd_info(args):
    """Show database information."""
    print("Getting database information...")
    info = get_db_info()
    
    if args.json:
        print(json.dumps(info, indent=2, default=str))
    else:
        print("\n📋 Database Information")
        print("=" * 50)
        print(f"Type: {info.get('database_type', 'unknown')}")
        print(f"Engine: {info.get('engine_name', 'unknown')}")
        print(f"Driver: {info.get('driver', 'unknown')}")
        print(f"URL: {info.get('database_url', 'unknown')}")
        print(f"SQL Echo: {info.get('echo_sql', False)}")
        
        # Pool information if available
        if 'pool_size' in info:
            print(f"\nConnection Pool:")
            print(f"  Size: {info.get('pool_size', 0)}")
            print(f"  Checked in: {info.get('checked_in', 0)}")
            print(f"  Checked out: {info.get('checked_out', 0)}")
            print(f"  Invalid: {info.get('invalid', 0)}")
    
    return 0


def cmd_cleanup(args):
    """Clean up orphaned records."""
    print("Cleaning up orphaned records...")
    results = DatabaseStats.cleanup_orphaned_records()
    
    sections_cleaned = results.get("sections", 0)
    frames_cleaned = results.get("frames", 0)
    
    print(f"✅ Cleaned up {sections_cleaned} orphaned sections")
    print(f"✅ Cleaned up {frames_cleaned} orphaned frames")
    
    return 0


def cmd_vacuum(args):
    """Vacuum the database (SQLite only)."""
    print("Vacuuming database...")
    success = DatabaseMaintenance.vacuum_database()
    
    if success:
        print("✅ Database vacuum completed successfully")
        return 0
    else:
        print("❌ Database vacuum failed")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database management CLI for Multi-Video Analysis Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a database backup")
    backup_parser.add_argument("--dir", default="backups", help="Backup directory")
    backup_parser.set_defaults(func=cmd_backup)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")
    stats_parser.set_defaults(func=cmd_stats)
    
    # Maintenance command
    maintenance_parser = subparsers.add_parser("maintenance", help="Run maintenance routine")
    maintenance_parser.add_argument("--json", action="store_true", help="Output as JSON")
    maintenance_parser.set_defaults(func=cmd_maintenance)
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check database health")
    health_parser.set_defaults(func=cmd_health)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show database information")
    info_parser.add_argument("--json", action="store_true", help="Output as JSON")
    info_parser.set_defaults(func=cmd_info)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up orphaned records")
    cleanup_parser.set_defaults(func=cmd_cleanup)
    
    # Vacuum command
    vacuum_parser = subparsers.add_parser("vacuum", help="Vacuum database (SQLite only)")
    vacuum_parser.set_defaults(func=cmd_vacuum)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 