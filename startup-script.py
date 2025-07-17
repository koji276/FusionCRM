#!/usr/bin/env python3
"""
FusionCRM 簡単起動スクリプト
初回セットアップと起動を自動化
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_python_version():
    """Pythonバージョンチェック"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8以上が必要です")
        print(f"現在のバージョン: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} 検出")
    return True

def check_and_install_requirements():
    """依存関係のチェックとインストール"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ requirements.txtが見つかりません")
        return False
    
    print("📦 依存関係をチェック中...")
    
    try:
        # pipのアップグレード
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # requirements.txtからインストール
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依存関係のインストール完了")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依存関係のインストールに失敗しました")
        return False

def setup_streamlit_config():
    """Streamlit設定ファイルの作成"""
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)
    
    # config.tomlの作成
    config_file = streamlit_dir / "config.toml"
    if not config_file.exists():
        config_content = """[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
headless = false
port = 8501

[browser]
gatherUsageStats = false
"""
        config_file.write_text(config_content)
        print("✅ Streamlit設定ファイルを作成しました")
    
    # secrets.tomlのチェック
    secrets_file = streamlit_dir / "secrets.toml"
    if not secrets_file.exists():
        print("\n⚠️  Google Apps Script URLの設定が必要です")
        print("以下の手順で設定してください：")
        print("1. Google Apps Scriptをデプロイ")
        print("2. 取得したURLを .streamlit/secrets.toml に保存")
        print("   例: google_apps_script_url = \"https://script.google.com/macros/s/xxx/exec\"")
        
        create_secrets = input("\n今すぐ設定しますか？ (y/n): ")
        if create_secrets.lower() == 'y':
            gas_url = input("Google Apps Script URL: ").strip()
            if gas_url:
                secrets_content = f'google_apps_script_url = "{gas_url}"'
                secrets_file.write_text(secrets_content)
                print("✅ secrets.tomlを作成しました")
            else:
                print("⚠️  URLが入力されませんでした。後で設定してください")

def check_files():
    """必要なファイルの存在確認"""
    required_files = [
        "fusion_crm_main.py",
        "company_management_module.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ 以下のファイルが見つかりません:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 必要なファイルを確認しました")
    return True

def start_app():
    """Streamlitアプリの起動"""
    print("\n🚀 FusionCRMを起動しています...")
    print("ブラウザが自動的に開きます")
    print("終了するには Ctrl+C を押してください\n")
    
    # ブラウザを自動的に開く
    import time
    import threading
    
    def open_browser():
        time.sleep(3)  # Streamlitが起動するまで待機
        webbrowser.open('http://localhost:8501')
    
    threading.Thread(target=open_browser).start()
    
    # Streamlitを起動
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "fusion_crm_main.py"])
    except KeyboardInterrupt:
        print("\n\n✅ FusionCRMを終了しました")

def main():
    """メイン処理"""
    print("=" * 50)
    print("🎯 FusionCRM セットアップ & 起動")
    print("=" * 50)
    
    # チェック処理
    if not check_python_version():
        return
    
    if not check_files():
        return
    
    if not check_and_install_requirements():
        return
    
    setup_streamlit_config()
    
    # 起動確認
    print("\n" + "=" * 50)
    start_confirm = input("FusionCRMを起動しますか？ (y/n): ")
    
    if start_confirm.lower() == 'y':
        start_app()
    else:
        print("\n起動をキャンセルしました")
        print("手動で起動する場合: streamlit run fusion_crm_main.py")

if __name__ == "__main__":
    main()