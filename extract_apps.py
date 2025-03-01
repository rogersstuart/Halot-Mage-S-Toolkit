import os
import tarfile
import shutil

# Constants
APPS_FILE = "apps.tar.gz"
APPS_DIR = "apps_temp"  # Temporary directory for extraction
REPO_DIR = "UltraFirmwareToolkit"
SCRIPTS_DIR = os.path.join(REPO_DIR, "scripts")

def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree, overwriting existing files."""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                os.makedirs(d)
            copytree(s, d, symlinks, ignore)
        else:
            if os.path.exists(d):
                os.remove(d)
            shutil.copy2(s, d)

def extract_apps():
    """Extract apps.tar.gz and copy contents to UltraFirmwareToolkit/scripts/"""
    print(f"\nExtracting {APPS_FILE}...")
    
    # Create temporary directory for extraction
    os.makedirs(APPS_DIR, exist_ok=True)
    
    # Extract apps.tar.gz
    with tarfile.open(APPS_FILE, 'r:gz') as tar:
        tar.extractall(APPS_DIR)
    
    # Copy contents to scripts directory
    print(f"Copying apps contents to {SCRIPTS_DIR}...")
    
    # Ensure scripts directory exists
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    # Copy all extracted files to scripts directory
    for item in os.listdir(APPS_DIR):
        src = os.path.join(APPS_DIR, item)
        dst = os.path.join(SCRIPTS_DIR, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Copied {item}")
        elif os.path.isdir(src):
            copytree(src, dst, symlinks=True)
            print(f"Copied directory {item}")
    
    # Clean up temporary directory
    shutil.rmtree(APPS_DIR)
    print("Cleanup complete")

if __name__ == "__main__":
    extract_apps()