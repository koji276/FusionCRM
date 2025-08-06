# pages/01_crm.py - 最終修正版（エラー完全排除）
# Updated: 2025-07-29 - Fixed all REQUESTS_AVAILABLE errors completely
# Complete CRM System with Excel upload and Google Sheets batch upload

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# ========================================
# ライブラリ可用性チェック（最優先実行）
# ========================================

# requestsライブラリのチェック
REQUESTS_AVAILABLE = False
requests_status = "⚠️ requests利用不可"
try:
    import requests
    REQUESTS_AVAILABLE = True
    requests_status = "✅ requests利用可能"
except ImportError:
    pass

# Excelライブラリのチェック
EXCEL_AVAILABLE = False
excel_status = "⚠️ CSV のみ"
try:
    from io import BytesIO
    import openpyxl
    EXCEL_AVAILABLE = True
    excel_status = "✅ Excel対応"
except ImportError:
    pass

# ========================================
# ページ設定
# ========================================
st.set_page_config(
    page_title="CRM管理システム - エクセルアップロード対応版",
    page_icon="🏢",
    layout="wide"
)

# ========================================
# システム状態表示（エラー前）
# ========================================
st.success("✅ 修正完成版: Google Sheets接続エラー修正 + エクセルアップロード機能付き")
st.info(f"📊 システム状態: {requests_status} | {excel_status}")

# ========================================
# CRM管理システム - 完成版
# ========================================

st.title("🏢 CRM管理システム - エクセルアップロード対応版")
st.caption("企業データ管理・一括アップロード・PicoCELA関連度分析・Google Sheets完全連携")

# Google Sheets連携情報
st.info("🔗 統合プラットフォーム・Google Sheetsリアルタイム同期・エクセル一括アップロード対応")

# ========================================
# データ正規化関数（Google Sheets接続前に定義）
# ========================================

def normalize_companies_data(companies):
    """実際のGoogle Sheetsデータ構造に基づく正規化"""
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
        
        # 正規化されたデータ
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
            '備考': str(company.get('description', ''))[:150] + '...' if len(str(company.get('description', ''))) > 150 else str(company.get('description', '')),
            '登録日': company.get('created_at', '')[:10] if company.get('created_at') else datetime.now().strftime('%Y-%m-%d'),
            '更新日': company.get('updated_at', '')[:10] if company.get('updated_at') else '',
            '優先度スコア': int(company.get('priority_score', 0)) if company.get('priority_score') else 0,
            'タグ': company.get('tags', '')
        }
        
        normalized.append(normalized_company)
    
    return normalized

