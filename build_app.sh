#!/bin/bash
# Builds dist/HFPSelcallApp.app on a Mac (needs Python 3 from python.org and internet access).
set -e
cd "$(dirname "$0")"
python3 -m pip install --user -r requirements.txt pyinstaller pillow
python3 tests/test_combined.py
python3 tests/test_i18n.py
python3 tests/test_gui.py
python3 -m PyInstaller --noconfirm hfp_selcall_mac.spec
# ad-hoc signature so macOS asks for microphone permission for the app
codesign --force --deep --sign - dist/HFPSelcallApp.app || true
echo "Готово: dist/HFPSelcallApp.app"
