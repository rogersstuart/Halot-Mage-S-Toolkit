import os
import subprocess
import requests
import tarfile
import shutil

# Constants
FIRMWARE_URL = "https://file2-cdn.creality.com/file/3909f9df226e771e9256718bff062c5d/V1_H2.228.1a2.228.1_C2.311.06_R2.230.tar.gz"
FIRMWARE_FILE = "firmware.tar.gz"
FIRMWARE_DIR = "extracted_files"
REPO_URL = "https://github.com/weashadow/UltraFirmwareToolkit.git"
REPO_DIR = "UltraFirmwareToolkit"
OUTPUT_DIR = "/app/output"

def run_command(command):
    """Run a shell command and ensure it executes successfully."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}\n{result.stderr}")
        exit(1)

def download_file(url, filename):
    """Download a file from a given URL and save it locally."""
    print(f"Downloading {url}...")
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download file. HTTP Status: {response.status_code}")
        exit(1)

def extract_tar(filename, extract_to):
    """Extract a .tar.gz archive to the specified directory."""
    print(f"Extracting {filename} to {extract_to}...")
    os.makedirs(extract_to, exist_ok=True)
    
    with tarfile.open(filename, "r:gz") as tar:
        tar.extractall(path=extract_to)
    
    print(f"Extraction complete. Files saved in {extract_to}")

def remove_sudo_from_script(script_path):
    """Remove all instances of 'sudo' from the script file."""
    print(f"Removing sudo from {script_path}...")
    
    # Read the file
    with open(script_path, 'r') as file:
        content = file.read()
    
    # Remove all instances of 'sudo'
    modified_content = content.replace('sudo ', '')
    
    # Write back to file
    with open(script_path, 'w') as file:
        file.write(modified_content)
    print("Removed sudo from script")

def copy_and_extract():
    """Copy firmware files to UltraFirmwareToolkit/scripts and run extract.sh"""
    scripts_dir = os.path.join(REPO_DIR, "scripts")
    print(f"\nCopying firmware files to {scripts_dir}...")
    
    # Make sure scripts directory exists
    os.makedirs(scripts_dir, exist_ok=True)
    
    # Copy all files from extracted_files to scripts directory
    for item in os.listdir(FIRMWARE_DIR):
        src = os.path.join(FIRMWARE_DIR, item)
        dst = os.path.join(scripts_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Copied {item}")
    
    # Run extract.sh
    print("\nRunning extract.sh...")
    extract_script = os.path.join(scripts_dir, "extract.sh")
    if os.path.exists(extract_script):
        # Make sure the script is executable
        os.chmod(extract_script, 0o755)
        run_command(f"cd {scripts_dir} && ./extract.sh")
        print("Extraction complete")
    else:
        print(f"Error: {extract_script} not found")
        exit(1)

    # Run extract_partition.sh
    print("\nRunning extract_partition.sh...")
    extract_script = os.path.join(scripts_dir, "extract_partition.sh")
    if os.path.exists(extract_script):
        # Make sure the script is executable
        remove_sudo_from_script(extract_script)
        os.chmod(extract_script, 0o755)
        run_command(f"cd {scripts_dir} && ./extract_partition.sh")
        print("Extraction complete")
    else:
        print(f"Error: {extract_script} not found")
        exit(1)

def clone_repository(repo_url, repo_dir):
    """Clone a GitHub repository if it hasn't been cloned yet."""
    if os.path.exists(repo_dir):
        print(f"Repository {repo_dir} already exists. Skipping clone.")
    else:
        print(f"Cloning repository {repo_url} into {repo_dir}...")
        run_command(f"git clone {repo_url} {repo_dir}")
        print("Clone complete.")

if __name__ == "__main__":
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Download and extract firmware
    download_file(FIRMWARE_URL, FIRMWARE_FILE)
    extract_tar(FIRMWARE_FILE, FIRMWARE_DIR)

    # Clone the GitHub repository
    clone_repository(REPO_URL, REPO_DIR)

    # List extracted files
    print("\nExtracted Firmware Files:")
    for root, dirs, files in os.walk(FIRMWARE_DIR):
        for file in files:
            print(os.path.join(root, file))

    # List cloned repository contents
    print("\nCloned Repository Files:")
    for root, dirs, files in os.walk(REPO_DIR):
        for file in files:
            print(os.path.join(root, file))

    # Copy files and run extract.sh
    copy_and_extract()

     # Copy files to output directory
    print("\nCopying files to output directory...")
    import shutil
    
    # Copy firmware files
    firmware_output = os.path.join(OUTPUT_DIR, "firmware")
    shutil.copytree(FIRMWARE_DIR, firmware_output, dirs_exist_ok=True)
    
    # Copy repository files
    repo_output = os.path.join(OUTPUT_DIR, "repo")
    shutil.copytree(REPO_DIR, repo_output, dirs_exist_ok=True)
