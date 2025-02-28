import subprocess
import sys
import subprocess
import winreg as reg
import sys
import ctypes


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


def run_command(command, capture_output=False):
    """Run a shell command, streaming output unless capture_output=True."""
    if capture_output:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    else:
        process = subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
        process.communicate()

        if process.returncode != 0:
            print(f"Error: Command failed with exit code {process.returncode}", file=sys.stderr)

def image_exists():
    """Check if the Docker image already exists."""
    try:
        result = subprocess.run(
            f"docker images -q {IMAGE_NAME}",
            shell=True,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())  # If there's output, the image exists
    except Exception as e:
        print(f"Error checking Docker images: {e}", file=sys.stderr)
        return False
    
def get_image_hash():
    """Get the hash of the currently built image."""
    return run_command(f"docker inspect --format='{{{{.Id}}}}' {IMAGE_NAME}", capture_output=True) if image_exists() else None

def get_new_image_hash():
    """Build a new image in dry-run mode and get its hash without modifying the existing one."""
    return run_command(f"docker build --quiet .", capture_output=True)

def rebuild_docker():
    """Remove outdated image and rebuild the Docker container."""
    print("Removing outdated Docker image...")
    run_command(f"docker rmi -f {IMAGE_NAME}")
    
    print("Building updated Docker image...")
    run_command(f"docker build -t {IMAGE_NAME} .")
    print("Build complete.")

def build_docker_if_needed():
    """Check if the current image is up-to-date. If not, rebuild it."""
    if not image_exists():
        print("No existing image found. Building Docker image...")
        run_command(f"docker build -t {IMAGE_NAME} .")
        print("Build complete.")
    else:
        current_hash = get_image_hash()
        new_hash = get_new_image_hash()

        if current_hash != new_hash:
            print("Docker image is outdated. Rebuilding...")
            rebuild_docker()
        else:
            print("Docker image is up to date. No rebuild needed.")

def run_docker():
    """Run the Docker container."""
    print(f"Running Docker container: {IMAGE_NAME}...")
    run_command(f"docker run --rm {IMAGE_NAME}")

if __name__ == "__main__":
    if not is_admin():
        print("This script requires administrator privileges. Relaunching with elevated permissions...")
        run_as_admin()
        sys.exit()  # Exit the current non-elevated script after relaunching with elevated permissions
    try:
        build_docker_if_needed()
        run_docker()
    except Exception as e:
        print(f"An error occurred: {e}")
        
    input("Press Enter to exit...")  # Keeps the console window open in case of an error