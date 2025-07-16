#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Google Drive OAuth版
Google Cloudプロジェクト不要、個人Googleアカウント利用
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import pickle
import os
import json
import hashlib
import smtplib
import time
import random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px

# ページ設定
st.set_page_config(
    page_title="FusionCRM Drive - PicoCELA営業支援システム",
    page_icon="🚀",
    layout="wide"
)

# OAuth 2.0設定（Google Drive API）
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# 簡易認証（Streamlit Cloud対応）
CLIENT_CONFIG = {
    "web": {
        "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
        "client_secret": "YOUR_CLIENT_SECRET",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8501"]
    }
}

class GoogleDriveDB:
    """Google Drive OAuth認証でのデータベース管理"""
    
    def __init__(self):
        self.gc = None
        self.spreadsheet = None
        self.companies_sheet = None
        self.users_sheet = None
        self.email_history_sheet = None
        self.authenticate()
    
    def authenticate(self):
        """OAuth認証"""
        try:
            # Streamlit secrets対応
            if hasattr(st, 'secrets') and 'google_oauth' in st.secrets:
                # Streamlit Cloudでの認証
                creds_data = dict(st.secrets["google_oauth"])
                creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            else:
                # ローカル開発での認証
                creds = self.get_local_credentials()
            
            if creds and creds.valid:
                self.gc = gspread.authorize(creds)
                st.success("✅ Google Drive認証成功")
                self.setup_spreadsheet()
                return True
            else:
                st.error("❌ Google Drive認証が必要です")
                self.show_auth_instructions()
                return False
                
        except Exception as e:
            st.error(f"認証エラー: {e}")
            return False
    
    def get_local_credentials(self):
        """ローカル認証トークンの取得"""
        token_file = 'token.pickle'
        creds = None
        
        # 既存トークンの読み込み
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # トークンが無効または期限切れの場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # 新規認証が必要
                return None
        
        # トークンの保存
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        
        return creds
    
    def show_auth_instructions(self):
        """認証手順の表示"""
        st.warning("🔐 Google Drive認証が必要です")
        
        with st.expander("📋 認証手順（初回のみ）"):
            st.markdown("""
            ### 1. Google APIs Console設定
            1. [Google APIs Console](https://console.developers.google.com/) にアクセス
            2. 「プロジェクトを作成」（または既存プロジェクト選択）
            3. 「ライブラリ」→「Google Sheets API」→「有効にする」
            4. 「ライブラリ」→「Google Drive API」→「有効にする」
            
            ### 2. OAuth認証情報作成
            1. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
            2. アプリケーションの種類：「ウェブアプリケーション」
            3. 承認済みリダイレクトURI：`http://localhost:8501`
            4. Client IDとClient Secretをコピー
            
            ### 3. ローカル認証
            ```python
            # auth_setup.py を実行して初回認証
            python auth_setup.py
            ```
            """)
        
        # 認証用コード生成
        auth_code = st.text_input("認証コードを入力してください（初回のみ）")
        if st.button("認証実行") and auth_code:
            self.process_auth_code(auth_code)
    
    def setup_spreadsheet(self):
        """スプレッドシートの設定"""
        try:
            # PicoCELA FusionCRM専用スプレッドシート
            spreadsheet_name = "PicoCELA_FusionCRM_Drive"
            
            try:
                self.spreadsheet = self.gc.open(spreadsheet_name)
                st.success(f"✅ 既存データベース '{spreadsheet_name}' に接続")
            except gspread.SpreadsheetNotFound:
                # 新規作成
                self.spreadsheet = self.gc.create(spreadsheet_name)
                st.success(f"✅ 新規データベース '{spreadsheet_name}' を作成")
                
                # PicoCELAチームと共有
                try:
                    self.spreadsheet.share('tokuda@picocela.com', perm_type='user', role='writer')
                    st.success("📧 tokuda@picocela.com と共有完了")
                except:
                    st.warning("⚠️ 共有設定は手動で行ってください")
            
            # ワークシートの初期化
            self.init_worksheets()
            
        except Exception as e:
            st.error(f"スプレッドシート設定エラー: {e}")
    
    def init_worksheets(self):
        """ワークシートの初期化"""
        # 企業データシート
        try:
            self.companies_sheet = self.spreadsheet.worksheet("companies")
        except gspread.WorksheetNotFound:
            self.companies_sheet = self.spreadsheet.add_worksheet(
                title="companies", rows=5000, cols=20
            )
            headers = [
                "id", "company_name", "email_address", "website", "phone",
                "status", "picocela_relevance_score", "keywords_matched",
                "created_at", "updated_at", "last_contact_date", "notes"
            ]
            self.companies_sheet.append_row(headers)
        
        # ユーザーシート
        try:
            self.users_sheet = self.spreadsheet.worksheet("users")
        except gspread.WorksheetNotFound:
            self.users_sheet = self.spreadsheet.add_worksheet(
                title="users", rows=100, cols=8
            )
            headers = ["id", "username", "password_hash", "email", "role", "created_at"]
            self.users_sheet.append_row(headers)
        
        # メール履歴シート
        try:
            self.email_history_sheet = self.spreadsheet.worksheet("email_history")
        except gspread.WorksheetNotFound:
            self.email_history_sheet = self.spreadsheet.add_worksheet(
                title="email_history", rows=5000, cols=10
            )
            headers = [
                "id", "company_name", "email_address", "template", "subject",
                "sent_at", "status", "error_message"
            ]
            self.email_history_sheet.append_row(headers)

