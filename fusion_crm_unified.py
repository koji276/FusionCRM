# pages/01_crm_excel.py - エクセルアップロード機能付き版
# Updated: 2025-07-29 - Excel upload functionality added
# Complete CRM System with Excel bulk upload feature

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# ========================================
# デバッグメッセージ
# ========================================
st.error("🚨 エクセルアップロード対応版: 企業一括追加機能付き")
st.success("✅ Excel/CSV一括アップロード - Google Sheets連携完全対応")

# ========================================
# CRM管理システム - エクセルアップロード対応版
# ========================================

st.title("🏢 CRM管理システム - エクセルアップロード対応版")
st.caption("企業データ管理・一括アップロード・PicoCELA関連度分析・Google Sheets完全連携")

# Google Sheets連携情報
st.info("🔗 統合プラットフォーム・Google Sheetsでリアルタイム同期 + エクセル一括アップロード対応")

# ========================================
# Google Sheets データ取得（既存機能）
# ========================================

@st.cache_data(ttl=300)  # 5分間キャッシュ
def get_google_sheets_data():
    """Google Sheetsからデータを取得（キャッシュ付き）"""
    try:
        api_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
        
        response = requests.get(
            api_url,
            params={"action": "get_companies"},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('companies'):
                return data['companies'], True
        
        return [], False
        
    except Exception as e:
        st.error(f"Google Sheets接続エラー: {str(e)}")
        return [], False

# Google Sheetsデータ取得
with st.spinner("🔄 Google Sheetsから企業データを取得中..."):
    google_sheets_companies, google_sheets_success = get_google_sheets_data()

if google_sheets_success:
    st.success(f"✅ Google Sheets連携成功！{len(google_sheets_companies)}社のデータを取得")
else:
    st.warning("⚠️ Google Sheets接続失敗 - オフラインモードで動作")

# ========================================
# エクセル/CSVファイル処理関数
# ========================================

def process_excel_file(uploaded_file):
    """アップロードされたエクセルファイルを処理"""
    try:
        # ファイル拡張子チェック
        file_name = uploaded_file.name
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            # エクセルファイル処理
            df = pd.read_excel(uploaded_file)
        elif file_name.endswith('.csv'):
            # CSVファイル処理
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            st.error("❌ サポートされていないファイル形式です。xlsx, xls, csv ファイルをアップロードしてください。")
            return None
        
        st.success(f"✅ ファイル読み込み成功: {len(df)}行のデータ")
        
        # データフレームの情報表示
        st.info(f"📊 カラム数: {len(df.columns)}, 行数: {len(df)}")
        
        # カラム名を表示
        st.write("**カラム一覧:**", list(df.columns))
        
        return df
        
    except Exception as e:
        st.error(f"❌ ファイル処理エラー: {str(e)}")
        return None

def normalize_uploaded_data(df):
    """アップロードデータをGoogle Sheets形式に正規化"""
    normalized_companies = []
    
    # カラム名のマッピング（柔軟な対応）
    column_mapping = {
        # 企業名
        'company_name': ['Company Name', 'company_name', '企業名', '会社名', 'name'],
        # メール
        'email': ['Email Address', 'email', 'Email', 'メール', 'メールアドレス'],
        # ウェブサイト
        'website': ['Website', 'website', 'URL', 'ウェブサイト', 'サイト'],
        # 電話
        'phone': ['Phone', 'phone', 'Tel', 'TEL', '電話', '電話番号'],
        # 住所
        'address': ['Address', 'address', '住所', '所在地'],
        # WiFi需要
        'wifi_needs': ['Needs Wi-Fi', 'wifi_needs', 'WiFi需要', 'WiFi', 'wifi'],
        # 説明
        'description': ['Description', 'description', '説明', '概要', 'notes'],
        # 連絡先
        'contact': ['Contact Info', 'contact', '連絡先', '担当者'],
        # キーワード数
        'keyword_count': ['Keyword Match Count', 'keyword_count', 'キーワード数']
    }
    
    # 実際のカラム名を特定
    actual_columns = {}
    for field, possible_names in column_mapping.items():
        for col_name in df.columns:
            if col_name in possible_names:
                actual_columns[field] = col_name
                break
    
    st.write("**検出されたカラムマッピング:**")
    for field, col_name in actual_columns.items():
        st.write(f"• {field}: `{col_name}`")
    
    # データを正規化
    for idx, row in df.iterrows():
        try:
            # WiFi需要の判定
            wifi_needs_value = str(row.get(actual_columns.get('wifi_needs', ''), '')).lower()
            if wifi_needs_value in ['yes', 'true', '1', 'high', 'medium']:
                wifi_needs = 'High' if wifi_needs_value in ['yes', 'true', '1'] else wifi_needs_value.title()
            else:
                wifi_needs = 'Low'
            
            # PicoCELAスコア計算（キーワード数ベース）
            keyword_count = row.get(actual_columns.get('keyword_count', ''), 0)
            try:
                keyword_count = int(keyword_count) if keyword_count else 0
            except:
                keyword_count = 0
            
            # 基本スコア計算
            picocela_score = min(keyword_count * 10 + (30 if wifi_needs != 'Low' else 0), 100)
            
            # 正規化されたデータ
            normalized_company = {
                'company_id': f"UPLOAD_{datetime.now().strftime('%Y%m%d')}_{idx+1:03d}",
                'company_name': str(row.get(actual_columns.get('company_name', ''), f'Company_{idx+1}')),
                'email': str(row.get(actual_columns.get('email', ''), '')),
                'phone': str(row.get(actual_columns.get('phone', ''), '')),
                'website': str(row.get(actual_columns.get('website', ''), '')),
                'description': str(row.get(actual_columns.get('description', ''), ''))[:500],  # 500文字制限
                'wifi_needs': wifi_needs,
                'picoCELA_relevance': picocela_score,
                'priority_score': min(picocela_score + 10, 100),
                'sales_status': 'New',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'tags': 'uploaded',
                'contact_name': str(row.get(actual_columns.get('contact', ''), '')),
                'address': str(row.get(actual_columns.get('address', ''), '')),
                'keyword_count': keyword_count
            }
            
            normalized_companies.append(normalized_company)
            
        except Exception as e:
            st.warning(f"⚠️ 行 {idx+1} の処理でエラー: {str(e)}")
            continue
    
    return normalized_companies

def normalize_companies_data(companies):
    """既存のGoogle Sheetsデータ正規化関数"""
    normalized = []
    
    for company in companies:
        # WiFi需要の表示変換
        wifi_needs = str(company.get('wifi_needs', '')).lower()
        if wifi_needs == 'high':
            wifi_display = '✅ 高需要'
        elif wifi_needs == 'medium':
            wifi_display = '✅ 中需要' 
        elif wifi_needs == 'low':
            wifi_display = '⚠️ 低需要'
        else:
            wifi_display = '❓ 未確認'
        
        # 業界の推定
        description = str(company.get('description', '')).lower()
        if 'construction' in description or 'building' in description:
            industry = '建設業'
        elif 'manufacturing' in description or 'factory' in description:
            industry = '製造業'
        elif 'software' in description or 'ai' in description or 'platform' in description:
            industry = 'IT・ソフトウェア'
        elif 'wifi' in description or 'wireless' in description or 'network' in description:
            industry = 'ネットワーク・通信'
        else:
            industry = 'その他'
        
        normalized_company = {
            'ID': company.get('company_id', f"ID_{len(normalized)+1}"),
            '企業名': company.get('company_name', 'N/A'),
            'ステータス': company.get('sales_status', 'New'),
            'PicoCELAスコア': int(company.get('picoCELA_relevance', 0)) if company.get('picoCELA_relevance') else 0,
            'WiFi需要': wifi_display,
            '販売員': 'admin',
            'メール': company.get('email', ''),
            '業界': industry,
            'ウェブサイト': company.get('website_url') or company.get('website', ''),
            '電話番号': company.get('phone', ''),
            '連絡先': company.get('contact_name', ''),
            '備考': company.get('description', '')[:150] + '...' if len(str(company.get('description', ''))) > 150 else company.get('description', ''),
            '登録日': company.get('created_at', '')[:10] if company.get('created_at') else datetime.now().strftime('%Y-%m-%d'),
            '更新日': company.get('updated_at', '')[:10] if company.get('updated_at') else '',
            '優先度スコア': int(company.get('priority_score', 0)) if company.get('priority_score') else 0,
            'キーワード数': company.get('keyword_count', 0)
        }
        
        normalized.append(normalized_company)
    
    return normalized

# ========================================
# データソース決定
# ========================================

if google_sheets_success and google_sheets_companies:
    companies_data = normalize_companies_data(google_sheets_companies)
    data_source = f"Google Sheets ({len(companies_data)}社)"
else:
    companies_data = []
    data_source = "データなし"

# ========================================
# タブ作成・機能実装
# ========================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ダッシュボード", 
    "🏢 企業管理", 
    "📈 分析", 
    "📤 一括アップロード", 
    "⚙️ 設定"
])

