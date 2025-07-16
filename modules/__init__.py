# FusionCRM Modules Package
"""
FusionCRM統合システムのモジュールパッケージ

このパッケージには以下のモジュールが含まれます：
- email_distribution: Gmail統合・メール配信機能
- database_manager: データベース管理機能
- data_processor: データ処理・分析機能
- auth_manager: 認証・ユーザー管理機能
"""

__version__ = "1.0.0"
__author__ = "PicoCELA Development Team"
__email__ = "tokuda@picocela.com"

# モジュールの初期化
import os
import sys

# パッケージのルートパスを取得
PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))

# 必要に応じてパスを追加
if PACKAGE_ROOT not in sys.path:
    sys.path.append(PACKAGE_ROOT)

# 共通設定
DEFAULT_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "database_name": "fusion_crm.db",
    "log_level": "INFO"
}

# エクスポートするクラス・関数
__all__ = [
    "email_distribution",
    "database_manager", 
    "data_processor",
    "auth_manager"
]

# バージョン情報表示
def show_version():
    """FusionCRMモジュールのバージョン情報を表示"""
    print(f"FusionCRM Modules v{__version__}")
    print(f"Developed by {__author__}")
    print(f"Contact: {__email__}")

# モジュール読み込み時の初期化処理
def initialize_modules():
    """モジュール初期化処理"""
    try:
        # ログ設定
        import logging
        logging.basicConfig(
            level=getattr(logging, DEFAULT_CONFIG["log_level"]),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 初期化完了メッセージ
        logger = logging.getLogger(__name__)
        logger.info("FusionCRM modules initialized successfully")
        
    except Exception as e:
        print(f"Warning: Module initialization failed: {e}")

# 自動初期化実行
initialize_modules()
