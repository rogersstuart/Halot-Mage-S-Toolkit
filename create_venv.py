import os
import subprocess
import sys

def create_virtualenv(venv_dir):
    """Create a virtual environment."""
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        print("Virtual environment created.")
    else:
        print(f"Virtual environment already exists in {venv_dir}.")

def install_requirements(venv_dir, requirements_file):
    """Install requirements in the virtual environment."""
    pip_executable = os.path.join(venv_dir, "Scripts", "pip.exe") if os.name == "nt" else os.path.join(venv_dir, "bin", "pip")
    print(f"Installing requirements from {requirements_file}...")
    subprocess.run([pip_executable, "install", "-r", requirements_file], check=True)
    print("Requirements installed.")

def main():
    current_dir = os.path.basename(os.getcwd())
    venv_dir = os.path.join(os.getcwd(), current_dir)
    requirements_file = "requirements.txt"

    create_virtualenv(venv_dir)
    install_requirements(venv_dir, requirements_file)

if __name__ == "__main__":
    main()