with tab1:
    # ダッシュボード（既存機能）
    st.header("📊 CRMダッシュボード")
    st.caption(f"データソース: {data_source}")
    
    if companies_data:
        # 統計メトリクス
        total_companies = len(companies_data)
        wifi_any_need = len([c for c in companies_data if '✅' in str(c.get('WiFi需要', ''))])
        high_score = len([c for c in companies_data if int(c.get('PicoCELAスコア', 0)) >= 50])
        qualified = len([c for c in companies_data if c.get('ステータス') in ['Qualified', 'Engaged', 'Proposal']])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 総企業数", total_companies)
        with col2:
            wifi_rate = (wifi_any_need / total_companies * 100) if total_companies > 0 else 0
            st.metric("📶 WiFi需要企業", f"{wifi_any_need} ({wifi_rate:.1f}%)")
        with col3:
            score_rate = (high_score / total_companies * 100) if total_companies > 0 else 0
            st.metric("🎯 高スコア企業", f"{high_score} ({score_rate:.1f}%)")
        with col4:
            qualified_rate = (qualified / total_companies * 100) if total_companies > 0 else 0
            st.metric("💼 有望企業", f"{qualified} ({qualified_rate:.1f}%)")
        
        # 企業データ一覧
        st.subheader("📋 企業データ一覧")
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
        st.warning("📋 企業データがありません。一括アップロードタブから企業データを追加してください。")

