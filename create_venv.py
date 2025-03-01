import os
import subprocess
import sys

def create_virtualenv(venv_name):
    """Create a virtual environment."""
    if not os.path.exists(venv_name):
        print(f"Creating virtual environment named {venv_name} in the current directory...")
        subprocess.run([sys.executable, "-m", "venv", venv_name], check=True)
        print("Virtual environment created.")
    else:
        print(f"Virtual environment named {venv_name} already exists in the current directory.")

def install_requirements(venv_name, requirements_file):
    """Install requirements in the virtual environment."""
    pip_executable = os.path.join(venv_name, "Scripts", "pip.exe") if os.name == "nt" else os.path.join(venv_name, "bin", "pip")
    print(f"Installing requirements from {requirements_file}...")
    subprocess.run([pip_executable, "install", "-r", requirements_file], check=True)
    print("Requirements installed.")

def main():
    current_dir = os.path.basename(os.getcwd())
    venv_name = current_dir  # Use the current directory name as the virtual environment name
    requirements_file = "requirements.txt"

    create_virtualenv(venv_name)
    install_requirements(venv_name, requirements_file)

if __name__ == "__main__":
    main()