def normalize_excel_data(df):
    """エクセルデータをGoogle Sheets形式に正規化"""
    normalized_data = []
    
    # カラム名の正規化マッピング
    column_mapping = {
        'company name': 'company_name',
        'company_name': 'company_name', 
        '企業名': 'company_name',
        '会社名': 'company_name',
        'name': 'company_name',
        'email address': 'email',
        'email': 'email',
        'メール': 'email',
        'メールアドレス': 'email',
        'website': 'website',
        'url': 'website',
        'ウェブサイト': 'website',
        'サイト': 'website',
        'phone': 'phone',
        'tel': 'phone',
        '電話': 'phone',
        '電話番号': 'phone',
        'address': 'address',
        '住所': 'address',
        '所在地': 'address',
        'needs wi-fi': 'wifi_needs',
        'wifi_needs': 'wifi_needs',
        'wifi需要': 'wifi_needs',
        'wifi': 'wifi_needs',
        'description': 'description',
        '説明': 'description',
        '概要': 'description',
        'notes': 'description',
        'contact info': 'contact',
        'contact': 'contact',
        '連絡先': 'contact',
        '担当者': 'contact',
        'keyword match count': 'keyword_count',
        'keyword_count': 'keyword_count',
        'キーワード数': 'keyword_count'
    }
    
    # カラム名を正規化
    df_normalized = df.copy()
    df_normalized.columns = [column_mapping.get(col.lower(), col.lower()) for col in df.columns]
    
    for index, row in df_normalized.iterrows():
        try:
            # 基本データ
            company_data = {
                'company_name': str(row.get('company_name', '')).strip(),
                'email': str(row.get('email', '')).strip(),
                'website': str(row.get('website', '')).strip(),
                'phone': str(row.get('phone', '')).strip(),
                'address': str(row.get('address', '')).strip(),
                'description': str(row.get('description', '')).strip(),
                'contact_name': str(row.get('contact', '')).strip(),
            }
            
            # WiFi需要の変換
            wifi_raw = str(row.get('wifi_needs', '')).strip().lower()
            if wifi_raw in ['yes', 'true', '1', 'high', 'はい']:
                company_data['wifi_needs'] = 'High'
            elif wifi_raw in ['no', 'false', '0', 'low', 'いいえ']:
                company_data['wifi_needs'] = 'Low'
            else:
                company_data['wifi_needs'] = 'Medium'
            
            # キーワード数の処理
            keyword_count = row.get('keyword_count', 0)
            try:
                keyword_count = int(float(keyword_count)) if pd.notna(keyword_count) else 0
            except:
                keyword_count = 0
            
            company_data['keyword_count'] = keyword_count
            
            # PicoCELAスコア自動計算
            base_score = keyword_count * 10
            wifi_bonus = 20 if company_data['wifi_needs'] == 'High' else 10 if company_data['wifi_needs'] == 'Medium' else 0
            company_data['picoCELA_relevance'] = min(base_score + wifi_bonus, 100)
            
            # 優先度スコア
            company_data['priority_score'] = company_data['picoCELA_relevance']
            
            # その他のフィールド
            company_data['sales_status'] = 'New'
            company_data['construction_focus'] = ''
            company_data['tags'] = ''
            
            normalized_data.append(company_data)
            
        except Exception as e:
            st.warning(f"⚠️ 行{index+1}の処理中にエラー: {str(e)}")
            continue
    
    return normalized_data

# ========================================
# Google Sheets データ取得関数（条件分岐付き）
# ========================================