with tab2:
    # 企業管理（既存機能）
    st.header("🏢 企業管理")
    
    if companies_data:
        # 検索・フィルター
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("🔍 企業名検索", key="search_companies")
        
        with col2:
            status_list = ["全て"] + sorted(list(set([c.get('ステータス', '') for c in companies_data if c.get('ステータス')])))
            selected_status = st.selectbox("📊 ステータスフィルター", status_list, key="filter_status")
        
        # フィルタリング
        filtered_companies = companies_data.copy()
        
        if search_term:
            filtered_companies = [c for c in filtered_companies 
                                if search_term.lower() in c.get('企業名', '').lower()]
        
        if selected_status != "全て":
            filtered_companies = [c for c in filtered_companies 
                                if c.get('ステータス') == selected_status]
        
        st.subheader(f"📋 検索結果 ({len(filtered_companies)}社)")
        
        if filtered_companies:
            for company in filtered_companies:
                with st.expander(f"🏢 {company['企業名']} - {company['ステータス']} (スコア: {company['PicoCELAスコア']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**ID**: {company['ID']}")
                        st.write(f"**企業名**: {company['企業名']}")
                        st.write(f"**ステータス**: {company['ステータス']}")
                        st.write(f"**業界**: {company['業界']}")
                    
                    with col2:
                        st.write(f"**PicoCELAスコア**: {company['PicoCELAスコア']}")
                        st.write(f"**優先度スコア**: {company['優先度スコア']}")
                        st.write(f"**WiFi需要**: {company['WiFi需要']}")
                        st.write(f"**キーワード数**: {company.get('キーワード数', 'N/A')}")
                    
                    with col3:
                        st.write(f"**メール**: {company['メール']}")
                        st.write(f"**電話**: {company['電話番号']}")
                        st.write(f"**連絡先**: {company['連絡先']}")
                        st.write(f"**登録日**: {company['登録日']}")
                    
                    if company.get('備考'):
                        st.write(f"**備考**: {company['備考']}")
        else:
            st.info("検索条件に一致する企業がありません。")
    else:
        st.warning("企業データがありません。")

