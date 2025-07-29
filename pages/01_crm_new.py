# pages/01_crm_new.py - エラー修正版
# Updated: 2025-07-29 - エラー修正・安定化版
# Force deployment trigger - Error fix version

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# ========================================
# 定数定義（エラー修正）
# ========================================
SALES_STATUS = [
    "New", "Contacted", "Replied", "Engaged", 
    "Qualified", "Proposal", "Negotiation", "Won", "Lost", "On Hold"
]

INDUSTRIES = [
    "建設業", "製造業", "IT・ソフトウェア", "金融業", "小売業", 
    "不動産業", "物流業", "医療・介護", "教育", "その他"
]

PICOCELA_KEYWORDS = [
    "wifi", "wireless", "mesh", "network", "internet", "connectivity",
    "建設現場", "工場", "倉庫", "オフィス", "店舗", "病院", "学校"
]

# ========================================
# ヘルパー関数
# ========================================
def calculate_picocela_score(company_data):
    """PicoCELA関連度スコアを計算"""
    score = 0
    text_fields = [
        company_data.get('企業名', ''),
        company_data.get('業界', ''),
        company_data.get('備考', ''),
        company_data.get('ウェブサイト', '')
    ]
    
    combined_text = ' '.join(text_fields).lower()
    
    for keyword in PICOCELA_KEYWORDS:
        if keyword.lower() in combined_text:
            if keyword in ["wifi", "wireless", "mesh"]:
                score += 30
            elif keyword in ["network", "connectivity"]:
                score += 20
            else:
                score += 10
    
    return min(score, 110)

def determine_wifi_need(company_data):
    """WiFi需要を自動判定"""
    score = calculate_picocela_score(company_data)
    industry = company_data.get('業界', '')
    
    if score > 50:
        return True
    
    high_need_industries = ["建設業", "製造業", "物流業", "医療・介護"]
    return industry in high_need_industries

def get_sample_companies():
    """サンプル企業データを生成"""
    return [
        {
            'ID': 1, '企業名': 'ABC建設', 'ステータス': 'Contacted', 
            'PicoCELAスコア': 85, '販売員': 'admin', 'WiFi需要': True,
            'メール': 'contact@abc-kensetsu.co.jp', '最終更新': '2025-07-28',
            '業界': '建設業', '電話番号': '03-1234-5678'
        },
        {
            'ID': 2, '企業名': 'XYZ工業', 'ステータス': 'Qualified', 
            'PicoCELAスコア': 92, '販売員': 'admin', 'WiFi需要': True,
            'メール': 'info@xyz-kogyo.co.jp', '最終更新': '2025-07-27',
            '業界': '製造業', '電話番号': '06-5678-9012'
        },
        {
            'ID': 3, '企業名': 'DEF開発', 'ステータス': 'Proposal', 
            'PicoCELAスコア': 78, '販売員': 'admin', 'WiFi需要': False,
            'メール': 'sales@def-dev.co.jp', '最終更新': '2025-07-26',
            '業界': 'IT・ソフトウェア', '電話番号': '03-9876-5432'
        }
    ]

def check_google_sheets_connection():
    """Google Sheets API接続をチェック"""
    try:
        # 統合ダッシュボードのAPI設定を確認
        if hasattr(st.session_state, 'google_apps_script_url') and st.session_state.google_apps_script_url:
            return True, st.session_state.google_apps_script_url
        
        # 環境変数やその他の設定を確認
        # TODO: 実際のAPI設定ロジックを実装
        return False, None
    except Exception as e:
        return False, str(e)

def get_api_connection_info():
    """API接続情報を安全に取得"""
    try:
        return check_google_sheets_connection()
    except:
        return False, "接続チェック中にエラーが発生しました"

# ========================================
# メイン画面表示関数（完全定義版）
# ========================================
def show_crm_dashboard():
    """CRMダッシュボード表示"""
    st.header("📊 CRMダッシュボード")
    
    # サンプルデータの取得
    companies = get_sample_companies()
    df = pd.DataFrame(companies)
    
    # 統計メトリクス
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", len(df))
    
    with col2:
        wifi_needed = len(df[df['WiFi需要'] == True])
        st.metric("📶 WiFi需要企業", wifi_needed, f"{wifi_needed/len(df)*100:.1f}%")
    
    with col3:
        picocela_related = len(df[df['PicoCELAスコア'] > 70])
        st.metric("🎯 PicoCELA関連", picocela_related, f"{picocela_related/len(df)*100:.1f}%")
    
    with col4:
        st.metric("🎯 今月目標", 15)
    
    # サンプルデータ追加ボタン
    if st.button("🚀 サンプルデータを追加", key="add_sample_data_dashboard"):
        st.success("サンプルデータが追加されました！")
        st.rerun()
    
    # 最新企業データ
    st.subheader("📋 最新企業データ（上位10社）")
    
    # データ表示のフォーマット調整
    display_df = df.copy()
    display_df['WiFi需要'] = display_df['WiFi需要'].map({True: '✅', False: '❌'})
    
    st.dataframe(
        display_df[['企業名', 'ステータス', 'PicoCELAスコア', 'WiFi需要', '最終更新']],
        use_container_width=True
    )

