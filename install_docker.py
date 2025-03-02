import requests
import subprocess
import os
import time
import winreg as reg
import sys
import ctypes
import inspect
import psutil

from yarg import get

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


def check_wsl_installed(caller_script):
    """ Check if WSL is installed and WSL 2 is set as default """
    try:
        # Check if WSL is installed and verify the version
        output = subprocess.check_output(["wsl", "--list", "--verbose"], text=True)
        print("WSL is installed. Verifying WSL version...")
        if "2" not in output:
            print("WSL 2 is not set as the default version. Setting WSL 2 as default...")
            subprocess.run(["wsl", "--set-default-version", "2"], check=True)
            print("WSL 2 set as default version.")
        else:
            print("WSL 2 is already the default version.")
    except Exception as e:
        print("WSL is not installed. Installing WSL...")
        install_wsl(caller_script)

    return True

def monitor_windows_modules_installer():
    """ Monitor the Windows Modules Installer Worker (TiWorker.exe) """
    try:
        # Find the process ID of the TiWorker.exe process
        tiworker_process = None
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'].lower() == 'tiworker.exe':
                tiworker_process = proc
                break
        
        if not tiworker_process:
            sys.stdout.write("\n[Monitoring] TiWorker.exe not found.\n")
            sys.stdout.flush()
            return

        # Monitor the CPU and memory usage of TiWorker.exe
        while tiworker_process.is_running():
            cpu_usage = tiworker_process.cpu_percent(interval=1)
            mem_usage = tiworker_process.memory_info().rss / (1024 * 1024)  # Convert to MB
            children = tiworker_process.children(recursive=True)  # Get subprocesses

            # Update monitoring output for TiWorker.exe
            sys.stdout.write(f"\r[Monitoring TiWorker] CPU: {cpu_usage:.2f}% | Memory: {mem_usage:.2f}MB | Subprocesses: {len(children)}   ")
            sys.stdout.flush()
            time.sleep(1)

    except psutil.NoSuchProcess:
        sys.stdout.write("\n[Monitoring] TiWorker.exe process ended.\n")
        sys.stdout.flush()

def enable_wsl_features():
    commands = [
        "wsl --install"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Start monitoring TiWorker.exe in a separate thread
        monitor_thread = threading.Thread(target=monitor_windows_modules_installer)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Handle subprocess output while TiWorker.exe is running
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                sys.stdout.write(f"\r{output.strip()}   ")  # Overwrites the current output line with subprocess stdout
                sys.stdout.flush()
        
        stderr_output = process.stderr.read()
        if stderr_output:
            print("\nError:", stderr_output)


def install_wsl(caller_script):
    script_key = "WSLInstallScriptExecuted"
    has_ran = False


    """ Install WSL and set it to version 2 """
    print("Enabling Windows Subsystem for Linux (WSL) and Virtual Machine Platform...")
    #subprocess.run(["powershell", "wsl --install"], check=True)
    enable_wsl_features()
    print("WSL installation complete. Rebooting system to finalize installation.")

    # Add the script to the startup registry key
    print("Adding script to Windows startup...")

    # Get the full path of the Python executable currently in use
    python_exe = sys.executable  # This gives you the exact path of the python interpreter

    # Create or open the registry key for startup
    try:
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, "WSLInstallScript", 0, reg.REG_SZ, f'{python_exe} {caller_script}')
        reg.CloseKey(registry_key)
        print("Script added to Windows startup successfully.")
    except Exception as e:
        print(f"Error adding script to Windows startup: {e}")

     # Now that the script has run, add a registry entry to mark that it has executed
    print("Marking the script as executed in the registry...")
    try:
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, script_key, 0, reg.REG_SZ, "Executed")
        reg.CloseKey(registry_key)
        print("Script marked as executed.")
    except Exception as e:
        print(f"Error marking script as executed in the registry: {e}")


    subprocess.run(["shutdown", "/r", "/t", "5"], check=True)

