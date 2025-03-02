import shutil
import subprocess
import sys
from token import GREATER
import winreg as reg
import ctypes
import os

IMAGE_NAME = "generate-firmware"
DOCKERFILE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory where the Dockerfile is located

def run_subprocess_in_venv(command):
    """Run a subprocess command using the virtual environment's Python interpreter."""
    dir_name = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(dir_name, "Scripts")
    python_executable = os.path.join(venv_path, "python.exe") if os.name == "nt" else os.path.join(venv_path, "python")
    full_command = [python_executable] + command
    subprocess.run(full_command, check=True)

def is_admin():
    """ Check if the script is running as an administrator """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        print(f"Error checking for admin status: {e}")
        return False

def run_as_admin():
    """ Relaunch the script with admin privileges """
    pypath = sys.executable
    print(pypath)
    isinstaller = True
    if pypath.endswith("pythonw.exe") or pypath.endswith("python.exe"):
        isinstaller = False

    print("relaunching with admin privileges")
    script = sys.argv[0]  # Get the script name
    print(script)
    params = " ".join(sys.argv[1:])  # Join all additional arguments
    # Run the script using PowerShell with elevated privileges
    if isinstaller:
        script = pypath
        subprocess.run(["powershell", "-Command", f"Start-Process '{script}' -Verb runAs"])
    else:
        subprocess.run(["powershell", "-Command", f"Start-Process '{pypath}' '{script}' -Verb runAs"])

def run_command(command):
    """Run a shell command and stream output in real time."""
    process = subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr, text=True, cwd=DOCKERFILE_DIR)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}", file=sys.stderr)
        print(stderr, file=sys.stderr)
        raise Exception(f"Error: Command failed with exit code {process.returncode}")

def run_command_output(command):
    """Run a shell command and stream output in real-time."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=DOCKERFILE_DIR)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}", file=sys.stderr)
        print(stderr, file=sys.stderr)
        raise Exception(f"Error: Command failed with exit code {process.returncode}")
    
    return stdout.strip()

def remove_old_containers():
    """Stop and remove all containers with the specified image name."""
    print(f"Checking for existing containers with image '{IMAGE_NAME}'...")
    all_containers = run_command_output("docker ps -a")
    print(all_containers)
    container_ids = [line.split()[0] for line in all_containers.splitlines() if IMAGE_NAME in line]

    if container_ids:
        print(f"Removing existing containers with image: {IMAGE_NAME}...")
        for container_id in container_ids:
            print(f"Stopping container {container_id}...")
            run_command(f"docker stop {container_id}")
            print(f"Removing container {container_id}...")
            run_command(f"docker rm {container_id}")
        print("Old containers removed.")
    else:
        print("No existing containers found.")

def remove_old_images():
    """Remove all images with the specified name."""
    print(f"Checking for existing images named '{IMAGE_NAME}'...")
    existing_images = run_command(f"docker images -q {IMAGE_NAME}")

    if existing_images:
        print(f"Removing existing images named: {IMAGE_NAME}...")
        image_ids = existing_images.splitlines()
        for image_id in image_ids:
            run_command(f"docker rmi -f {image_id}")
        print("Old images removed.")
    else:
        print("No existing images found.")

def rebuild_docker():
    """Remove the old image and rebuild the Docker container."""
    remove_old_images()

    print("Building new Docker image...")
    run_command(f"docker build -t {IMAGE_NAME} .")
    print("Build complete.")

def run_docker():
    """Run the Docker container."""
    print(f"Running Docker container: {IMAGE_NAME}...")
    
    basedir = os.path.dirname(__file__)
    print(basedir)
    host_output_dir = basedir + "\\output"
    if(os.path.exists(host_output_dir)):
        shutil.rmtree(host_output_dir)
    os.makedirs(host_output_dir, exist_ok=True)

    retries = 3
    while retries > 0:
        try:
            run_command(f'docker run -v "{host_output_dir}:/app/output" -it {IMAGE_NAME}')
            retries -= 1
            break
        except Exception as e:
            print(f"An error occurred while running the Docker container: {e}")

def clean_docker_system():
    """Clean up Docker system to remove unused data."""
    print("Cleaning up Docker system...")
    run_command("docker system prune -a --volumes -f")
    print("Docker system cleanup complete.")

def begin():
    if not is_admin():
        print("This script requires administrator privileges. Relaunching with elevated permissions...")
        run_as_admin()
        sys.exit()  # Exit the current non-elevated script after relaunching with elevated permissions
    try:
        remove_old_containers()
        clean_docker_system()
        rebuild_docker()
        run_docker()
        remove_old_containers()
        clean_docker_system()
    except Exception as e:
        print(f"An error occurred: {e}")
        
    input("Press Enter to exit...")  # Keeps the console window open in case of an error

if __name__ == "__main__":
    begin()