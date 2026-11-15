@echo off
rem Builds HFPSelcallApp (folder dist\HFPSelcallApp). For Windows 7 use Python 3.8 (32 or 64 bit, matching the PC).
cd /d "%~dp0"
py -m pip install -r requirements.txt "pyinstaller==5.13.2"
py -m PyInstaller --noconfirm --onedir --windowed --name HFPSelcallApp --collect-all sounddevice --hidden-import hfpager_modem --hidden-import hfpager_rx --hidden-import hfpager_ptt --hidden-import hfpager_rig --hidden-import selcall --hidden-import selcall_engine --hidden-import serial.tools.list_ports hfp_selcall_app.py
echo.
echo Done: dist\HFPSelcallApp\HFPSelcallApp.exe
pause
