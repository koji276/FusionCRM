"""
CRM UI コンポーネントモジュール
fusion_crm_main.pyから抽出
"""

import streamlit as st
import time
from .constants import SALES_STATUS


def show_company_management(company_manager):
    """企業管理"""
    st.header("🏢 企業管理")
    
    tab1, tab2 = st.tabs(["📝 企業追加", "📋 企業一覧"])
    
    with tab1:
        show_company_form(company_manager)
    
    with tab2:
        show_company_list(company_manager)


def show_company_form(company_manager):
    """企業追加フォーム"""
    st.subheader("新規企業追加")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("企業名*", placeholder="例: 株式会社サンプル")
            email = st.text_input("メールアドレス", placeholder="contact@example.com")
            industry = st.text_input("業界", placeholder="建設業")
        
        with col2:
            phone = st.text_input("電話番号", placeholder="03-1234-5678")
            website_url = st.text_input("ウェブサイト", placeholder="https://example.com")
            source = st.selectbox("情報源", ["Manual", "ENR Import", "Web Research", "Referral"])
        
        notes = st.text_area("備考・メモ", placeholder="企業の特徴、WiFi需要、その他重要な情報")
        
        submitted = st.form_submit_button("🏢 企業を追加", type="primary", use_container_width=True)
        
        if submitted:
            if company_name:
                company_data = {
                    'company_name': company_name,
                    'email': email,
                    'phone': phone,
                    'website_url': website_url,
                    'industry': industry,
                    'notes': notes,
                    'source': source
                }
                
                with st.spinner("企業を追加中..."):
                    company_id = company_manager.add_company(company_data, 'user')
                
                if company_id:
                    st.success(f"✅ 企業「{company_name}」を追加しました！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 企業追加に失敗しました")
            else:
                st.error("❌ 企業名は必須です")


def show_company_list(company_manager):
    """企業一覧表示"""
    st.subheader("企業一覧")
    
    companies_df = company_manager.get_all_companies()
    
    if not companies_df.empty:
        # フィルター
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "ステータスフィルター",
                ["すべて"] + list(SALES_STATUS.keys())
            )
        
        with col2:
            wifi_filter = st.selectbox(
                "WiFi需要フィルター",
                ["すべて", "WiFi必要", "WiFi不要"]
            )
        
        # フィルタリング適用
        filtered_df = companies_df.copy()
        
        if status_filter != "すべて" and 'sales_status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sales_status'] == status_filter]
        
        if wifi_filter != "すべて" and 'wifi_required' in filtered_df.columns:
            wifi_value = 1 if wifi_filter == "WiFi必要" else 0
            filtered_df = filtered_df[filtered_df['wifi_required'] == wifi_value]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # ステータス更新機能
        if not filtered_df.empty:
            show_status_update_form(company_manager, filtered_df)
    else:
        st.info("企業データがありません。まず企業を追加してください。")


def show_status_update_form(company_manager, companies_df):
    """ステータス更新フォーム"""
    st.subheader("📈 ステータス更新")
    
    with st.form("update_status_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_options = companies_df['company_name'].tolist() if 'company_name' in companies_df.columns else []
            selected_company = st.selectbox("企業選択", company_options)
        
        with col2:
            new_status = st.selectbox("新しいステータス", list(SALES_STATUS.keys()))
        
        with col3:
            notes = st.text_input("更新理由・備考")
        
        if st.form_submit_button("📈 ステータス更新", type="primary"):
            if selected_company:
                # 企業IDを取得
                company_row = companies_df[companies_df['company_name'] == selected_company].iloc[0]
                company_id = company_row.get('company_id', company_row.get('id'))
                
                with st.spinner("ステータス更新中..."):
                    success = company_manager.update_status(company_id, new_status, 'user', notes=notes)
                
                if success:
                    st.success(f"✅ {selected_company}のステータスを{SALES_STATUS[new_status]}に更新しました")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ ステータス更新に失敗しました")


def show_sidebar_info():
    """サイドバー情報表示"""
    st.sidebar.title("🌟 FusionCRM")
    st.sidebar.markdown("☁️ **Google Sheets版 v6.1**")
    
    # 接続状況表示
    show_connection_status()
    
    # 統計情報
    with st.sidebar.expander("📊 クイック統計"):
        st.info("統計情報はダッシュボードで確認できます")


def show_connection_status():
    """接続状況表示"""
    if 'google_apps_script_url' in st.secrets:
        st.sidebar.success("🔒 管理者設定済み")
    elif 'gas_url' in st.session_state:
        st.sidebar.success("✅ 接続済み")
        if st.sidebar.button("🔌 切断"):
            del st.session_state.gas_url
            if 'last_attempted_url' in st.session_state:
                del st.session_state.last_attempted_url
            st.rerun()
    else:
        st.sidebar.warning("⚠️ 未接続")


def show_error_handling(error_message, api=None):
    """エラーハンドリング表示"""
    st.error(f"アプリケーションエラー: {str(error_message)}")
    st.error("Google Sheets接続に問題がある可能性があります。")
    
    # エラー時の対処オプション
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 接続をリセット", type="primary"):
            if 'gas_url' in st.session_state:
                del st.session_state.gas_url
            if 'spreadsheet_url' in st.session_state:
                del st.session_state.spreadsheet_url
            st.rerun()
    
    with col2:
        if st.button("🚀 強制継続", type="secondary"):
            st.info("エラーを無視してアプリケーションを継続します。")
            # 基本的なダッシュボードを表示
            st.subheader("📊 基本ダッシュボード")
            st.info("接続に問題がありますが、アプリケーションは利用可能です。")


def render_navigation_menu():
    """ナビゲーションメニュー"""
    return st.sidebar.selectbox(
        "📋 メニュー",
        ["📊 ダッシュボード", "🏢 企業管理", "📧 メールキャンペーン", 
         "📈 分析・レポート", "📁 データインポート"]
    )


def show_page_header(title, subtitle=None):
    """ページヘッダー表示"""
    st.title(title)
    if subtitle:
        st.markdown(subtitle)
    
    # Google Sheetsリンク表示
    if 'spreadsheet_url' in st.session_state:
        st.success(f"✅ Google Sheets接続中 | [📊 スプレッドシートを開く]({st.session_state.spreadsheet_url})")
    else:
        st.info("🔄 Google Sheetsとの接続を確立中...")


def show_quick_stats(company_manager):
    """クイック統計表示（サイドバー用）"""
    try:
        companies_df = company_manager.get_all_companies()
        
        if not companies_df.empty:
            total_companies = len(companies_df)
            wifi_companies = len(companies_df[companies_df['wifi_required'] == 1]) if 'wifi_required' in companies_df.columns else 0
            high_priority = len(companies_df[companies_df['priority_score'] >= 100]) if 'priority_score' in companies_df.columns else 0
            
            st.sidebar.metric("総企業数", total_companies)
            st.sidebar.metric("WiFi必要企業", wifi_companies)
            st.sidebar.metric("高優先度企業", high_priority)
        else:
            st.sidebar.info("データがありません")
    except Exception as e:
        st.sidebar.error(f"統計取得エラー: {str(e)}")


def show_success_message(message, auto_rerun=True, delay=1):
    """成功メッセージと自動リロード"""
    st.success(message)
    if auto_rerun:
        time.sleep(delay)
        st.rerun()


def show_loading_spinner(message="処理中..."):
    """ローディングスピナー"""
    return st.spinner(message)
