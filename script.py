import os
import subprocess
import requests
import tarfile

# Constants
FIRMWARE_URL = "https://file2-cdn.creality.com/file/3909f9df226e771e9256718bff062c5d/V1_H2.228.1a2.228.1_C2.311.06_R2.230.tar.gz"
FIRMWARE_FILE = "firmware.tar.gz"
FIRMWARE_DIR = "extracted_files"
REPO_URL = "https://github.com/weashadow/UltraFirmwareToolkit.git"
REPO_DIR = "UltraFirmwareToolkit"

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

def clone_repository(repo_url, repo_dir):
    """Clone a GitHub repository if it hasn't been cloned yet."""
    if os.path.exists(repo_dir):
        print(f"Repository {repo_dir} already exists. Skipping clone.")
    else:
        print(f"Cloning repository {repo_url} into {repo_dir}...")
        run_command(f"git clone {repo_url} {repo_dir}")
        print("Clone complete.")

if __name__ == "__main__":
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
