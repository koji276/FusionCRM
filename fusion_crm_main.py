import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import re

# ページ設定
st.set_page_config(
    page_title="FusionCRM - PicoCELA営業管理システム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class GoogleSheetsManager:
    """Google Apps Script経由でGoogle Sheetsを管理するクラス"""
    
    def __init__(self, script_url=None):
        self.script_url = script_url
        self.is_connected = False
        
    def test_connection(self):
        """接続テスト"""
        if not self.script_url:
            return False, "Google Apps Script URLが設定されていません"
            
        try:
            # テスト用のPINGリクエスト
            response = requests.post(
                self.script_url,
                json={"action": "ping"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.is_connected = True
                    return True, "接続成功！"
                else:
                    return False, f"エラー: {result.get('message', '不明なエラー')}"
            else:
                return False, f"HTTP エラー: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "接続タイムアウト（10秒）"
        except requests.exceptions.RequestException as e:
            return False, f"接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラー: {str(e)}"
    
    def get_companies(self):
        """企業データを取得"""
        if not self.is_connected:
            return []
            
        try:
            response = requests.post(
                self.script_url,
                json={"action": "getCompanies"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return result.get("data", [])
            return []
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return []
    
    def add_company(self, company_data):
        """企業を追加"""
        if not self.is_connected:
            return False, "接続されていません"
            
        try:
            response = requests.post(
                self.script_url,
                json={
                    "action": "addCompany",
                    "data": company_data
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"追加エラー: {str(e)}"
    
    def update_company_status(self, company_id, new_status, note=""):
        """企業ステータスを更新"""
        if not self.is_connected:
            return False, "接続されていません"
            
        try:
            response = requests.post(
                self.script_url,
                json={
                    "action": "updateStatus",
                    "companyId": company_id,
                    "status": new_status,
                    "note": note
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"更新エラー: {str(e)}"

    def import_bulk_data(self, companies_list):
        """複数企業データを一括インポート"""
        if not self.is_connected:
            return False, "接続されていません"
            
        try:
            response = requests.post(
                self.script_url,
                json={
                    "action": "bulkImport",
                    "companies": companies_list
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"一括インポートエラー: {str(e)}"

def init_session_state():
    """セッション状態を初期化"""
    if 'sheets_manager' not in st.session_state:
        st.session_state.sheets_manager = None
    if 'companies_data' not in st.session_state:
        st.session_state.companies_data = []
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None

def show_connection_setup():
    """Google Apps Script接続設定画面"""
    st.markdown('<h1 class="main-header">🚀 FusionCRM - PicoCELA営業管理システム</h1>', unsafe_allow_html=True)
    st.markdown("### ☁️ Google Sheets版（クラウド対応）")
    
    if st.session_state.sheets_manager and st.session_state.sheets_manager.is_connected:
        st.markdown("""
        <div class="success-box">
            ✅ <strong>Google Sheets接続中</strong> - システム準備完了
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("""
    <div class="info-box">
        📋 <strong>セットアップが必要です</strong><br>
        Google Apps Scriptとの接続を設定してください。
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("🔧 Google Apps Script接続設定", expanded=True):
        st.markdown("""
        **📋 セットアップ手順:**
        1. [Google Apps Script](https://script.google.com/) にアクセス
        2. 新しいプロジェクトを作成
        3. 提供されたコードを貼り付け
        4. デプロイして Web アプリURLを取得
        5. 下記にURLを入力して接続テスト
        """)
        
        # 既知のURLを事前入力
        default_url = "https://script.google.com/macros/s/AKfycbw3nXJ0vQGBDr_RfZGmYRy2rWH4Jv02ZfelpMCC-oKk1sgkiDB0RYIrh2Ym3De1_aKv/exec"
        
        script_url = st.text_input(
            "📍 Google Apps Script Web アプリ URL:",
            value=default_url,
            placeholder="https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec",
            help="Google Apps ScriptでデプロイしたウェブアプリのURLを入力してください"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔗 接続テスト", type="primary"):
                if script_url:
                    with st.spinner("接続テスト中..."):
                        manager = GoogleSheetsManager(script_url)
                        success, message = manager.test_connection()
                        
                        if success:
                            st.session_state.sheets_manager = manager
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("URLを入力してください")
        
        with col2:
            if script_url:
                st.info("💡 URLが入力されました。接続テストを実行してください。")

def show_dashboard():
    """メインダッシュボード"""
    if not st.session_state.sheets_manager or not st.session_state.sheets_manager.is_connected:
        show_connection_setup()
        return
    
    st.markdown('<h1 class="main-header">📊 FusionCRM Dashboard</h1>', unsafe_allow_html=True)
    
    # データ更新ボタン
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 データ更新", type="secondary"):
            with st.spinner("データを取得中..."):
                st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
                st.session_state.last_refresh = datetime.now()
                st.success("データを更新しました！")
    
    with col2:
        if st.session_state.last_refresh:
            st.info(f"最終更新: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # 企業データがない場合は自動取得
    if not st.session_state.companies_data:
        with st.spinner("企業データを読み込み中..."):
            st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
    
    companies = st.session_state.companies_data
    
    if not companies:
        st.warning("📋 企業データがありません。新しい企業を追加するか、データをインポートしてください。")
        
        # サンプルデータ追加オプション
        with st.expander("🎯 サンプルデータを追加"):
            if st.button("📊 サンプル企業データを追加", type="primary"):
                sample_companies = [
                    {
                        "name": "テスト建設株式会社",
                        "industry": "建設業",
                        "website": "https://test-construction.com",
                        "contact_person": "山田太郎",
                        "email": "yamada@test-construction.com",
                        "phone": "03-1234-5678",
                        "picoCela_score": 8,
                        "notes": "メッシュネットワークに興味あり",
                        "status": "New"
                    },
                    {
                        "name": "サンプル製造業株式会社",
                        "industry": "製造業",
                        "website": "https://sample-manufacturing.com",
                        "contact_person": "佐藤花子",
                        "email": "sato@sample-manufacturing.com",
                        "phone": "06-9876-5432",
                        "picoCela_score": 6,
                        "notes": "工場でのWiFi環境改善を検討",
                        "status": "Contacted"
                    }
                ]
                
                with st.spinner("サンプルデータを追加中..."):
                    for company in sample_companies:
                        success, message = st.session_state.sheets_manager.add_company(company)
                        if not success:
                            st.error(f"追加失敗: {message}")
                            break
                    else:
                        st.success("✅ サンプルデータを追加しました！")
                        st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
                        st.rerun()
        return
    
    # KPIメトリクス
    df = pd.DataFrame(companies)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏢 総企業数", len(df))
    
    with col2:
        if 'status' in df.columns:
            qualified_count = len(df[df['status'] == 'Qualified'])
            st.metric("⭐ 有望企業", qualified_count)
        else:
            st.metric("⭐ 有望企業", 0)
    
    with col3:
        if 'picoCela_score' in df.columns:
            high_score = len(df[df['picoCela_score'] >= 7])
            st.metric("🎯 高関連度企業", high_score)
        else:
            st.metric("🎯 高関連度企業", 0)
    
    with col4:
        if 'status' in df.columns:
            new_count = len(df[df['status'] == 'New'])
            st.metric("🆕 新規企業", new_count)
        else:
            st.metric("🆕 新規企業", 0)
    
    # ステータス分布チャート
    if 'status' in df.columns and not df.empty:
        st.markdown("### 📊 ステータス分布")
        status_counts = df['status'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="企業ステータス分布",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 企業リスト
    st.markdown("### 🏢 企業一覧")
    
    # フィルター
    col1, col2 = st.columns(2)
    with col1:
        if 'status' in df.columns:
            status_filter = st.selectbox(
                "ステータスでフィルター:",
                ["全て"] + list(df['status'].unique())
            )
        else:
            status_filter = "全て"
    
    with col2:
        if 'picoCela_score' in df.columns:
            score_filter = st.slider(
                "PicoCELA関連度スコア以上:",
                min_value=0,
                max_value=10,
                value=0
            )
        else:
            score_filter = 0
    
    # フィルター適用
    filtered_df = df.copy()
    if status_filter != "全て" and 'status' in df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    if 'picoCela_score' in df.columns:
        filtered_df = filtered_df[filtered_df['picoCela_score'] >= score_filter]
    
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("フィルター条件に一致する企業がありません。")

def show_company_management():
    """企業管理画面"""
    if not st.session_state.sheets_manager or not st.session_state.sheets_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 🏢 企業管理")
    
    tab1, tab2, tab3 = st.tabs(["➕ 企業追加", "✏️ 企業編集", "📋 企業一覧"])
    
    with tab1:
        show_add_company()
    
    with tab2:
        show_edit_company()
    
    with tab3:
        show_company_list()

def show_add_company():
    """企業追加画面"""
    st.markdown("#### ➕ 新規企業追加")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("🏢 企業名*", placeholder="例: 株式会社○○建設")
            industry = st.selectbox(
                "🏗️ 業界",
                ["建設業", "製造業", "IT・通信", "不動産", "エネルギー", "運輸・物流", "その他"]
            )
            website = st.text_input("🌐 ウェブサイト", placeholder="https://example.com")
        
        with col2:
            contact_person = st.text_input("👤 担当者名", placeholder="山田太郎")
            email = st.text_input("📧 メールアドレス", placeholder="yamada@example.com")
            phone = st.text_input("📞 電話番号", placeholder="03-1234-5678")
        
        picoCela_score = st.slider(
            "🎯 PicoCELA関連度スコア",
            min_value=1,
            max_value=10,
            value=5,
            help="1: 関連性低い ← → 10: 関連性高い"
        )
        
        notes = st.text_area("📝 備考", placeholder="追加情報やメモ")
        
        submitted = st.form_submit_button("✅ 企業を追加", type="primary")
        
        if submitted:
            if not company_name:
                st.error("❌ 企業名は必須です")
            else:
                company_data = {
                    "name": company_name,
                    "industry": industry,
                    "website": website,
                    "contact_person": contact_person,
                    "email": email,
                    "phone": phone,
                    "picoCela_score": picoCela_score,
                    "notes": notes,
                    "status": "New",
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with st.spinner("企業を追加中..."):
                    success, message = st.session_state.sheets_manager.add_company(company_data)
                    
                    if success:
                        st.success(f"✅ {company_name} を追加しました！")
                        # データを更新
                        st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ 追加失敗: {message}")

def show_edit_company():
    """企業編集画面"""
    st.markdown("#### ✏️ 企業編集")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 企業データがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 企業選択
    company_names = df['name'].tolist() if 'name' in df.columns else []
    if not company_names:
        st.warning("表示可能な企業がありません")
        return
        
    selected_company = st.selectbox("🏢 編集する企業を選択:", company_names)
    
    if selected_company:
        company_row = df[df['name'] == selected_company].iloc[0]
        
        st.markdown("#### 企業情報編集")
        
        with st.form("edit_company_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                current_status = company_row.get('status', 'New')
                new_status = st.selectbox(
                    "📊 ステータス:",
                    ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost", "Dormant"],
                    index=["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost", "Dormant"].index(current_status) if current_status in ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost", "Dormant"] else 0
                )
                
                picoCela_score = st.slider(
                    "🎯 PicoCELA関連度スコア:",
                    min_value=1,
                    max_value=10,
                    value=int(company_row.get('picoCela_score', 5))
                )
            
            with col2:
                st.info(f"📊 現在のステータス: **{current_status}**")
                st.info(f"📧 メール: {company_row.get('email', 'N/A')}")
                st.info(f"📞 電話: {company_row.get('phone', 'N/A')}")
            
            note = st.text_area("📝 更新理由・メモ:", placeholder="ステータス変更の理由を記入")
            
            submitted = st.form_submit_button("🔄 更新実行", type="primary")
            
            if submitted:
                company_id = company_row.get('id', selected_company)
                
                with st.spinner("情報を更新中..."):
                    success, message = st.session_state.sheets_manager.update_company_status(
                        company_id, new_status, note
                    )
                    
                    if success:
                        st.success(f"✅ {selected_company} の情報を更新しました！")
                        # データを更新
                        st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ 更新失敗: {message}")

def show_company_list():
    """企業一覧表示"""
    st.markdown("#### 📋 企業一覧")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 企業データがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 検索・フィルター
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 企業名で検索:", placeholder="企業名を入力")
    
    with col2:
        if 'status' in df.columns:
            status_filter = st.selectbox("📊 ステータス:", ["全て"] + list(df['status'].unique()))
        else:
            status_filter = "全て"
    
    with col3:
        if 'industry' in df.columns:
            industry_filter = st.selectbox("🏗️ 業界:", ["全て"] + list(df['industry'].unique()))
        else:
            industry_filter = "全て"
    
    # フィルター適用
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]
    
    if status_filter != "全て" and 'status' in df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if industry_filter != "全て" and 'industry' in df.columns:
        filtered_df = filtered_df[filtered_df['industry'] == industry_filter]
    
    # 結果表示
    st.markdown(f"**検索結果: {len(filtered_df)}件**")
    
    if not filtered_df.empty:
        # 重要な列のみを表示
        display_columns = ['name', 'industry', 'status', 'picoCela_score', 'contact_person', 'email']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True,
            column_config={
                "name": "企業名",
                "industry": "業界",
                "status": "ステータス",
                "picoCela_score": "関連度",
                "contact_person": "担当者",
                "email": "メール"
            }
        )
    else:
        st.info("検索条件に一致する企業がありません。")

def show_data_import():
    """データインポート画面"""
    if not st.session_state.sheets_manager or not st.session_state.sheets_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 📁 データインポート")
    
    st.markdown("""
    **📋 対応フォーマット:**
    - CSV ファイル
    - Excel ファイル (.xlsx, .xls)
    
    **📝 必要なカラム:**
    - 企業名 (name, company_name, 会社名)
    - 業界 (industry, 業界)
    - メール (email, メール)
    - 担当者 (contact_person, 担当者)
    """)
    
    uploaded_file = st.file_uploader(
        "📎 ファイルを選択してください",
        type=['csv', 'xlsx', 'xls'],
        help="CSV または Excel ファイルをアップロードしてください"
    )
    
    if uploaded_file is not None:
        try:
            # ファイル読み込み
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.markdown("#### 📊 プレビュー")
            st.dataframe(df.head(10), use_container_width=True)
            
            # カラムマッピング
            st.markdown("#### 🔗 カラムマッピング")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name_col = st.selectbox("企業名カラム:", df.columns.tolist())
                industry_col = st.selectbox("業界カラム:", [''] + df.columns.tolist())
                email_col = st.selectbox("メールカラム:", [''] + df.columns.tolist())
            
            with col2:
                contact_col = st.selectbox("担当者カラム:", [''] + df.columns.tolist())
                phone_col = st.selectbox("電話番号カラム:", [''] + df.columns.tolist())
                website_col = st.selectbox("ウェブサイトカラム:", [''] + df.columns.tolist())
            
            # インポート設定
            default_score = st.slider("デフォルト関連度スコア:", 1, 10, 5)
            
            if st.button("📥 インポート実行", type="primary"):
                with st.spinner("データをインポート中..."):
                    companies_to_import = []
                    
                    for _, row in df.iterrows():
                        company_data = {
                            "name": str(row[name_col]) if pd.notna(row[name_col]) else "",
                            "industry": str(row[industry_col]) if industry_col and pd.notna(row[industry_col]) else "",
                            "email": str(row[email_col]) if email_col and pd.notna(row[email_col]) else "",
                            "contact_person": str(row[contact_col]) if contact_col and pd.notna(row[contact_col]) else "",
                            "phone": str(row[phone_col]) if phone_col and pd.notna(row[phone_col]) else "",
                            "website": str(row[website_col]) if website_col and pd.notna(row[website_col]) else "",
                            "picoCela_score": default_score,
                            "status": "New",
                            "notes": "インポートデータ",
                            "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        if company_data["name"]:  # 企業名が空でない場合のみ追加
                            companies_to_import.append(company_data)
                    
                    if companies_to_import:
                        success, message = st.session_state.sheets_manager.import_bulk_data(companies_to_import)
                        
                        if success:
                            st.success(f"✅ {len(companies_to_import)}社のデータをインポートしました！")
                            st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
                        else:
                            st.error(f"❌ インポート失敗: {message}")
                    else:
                        st.warning("⚠️ インポート可能なデータがありません")
        
        except Exception as e:
            st.error(f"❌ ファイル読み込みエラー: {str(e)}")

def show_analytics():
    """分析・レポート画面"""
    if not st.session_state.sheets_manager or not st.session_state.sheets_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 📈 分析・レポート")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 分析するデータがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 基本統計
    st.markdown("#### 📊 基本統計")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", len(df))
    
    with col2:
        if 'picoCela_score' in df.columns:
            avg_score = df['picoCela_score'].mean()
            st.metric("平均関連度", f"{avg_score:.1f}")
        else:
            st.metric("平均関連度", "N/A")
    
    with col3:
        if 'status' in df.columns:
            qualified_rate = len(df[df['status'].isin(['Qualified', 'Proposal', 'Negotiation', 'Won'])]) / len(df) * 100
            st.metric("有望化率", f"{qualified_rate:.1f}%")
        else:
            st.metric("有望化率", "N/A")
    
    with col4:
        if 'status' in df.columns:
            won_rate = len(df[df['status'] == 'Won']) / len(df) * 100
            st.metric("受注率", f"{won_rate:.1f}%")
        else:
            st.metric("受注率", "N/A")
    
    # ビジュアライゼーション
    tab1, tab2, tab3 = st.tabs(["📊 ステータス分析", "🎯 関連度分析", "🏗️ 業界分析"])
    
    with tab1:
        if 'status' in df.columns:
            st.markdown("##### ステータス分布")
            status_counts = df['status'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="ステータス分布（円グラフ）"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                fig_bar = px.bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    title="ステータス分布（棒グラフ）",
                    labels={'x': 'ステータス', 'y': '企業数'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab2:
        if 'picoCela_score' in df.columns:
            st.markdown("##### 関連度スコア分布")
            
            fig_hist = px.histogram(
                df,
                x='picoCela_score',
                nbins=10,
                title="関連度スコア分布",
                labels={'picoCela_score': '関連度スコア', 'count': '企業数'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 高関連度企業リスト
            high_score_companies = df[df['picoCela_score'] >= 8]
            if not high_score_companies.empty:
                st.markdown("##### 🎯 高関連度企業（スコア8以上）")
                display_cols = ['name', 'industry', 'status', 'picoCela_score']
                available_cols = [col for col in display_cols if col in high_score_companies.columns]
                st.dataframe(high_score_companies[available_cols], use_container_width=True)
    
    with tab3:
        if 'industry' in df.columns:
            st.markdown("##### 業界別分析")
            
            industry_counts = df['industry'].value_counts()
            
            fig_industry = px.bar(
                x=industry_counts.values,
                y=industry_counts.index,
                orientation='h',
                title="業界別企業数",
                labels={'x': '企業数', 'y': '業界'}
            )
            st.plotly_chart(fig_industry, use_container_width=True)
            
            # 業界別平均関連度
            if 'picoCela_score' in df.columns:
                industry_avg_score = df.groupby('industry')['picoCela_score'].mean().sort_values(ascending=False)
                
                fig_avg = px.bar(
                    x=industry_avg_score.values,
                    y=industry_avg_score.index,
                    orientation='h',
                    title="業界別平均関連度スコア",
                    labels={'x': '平均関連度', 'y': '業界'}
                )
                st.plotly_chart(fig_avg, use_container_width=True)

def main():
    """メイン関数"""
    # セッション状態初期化
    init_session_state()
    
    # サイドバーメニュー
    with st.sidebar:
        st.markdown("### 🚀 FusionCRM メニュー")
        
        menu_options = [
            "📊 ダッシュボード",
            "🏢 企業管理",
            "📁 データインポート",
            "📈 分析・レポート",
            "⚙️ 設定"
        ]
        
        selected_menu = st.radio("メニュー選択:", menu_options)
        
        st.markdown("---")
        
        # 接続状態表示
        if st.session_state.sheets_manager and st.session_state.sheets_manager.is_connected:
            st.success("✅ Google Sheets 接続中")
            
            # データ統計
            if st.session_state.companies_data:
                st.markdown("### 📊 データ統計")
                df = pd.DataFrame(st.session_state.companies_data)
                st.metric("企業数", len(df))
                
                if 'status' in df.columns:
                    new_count = len(df[df['status'] == 'New'])
                    st.metric("新規企業", new_count)
        else:
            st.error("❌ 未接続")
            st.markdown("⚙️ 設定から接続してください")
    
    # メイン画面表示
    try:
        if selected_menu == "📊 ダッシュボード":
            show_dashboard()
        elif selected_menu == "🏢 企業管理":
            show_company_management()
        elif selected_menu == "📁 データインポート":
            show_data_import()
        elif selected_menu == "📈 分析・レポート":
            show_analytics()
        elif selected_menu == "⚙️ 設定":
            show_connection_setup()
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("💡 設定画面で接続を確認してください")
        
        # デバッグ情報
        with st.expander("🔧 デバッグ情報"):
            st.text(f"エラー詳細: {str(e)}")
            st.text(f"接続状態: {st.session_state.sheets_manager is not None}")
            if st.session_state.sheets_manager:
                st.text(f"接続確認: {st.session_state.sheets_manager.is_connected}")

if __name__ == "__main__":
    main()
