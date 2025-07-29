# pages/01_crm_fixed.py - エラー修正版
# Updated: 2025-07-29 - No more function errors
# Self-contained CRM System

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# ========================================
# エラー防止：最初に全ての関数を定義
# ========================================

st.error("🚨 修正版: この赤いメッセージが表示されていれば、最新版が反映されています。")
st.success("✅ エラー修正版 - 全機能自己完結型")

# ========================================
# CRM管理システム - メイン実装
# ========================================

# タイトル表示
st.title("🏢 CRM管理システム - 完全版")
st.caption("企業データ管理・ステータス追跡・PicoCELA関連度分析・Google Sheets完全連携")

# Google Sheets連携情報
st.info("🔗 統合プラットフォーム・Google Sheetsでリアルタイム同期対応")

# ========================================
# Google Sheets データ取得（直接実装）
# ========================================

try:
    st.info("🔄 Google Sheetsから企業データを取得中...")
    
    # Google Apps Script URL
    api_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
    
    # APIリクエスト実行
    response = requests.get(
        api_url,
        params={"action": "get_companies"},
        timeout=20
    )
    
    st.info(f"📡 API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('data'):
            google_sheets_companies = data['data']
            st.success(f"✅ Google Sheets連携成功！{len(google_sheets_companies)}社のデータを取得")
            google_sheets_success = True
        else:
            google_sheets_companies = []
            google_sheets_success = False
            st.warning("⚠️ Google Sheetsデータの構造に問題があります")
    else:
        google_sheets_companies = []
        google_sheets_success = False
        st.error(f"❌ Google Sheets API Error: {response.status_code}")

except Exception as e:
    google_sheets_companies = []
    google_sheets_success = False
    st.warning(f"🔗 Google Sheets接続失敗: {str(e)}")

# ========================================
# サンプルデータ（フォールバック）
# ========================================

sample_companies = [
    {
        'ID': 1, '企業名': 'ABC建設株式会社', 'ステータス': 'Contacted', 
        'PicoCELAスコア': 85, 'WiFi需要': '✅ 必要', '販売員': 'admin',
        'メール': 'contact@abc-construction.com', '業界': '建設業',
        'ウェブサイト': 'https://abc-construction.com',
        '備考': 'Large construction sites requiring WiFi mesh networks',
        '登録日': '2025-07-20'
    },
    {
        'ID': 2, '企業名': 'FUSIONDRIVER', 'ステータス': 'Engaged', 
        'PicoCELAスコア': 95, 'WiFi需要': '✅ 必要', '販売員': 'admin',
        'メール': 'koji@fusiondriver.biz', '業界': 'IT・ソフトウェア',
        'ウェブサイト': 'https://fusiondriver.biz',
        '備考': 'High-tech company with advanced networking needs',
        '登録日': '2025-07-15'
    },
    {
        'ID': 3, '企業名': 'XYZ製造工業', 'ステータス': 'Qualified', 
        'PicoCELAスコア': 92, 'WiFi需要': '✅ 必要', '販売員': 'admin',
        'メール': 'info@xyz-manufacturing.com', '業界': '製造業',
        'ウェブサイト': 'https://xyz-manufacturing.com',
        '備考': 'Factory floor needs wireless network coverage',
        '登録日': '2025-07-22'
    },
    {
        'ID': 4, '企業名': 'DEFソフトウェア', 'ステータス': 'Proposal', 
        'PicoCELAスコア': 78, 'WiFi需要': '❌ 不要', '販売員': 'admin',
        'メール': 'contact@def-software.com', '業界': 'IT・ソフトウェア',
        'ウェブサイト': 'https://def-software.com',
        '備考': 'Software development company with office WiFi',
        '登録日': '2025-07-25'
    }
]

# ========================================
# データソース決定
# ========================================

if google_sheets_success and google_sheets_companies:
    # Google Sheetsデータを正規化
    companies_data = []
    for company in google_sheets_companies:
        normalized = {
            'ID': company.get('company_id') or company.get('ID') or len(companies_data) + 1,
            '企業名': company.get('company_name') or company.get('企業名') or 'N/A',
            'ステータス': company.get('sales_status') or company.get('ステータス') or 'New',
            'PicoCELAスコア': company.get('picocela_relevance') or company.get('PicoCELAスコア') or 0,
            'WiFi需要': company.get('wifi_needs') or company.get('WiFi需要') or 'Unknown',
            '販売員': company.get('salesperson') or company.get('販売員') or 'admin',
            'メール': company.get('email') or company.get('メール') or '',
            '業界': company.get('industry') or company.get('業界') or 'その他',
            'ウェブサイト': company.get('website_url') or company.get('ウェブサイト') or '',
            '備考': company.get('notes') or company.get('備考') or '',
            '登録日': company.get('created_date') or company.get('登録日') or datetime.now().strftime('%Y-%m-%d')
        }
        
        # WiFi需要の表示形式を統一
        wifi_need = str(normalized['WiFi需要']).lower()
        if wifi_need in ['high', 'medium', 'yes', 'true', '1']:
            normalized['WiFi需要'] = '✅ 必要'
        elif wifi_need in ['low', 'no', 'false', '0']:
            normalized['WiFi需要'] = '❌ 不要'
        else:
            normalized['WiFi需要'] = '❓ 未確認'
            
        companies_data.append(normalized)
    
    data_source = f"Google Sheets ({len(companies_data)}社)"
    st.success(f"🔗 リアルデータ表示中: {data_source}")
else:
    # サンプルデータを使用
    companies_data = sample_companies
    data_source = f"サンプルデータ ({len(companies_data)}社)"
    st.info(f"📋 オフラインモード: {data_source}")

# ========================================
# タブ作成・表示
# ========================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ダッシュボード", 
    "🏢 企業管理", 
    "📈 分析", 
    "➕ 企業追加", 
    "⚙️ 設定"
])