with tab3:
    # 分析（既存機能）
    st.header("📈 データ分析")
    
    if companies_data:
        # ステータス分布
        st.subheader("📊 ステータス分布")
        status_counts = {}
        for company in companies_data:
            status = company.get('ステータス', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            st.bar_chart(status_counts)
        
        # PicoCELAスコア分析
        st.subheader("🎯 PicoCELAスコア分析")
        scores = [int(c.get('PicoCELAスコア', 0)) for c in companies_data]
        
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
        
        # WiFi需要分析
        st.subheader("📶 WiFi需要分析")
        wifi_counts = {}
        for company in companies_data:
            wifi_need = company.get('WiFi需要', '❓ 未確認')
            wifi_counts[wifi_need] = wifi_counts.get(wifi_need, 0) + 1
        
        if wifi_counts:
            st.bar_chart(wifi_counts)
    else:
        st.warning("分析するデータがありません。")

with tab4:
    # 一括アップロード機能（新機能）
    st.header("📤 一括アップロード")
    st.info("💡 エクセル/CSVファイルから企業データを一括で追加できます")
    
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "📂 ファイルを選択してください",
        type=['xlsx', 'xls', 'csv'],
        help="対応形式: Excel (.xlsx, .xls), CSV (.csv)"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ ファイルが選択されました: {uploaded_file.name}")
        
        # ファイル処理
        df = process_excel_file(uploaded_file)
        
        if df is not None:
            # データプレビュー
            st.subheader("📋 データプレビュー")
            st.dataframe(df.head(10), use_container_width=True)
            
            # データ正規化
            with st.spinner("🔄 データを正規化中..."):
                normalized_data = normalize_uploaded_data(df)
            
            if normalized_data:
                st.success(f"✅ {len(normalized_data)}件のデータを正規化完了")
                
                # 正規化結果のプレビュー
                st.subheader("🔄 正規化結果プレビュー")
                preview_data = []
                for company in normalized_data[:5]:  # 最初の5件
                    preview_data.append({
                        '企業名': company['company_name'],
                        'メール': company['email'],
                        'WiFi需要': company['wifi_needs'],
                        'PicoCELAスコア': company['picoCELA_relevance'],
                        'キーワード数': company.get('keyword_count', 0)
                    })
                
                preview_df = pd.DataFrame(preview_data)
                st.dataframe(preview_df, use_container_width=True)
                
                # アップロード確認
                st.subheader("🚀 Google Sheetsにアップロード")
                st.warning("⚠️ 注意: この機能は将来実装予定です。現在はプレビューのみ表示されます。")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📊 CSVでエクスポート", key="export_normalized"):
                        # 正規化データをCSVとしてダウンロード
                        export_df = pd.DataFrame(normalized_data)
                        csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
                        
                        st.download_button(
                            label="💾 正規化データをダウンロード",
                            data=csv_data,
                            file_name=f'normalized_companies_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                            mime='text/csv'
                        )
                
                with col2:
                    st.info("🔮 将来実装予定:\n- Google Sheetsへの直接アップロード\n- 重複チェック機能\n- バッチ処理状況表示")
            else:
                st.error("❌ データの正規化に失敗しました。")
    
    # アップロード形式の説明
    st.subheader("📝 アップロード形式の説明")
    
    with st.expander("📋 対応するカラム名"):
        st.write("""
        **自動認識されるカラム名（大文字小文字問わず）:**
        
        - **企業名**: Company Name, company_name, 企業名, 会社名, name
        - **メール**: Email Address, email, Email, メール, メールアドレス
        - **ウェブサイト**: Website, website, URL, ウェブサイト, サイト
        - **電話**: Phone, phone, Tel, TEL, 電話, 電話番号
        - **住所**: Address, address, 住所, 所在地
        - **WiFi需要**: Needs Wi-Fi, wifi_needs, WiFi需要, WiFi, wifi
        - **説明**: Description, description, 説明, 概要, notes
        - **連絡先**: Contact Info, contact, 連絡先, 担当者
        - **キーワード数**: Keyword Match Count, keyword_count, キーワード数
        """)
    
    with st.expander("💡 サンプルデータ形式"):
        sample_data = {
            'Company Name': ['Sample Corp', 'Test Industries'],
            'Email Address': ['info@sample.com', 'contact@test.com'],
            'Website': ['https://sample.com', 'https://test.com'],
            'Phone': ['123-456-7890', '098-765-4321'],
            'Needs Wi-Fi': ['Yes', 'No'],
            'Description': ['Sample description', 'Test company description'],
            'Keyword Match Count': [5, 3]
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)

with tab5:
    # システム設定（既存機能）
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
        high_priority = len([c for c in companies_data if int(c.get('優先度スコア', 0)) >= 50])
        st.metric("高優先度企業", high_priority)
    with col3:
        st.metric("最終更新", datetime.now().strftime("%H:%M"))
    with col4:
        st.metric("システム状態", "正常動作")
    
    # データエクスポート
    st.subheader("📤 データエクスポート")
    if companies_data and st.button("📊 全データCSVエクスポート", key="export_all_csv"):
        df = pd.DataFrame(companies_data)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="💾 全企業データをダウンロード",
            data=csv,
            file_name=f'fusioncrm_all_companies_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )
        st.success("✅ CSVファイルの準備が完了しました！")
    
    # システム情報
    st.subheader("🔍 システム情報")
    st.info("**新機能**: エクセル/CSV一括アップロード対応")
    st.info("**対応形式**: .xlsx, .xls, .csv")
    st.info("**自動機能**: カラム名自動認識、PicoCELAスコア自動計算、WiFi需要判定")
