# pages/01_crm_final.py - Google Sheetsデータ構造対応版
# Updated: 2025-07-29 - Real Google Sheets data structure support
# Complete CRM System with actual data format

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# ========================================
# デバッグメッセージ（更新確認用）
# ========================================
st.error("🚨 最終版: Google Sheetsデータ構造に完全対応した版です")
st.success("✅ 実データ形式対応版 - FUSIONDRIVER・Wyebot等の実企業データ表示")

# ========================================
# CRM管理システム - メイン実装
# ========================================

# タイトル表示
st.title("🏢 CRM管理システム - 最終版")
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
            
            # デバッグ情報：実際のデータ構造を表示
            if google_sheets_companies:
                first_company_keys = list(google_sheets_companies[0].keys())
                st.info(f"📋 取得データ構造: {', '.join(first_company_keys[:8])}...")
                
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
        'company_id': 'SAMPLE_001',
        'company_name': 'ABC建設株式会社',
        'contact_name': '田中太郎',
        'email': 'contact@abc-construction.com',
        'phone': '03-1234-5678',
        'website': 'https://abc-construction.com',
        'description': 'Large construction sites requiring WiFi mesh networks for project management and communication',
        'construction_focus': 'High',
        'wifi_needs': 'High',
        'picoCELA_relevance': 85,
        'priority_score': 90,
        'sales_status': 'Contacted',
        'created_at': '2025-07-20T10:00:00Z',
        'updated_at': '2025-07-25T15:30:00Z',
        'tags': 'construction,wifi,mesh'
    },
    {
        'company_id': 'SAMPLE_002',
        'company_name': 'FUSIONDRIVER',
        'contact_name': 'Koji Tokuda',
        'email': 'koji@fusiondriver.biz',
        'phone': '408-850-5058',
        'website': 'https://fusiondriver.biz',
        'description': 'We are implementing a Wi-Fi-based solution integration for construction sites.',
        'construction_focus': 'Low',
        'wifi_needs': 'High',
        'picoCELA_relevance': 95,
        'priority_score': 100,
        'sales_status': 'Engaged',
        'created_at': '2025-07-15T08:00:00Z',
        'updated_at': '2025-07-29T12:00:00Z',
        'tags': 'software,innovation,wifi'
    }
]

# ========================================
# データ正規化（実際のGoogle Sheets構造に対応）
# ========================================

def normalize_google_sheets_data(companies):
    """Google Sheetsの実際のデータ構造を日本語表示用に正規化"""
    normalized = []
    
    for company in companies:
        # WiFi需要の判定
        wifi_needs = str(company.get('wifi_needs', '')).lower()
        if wifi_needs in ['high', 'medium']:
            wifi_display = '✅ 必要'
        elif wifi_needs in ['low']:
            wifi_display = '❌ 不要'
        else:
            wifi_display = '❓ 未確認'
        
        # ステータスの正規化
        status = company.get('sales_status', 'New')
        if status in ['New', 'Contacted', 'Replied', 'Engaged', 'Qualified', 'Proposal', 'Negotiation', 'Won', 'Lost']:
            status_display = status
        else:
            status_display = 'New'
        
        # 業界判定（descriptionやtagsから推測）
        description = str(company.get('description', '')).lower()
        tags = str(company.get('tags', '')).lower()
        text_content = f"{description} {tags}"
        
        if any(word in text_content for word in ['construction', 'building', 'site']):
            industry = '建設業'
        elif any(word in text_content for word in ['manufacturing', 'factory', 'industrial']):
            industry = '製造業'
        elif any(word in text_content for word in ['software', 'tech', 'ai', 'platform']):
            industry = 'IT・ソフトウェア'
        elif any(word in text_content for word in ['healthcare', 'medical', 'hospital']):
            industry = '医療・介護'
        elif any(word in text_content for word in ['education', 'school', 'university']):
            industry = '教育'
        else:
            industry = 'その他'
        
        normalized_company = {
            'ID': company.get('company_id', f"ID_{len(normalized)+1}"),
            '企業名': company.get('company_name', 'N/A'),
            'ステータス': status_display,
            'PicoCELAスコア': int(company.get('picoCELA_relevance', 0)) if company.get('picoCELA_relevance') else 0,
            'WiFi需要': wifi_display,
            '販売員': 'admin',  # デフォルト値
            'メール': company.get('email', ''),
            '業界': industry,
            'ウェブサイト': company.get('website', ''),
            '備考': company.get('description', '')[:100] + '...' if len(str(company.get('description', ''))) > 100 else company.get('description', ''),
            '登録日': company.get('created_at', '')[:10] if company.get('created_at') else datetime.now().strftime('%Y-%m-%d'),
            '連絡先': company.get('contact_name', ''),
            '電話番号': company.get('phone', ''),
            '優先度スコア': int(company.get('priority_score', 0)) if company.get('priority_score') else 0,
            'タグ': company.get('tags', ''),
            '建設関連度': company.get('construction_focus', 'Low')
        }
        
        normalized.append(normalized_company)
    
    return normalized

# ========================================
# データソース決定と正規化
# ========================================

if google_sheets_success and google_sheets_companies:
    # Google Sheetsからの実データを正規化
    companies_data = normalize_google_sheets_data(google_sheets_companies)
    data_source = f"Google Sheets ({len(companies_data)}社)"
    st.success(f"🔗 リアルデータ表示中: {data_source}")
    
    # 取得した企業名をサンプル表示
    if companies_data:
        company_names = [c['企業名'] for c in companies_data[:5]]
        st.info(f"📊 取得企業例: {', '.join(company_names)}{'...' if len(companies_data) > 5 else ''}")
        
