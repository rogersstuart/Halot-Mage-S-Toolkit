import subprocess
import sys
import winreg as reg
import ctypes
import os

IMAGE_NAME = "my-python-app"

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
    process = subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
    process.communicate()

    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}", file=sys.stderr)

def run_command_output(command):
    """Run a shell command and stream output in real-time."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}", file=sys.stderr)
        print(stderr, file=sys.stderr)
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
    host_output_dir = os.path.abspath("output")
    os.makedirs(host_output_dir, exist_ok=True)
    run_command(f'docker run -v "{host_output_dir}:/app/output" -it {IMAGE_NAME}')

if __name__ == "__main__":
    if not is_admin():
        print("This script requires administrator privileges. Relaunching with elevated permissions...")
        run_as_admin()
        sys.exit()  # Exit the current non-elevated script after relaunching with elevated permissions
    try:
        remove_old_containers()
        rebuild_docker()
        run_docker()
    except Exception as e:
        print(f"An error occurred: {e}")
        
    input("Press Enter to exit...")  # Keeps the console window open in case of an error