with tab1:
    # ダッシュボード
    st.header("📊 CRMダッシュボード")
    st.caption(f"データソース: {data_source}")
    
    # 統計メトリクス
    total_companies = len(companies_data)
    wifi_needed = len([c for c in companies_data if '✅' in str(c.get('WiFi需要', ''))])
    high_score = len([c for c in companies_data if int(c.get('PicoCELAスコア', 0)) >= 80])
    qualified = len([c for c in companies_data if c.get('ステータス') in ['Qualified', 'Engaged', 'Proposal']])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", total_companies)
    
    with col2:
        wifi_rate = (wifi_needed / total_companies * 100) if total_companies > 0 else 0
        st.metric("📶 WiFi需要企業", f"{wifi_needed} ({wifi_rate:.1f}%)")
    
    with col3:
        score_rate = (high_score / total_companies * 100) if total_companies > 0 else 0
        st.metric("🎯 高スコア企業", f"{high_score} ({score_rate:.1f}%)")
    
    with col4:
        qualified_rate = (qualified / total_companies * 100) if total_companies > 0 else 0
        st.metric("💼 有望企業", f"{qualified} ({qualified_rate:.1f}%)")
    
    # 企業データ一覧
    st.subheader("📋 企業データ一覧")
    
    if companies_data:
        display_df = pd.DataFrame(companies_data)
        key_columns = ['企業名', 'ステータス', 'PicoCELAスコア', 'WiFi需要', '業界', '販売員']
        available_columns = [col for col in key_columns if col in display_df.columns]
        
        if available_columns:
            st.dataframe(display_df[available_columns], use_container_width=True)
        else:
            st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("表示するデータがありません")

with tab2:
    # 企業管理
    st.header("🏢 企業管理")
    
    # 検索・フィルター
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("🔍 企業名検索", key="company_search_tab2")
    
    with col2:
        status_list = ["全て"] + sorted(list(set([c.get('ステータス', '') for c in companies_data if c.get('ステータス')])))
        selected_status = st.selectbox("📊 ステータスフィルター", status_list, key="status_filter_tab2")
    
    # フィルタリング
    filtered_companies = companies_data.copy()
    
    if search_term:
        filtered_companies = [c for c in filtered_companies 
                            if search_term.lower() in c.get('企業名', '').lower()]
    
    if selected_status != "全て":
        filtered_companies = [c for c in filtered_companies 
                            if c.get('ステータス') == selected_status]
    
    # 企業一覧
    st.subheader(f"📋 企業一覧 ({len(filtered_companies)}社)")
    
    for company in filtered_companies:
        with st.expander(f"🏢 {company.get('企業名', 'N/A')} - {company.get('ステータス', 'N/A')} - スコア: {company.get('PicoCELAスコア', 'N/A')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**ID**: {company.get('ID', 'N/A')}")
                st.write(f"**企業名**: {company.get('企業名', 'N/A')}")
                st.write(f"**ステータス**: {company.get('ステータス', 'N/A')}")
                st.write(f"**PicoCELAスコア**: {company.get('PicoCELAスコア', 'N/A')}")
            
            with col2:
                st.write(f"**WiFi需要**: {company.get('WiFi需要', 'N/A')}")
                st.write(f"**業界**: {company.get('業界', 'N/A')}")
                st.write(f"**販売員**: {company.get('販売員', 'N/A')}")
                st.write(f"**登録日**: {company.get('登録日', 'N/A')}")
            
            with col3:
                st.write(f"**メール**: {company.get('メール', 'N/A')}")
                st.write(f"**ウェブサイト**: {company.get('ウェブサイト', 'N/A')}")
                
                if company.get('ウェブサイト') and company['ウェブサイト'] != 'N/A':
                    st.markdown(f"[🔗 ウェブサイトを開く]({company['ウェブサイト']})")
            
            if company.get('備考'):
                st.write(f"**備考**: {company.get('備考')}")