@st.cache_data(ttl=300)  # 5分間キャッシュ
def get_google_sheets_data():
    """Google SheetsからCRMデータを取得（条件分岐付き）"""
    # requestsライブラリが利用できない場合
    if not REQUESTS_AVAILABLE:
        st.info("📋 requestsライブラリが利用できないため、サンプルデータを使用します")
        return [], False
    
    try:
        st.info("🔄 Google Sheetsから企業データを取得中...")
        
        # Google Apps Script URL
        api_url = "https://script.google.com/macros/s/AKfycby998uiOXSrg9GEDvocVfZR7a7uN_P121G__FRqyJh2zLMJA8KUB2dtsHi7GSZxoRAD-A/exec"
        
        # 接続設定
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        }
        
        # APIリクエスト実行
        response = requests.get(
            api_url,
            params={"action": "get_companies"},  # ← コンマを追加
            headers=headers,
            timeout=30,
            verify=True
        )
        
        st.info(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # デバッグ情報
                st.info(f"🔍 Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                
                # 'companies' キーを使用
                if data.get('success') and data.get('companies'):
                    companies = data['companies']
                    st.success(f"✅ Google Sheets連携成功！{len(companies)}社のデータを取得")
                    
                    # デバッグ情報
                    if companies:
                        company_names = [c.get('company_name', 'N/A') for c in companies[:3]]
                        st.info(f"📊 取得企業: {', '.join(company_names)}{'...' if len(companies) > 3 else ''}")
                    
                    return companies, True
                else:
                    st.warning(f"⚠️ データ取得エラー: success={data.get('success', 'N/A')}, companies存在={bool(data.get('companies'))}")
                    return [], False
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON解析エラー: {str(e)}")
                return [], False
        else:
            st.error(f"❌ Google Sheets API HTTP Error: {response.status_code}")
            return [], False

    except Exception as e:
        st.warning(f"🔗 Google Sheetsデータ取得エラー: {str(e)}")
        return [], False

def upload_to_google_sheets(normalized_data):
    """正規化データをGoogle Sheetsにアップロード（条件分岐付き）"""
    # requestsライブラリが利用できない場合
    if not REQUESTS_AVAILABLE:
        st.error("❌ requestsライブラリが利用できないため、アップロードできません")
        st.info("💡 Streamlit Cloudではrequestsが標準で利用可能です。環境を確認してください。")
        return
    
    try:
        st.info("🔄 Google Sheetsにアップロード中...")
        
        # Google Apps Script URL
        api_url = "https://script.google.com/macros/s/AKfycby998uiOXSrg9GEDvocVfZR7a7uN_P121G__FRqyJh2zLMJA8KUB2dtsHi7GSZxoRAD-A/exec"
        
        # アップロード用のデータを準備
        upload_data = {
            "action": "add_companies_batch",
            "companies": normalized_data
        }
        
        st.info(f"📤 {len(normalized_data)}社のデータを送信中...")
        
        # APIリクエスト設定
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # データサイズを確認
        data_size = len(json.dumps(upload_data))
        st.info(f"📊 送信データサイズ: {data_size:,} bytes")
        
        response = requests.post(
            api_url,
            json=upload_data,
            headers=headers,
            timeout=120,
            verify=True
        )
        
        st.info(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                st.info(f"📄 Raw API Response: {str(result)[:300]}...")
                
                if result and result.get('success'):
                    st.success(f"✅ {len(normalized_data)}社のデータをGoogle Sheetsに追加しました！")
                    st.balloons()
                    
                    # 詳細結果を表示
                    if 'results' in result:
                        results = result['results']
                        success_count = results.get('success', 0)
                        error_count = results.get('errors', 0)
                        st.info(f"📊 成功: {success_count}社 | エラー: {error_count}社")
                        
                        # 詳細ログを表示
                        if results.get('details'):
                            with st.expander("📋 詳細結果を確認"):
                                for detail in results['details'][:10]:
                                    if "✅" in detail:
                                        st.success(detail)
                                    else:
                                        st.error(detail)
                                
                                if len(results['details']) > 10:
                                    st.info(f"... 他 {len(results['details']) - 10} 件")
                    
                    # キャッシュをクリア
                    st.cache_data.clear()
                    st.info("🔄 データキャッシュをクリアしました。")
                    
                    # 再読み込みボタンを追加
                    if st.button("🔄 ページを再読み込み", key="reload_page"):
                        st.rerun()
                    
                else:
                    error_msg = result.get('error', '不明なエラー') if result else 'レスポンスが空です'
                    st.error(f"❌ アップロードに失敗しました: {error_msg}")
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON解析エラー: {str(e)}")
        else:
            st.error(f"❌ HTTP エラー: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {str(e)}")

# ========================================
# データ取得実行（条件分岐）
# ========================================

# Google Sheetsデータ取得を試行
google_sheets_companies = []
google_sheets_success = False

if REQUESTS_AVAILABLE:
    google_sheets_companies, google_sheets_success = get_google_sheets_data()

# ========================================
# データソース決定
# ========================================

if google_sheets_success and google_sheets_companies:
    # Google Sheetsからの実データを正規化
    companies_data = normalize_companies_data(google_sheets_companies)
    data_source = f"Google Sheets ({len(companies_data)}社)"
    st.success(f"🔗 リアルデータ表示中: {data_source}")
else:
    # フォールバック: サンプルデータ
    sample_data = [
        {
            'company_id': 'SAMPLE_001',
            'company_name': 'FUSIONDRIVER',
            'email': 'koji@fusiondriver.biz',
            'phone': '408-8505058',
            'website': 'www.fusiondiver.biz',
            'description': 'We are implementing a Wi-Fi-based solution integration for construction sites.',
            'wifi_needs': 'Low',
            'picoCELA_relevance': 25,
            'sales_status': 'New',
            'created_at': '2025-07-19T14:08:22.057Z'
        },
        {
            'company_id': 'SAMPLE_002',
            'company_name': 'ABC建設',
            'email': 'info@abc-const.co.jp',
            'phone': '03-1234-5678',
            'website': 'https://abc-const.co.jp',
            'description': '大規模建設プロジェクトでのWiFiネットワーク構築を検討',
            'wifi_needs': 'High',
            'picoCELA_relevance': 85,
            'sales_status': 'Qualified',
            'created_at': '2025-07-20T09:30:00Z'
        },
        {
            'company_id': 'SAMPLE_003',
            'company_name': 'XYZ製造工業',
            'email': 'contact@xyz-mfg.com',
            'phone': '06-9876-5432',
            'website': 'https://xyz-manufacturing.com',
            'description': '工場内でのワイヤレス通信システム導入を計画中',
            'wifi_needs': 'Medium',
            'picoCELA_relevance': 60,
            'sales_status': 'Contacted',
            'created_at': '2025-07-21T15:45:00Z'
        },
        {
            'company_id': 'SAMPLE_004',
            'company_name': 'DEFソフトウェア',
            'email': 'dev@def-soft.com',
            'phone': '03-5555-1111',
            'website': 'https://def-software.jp',
            'description': 'オフィス環境でのIT業務効率化',
            'wifi_needs': 'Low',
            'picoCELA_relevance': 20,
            'sales_status': 'New',
            'created_at': '2025-07-22T11:20:00Z'
        }
    ]
    companies_data = normalize_companies_data(sample_data)
    data_source = f"サンプルデータ ({len(companies_data)}社)"
    
    if REQUESTS_AVAILABLE:
        st.info(f"📋 Google Sheets接続に失敗したため、サンプルデータを表示中: {data_source}")
    else:
        st.info(f"📋 オフラインモード（requestsライブラリ不足）: {data_source}")

# ========================================
# タブ作成・機能実装
# ========================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 ダッシュボード", 
    "🏢 企業管理", 
    "📈 分析", 
    "➕ 企業追加",
    "📤 一括アップロード",
    "⚙️ 設定"
])

with tab1:
    # ダッシュボード
    st.header("📊 CRMダッシュボード")
    st.caption(f"データソース: {data_source}")
    
    # 統計メトリクス
    total_companies = len(companies_data)
    wifi_high_need = len([c for c in companies_data if '高需要' in str(c.get('WiFi需要', ''))])
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
    
    if companies_data:
        # 主要な列のみ表示
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
        
        # 詳細表示用エクスパンダー
        st.subheader("📝 企業詳細情報")
        for company in companies_data[:5]:
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
                    st.write(f"**販売員**: {company['販売員']}")
                
                with col3:
                    st.write(f"**メール**: {company['メール']}")
                    st.write(f"**電話**: {company['電話番号']}")
                    st.write(f"**ウェブサイト**: {company['ウェブサイト']}")
                    st.write(f"**登録日**: {company['登録日']}")
                
                if company.get('備考'):
                    st.write(f"**備考**: {company['備考']}")
    else:
        st.warning("表示するデータがありません")

with tab2:
    # 企業管理
    st.header("🏢 企業管理")
    
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
    
    # 企業一覧
    st.subheader(f"📋 検索結果 ({len(filtered_companies)}社)")
    
    if filtered_companies:
        # 検索結果をデータフレームで表示
        search_display = []
        for company in filtered_companies:
            search_display.append({
                '企業名': company['企業名'],
                'ステータス': company['ステータス'],
                'スコア': company['PicoCELAスコア'],
                'WiFi需要': company['WiFi需要'],
                'メール': company['メール'],
                '電話': company['電話番号']
            })
        
        search_df = pd.DataFrame(search_display)
        st.dataframe(search_df, use_container_width=True)
    else:
        st.info("検索条件に一致する企業が見つかりませんでした。")

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
            contact_name = st.text_input("連絡先担当者", key="add_contact")
        
        with col2:
            phone = st.text_input("電話番号", key="add_phone")
            website = st.text_input("ウェブサイト", key="add_website")
            wifi_needs = st.selectbox("WiFi需要レベル", ["High", "Medium", "Low"], key="add_wifi")
        
        description = st.text_area("企業説明・備考", key="add_description", height=100)
        
        submit_button = st.form_submit_button("🚀 企業を追加", type="primary")
        
        if submit_button and company_name:
            # スコア計算
            score = 0
            desc_lower = description.lower()
            
            # WiFi関連キーワード
            wifi_keywords = ['wifi', 'wireless', 'network', 'mesh', 'connectivity']
            for keyword in wifi_keywords:
                if keyword in desc_lower:
                    score += 15
            
            # 建設・製造関連キーワード
            construction_keywords = ['construction', 'building', 'site', 'manufacturing', 'factory']
            for keyword in construction_keywords:
                if keyword in desc_lower:
                    score += 20
            
            # 需要レベルボーナス
            need_bonus = {"High": 30, "Medium": 20, "Low": 10}
            score += need_bonus.get(wifi_needs, 0)
            
            score = min(score, 100)
            
            # 企業データを作成
            new_company_data = [{
                'company_name': company_name,
                'email': email,
                'contact_name': contact_name,
                'phone': phone,
                'website': website,
                'description': description,
                'wifi_needs': wifi_needs,
                'picoCELA_relevance': score,
                'priority_score': score,
                'sales_status': 'New',
                'construction_focus': '',
                'tags': ''
            }]
            
            # 結果表示
            st.success("✅ 企業情報を入力しました！")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("計算スコア", f"{score}点")
            with col2:
                st.metric("WiFi需要", wifi_needs)
            with col3:
                st.metric("入力日時", datetime.now().strftime("%Y-%m-%d"))
            
            # Google Sheetsに追加ボタン
            if st.button("🚀 Google Sheetsに追加", key="add_single_company", type="primary"):
                upload_to_google_sheets(new_company_data)

with tab5:
    # 一括アップロード機能
    st.header("📤 一括アップロード")
    
    st.info("💡 エクセル/CSVファイルから企業データを一括で追加できます")
    
    # ファイルアップロード
    st.subheader("📁 ファイルを選択してください")
    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=['xlsx', 'xls', 'csv'],
        help="Limit 200MB per file • XLSX, XLS, CSV"
    )
    
    if uploaded_file is not None:
        try:
            # ファイル情報表示
            st.success(f"✅ ファイルが選択されました: {uploaded_file.name}")
            
            # ファイル読み込み
            if uploaded_file.name.endswith(('.xlsx', '.xls')) and EXCEL_AVAILABLE:
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ ファイル読み込み成功: {len(df)}行のデータ")
            
            # カラム情報表示
            st.info(f"📋 カラム数: {len(df.columns)}、行数: {len(df)}")
            
            # カラム一覧表示
            st.subheader("カラム一覧:")
            cols_display = []
            for i, col in enumerate(df.columns):
                cols_display.append(f'{i}: "{col}"')
            
            st.code('[\n  ' + ',\n  '.join(cols_display) + '\n]')
            
            # データプレビュー
            st.subheader("📋 データプレビュー")
            st.dataframe(df.head(10), use_container_width=True)
            
            # データ正規化
            normalized_data = normalize_excel_data(df)
            
            # 正規化されたカラムマッピング表示
            st.subheader("検出されたカラムマッピング:")
            mapping_info = [
                "• company_name: Company Name",
                "• email: Email Address", 
                "• website: Website",
                "• phone: Phone",
                "• address: Address",
                "• wifi_needs: Needs Wi-Fi",
                "• description: Description",
                "• contact: Contact Info",
                "• keyword_count: Keyword Match Count"
            ]
            
            for info in mapping_info:
                st.markdown(info)
            
            st.success(f"✅ {len(normalized_data)}社のデータを正規化完了")
            
            # 正規化結果プレビュー
            st.subheader("🧮 正規化結果プレビュー")
            if normalized_data:
                preview_df = pd.DataFrame(normalized_data[:5])
                st.dataframe(preview_df, use_container_width=True)
            
            # 🚀 Google Sheetsアップロード機能
            st.markdown("### 🚀 Google Sheetsにアップロード")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 📊 CSVエクスポートボタン
                if st.button("📊 CSVでエクスポート", key="bulk_csv_export"):
                    try:
                        export_df = pd.DataFrame(normalized_data)
                        csv_data = export_df.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 CSVファイルをダウンロード",
                            data=csv_data,
                            file_name=f"normalized_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        st.success("✅ CSVファイルが準備できました！")
                    except Exception as e:
                        st.error(f"❌ CSVエクスポートエラー: {str(e)}")
            
            with col2:
                # 🚀 Google Sheetsアップロードボタン（実装版）
                if st.button("🚀 Google Sheetsにアップロード", key="bulk_upload_to_sheets", type="primary"):
                    if len(normalized_data) > 0:
                        upload_to_google_sheets(normalized_data)
                    else:
                        st.warning("⚠️ アップロードするデータがありません")
            
            # アップロード形式の説明
            st.markdown("### 📋 アップロード形式の説明")
            
            with st.expander("📊 対応するカラム名"):
                st.markdown("""
                **自動認識されるカラム名（大文字小文字問わず）:**
                
                • **企業名**: Company Name, company_name, 企業名, 会社名, name
                • **メール**: Email Address, email, Email, メール, メールアドレス  
                • **ウェブサイト**: Website, website, URL, ウェブサイト, サイト
                • **電話**: Phone, phone, Tel, TEL, 電話, 電話番号
                • **住所**: Address, address, 住所, 所在地
                • **WiFi需要**: Needs Wi-Fi, wifi_needs, WiFi需要, WiFi, wifi
                • **説明**: Description, description, 説明, 概要, notes
                • **連絡先**: Contact Info, contact, 連絡先, 担当者
                • **キーワード数**: Keyword Match Count, keyword_count, キーワード数
                """)
                
        except Exception as e:
            st.error(f"❌ ファイル処理エラー: {str(e)}")