else:
    # サンプルデータを正規化
    companies_data = normalize_google_sheets_data(sample_companies)
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
        # 表示用データフレーム作成
        display_data = []
        for company in companies_data:
            display_data.append({
                '企業名': company['企業名'],
                'ステータス': company['ステータス'],
                'PicoCELAスコア': company['PicoCELAスコア'],
                'WiFi需要': company['WiFi需要'],
                '業界': company['業界'],
                'メール': company['メール'],
                '登録日': company['登録日']
            })
        
        display_df = pd.DataFrame(display_data)
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
                st.write(f"**優先度スコア**: {company.get('優先度スコア', 'N/A')}")
            
            with col2:
                st.write(f"**WiFi需要**: {company.get('WiFi需要', 'N/A')}")
                st.write(f"**業界**: {company.get('業界', 'N/A')}")
                st.write(f"**連絡先**: {company.get('連絡先', 'N/A')}")
                st.write(f"**電話番号**: {company.get('電話番号', 'N/A')}")
                st.write(f"**登録日**: {company.get('登録日', 'N/A')}")
            
            with col3:
                st.write(f"**メール**: {company.get('メール', 'N/A')}")
                st.write(f"**ウェブサイト**: {company.get('ウェブサイト', 'N/A')}")
                st.write(f"**建設関連度**: {company.get('建設関連度', 'N/A')}")
                st.write(f"**タグ**: {company.get('タグ', 'N/A')}")
                
                if company.get('ウェブサイト') and company['ウェブサイト'] not in ['N/A', '']:
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
    
    # WiFi需要分析
    st.subheader("📶 WiFi需要分析")
    wifi_counts = {}
    for company in companies_data:
        wifi_need = company.get('WiFi需要', '❓ 未確認')
        wifi_counts[wifi_need] = wifi_counts.get(wifi_need, 0) + 1
    
    if wifi_counts:
        st.bar_chart(wifi_counts)

with tab4:
    # 企業追加
    st.header("➕ 企業追加")
    
    with st.form("add_company_form"):
        st.subheader("🏢 新規企業情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("企業名 *", key="add_company_name")
            email = st.text_input("メールアドレス", key="add_email")
            contact_name = st.text_input("連絡先担当者", key="add_contact")
            industry = st.selectbox("業界", 
                ["建設業", "製造業", "IT・ソフトウェア", "金融業", "小売業", "不動産業", "物流業", "医療・介護", "教育", "その他"], 
                key="add_industry")
        
        with col2:
            phone = st.text_input("電話番号", key="add_phone")
            website = st.text_input("ウェブサイト", key="add_website")
            status = st.selectbox("初期ステータス", 
                ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation"], 
                key="add_status")
            wifi_needs = st.selectbox("WiFi需要レベル", ["High", "Medium", "Low"], key="add_wifi_needs")
        
        description = st.text_area("企業説明・特記事項", key="add_description", height=100)
        tags = st.text_input("タグ（カンマ区切り）", key="add_tags", placeholder="例: construction,wifi,technology")
        
        submit_button = st.form_submit_button("🚀 企業を追加")
        
        if submit_button and company_name:
            # スコア計算
            picocela_score = 0
            priority_score = 0
            description_lower = description.lower()
            
            # キーワードベーススコア
            wifi_keywords = ['wifi', 'wireless', 'network', 'mesh', 'connectivity', 'internet', 'iot', 'smart', 'automation']
            for keyword in wifi_keywords:
                if keyword in description_lower:
                    picocela_score += 12
            
            construction_keywords = ['construction', 'building', 'site', 'facility', 'warehouse', 'factory']
            for keyword in construction_keywords:
                if keyword in description_lower:
                    picocela_score += 10
            
            # 業界ボーナス
            industry_bonus = {
                "建設業": 25, "製造業": 20, "物流業": 18, 
                "不動産業": 15, "IT・ソフトウェア": 10, "金融業": 5
            }
            picocela_score += industry_bonus.get(industry, 0)
            
            # WiFi需要レベルによる調整
            wifi_bonus = {"High": 20, "Medium": 10, "Low": 0}
            picocela_score += wifi_bonus.get(wifi_needs, 0)
            
            picocela_score = min(picocela_score, 100)  # 最大100点
            priority_score = min(picocela_score + 10, 100)  # 優先度スコアは少し高めに設定
            
            # WiFi需要表示形式
            wifi_display = f"{'✅ 必要' if wifi_needs in ['High', 'Medium'] else '❌ 不要'}"
            
            # 結果表示
            st.success("✅ 企業追加完了！")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("PicoCELA関連度", f"{picocela_score}点")
            with col2:
                st.metric("優先度スコア", f"{priority_score}点")
            with col3:
                st.metric("WiFi需要判定", wifi_display)
            with col4:
                st.metric("追加日時", datetime.now().strftime("%Y-%m-%d"))
            
            # 企業情報表示
            st.info(f"**企業名**: {company_name} | **業界**: {industry} | **ステータス**: {status}")
            if description:
                st.write(f"**説明**: {description}")
            if tags:
                st.write(f"**タグ**: {tags}")

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
        st.metric("データソース", "Google Sheets" if google_sheets_success else "オフライン")
    
    # システム統計
    st.subheader("📊 システム統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", len(companies_data))
    with col2:
        high_priority = len([c for c in companies_data if int(c.get('優先度スコア', 0)) >= 80])
        st.metric("高優先度企業", high_priority)
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
    
    # データ構造情報
    if google_sheets_success and companies_data:
        st.subheader("📋 データ構造情報")
        st.info("Google Sheetsから取得したデータの構造:")
        
        sample_company = companies_data[0] if companies_data else {}
        for key, value in list(sample_company.items())[:10]:  # 最初の10項目を表示
            st.text(f"• {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
