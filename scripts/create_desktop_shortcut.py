import sys
import ctypes.wintypes
from pathlib import Path
import subprocess

CSIDL_DESKTOP = 0
buf = ctypes.create_unicode_buffer(520)
ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, 0, buf)
desktop_dir = Path(buf.value)

project_dir = Path("c:/Quilltale").resolve()
launcher_py = project_dir / "scripts" / "spectate_launcher.py"
icon_path = project_dir / "assets" / "icon.ico"

# 1. Create .bat launcher on desktop
bat_path = desktop_dir / "Quilltale_AI_관전.bat"
bat_content = f"@echo off\r\nchcp 65001 >nul\r\ncd /d \"{project_dir}\"\r\npython \"{launcher_py}\"\r\npause\r\n"
bat_path.write_text(bat_content, encoding="utf-8")

# 2. Create Windows Shortcut (.lnk)
lnk_path = desktop_dir / "Quilltale_AI_관전.lnk"
python_exe = sys.executable

ps_cmd = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{str(lnk_path)}')
$Shortcut.TargetPath = '{python_exe}'
$Shortcut.Arguments = '"{str(launcher_py)}"'
$Shortcut.WorkingDirectory = '{str(project_dir)}'
$Shortcut.Description = 'Quilltale TRPG - AI 자동 플레이 및 학습 데이터 수집 관전'
if (Test-Path '{str(icon_path)}') {{
    $Shortcut.IconLocation = '{str(icon_path)}'
}}
$Shortcut.Save()
"""
subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
print("Desktop shortcut created successfully!")
