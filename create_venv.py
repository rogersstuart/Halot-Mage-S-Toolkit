import os
import subprocess
import sys

def create_virtualenv(venv_name):
    """Create a virtual environment."""
    if not os.path.exists(venv_name):
        print(f"Creating virtual environment named {venv_name} in the current directory...")
        subprocess.run([sys.executable, "-m", "venv", "."], check=True)
        print("Virtual environment created.")
    else:
        print(f"Virtual environment named {venv_name} already exists in the current directory.")

def install_requirements(venv_name, requirements_file):
    """Install requirements in the virtual environment."""
    if os.name == "nt":
        activate_script = os.path.join("Scripts", "activate.bat")
        pip_executable = os.path.join("Scripts", "pip.exe")
    else:
        activate_script = os.path.join("bin", "activate")
        pip_executable = os.path.join("bin", "pip")

    print(f"Activating virtual environment using {activate_script}...")
    activate_command = f"{activate_script} && {pip_executable} install -r {requirements_file}"
    subprocess.run(activate_command, shell=True, check=True)
    print("Requirements installed.")

def detect_shell():
    """Detect the shell being used (PowerShell, CMD, or Linux shell)."""
    if os.name == "nt":
        parent_process = os.environ.get("COMSPEC", "").lower()
        if "powershell" in parent_process:
            return "powershell"
        else:
            return "cmd"
    else:
        return "linux"
    
def activate_virtualenv(shell):
    """Activate the virtual environment based on the shell."""
    if shell == "powershell":
        activate_command = f".\\Scripts\\Activate.ps1"
    elif shell == "cmd":
        activate_command = f"Scripts\\activate.bat"
    else:  # Linux shell
        activate_command = f"source bin/activate"

    print(f"Activating virtual environment using {activate_command}...")
    subprocess.run(activate_command, shell=True, check=True)
    print("Virtual environment activated.")

def main():
    current_dir = os.path.basename(os.getcwd())
    venv_name = current_dir  # Use the current directory name as the virtual environment name
    requirements_file = "requirements.txt"

    create_virtualenv(venv_name)
    install_requirements(venv_name, requirements_file)

    shell = detect_shell()
    print_activation_command(shell, venv_name)

if __name__ == "__main__":
    main()