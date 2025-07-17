import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

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
                timeout=10
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
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"更新エラー: {str(e)}"

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
    
    st.markdown("""
    <div class="success-box">
        ✅ <strong>Google Sheets接続中</strong> 📊 スプレッドシートを開く
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
        
        script_url = st.text_input(
            "📍 Google Apps Script Web アプリ URL:",
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
    
    st.markdown('<h1 class="main-header">🚀 FusionCRM Dashboard</h1>', unsafe_allow_html=True)
    
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
        st.warning("📋 企業データがありません。新しい企業を追加してください。")
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
    
    with col3:
        if 'picoCela_score' in df.columns:
            high_score = len(df[df['picoCela_score'] >= 7])
            st.metric("🎯 高関連度企業", high_score)
    
    with col4:
        if 'status' in df.columns:
            new_count = len(df[df['status'] == 'New'])
            st.metric("🆕 新規企業", new_count)
    
    # ステータス分布チャート
    if 'status' in df.columns:
        st.markdown("### 📊 ステータス分布")
        status_counts = df['status'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="企業ステータス分布"
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
    
    st.dataframe(filtered_df, use_container_width=True)

def show_add_company():
    """企業追加画面"""
    if not st.session_state.sheets_manager or not st.session_state.sheets_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### ➕ 新規企業追加")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("🏢 企業名*", placeholder="例: 株式会社○○建設")
            industry = st.selectbox(
                "🏗️ 業界",
                ["建設業", "製造業", "IT・通信", "不動産", "その他"]
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

def show_status_management():
    """ステータス管理画面"""
    if not st.session_state.sheets_manager or not st.session_state.sheets_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 📈 ステータス管理")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 企業データがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 企業選択
    company_names = df['name'].tolist() if 'name' in df.columns else []
    selected_company = st.selectbox("🏢 企業を選択:", company_names)
    
    if selected_company:
        company_row = df[df['name'] == selected_company].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**現在の情報:**")
            st.info(f"📊 現在のステータス: {company_row.get('status', 'N/A')}")
            st.info(f"🎯 PicoCELA関連度: {company_row.get('picoCela_score', 'N/A')}")
            
        with col2:
            st.markdown("**ステータス更新:**")
            new_status = st.selectbox(
                "新しいステータス:",
                ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost", "Dormant"]
            )
            
            note = st.text_area("📝 更新理由・メモ:", placeholder="ステータス変更の理由を記入")
            
            if st.button("🔄 ステータス更新", type="primary"):
                with st.spinner("ステータスを更新中..."):
                    company_id = company_row.get('id', selected_company)
                    success, message = st.session_state.sheets_manager.update_company_status(
                        company_id, new_status, note
                    )
                    
                    if success:
                        st.success(f"✅ {selected_company} のステータスを {new_status} に更新しました！")
                        # データを更新
                        st.session_state.companies_data = st.session_state.sheets_manager.get_companies()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ 更新失敗: {message}")

def main():
    """メイン関数"""
    # セッション状態初期化
    init_session_state()
    
    # サイドバーメニュー
    with st.sidebar:
        st.markdown("### 🚀 FusionCRM メニュー")
        
        menu_options = [
            "📊 ダッシュボード",
            "➕ 企業追加",
            "📈 ステータス管理",
            "⚙️ 設定"
        ]
        
        selected_menu = st.radio("メニュー選択:", menu_options)
        
        st.markdown("---")
        
        # 接続状態表示
        if st.session_state.sheets_manager and st.session_state.sheets_manager.is_connected:
            st.success("✅ Google Sheets 接続中")
        else:
            st.error("❌ 未接続")
        
        # データ統計
        if st.session_state.companies_data:
            st.markdown("### 📊 データ統計")
            st.metric("企業数", len(st.session_state.companies_data))
    
    # メイン画面表示
    try:
        if selected_menu == "📊 ダッシュボード":
            show_dashboard()
        elif selected_menu == "➕ 企業追加":
            show_add_company()
        elif selected_menu == "📈 ステータス管理":
            show_status_management()
        elif selected_menu == "⚙️ 設定":
            show_connection_setup()
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("💡 設定画面で接続を確認してください")

if __name__ == "__main__":
    main()
