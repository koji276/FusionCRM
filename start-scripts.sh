# === start_fusioncrm.bat (Windows用) ===
@echo off
echo ========================================
echo FusionCRM - Starting...
echo ========================================

REM Pythonバージョンチェック
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM 起動スクリプト実行
python start_fusioncrm.py

pause

# === start_fusioncrm.sh (Mac/Linux用) ===
#!/bin/bash

echo "========================================"
echo "FusionCRM - Starting..."
echo "========================================"

# Pythonバージョンチェック
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# 実行権限を付与
chmod +x start_fusioncrm.py

# 起動スクリプト実行
python3 start_fusioncrm.py