class SimpleCRMManager:
    """簡易CRM管理クラス"""
    
    def __init__(self, db):
        self.db = db
    
    def get_companies(self, status_filter=None, search_term=None):
        """企業データの取得"""
        try:
            if not self.db.companies_sheet:
                return pd.DataFrame()
            
            records = self.db.companies_sheet.get_all_records()
            df = pd.DataFrame(records)
            
            if df.empty:
                return df
            
            # フィルタリング
            if status_filter and status_filter != "すべて":
                df = df[df['status'] == status_filter]
            
            if search_term:
                df = df[df['company_name'].str.contains(search_term, case=False, na=False)]
            
            return df
            
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            return pd.DataFrame()
    
    def add_company(self, company_data):
        """企業データの追加"""
        try:
            # 新しいIDを生成
            records = self.db.companies_sheet.get_all_records()
            max_id = max([int(r.get('id', 0)) for r in records if r.get('id')]) if records else 0
            new_id = max_id + 1
            
            row_data = [
                new_id,
                company_data.get('company_name', ''),
                company_data.get('email_address', ''),
                company_data.get('website', ''),
                company_data.get('phone', ''),
                company_data.get('status', 'New'),
                company_data.get('picocela_relevance_score', 50),
                company_data.get('keywords_matched', 'construction,network'),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                '',
                company_data.get('notes', '')
            ]
            
            self.db.companies_sheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"企業データ追加エラー: {e}")
            return False
    
    def import_excel_data(self, uploaded_file):
        """Excelファイルからデータインポート"""
        try:
            df = pd.read_excel(uploaded_file)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            imported_count = 0
            total = len(df)
            
            for i, row in df.iterrows():
                company_data = {
                    'company_name': str(row.get('Company Name', row.get('company_name', f'Company_{i+1}'))),
                    'email_address': str(row.get('Email', row.get('email', ''))),
                    'website': str(row.get('Website', row.get('website', ''))),
                    'phone': str(row.get('Phone', row.get('phone', ''))),
                    'status': 'New',
                    'picocela_relevance_score': int(row.get('picocela_relevance_score', 50)),
                    'keywords_matched': str(row.get('keywords_matched', 'construction,network')),
                    'notes': str(row.get('notes', ''))
                }
                
                if self.add_company(company_data):
                    imported_count += 1
                
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status_text.text(f"インポート中: {imported_count}/{total}")
                
                # API制限対策
                if i % 100 == 0:
                    time.sleep(1)
            
            status_text.text("✅ インポート完了")
            return True, f"✅ {imported_count}社のデータをインポートしました"
            
        except Exception as e:
            return False, f"インポートエラー: {e}"

# 認証セットアップスクリプト
AUTH_SETUP_CODE = '''
#!/usr/bin/env python3
"""
Google Drive OAuth 初回認証スクリプト
一度だけ実行してtoken.pickleを生成
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# OAuth設定（実際のClient IDとSecretに置き換え）
CLIENT_CONFIG = {
    "installed": {
        "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
        "client_secret": "YOUR_CLIENT_SECRET",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
    }
}

def setup_oauth():
    """OAuth認証のセットアップ"""
    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # トークンを保存
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
    
    print("✅ OAuth認証完了！token.pickleが生成されました。")
    print("🚀 FusionCRMを起動してください。")

if __name__ == '__main__':
    setup_oauth()
'''

