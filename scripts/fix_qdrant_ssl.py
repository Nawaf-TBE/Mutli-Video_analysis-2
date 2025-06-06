#!/usr/bin/env python3
"""
Script to fix Qdrant SSL connection issues by ensuring proper configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_qdrant_status():
    """Check if Qdrant is running."""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if 'qdrant' in result.stdout:
            print("✅ Qdrant container is running")
            return True
        else:
            print("❌ Qdrant container is not running")
            return False
    except Exception as e:
        print(f"❌ Error checking Qdrant status: {e}")
        return False

def restart_qdrant():
    """Restart Qdrant with proper configuration."""
    print("🔄 Restarting Qdrant...")
    
    # Stop existing container
    subprocess.run(['docker', 'stop', 'qdrant'], capture_output=True)
    subprocess.run(['docker', 'rm', 'qdrant'], capture_output=True)
    
    # Ensure storage directory exists
    storage_dir = Path("storage/qdrant")
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Start Qdrant with HTTP only (no TLS)
    cmd = [
        'docker', 'run', '-d',
        '--name', 'qdrant',
        '-p', '6333:6333',
        '-p', '6334:6334',
        '-v', f'{storage_dir.absolute()}:/qdrant/storage',
        '-e', 'QDRANT__SERVICE__HTTP_PORT=6333',
        '-e', 'QDRANT__SERVICE__GRPC_PORT=6334',
        'qdrant/qdrant:latest'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Qdrant restarted successfully")
        
        # Wait a moment for startup
        import time
        time.sleep(3)
        
        # Test connection
        test_connection()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Qdrant: {e}")
        print(f"Error output: {e.stderr}")

def test_connection():
    """Test Qdrant connection."""
    try:
        import requests
        response = requests.get("http://localhost:6333/collections", timeout=10)
        if response.status_code == 200:
            print("✅ Qdrant HTTP connection working")
        else:
            print(f"⚠️ Qdrant responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")

def update_qdrant_config():
    """Update application Qdrant configuration for HTTP-only."""
    config_file = Path("src/app/services/embeddings.py")
    
    if config_file.exists():
        content = config_file.read_text()
        
        # Replace HTTPS with HTTP if needed
        if "https://localhost:6333" in content:
            content = content.replace("https://localhost:6333", "http://localhost:6333")
            config_file.write_text(content)
            print("✅ Updated Qdrant configuration to use HTTP")
        else:
            print("ℹ️ Qdrant configuration already uses HTTP")

def main():
    """Main function to fix Qdrant issues."""
    print("🔧 Fixing Qdrant SSL/Connection Issues...")
    
    # Check if Docker is running
    try:
        subprocess.run(['docker', '--version'], capture_output=True, check=True)
        print("✅ Docker is available")
    except:
        print("❌ Docker is not available. Please install Docker first.")
        sys.exit(1)
    
    # Update configuration
    update_qdrant_config()
    
    # Restart Qdrant
    restart_qdrant()
    
    print("\n🎉 Qdrant fix completed!")
    print("💡 You can now restart your application and it should connect properly.")

if __name__ == "__main__":
    main() 