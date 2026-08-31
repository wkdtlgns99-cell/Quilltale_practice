import os
import sys
import time
import subprocess
import webbrowser

def kill_existing_server():
    """Kill any previous server instance locking port 7860"""
    try:
        cmd = "netstat -ano | findstr :7860"
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
        for line in output.strip().splitlines():
            if "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                time.sleep(0.5)
    except Exception:
        pass

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    kill_existing_server()
    
    # Prioritize .venv python if exists, otherwise fallback to current sys.executable
    venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable
    subprocess.run([python_exe, "app.py"])