def install_docker(caller_script):
    # Check if the script has already run before by checking a registry value
    script_key = "DockerInstallScriptExecuted"
    has_ran = False

    try:
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_READ)
        # Try to read the registry value to see if the script has been run before
        reg.QueryValueEx(registry_key, script_key)
        reg.CloseKey(registry_key)
        print("Script has already run before. Exiting.")
        has_ran = True
    except FileNotFoundError:
        # This means the registry key doesn't exist, so the script hasn't run before
        pass

    if not has_ran:
        docker_url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        installer_path = "DockerDesktopInstaller.exe"

        # Check if Docker is already installed
        try:
            print("Checking if Docker is already installed...")
            output = subprocess.check_output(["docker", "--version"], text=True)
            print(f"Docker is already installed: {output}")
            return
        except:
            print("Docker is not installed. Proceeding with installation...")

        # Download Docker Desktop
        print("Downloading Docker Desktop...")
        response = requests.get(docker_url, stream=True)
        with open(installer_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print("Docker Desktop downloaded.")

        # Install Docker Desktop silently
        print("Installing Docker Desktop...")
        subprocess.run([installer_path, "install", "--quiet", "--accept-license"], check=True)  # No need for --quiet, "install" is sufficient
        print("Docker Desktop installed.")
        os.remove(installer_path)

        try:
            # Add user to docker-users group
            username = os.getlogin()
            print(f"Adding user {username} to docker-users group...")
            subprocess.run(["net", "localgroup", "docker-users", username, "/add"], check=True)
            print(f"User {username} added to docker-users group.")
        except:
            print("Error adding user to docker-users group.")

        # Manually update the PATH environment variable
        docker_path = r"C:\Program Files\Docker\Docker\resources\bin"
        os.environ["PATH"] += os.pathsep + docker_path

        # Verify Docker installation
        print("Verifying Docker installation...")
        try:
            output = subprocess.check_output(["docker", "--version"], text=True)
            print("Docker installation verified:")
            print(output)
        except Exception as e:
            print(f"Error verifying Docker installation: {e}")

        # Add the script to the startup registry key
        print("Adding script to Windows startup...")

        # Get the full path of the Python executable currently in use
        python_exe = sys.executable  # This gives you the exact path of the python interpreter

        # Create or open the registry key for startup
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.SetValueEx(registry_key, "DockerInstallScript", 0, reg.REG_SZ, f'{python_exe} {caller_script}')
            reg.CloseKey(registry_key)
            print("Script added to Windows startup successfully.")
        except Exception as e:
            print(f"Error adding script to Windows startup: {e}")

        # Now that the script has run, add a registry entry to mark that it has executed
        print("Marking the script as executed in the registry...")
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.SetValueEx(registry_key, script_key, 0, reg.REG_SZ, "Executed")
            reg.CloseKey(registry_key)
            print("Script marked as executed.")
        except Exception as e:
            print(f"Error marking script as executed in the registry: {e}")

        # Restart the system
        print("Restarting the system...")
        subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
        print("System is restarting. Please wait...")
        time.sleep(60)  # Wait for restart
    else:
        # Remove the startup registry entry
        print("Removing script from Windows startup registry...")
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.DeleteValue(registry_key, "DockerInstallScript")
            reg.CloseKey(registry_key)
            print("Script removed from Windows startup registry.")
        except Exception as e:
            print(f"Error removing script from Windows startup registry: {e}")

         # Now that the script has run, add a registry entry to mark that it has executed
        print("Removing flag from registry...")
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.DeleteValue(registry_key, script_key)
            reg.CloseKey(registry_key)
            print("Flag removed.")
        except Exception as e:
            print(f"Error unmarking script as executed in the registry: {e}")

        start_docker_desktop()

def get_caller_script():
    """ Get the script that called the current function """
    frame = inspect.currentframe()
    caller_frame = frame.f_back.f_back  # Go back two frames to get the caller
    caller_script = caller_frame.f_globals["__file__"]
    return os.path.abspath(caller_script)
    
def start_docker_desktop():
    docker_desktop_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"

    if os.path.exists(docker_desktop_path):
        print("Starting Docker Desktop...")
        subprocess.Popen([docker_desktop_path])
        time.sleep(30)  # Wait for Docker Desktop to start
        print("Docker Desktop started.")
    else:
        print(f"Docker Desktop not found at {docker_desktop_path}")

def remove_startup_registry_entry_wsl():
     # Remove the startup registry entry
    script_key = "WSLInstallScriptExecuted"
    print("Removing script from Windows startup registry...")
    try:
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
        reg.DeleteValue(registry_key, "WSLInstallScript")
        reg.CloseKey(registry_key)
        print("Script removed from Windows startup registry.")
    except Exception as e:
        print(f"Error removing script from Windows startup registry: {e}")

        # Now that the script has run, add a registry entry to mark that it has executed
    print("Removing flag from registry...")
    try:
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
        reg.DeleteValue(registry_key, script_key)
        reg.CloseKey(registry_key)
        print("Flag removed.")
    except Exception as e:
        print(f"Error unmarking script as executed in the registry: {e}")

def begin():
    # Step 1: Request elevated permissions if not running as admin
    if not is_admin():
        print("This script requires administrator privileges. Relaunching with elevated permissions...")
        run_as_admin()
        sys.exit()  # Exit the current non-elevated script after relaunching with elevated permissions

    try:
        has_rebooted = False

        script_key = "WSLInstallScriptExecuted"
        has_ran = False

        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_READ)
            # Try to read the registry value to see if the script has been run before
            reg.QueryValueEx(registry_key, script_key)
            reg.CloseKey(registry_key)
            print("Script has already run before. Exiting.")
            has_ran = True
        except FileNotFoundError:
            # This means the registry key doesn't exist, so the script hasn't run before
            pass

        caller_script = get_caller_script()
        print(f"Caller script: {caller_script}")

        if has_ran:
            remove_startup_registry_entry_wsl()

        if has_ran == True:
            # Step 3: Install Docker Desktop if not already done

            
            install_docker(caller_script)
        else:
             install_wsl(caller_script)

    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...")  # Keeps the console window open in case of an error