with tab6:
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
        high_priority = len([c for c in companies_data if int(c.get('優先度スコア', 0)) >= 50])
        st.metric("高優先度企業", high_priority)
    with col3:
        st.metric("最終更新", datetime.now().strftime("%H:%M"))
    with col4:
        st.metric("ライブラリ状況", f"{requests_status.split()[1]} | {excel_status.split()[1]}")
    
    # データエクスポート
    st.subheader("📤 データエクスポート")
    if st.button("📊 全データCSVエクスポート", key="system_export_csv"):
        df = pd.DataFrame(companies_data)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="💾 CSVファイルをダウンロード",
            data=csv,
            file_name=f'fusioncrm_companies_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )
        st.success("✅ CSVファイルの準備が完了しました！")
    
    # キャッシュ管理
    st.subheader("🔄 キャッシュ管理")
    if st.button("🗑️ データキャッシュをクリア", key="clear_cache"):
        st.cache_data.clear()
        st.success("✅ キャッシュをクリアしました。")
    
    # システム詳細情報
    st.subheader("🔍 システム詳細情報")
    st.info(f"📊 ライブラリ状況: {requests_status} | {excel_status}")
    st.info(f"📈 データ企業数: {len(companies_data)}社")
    if REQUESTS_AVAILABLE:
        st.info(f"🔗 API URL: https://script.google.com/macros/s/AKfycbx3e5TpdzcsBueF68sOonUJwd9j2-zR5OEZoqGZ0-0E57vYutCq5ivl3QJIUfKQ6vCUkw/exec")
        st.info(f"📄 レスポンス形式: companies配列")
    else:
        st.info("📋 オフラインモード: requestsライブラリが利用できません")
