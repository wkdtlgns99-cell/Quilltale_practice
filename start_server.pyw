import os, subprocess, webbrowser, time
base_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(base_dir, '.venv', 'Scripts', 'pythonw.exe')
py_exe = venv_python if os.path.exists(venv_python) else 'pythonw'
subprocess.Popen([py_exe, 'app.py'], cwd=base_dir)
time.sleep(5)
webbrowser.open('http://127.0.0.1:7860')