# グローバルインスタンス
@st.cache_resource
def get_drive_instances():
    db = GoogleDriveDB()
    crm = SimpleCRMManager(db)
    return db, crm

def main():
    """メインアプリケーション"""
    st.title("🚀 FusionCRM Drive Edition")
    st.caption("Google Drive + OAuth認証版")
    
    db, crm = get_drive_instances()
    
    if not db.gc:
        st.error("❌ Google Drive認証が必要です")
        
        # 認証セットアップコードの提供
        with st.expander("🔧 認証セットアップコード"):
            st.code(AUTH_SETUP_CODE, language='python')
            st.download_button(
                label="📥 auth_setup.py をダウンロード",
                data=AUTH_SETUP_CODE,
                file_name="auth_setup.py",
                mime="text/plain"
            )
        
        return
    
    # サイドバーナビゲーション
    st.sidebar.title("📋 メニュー")
    page = st.sidebar.radio(
        "ページ選択",
        ["📊 ダッシュボード", "📥 データインポート", "🏢 企業管理", "📧 メール配信"]
    )
    
    # スプレッドシート情報
    if db.spreadsheet:
        st.sidebar.success(f"✅ DB接続: {db.spreadsheet.title}")
        st.sidebar.info(f"🔗 [スプレッドシートを開く]({db.spreadsheet.url})")
    
    # ページルーティング
    if page == "📊 ダッシュボード":
        dashboard_page(crm)
    elif page == "📥 データインポート":
        import_page(crm)
    elif page == "🏢 企業管理":
        companies_page(crm)
    elif page == "📧 メール配信":
        email_page(crm)

def dashboard_page(crm):
    """ダッシュボードページ"""
    st.header("📊 ダッシュボード")
    
    companies_df = crm.get_companies()
    
    if not companies_df.empty:
        # 基本統計
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(companies_df)
            st.metric("総企業数", total)
        
        with col2:
            new_count = len(companies_df[companies_df['status'] == 'New'])
            st.metric("新規企業", new_count)
        
        with col3:
            contacted = len(companies_df[companies_df['status'] == 'Contacted'])
            st.metric("連絡済み", contacted)
        
        with col4:
            email_available = len(companies_df[
                companies_df['email_address'].notna() & 
                (companies_df['email_address'] != '')
            ])
            st.metric("メール配信可能", email_available)
        
        # ステータス分布
        if 'status' in companies_df.columns:
            status_counts = companies_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, title="ステータス分布")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📥 まずはデータをインポートしてください")

def import_page(crm):
    """データインポートページ"""
    st.header("📥 データインポート")
    
    uploaded_file = st.file_uploader(
        "Excelファイルをアップロード", 
        type=['xlsx', 'xls'],
        help="ENRデータファイルまたは企業リストをアップロード"
    )
    
    if uploaded_file:
        # プレビュー
        try:
            preview_df = pd.read_excel(uploaded_file)
            st.write("📋 データプレビュー（最初の5行）:")
            st.dataframe(preview_df.head())
            st.write(f"📊 総データ数: {len(preview_df)}社")
            
            if st.button("🚀 インポート実行", type="primary"):
                with st.spinner("インポート中..."):
                    success, message = crm.import_excel_data(uploaded_file)
                    
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
        
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")

def companies_page(crm):
    """企業管理ページ"""
    st.header("🏢 企業管理")
    
    # フィルター
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("ステータス", ["すべて", "New", "Contacted", "Replied", "Qualified"])
    with col2:
        search_term = st.text_input("企業名検索")
    
    # データ表示
    companies_df = crm.get_companies(status_filter, search_term)
    
    if not companies_df.empty:
        st.dataframe(companies_df, use_container_width=True)
    else:
        st.info("該当する企業が見つかりません")

def email_page(crm):
    """メール配信ページ"""
    st.header("📧 メール配信")
    
    st.info("🚧 メール配信機能は開発中です")
    st.write("Gmail統合機能を実装予定")
    
    # 簡易メール配信フォーム
    with st.form("simple_email"):
        recipient = st.text_input("送信先メールアドレス")
        subject = st.text_input("件名", value="PicoCELA メッシュネットワークのご案内")
        message = st.text_area("メッセージ", height=200)
        
        submitted = st.form_submit_button("📧 送信")
        
        if submitted:
            st.success("✅ メール送信機能は今後実装予定です")

if __name__ == "__main__":
    main()
