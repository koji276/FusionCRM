"""
FusionCRM - PicoCELA営業管理システム（リファクタリング版）
モジュール分離による保守性向上版
Version: 6.1 (2025年7月20日)
"""

import streamlit as st

# ページ設定
st.set_page_config(
    page_title="FusionCRM - PicoCELA営業管理システム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CRMモジュールのインポート
try:
    from crm_modules.google_sheets_api import (
        get_google_sheets_api, 
        setup_google_sheets_connection,
        show_connection_status
    )
    from crm_modules.company_manager import CompanyManager, EmailCampaignManager
    from crm_modules.crm_dashboard import show_dashboard, show_analytics, show_email_campaigns
    from crm_modules.data_import import show_data_import
    from crm_modules.ui_components import (
        show_company_management,
        show_sidebar_info,
        show_error_handling,
        render_navigation_menu,
        show_page_header,
        show_quick_stats
    )
except ImportError as e:
    st.error(f"❌ モジュールインポートエラー: {str(e)}")
    st.info("crm_modules/ ディレクトリとモジュールファイルが正しく配置されているか確認してください")
    st.stop()


def main():
    """メインアプリケーション"""
    
    # ページヘッダー
    show_page_header(
        "🚀 FusionCRM - PicoCELA営業管理システム",
        "**☁️ Google Sheets版（モジュール分離版）- Version 6.1**"
    )
    
    # Google Sheets API取得
    api = get_google_sheets_api()
    
    if api is None:
        setup_google_sheets_connection()
        return
    
    # 接続成功時の処理
    try:
        # マネージャー初期化
        company_manager = CompanyManager(api)
        email_manager = EmailCampaignManager(api)
        
        # サイドバー設定
        show_sidebar_info()
        
        # クイック統計表示
        with st.sidebar:
            with st.expander("📊 クイック統計"):
                show_quick_stats(company_manager)
        
        # ナビゲーション
        page = render_navigation_menu()
        
        # ページルーティング
        route_to_page(page, company_manager, email_manager)
        
    except Exception as e:
        show_error_handling(e, api)


def route_to_page(page, company_manager, email_manager):
    """ページルーティング"""
    
    if page == "📊 ダッシュボード":
        show_dashboard(company_manager)
        
    elif page == "🏢 企業管理":
        show_company_management(company_manager)
        
    elif page == "📧 メールキャンペーン":
        show_email_campaigns(email_manager, company_manager)
        
    elif page == "📈 分析・レポート":
        show_analytics(company_manager)
        
    elif page == "📁 データインポート":
        show_data_import(company_manager)
    
    else:
        st.error(f"❌ 不明なページ: {page}")


if __name__ == "__main__":
    main()
