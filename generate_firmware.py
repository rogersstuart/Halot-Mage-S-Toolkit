import install_docker
import docker_start
import requests
import subprocess
import os
import time
import winreg as reg
import sys
import ctypes
import inspect

def get_caller_script():
    return os.path.abspath(__file__)

def main():
    install_docker.begin()

    python_exe = sys.executable
    caller_script = get_caller_script()
    script_key = "PreRunScriptExecuted"
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

    if has_ran == False:
        # Create or open the registry key for startup
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.SetValueEx(registry_key, "PreRunScript", 0, reg.REG_SZ, f'{python_exe} {caller_script}')
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

    else:
        # Remove the startup registry entry
        print("Removing script from Windows startup registry...")
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_WRITE)
            reg.DeleteValue(registry_key, "PreRunScript")
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


    docker_start.begin()

if __name__ == "__main__":
    main()