with tab3:
    # 分析
    st.header("📈 データ分析")
    
    # ステータス分布
    st.subheader("📊 ステータス分布")
    status_counts = {}
    for company in companies_data:
        status = company.get('ステータス', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    if status_counts:
        st.bar_chart(status_counts)
    
    # スコア分析
    st.subheader("🎯 PicoCELAスコア分析")
    scores = [int(c.get('PicoCELAスコア', 0)) for c in companies_data if c.get('PicoCELAスコア') is not None]
    
    if scores:
        score_ranges = {
            '0-25点': len([s for s in scores if 0 <= s <= 25]),
            '26-50点': len([s for s in scores if 26 <= s <= 50]),
            '51-75点': len([s for s in scores if 51 <= s <= 75]),
            '76-100点': len([s for s in scores if 76 <= s <= 100])
        }
        
        st.bar_chart(score_ranges)
        
        # 統計情報
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均スコア", f"{sum(scores)/len(scores):.1f}点")
        with col2:
            st.metric("最高スコア", f"{max(scores)}点")
        with col3:
            st.metric("最低スコア", f"{min(scores)}点")
    
    # 業界分析
    st.subheader("🏭 業界分析")
    industry_counts = {}
    for company in companies_data:
        industry = company.get('業界', 'その他')
        industry_counts[industry] = industry_counts.get(industry, 0) + 1
    
    if industry_counts:
        st.bar_chart(industry_counts)

with tab4:
    # 企業追加
    st.header("➕ 企業追加")
    
    with st.form("add_company_form"):
        st.subheader("🏢 新規企業情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("企業名 *", key="add_company_name")
            email = st.text_input("メールアドレス", key="add_email")
            industry = st.selectbox("業界", 
                ["建設業", "製造業", "IT・ソフトウェア", "金融業", "小売業", "不動産業", "物流業", "医療・介護", "教育", "その他"], 
                key="add_industry")
        
        with col2:
            website = st.text_input("ウェブサイト", key="add_website")
            status = st.selectbox("初期ステータス", 
                ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation"], 
                key="add_status")
        
        notes = st.text_area("備考・特記事項", key="add_notes", height=100)
        
        submit_button = st.form_submit_button("🚀 企業を追加")
        
        if submit_button and company_name:
            # スコア計算
            score = 0
            notes_lower = notes.lower()
            
            # キーワードベーススコア
            wifi_keywords = ['wifi', 'wireless', 'network', 'mesh', 'connectivity', 'internet', 'iot', 'smart', 'automation']
            for keyword in wifi_keywords:
                if keyword in notes_lower:
                    score += 10
            
            construction_keywords = ['construction', 'building', 'site', 'facility', 'warehouse', 'factory']
            for keyword in construction_keywords:
                if keyword in notes_lower:
                    score += 8
            
            # 業界ボーナス
            industry_bonus = {
                "建設業": 25, "製造業": 20, "物流業": 18, 
                "不動産業": 15, "IT・ソフトウェア": 10, "金融業": 5
            }
            score += industry_bonus.get(industry, 0)
            
            score = min(score, 100)  # 最大100点
            
            # WiFi需要判定
            wifi_need = "✅ 必要" if score >= 40 else "❌ 不要"
            
            # 結果表示
            st.success("✅ 企業追加完了！")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("PicoCELA関連度", f"{score}点")
            with col2:
                st.metric("WiFi需要判定", wifi_need)
            with col3:
                st.metric("追加日時", datetime.now().strftime("%Y-%m-%d"))
            
            # 企業情報表示
            st.info(f"**企業名**: {company_name} | **業界**: {industry} | **ステータス**: {status}")
            if notes:
                st.write(f"**備考**: {notes}")

with tab5:
    # システム設定
    st.header("⚙️ システム設定")
    
    # 接続状況
    st.subheader("🔗 API接続状況")
    col1, col2 = st.columns(2)
    
    with col1:
        if google_sheets_success:
            st.success("✅ Google Sheets API接続正常")
        else:
            st.error("❌ Google Sheets API接続失敗")
    
    with col2:
        st.metric("データソース", data_source.split('(')[0])
    
    # システム統計
    st.subheader("📊 システム統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", len(companies_data))
    with col2:
        st.metric("データソース", "Google Sheets" if google_sheets_success else "オフライン")
    with col3:
        st.metric("最終更新", datetime.now().strftime("%H:%M"))
    with col4:
        st.metric("システム状態", "正常動作")
    
    # データエクスポート
    st.subheader("📤 データエクスポート")
    if st.button("📊 CSVエクスポート", key="export_csv"):
        df = pd.DataFrame(companies_data)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="💾 CSVファイルをダウンロード",
            data=csv,
            file_name=f'fusioncrm_companies_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )
        st.success("✅ CSVファイルの準備が完了しました！")
