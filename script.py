import os
import subprocess
import requests
import tarfile
import shutil
import sys
import extract_apps

# Constants
FIRMWARE_URL = "https://file2-cdn.creality.com/file/3909f9df226e771e9256718bff062c5d/V1_H2.228.1a2.228.1_C2.311.06_R2.230.tar.gz"
FIRMWARE_FILE = "firmware.tar.gz"
FIRMWARE_DIR = "extracted_files"
REPO_URL = "https://github.com/weashadow/UltraFirmwareToolkit.git"
REPO_DIR = "UltraFirmwareToolkit"
OUTPUT_DIR = "/app/output"
FIRMWARE_OUTPUT_DIR = "output/firmware"

def run_command(command):
    """Run a shell command and ensure it executes successfully."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing command: {command}\n{result.stderr}")
        exit(1)

def run_command_output(command):
    """Run a shell command and stream output in real-time."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    
    stderr = process.stderr.read()
    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}", file=sys.stderr)
        print(stderr, file=sys.stderr)
    return process.returncode

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
        run_command_output(f"cd {scripts_dir} && ./extract.sh")
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

def run_build_script():
    """Run build.sh in the UltraFirmwareToolkit/scripts directory."""
    scripts_dir = os.path.join(REPO_DIR, "scripts")
    build_script = os.path.join(scripts_dir, "build.sh")
    automated_build_script = "/app/run_build.sh"
    print("\nRunning build.sh...")
    if os.path.exists(build_script):
        # Make sure the script is executable
        os.chmod(build_script, 0o755)
        os.chmod(automated_build_script, 0o755)
        run_command(f"expect {automated_build_script} {scripts_dir}")
        print("Build complete")
    else:
        print(f"Error: {build_script} not found")
        exit(1)

def copy_firmware_to_host():
    """Copy ChituUpgrade.bin.out from the scripts directory to the host, rename it to ChituUpgrade.bin, and put it in a folder called firmware."""
    scripts_dir = os.path.join(REPO_DIR, "scripts")
    src_file = os.path.join(scripts_dir, "ChituUpgrade.bin.out")
    dest_dir = os.path.join(os.getcwd(), FIRMWARE_OUTPUT_DIR)
    dest_file = os.path.join(dest_dir, "ChituUpgrade.bin")

    if os.path.exists(src_file):
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        print(f"Copied and renamed {src_file} to {dest_file}")
    else:
        print(f"Error: {src_file} not found")
        exit(1)

if __name__ == "__main__":
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Download and extract firmware
    download_file(FIRMWARE_URL, FIRMWARE_FILE)
    extract_tar(FIRMWARE_FILE, FIRMWARE_DIR)

    # Clone the GitHub repository
    clone_repository(REPO_URL, REPO_DIR)

    # List extracted files
    #print("\nExtracted Firmware Files:")
    #for root, dirs, files in os.walk(FIRMWARE_DIR):
    #    for file in files:
    #        print(os.path.join(root, file))

    # List cloned repository contents
    #print("\nCloned Repository Files:")
    #for root, dirs, files in os.walk(REPO_DIR):
    #    for file in files:
    #        print(os.path.join(root, file))

    # Copy files and run extract.sh
    copy_and_extract()

    extract_apps.extract_apps()

    remove_sudo_from_script(os.path.join(REPO_DIR, "scripts", "build.sh"))
    run_build_script()

    copy_firmware_to_host()