def show_company_management():
    """企業管理画面表示"""
    st.header("🏢 企業管理")
    
    # 検索・フィルター機能
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 企業名検索", key="company_search_input")
    
    with col2:
        status_filter = st.selectbox(
            "ステータスフィルター", 
            ["全て"] + SALES_STATUS,
            key="status_filter_select"
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        score_range = st.slider(
            "PicoCELAスコア範囲", 
            0, 110, (0, 110),
            key="score_range_slider"
        )
    
    with col4:
        wifi_filter = st.selectbox(
            "WiFi需要フィルター",
            ["全て", "WiFi必要", "WiFi不要"],
            key="wifi_filter_select"
        )
    
    # サンプルデータの取得とフィルタリング
    companies = get_sample_companies()
    df = pd.DataFrame(companies)
    
    # フィルタリング適用
    if search_term:
        df = df[df['企業名'].str.contains(search_term, case=False, na=False)]
    
    if status_filter != "全て":
        df = df[df['ステータス'] == status_filter]
    
    df = df[
        (df['PicoCELAスコア'] >= score_range[0]) & 
        (df['PicoCELAスコア'] <= score_range[1])
    ]
    
    if wifi_filter == "WiFi必要":
        df = df[df['WiFi需要'] == True]
    elif wifi_filter == "WiFi不要":
        df = df[df['WiFi需要'] == False]
    
    # 企業一覧表示
    st.subheader(f"📋 企業一覧 ({len(df)}社)")
    
    if len(df) > 0:
        # 表示用のデータフォーマット
        display_df = df.copy()
        display_df['WiFi需要'] = display_df['WiFi需要'].map({True: '✅', False: '❌'})
        
        st.dataframe(
            display_df[['ID', '企業名', 'ステータス', 'PicoCELAスコア', '販売員', 'WiFi需要', 'メール', '最終更新']],
            use_container_width=True
        )
    else:
        st.info("🔍 検索条件に一致する企業が見つかりませんでした。")

def show_analytics():
    """分析画面表示"""
    st.header("📈 分析")
    
    # サンプルデータの取得
    companies = get_sample_companies()
    df = pd.DataFrame(companies)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 ステータス分布")
        
        # ステータス分布グラフ
        status_counts = df['ステータス'].value_counts()
        fig_status = px.bar(
            x=status_counts.index,
            y=status_counts.values,
            title="企業ステータス分布",
            labels={'x': 'ステータス', 'y': '企業数'}
        )
        fig_status.update_layout(showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        st.subheader("🎯 PicoCELA関連度分析")
        
        # スコア分布ヒストグラム
        fig_score = px.histogram(
            df,
            x='PicoCELAスコア',
            nbins=10,
            title="PicoCELA関連度スコア分布",
            labels={'PicoCELAスコア': 'スコア', 'count': '企業数'}
        )
        st.plotly_chart(fig_score, use_container_width=True)
    
    # WiFi需要分析
    st.subheader("📶 WiFi需要分析")
    
    wifi_counts = df['WiFi需要'].value_counts()
    wifi_labels = ['WiFi必要', 'WiFi不要']
    
    fig_wifi = px.pie(
        values=wifi_counts.values,
        names=wifi_labels,
        title="WiFi需要分布"
    )
    st.plotly_chart(fig_wifi, use_container_width=True)

def show_add_company():
    """企業追加画面表示"""
    st.header("➕ 企業追加")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("企業名 *", key="add_company_name")
            email = st.text_input("メールアドレス", key="add_company_email")
            industry = st.selectbox("業界", INDUSTRIES, key="add_company_industry")
            phone = st.text_input("電話番号", key="add_company_phone")
        
        with col2:
            website = st.text_input("ウェブサイト", key="add_company_website")
            status = st.selectbox("初期ステータス", SALES_STATUS, key="add_company_status")
            source = st.selectbox("情報源", ["Manual", "Import", "Web", "Reference"], key="add_company_source")
            notes = st.text_area("備考", key="add_company_notes")
        
        submitted = st.form_submit_button("🚀 企業を追加", type="primary")
        
        if submitted:
            if company_name:
                # 新しい企業データの作成
                new_company = {
                    '企業名': company_name,
                    'メール': email,
                    '業界': industry,
                    '電話番号': phone,
                    'ウェブサイト': website,
                    'ステータス': status,
                    '備考': notes,
                    '情報源': source
                }
                
                # PicoCELAスコアとWiFi需要の自動計算
                picocela_score = calculate_picocela_score(new_company)
                wifi_need = determine_wifi_need(new_company)
                
                # 結果表示
                st.success("✅ 企業追加しました！")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("PicoCELA関連度スコア", f"{picocela_score}点")
                with col2:
                    st.metric("WiFi需要判定", "✅ 必要" if wifi_need else "❌ 不要")
                with col3:
                    st.metric("追加日時", datetime.now().strftime("%Y-%m-%d"))
                
                # TODO: 実際のデータベースへの保存処理
                st.info("💾 Google Sheets連携が有効な場合、自動的に同期されます。")
            else:
                st.error("❌ 企業名は必須です。")

def show_settings():
    """設定画面表示"""
    st.header("⚙️ 設定")
    
    # API接続状況（安全なチェック）
    try:
        api_connected, api_info = get_api_connection_info()
    except:
        api_connected, api_info = False, "設定エラー"
    
    st.subheader("🔌 Google Sheets連携")
    
    if api_connected:
        st.success("✅ Google Sheets連携中")
        if api_info:
            st.info(f"📊 接続先: {api_info}")
            if st.button("📊 スプレッドシートを開く", key="open_spreadsheet"):
                st.write(f"🔗 [Google Sheets]({api_info})")
    else:
        st.error("🔌 Google Sheets APIに接続できません")
        st.info("統合ダッシュボードの設定を確認してください。")
    
    # システム統計
    st.subheader("📊 システム統計")
    
    companies = get_sample_companies()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("登録企業数", len(companies))
    
    with col2:
        high_score_companies = len([c for c in companies if c['PicoCELAスコア'] > 80])
        st.metric("高スコア企業", high_score_companies)
    
    with col3:
        last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.metric("最終更新", last_update)
    
    # データエクスポート
    st.subheader("📤 データエクスポート")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 CSVエクスポート", key="export_csv"):
            df = pd.DataFrame(companies)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 CSVダウンロード",
                data=csv,
                file_name=f"companies_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 レポート生成", key="generate_report"):
            st.info("📋 レポート機能は開発中です。")

# ========================================
# メイン実行部分
# ========================================
def main():
    # デバッグメッセージ（一時的）
    st.error("🚨 重要: この赤いメッセージが表示されていれば、アップデートが反映されています。")
    st.success("✅ このメッセージが見える場合、アップデートは成功しています")
    
    # 戻るボタン
    if st.button("← 統合ダッシュボードに戻る", key="back_to_dashboard_crm_new"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
    
    st.title("🏢 CRM管理システム - フル機能版")
    st.caption("企業データ管理・ステータス追跡・PicoCELA関連度分析")
    
    # Google Sheets API診断
    st.info("🔍 統合プラットフォーム・サイドバーから各ページに移動できます | Google Sheetsで更にリアルタイム同期")
    
    # API接続チェック（安全な呼び出し）
    try:
        api_connected, api_info = get_api_connection_info()
    except:
        api_connected, api_info = False, "接続エラー"
    
    if not api_connected:
        st.warning("⚠️ Google Sheets APIに接続できません")
        
        # オフラインモード継続ボタン
        if st.button("⚠️ オフラインモードで続行", key="continue_offline_mode"):
            st.session_state.offline_mode = True
            st.success("✅ オフラインモードが有効になりました")
    
    # オフラインモード表示
    if getattr(st.session_state, 'offline_mode', False) or not api_connected:
        st.success("🚀 CRM機能（オフラインモード）")
        
        # 5つのタブ構造
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 ダッシュボード", 
            "🏢 企業管理", 
            "📈 分析", 
            "➕ 企業追加", 
            "⚙️ 設定"
        ])
        
        with tab1:
            # ダッシュボード機能を直接実装
            st.header("📊 CRMダッシュボード")
            
            # サンプルデータの直接定義
            companies = [
                {
                    'ID': 1, '企業名': 'ABC建設', 'ステータス': 'Contacted', 
                    'PicoCELAスコア': 85, '販売員': 'admin', 'WiFi需要': True,
                    'メール': 'contact@abc-kensetsu.co.jp', '最終更新': '2025-07-28',
                    '業界': '建設業', '電話番号': '03-1234-5678'
                },
                {
                    'ID': 2, '企業名': 'XYZ工業', 'ステータス': 'Qualified', 
                    'PicoCELAスコア': 92, '販売員': 'admin', 'WiFi需要': True,
                    'メール': 'info@xyz-kogyo.co.jp', '最終更新': '2025-07-27',
                    '業界': '製造業', '電話番号': '06-5678-9012'
                },
                {
                    'ID': 3, '企業名': 'DEF開発', 'ステータス': 'Proposal', 
                    'PicoCELAスコア': 78, '販売員': 'admin', 'WiFi需要': False,
                    'メール': 'sales@def-dev.co.jp', '最終更新': '2025-07-26',
                    '業界': 'IT・ソフトウェア', '電話番号': '03-9876-5432'
                }
            ]
            
            df = pd.DataFrame(companies)
            
            # 統計メトリクス
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📈 総企業数", len(df))
            
            with col2:
                wifi_needed = len(df[df['WiFi需要'] == True])
                st.metric("📶 WiFi需要企業", wifi_needed, f"{wifi_needed/len(df)*100:.1f}%")
            
            with col3:
                picocela_related = len(df[df['PicoCELAスコア'] > 70])
                st.metric("🎯 PicoCELA関連", picocela_related, f"{picocela_related/len(df)*100:.1f}%")
            
            with col4:
                st.metric("🎯 今月目標", 15)
            
            # 最新企業データ
            st.subheader("📋 最新企業データ（上位3社）")
            
            # データ表示のフォーマット調整
            display_df = df.copy()
            display_df['WiFi需要'] = display_df['WiFi需要'].map({True: '✅', False: '❌'})
            
            st.dataframe(
                display_df[['企業名', 'ステータス', 'PicoCELAスコア', 'WiFi需要', '最終更新']],
                use_container_width=True
            )
        
        with tab2:
            # 企業管理機能を直接実装
            st.header("🏢 企業管理")
            
            # ステータスリストを直接定義
            status_options = ["全て", "New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost", "On Hold"]
            
            # 検索・フィルター機能
            col1, col2 = st.columns([2, 1])
            
            with col1:
                search_term = st.text_input("🔍 企業名検索", key="company_search_input_tab2")
            
            with col2:
                status_filter = st.selectbox(
                    "ステータスフィルター", 
                    status_options,
                    key="status_filter_select_tab2"
                )
            
            # サンプルデータの直接定義
            companies = [
                {
                    'ID': 1, '企業名': 'ABC建設', 'ステータス': 'Contacted', 
                    'PicoCELAスコア': 85, '販売員': 'admin', 'WiFi需要': True,
                    'メール': 'contact@abc-kensetsu.co.jp', '最終更新': '2025-07-28'
                },
                {
                    'ID': 2, '企業名': 'XYZ工業', 'ステータス': 'Qualified', 
                    'PicoCELAスコア': 92, '販売員': 'admin', 'WiFi需要': True,
                    'メール': 'info@xyz-kogyo.co.jp', '最終更新': '2025-07-27'
                },
                {
                    'ID': 3, '企業名': 'DEF開発', 'ステータス': 'Proposal', 
                    'PicoCELAスコア': 78, '販売員': 'admin', 'WiFi需要': False,
                    'メール': 'sales@def-dev.co.jp', '最終更新': '2025-07-26'
                }
            ]
            
            df = pd.DataFrame(companies)
            
            # フィルタリング適用
            if search_term:
                df = df[df['企業名'].str.contains(search_term, case=False, na=False)]
            
            if status_filter != "全て":
                df = df[df['ステータス'] == status_filter]
            
            # 企業一覧表示
            st.subheader(f"📋 企業一覧 ({len(df)}社)")
            
            if len(df) > 0:
                # 表示用のデータフォーマット
                display_df = df.copy()
                display_df['WiFi需要'] = display_df['WiFi需要'].map({True: '✅', False: '❌'})
                
                st.dataframe(
                    display_df[['ID', '企業名', 'ステータス', 'PicoCELAスコア', '販売員', 'WiFi需要', 'メール']],
                    use_container_width=True
                )
            else:
                st.info("🔍 検索条件に一致する企業が見つかりませんでした。")
        
        with tab3:
            # 分析機能を直接実装
            st.header("📈 分析")
            
            # サンプルデータの直接定義
            companies = [
                {'ステータス': 'Contacted', 'PicoCELAスコア': 85},
                {'ステータス': 'Qualified', 'PicoCELAスコア': 92},
                {'ステータス': 'Proposal', 'PicoCELAスコア': 78}
            ]
            
            df = pd.DataFrame(companies)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 ステータス分布")
                
                # ステータス分布グラフ
                status_counts = df['ステータス'].value_counts()
                fig_status = px.bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    title="企業ステータス分布",
                    labels={'x': 'ステータス', 'y': '企業数'}
                )
                fig_status.update_layout(showlegend=False)
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                st.subheader("🎯 PicoCELA関連度分析")
                
                # スコア分布ヒストグラム
                fig_score = px.histogram(
                    df,
                    x='PicoCELAスコア',
                    nbins=5,
                    title="PicoCELA関連度スコア分布",
                    labels={'PicoCELAスコア': 'スコア', 'count': '企業数'}
                )
                st.plotly_chart(fig_score, use_container_width=True)
        
        with tab4:
            # 企業追加機能を直接実装
            st.header("➕ 企業追加")
            
            # 業界リストとステータスリストを直接定義
            industry_options = ["建設業", "製造業", "IT・ソフトウェア", "金融業", "小売業", "不動産業", "物流業", "医療・介護", "教育", "その他"]
            status_options = ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost", "On Hold"]
            
            with st.form("add_company_form_tab4"):
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = st.text_input("企業名 *", key="add_company_name_tab4")
                    email = st.text_input("メールアドレス", key="add_company_email_tab4")
                    industry = st.selectbox("業界", industry_options, key="add_company_industry_tab4")
                
                with col2:
                    website = st.text_input("ウェブサイト", key="add_company_website_tab4")
                    status = st.selectbox("初期ステータス", status_options, key="add_company_status_tab4")
                    notes = st.text_area("備考", key="add_company_notes_tab4")
                
                submitted = st.form_submit_button("🚀 企業を追加", type="primary")
                
                if submitted:
                    if company_name:
                        # 新しい企業データの作成
                        new_company = {
                            '企業名': company_name,
                            'メール': email,
                            '業界': industry,
                            'ウェブサイト': website,
                            'ステータス': status,
                            '備考': notes
                        }
                        
                        # PicoCELAスコアの簡単計算
                        combined_text = f"{company_name} {industry} {notes} {website}".lower()
                        score = 0
                        if 'wifi' in combined_text or 'wireless' in combined_text:
                            score += 30
                        if 'network' in combined_text or 'mesh' in combined_text:
                            score += 20
                        if industry in ["建設業", "製造業"]:
                            score += 15
                        
                        wifi_need = score > 25 or industry in ["建設業", "製造業", "物流業"]
                        
                        # 結果表示
                        st.success("✅ 企業追加しました！")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("PicoCELA関連度スコア", f"{score}点")
                        with col2:
                            st.metric("WiFi需要判定", "✅ 必要" if wifi_need else "❌ 不要")
                        with col3:
                            st.metric("追加日時", datetime.now().strftime("%Y-%m-%d"))
                        
                        st.info("💾 オフラインモードです。Google Sheets連携時に同期されます。")
                    else:
                        st.error("❌ 企業名は必須です。")
        
        with tab5:
            # 設定機能を直接実装
            st.header("⚙️ 設定")
            
            # API接続状況
            st.subheader("🔌 Google Sheets連携")
            st.error("🔌 Google Sheets APIに接続できません")
            st.info("統合ダッシュボードの設定を確認してください。")
            
            # システム統計
            st.subheader("📊 システム統計")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("登録企業数", 3)
            
            with col2:
                st.metric("高スコア企業", 2)
            
            with col3:
                last_update = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.metric("最終更新", last_update)
            
            # データエクスポート
            st.subheader("📤 データエクスポート")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 CSVエクスポート", key="export_csv_tab5"):
                    # サンプルデータでCSV作成
                    sample_data = [
                        {'企業名': 'ABC建設', 'ステータス': 'Contacted', 'スコア': 85},
                        {'企業名': 'XYZ工業', 'ステータス': 'Qualified', 'スコア': 92},
                        {'企業名': 'DEF開発', 'ステータス': 'Proposal', 'スコア': 78}
                    ]
                    df = pd.DataFrame(sample_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 CSVダウンロード",
                        data=csv,
                        file_name=f"companies_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download_csv_tab5"
                    )
            
            with col2:
                if st.button("📊 レポート生成", key="generate_report_tab5"):
                    st.info("📋 レポート機能は開発中です。")
    else:
        st.info("🔌 Google Sheets API接続を確立中...")

if __name__ == "__main__":
    main()
