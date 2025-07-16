#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - ENR Data Optimized Version
PicoCELA社専用統合CRMシステム（ENRデータ最適化版）
実際のENRファイル構造に最適化されたGoogle Sheets統合
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
import hashlib
import smtplib
import time
import random
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px
import plotly.graph_objects as go

# Google Sheets統合用ライブラリ
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="FusionCRM - PicoCELA統合営業支援システム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
    }
    .high-priority {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .medium-priority {
        background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class GoogleSheetsDB:
    """Google Sheetsデータベース管理クラス（ENR最適化版）"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.companies_sheet = None
        self.email_history_sheet = None
        self.users_sheet = None
        self.init_connection()
    
    def init_connection(self):
        """Google Sheets接続初期化"""
        try:
            # Streamlit Secretsから認証情報取得
            if 'google_sheets' in st.secrets:
                credentials_info = st.secrets["google_sheets"]
                credentials = Credentials.from_service_account_info(
                    credentials_info,
                    scopes=[
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"
                    ]
                )
                self.client = gspread.authorize(credentials)
                
                # スプレッドシート取得または作成
                try:
                    self.spreadsheet = self.client.open("FusionCRM_PicoCELA_ENR_Data")
                except gspread.SpreadsheetNotFound:
                    self.spreadsheet = self.client.create("FusionCRM_PicoCELA_ENR_Data")
                    self.spreadsheet.share('tokuda@picocela.com', perm_type='user', role='owner')
                
                self.init_sheets()
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"Google Sheets接続エラー: {e}")
            return False
    
    def init_sheets(self):
        """ワークシート初期化（ENR構造最適化）"""
        try:
            # ENR企業データシート
            try:
                self.companies_sheet = self.spreadsheet.worksheet("enr_companies")
            except gspread.WorksheetNotFound:
                self.companies_sheet = self.spreadsheet.add_worksheet(title="enr_companies", rows="1000", cols="25")
                # ENRファイル構造に基づくヘッダー
                headers = [
                    "id", "company_name", "email_address", "website", "phone", 
                    "address", "needs_wifi", "description", "pdf_url", "contact_info",
                    "source_url", "keyword_match_count", "picocela_relevance_score",
                    "status", "priority_level", "last_contact_date", "next_followup_date",
                    "created_at", "updated_at", "notes", "industry_sector",
                    "company_size", "decision_maker", "budget_range", "project_timeline"
                ]
                self.companies_sheet.append_row(headers)
            
            # メール履歴シート
            try:
                self.email_history_sheet = self.spreadsheet.worksheet("email_history")
            except gspread.WorksheetNotFound:
                self.email_history_sheet = self.spreadsheet.add_worksheet(title="email_history", rows="1000", cols="15")
                headers = [
                    "id", "company_id", "company_name", "email_type", "subject", 
                    "content", "sent_at", "status", "error_message", "open_count",
                    "click_count", "reply_received", "template_used", "campaign_id", "notes"
                ]
                self.email_history_sheet.append_row(headers)
            
            # ユーザーシート
            try:
                self.users_sheet = self.spreadsheet.worksheet("users")
            except gspread.WorksheetNotFound:
                self.users_sheet = self.spreadsheet.add_worksheet(title="users", rows="100", cols="10")
                headers = ["id", "username", "password_hash", "email", "role", "created_at", "last_login", "active"]
                self.users_sheet.append_row(headers)
                
                # デフォルト管理者追加
                default_password_hash = hashlib.sha256("picocela2024".encode()).hexdigest()
                self.users_sheet.append_row([
                    1, "admin", default_password_hash, "tokuda@picocela.com", "admin", 
                    datetime.now().isoformat(), "", True
                ])
            
        except Exception as e:
            st.error(f"ワークシート初期化エラー: {e}")
    
    def calculate_picocela_relevance_score(self, company_data):
        """PicoCELA関連度スコア計算（ENRデータ基準）"""
        score = 30  # ベーススコア
        
        # Wi-Fi必要性（最重要要素）
        if company_data.get('needs_wifi') == 'Yes':
            score += 30
        
        # キーワードマッチ数
        keyword_count = int(company_data.get('keyword_match_count', 0))
        if keyword_count > 0:
            score += min(keyword_count * 10, 30)  # 最大30点
        
        # 連絡可能性
        if company_data.get('email_address'):
            score += 15
        if company_data.get('phone'):
            score += 10
        if company_data.get('address'):
            score += 5
        
        # 企業情報の充実度
        if company_data.get('description') and len(company_data.get('description', '')) > 50:
            score += 5
        if company_data.get('website'):
            score += 5
        
        return min(score, 100)  # 最大100点
    
    def get_companies(self, status_filter=None, search_term=None, min_score=0, priority_filter=None):
        """企業データ取得（ENR最適化版）"""
        try:
            if not self.companies_sheet:
                return pd.DataFrame()
            
            # 全データ取得
            data = self.companies_sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty:
                return df
            
            # 数値列の変換
            numeric_columns = ['picocela_relevance_score', 'keyword_match_count', 'priority_level']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # フィルタリング
            if status_filter and status_filter != "すべて":
                df = df[df['status'] == status_filter]
            
            if search_term:
                df = df[df['company_name'].str.contains(search_term, case=False, na=False)]
            
            if min_score > 0:
                df = df[df['picocela_relevance_score'] >= min_score]
            
            if priority_filter and priority_filter != "すべて":
                if priority_filter == "Wi-Fi必要":
                    df = df[df['needs_wifi'] == 'Yes']
                elif priority_filter == "高スコア":
                    df = df[df['picocela_relevance_score'] >= 80]
                elif priority_filter == "キーワードマッチ":
                    df = df[df['keyword_match_count'] > 0]
            
            return df
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {e}")
            return pd.DataFrame()
    
    def add_company(self, company_data):
        """企業追加（ENR最適化版）"""
        try:
            if not self.companies_sheet:
                return False
            
            # 新しいIDを生成
            existing_data = self.companies_sheet.get_all_records()
            new_id = len(existing_data) + 1
            
            # PicoCELA関連度スコア計算
            relevance_score = self.calculate_picocela_relevance_score(company_data)
            
            # 優先度レベル決定
            priority_level = 1  # デフォルト
            if company_data.get('needs_wifi') == 'Yes' and int(company_data.get('keyword_match_count', 0)) > 0:
                priority_level = 3  # 最高優先度
            elif company_data.get('needs_wifi') == 'Yes' or int(company_data.get('keyword_match_count', 0)) > 0:
                priority_level = 2  # 高優先度
            
            # データ準備
            row_data = [
                new_id,
                company_data.get('company_name', ''),
                company_data.get('email_address', ''),
                company_data.get('website', ''),
                company_data.get('phone', ''),
                company_data.get('address', ''),
                company_data.get('needs_wifi', 'No'),
                company_data.get('description', ''),
                company_data.get('pdf_url', ''),
                company_data.get('contact_info', ''),
                company_data.get('source_url', ''),
                company_data.get('keyword_match_count', 0),
                relevance_score,
                company_data.get('status', 'New'),
                priority_level,
                '',  # last_contact_date
                '',  # next_followup_date
                datetime.now().isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
                company_data.get('notes', ''),
                company_data.get('industry_sector', '建設業'),
                company_data.get('company_size', ''),
                company_data.get('decision_maker', ''),
                company_data.get('budget_range', ''),
                company_data.get('project_timeline', '')
            ]
            
            self.companies_sheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"企業追加エラー: {e}")
            return False
    
    def update_company_status(self, company_name, status):
        """企業ステータス更新"""
        try:
            if not self.companies_sheet:
                return False
            
            companies = self.companies_sheet.get_all_records()
            for i, company in enumerate(companies, start=2):
                if company['company_name'] == company_name:
                    self.companies_sheet.update_cell(i, 14, status)  # status列
                    self.companies_sheet.update_cell(i, 16, datetime.now().isoformat())  # last_contact_date列
                    self.companies_sheet.update_cell(i, 19, datetime.now().isoformat())  # updated_at列
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"ステータス更新エラー: {e}")
            return False
    
    def add_email_history(self, history_data):
        """メール履歴追加（ENR最適化版）"""
        try:
            if not self.email_history_sheet:
                return False
            
            existing_data = self.email_history_sheet.get_all_records()
            new_id = len(existing_data) + 1
            
            row_data = [
                new_id,
                history_data.get('company_id', ''),
                history_data.get('company_name', ''),
                history_data.get('email_type', ''),
                history_data.get('subject', ''),
                history_data.get('content', ''),
                datetime.now().isoformat(),
                history_data.get('status', ''),
                history_data.get('error_message', ''),
                0,  # open_count
                0,  # click_count
                False,  # reply_received
                history_data.get('template_used', ''),
                history_data.get('campaign_id', ''),
                history_data.get('notes', '')
            ]
            
            self.email_history_sheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"メール履歴追加エラー: {e}")
            return False
    
    def get_email_history(self, days_back=30, status_filter=None, limit=50):
        """メール履歴取得"""
        try:
            if not self.email_history_sheet:
                return pd.DataFrame()
            
            data = self.email_history_sheet.get_all_records()
            df = pd.DataFrame(data)
            
            if df.empty:
                return df
            
            # 日付フィルタリング
            if 'sent_at' in df.columns:
                df['sent_at'] = pd.to_datetime(df['sent_at'], errors='coerce')
                cutoff_date = datetime.now() - timedelta(days=days_back)
                df = df[df['sent_at'] >= cutoff_date]
            
            # ステータスフィルタリング
            if status_filter and status_filter != "すべて":
                df = df[df['status'] == status_filter]
            
            # 制限
            df = df.tail(limit)
            
            return df
            
        except Exception as e:
            st.error(f"メール履歴取得エラー: {e}")
            return pd.DataFrame()
    
    def authenticate_user(self, username, password):
        """ユーザー認証"""
        try:
            if not self.users_sheet:
                return None
            
            users = self.users_sheet.get_all_records()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            for user in users:
                if user['username'] == username and user['password_hash'] == password_hash:
                    return user
            
            return None
            
        except Exception as e:
            st.error(f"認証エラー: {e}")
            return None

class EmailService:
    """メール配信サービス（ENR最適化版）"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def send_email(self, to_email, company_name, template_name="initial_contact"):
        """メール送信"""
        gmail_config = st.session_state.get('gmail_config')
        if not gmail_config:
            return False, "Gmail設定が見つかりません"
        
        templates = self.get_email_templates()
        template = templates.get(template_name, templates["initial_contact"])
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{gmail_config['sender_name']} <{gmail_config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = template['subject']
            
            body = template['body'].format(company_name=company_name)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(gmail_config['smtp_server'], gmail_config['smtp_port'])
            server.starttls()
            server.login(gmail_config['email'], gmail_config['password'])
            
            text = msg.as_string()
            server.sendmail(gmail_config['email'], to_email, text)
            server.quit()
            
            # 履歴記録
            self.log_email_history(company_name, to_email, template_name, "success")
            
            return True, "送信成功"
            
        except Exception as e:
            error_msg = f"送信エラー: {str(e)}"
            self.log_email_history(company_name, to_email, template_name, "failed", error_msg)
            return False, error_msg
    
    def log_email_history(self, company_name, email, template_name, status, error_msg=None):
        """メール履歴の記録"""
        try:
            # 企業IDを取得
            companies_df = self.db_manager.get_companies()
            company_id = None
            
            if not companies_df.empty:
                company_row = companies_df[companies_df['company_name'] == company_name]
                if not company_row.empty:
                    company_id = company_row.iloc[0]['id']
            
            # 履歴記録
            history_data = {
                'company_id': company_id,
                'company_name': company_name,
                'email_type': template_name,
                'subject': f"【PicoCELA】{company_name}様へのご提案",
                'content': f"Email sent to {email}",
                'status': status,
                'error_message': error_msg,
                'template_used': template_name
            }
            
            self.db_manager.add_email_history(history_data)
            
        except Exception as e:
            st.warning(f"履歴記録エラー: {e}")
    
    def get_email_templates(self):
        """メールテンプレートの取得（ENR企業向け）"""
        return {
            "initial_contact": {
                "subject": "【PicoCELA】建設現場向けメッシュネットワークソリューションのご案内",
                "body": """Dear {company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当と申します。

ENR Future Techにご出展されている{company_name}様の建設プロジェクトにおいて、
弊社のメッシュネットワーク技術がお役に立てるのではないかと思いご連絡いたしました。

■ PicoCELAメッシュネットワークの特徴
• 建設現場での安定したワイヤレス通信環境を実現
• 既存インフラに依存しない独立したネットワーク構築
• IoTセンサー・監視カメラ・モニタリング機器との連携
• 現場安全性向上・デジタル化・DX推進をサポート
• 工期短縮・コスト削減・作業効率向上に貢献

建設業界でのWi-Fi・通信インフラでお困りの点がございましたら、
無料でご相談・デモンストレーションも承っております。

詳細資料をお送りしますので、ぜひお時間をいただけますでしょうか。

どうぞよろしくお願いいたします。

---
株式会社PicoCELA
営業部
Email: tokuda@picocela.com
Web: https://www.picocela.com
※建設現場向けメッシュネットワークの専門企業"""
            },
            "wifi_focused": {
                "subject": "【PicoCELA】建設現場のWi-Fi課題解決ソリューション",
                "body": """Dear {company_name} 様

お世話になっております。
株式会社PicoCELAです。

{company_name}様のプロジェクトにおいて、建設現場でのWi-Fi環境構築に
お困りの点はございませんでしょうか？

弊社のメッシュネットワーク技術なら：
• 電源があればどこでも簡単設置
• 障害物に強い安定通信
• 現場レイアウト変更にも柔軟対応
• 複数の建設機械・IoT機器を同時接続

建設業界専門のWi-Fi・通信ソリューションとして、
多くの大手建設会社様にご採用いただいております。

現場でのデモンストレーションも可能です。
お気軽にお声がけください。

---
株式会社PicoCELA
営業部
Email: tokuda@picocela.com"""
            },
            "follow_up": {
                "subject": "【PicoCELA】フォローアップ - 建設現場向けソリューション",
                "body": """Dear {company_name} 様

先日はお忙しい中、お時間をいただき
ありがとうございました。

弊社のメッシュネットワークソリューションについて、
追加でご質問やご相談がございましたら、
お気軽にお声がけください。

建設現場での通信課題解決のお手伝いをさせていただければ幸いです。

引き続きどうぞよろしくお願いいたします。

---
株式会社PicoCELA
営業部
Email: tokuda@picocela.com"""
            }
        }

# グローバルインスタンス
@st.cache_resource
def get_managers():
    """マネージャーの取得"""
    if GOOGLE_SHEETS_AVAILABLE:
        db_manager = GoogleSheetsDB()
        email_service = EmailService(db_manager)
        return db_manager, email_service
    else:
        st.error("Google Sheetsライブラリが不足しています")
        return None, None

def check_google_sheets_setup():
    """Google Sheets設定確認"""
    if not GOOGLE_SHEETS_AVAILABLE:
        st.error("❌ Google Sheetsライブラリが見つかりません")
        st.info("requirements.txtに必要ライブラリが含まれています")
        return False
    
    if 'google_sheets' not in st.secrets:
        st.warning("⚠️ Google Sheetsの認証設定が必要です")
        
        with st.expander("🔧 Google Sheets設定手順"):
            st.markdown("""
            ### 📋 設定手順（初回のみ）
            
            1. **Google Cloud Console でプロジェクト作成**
            2. **Google Sheets API を有効化**
            3. **サービスアカウント作成**
            4. **認証キーをダウンロード**
            5. **Streamlit Secrets に設定**
            
            ### 🔑 Streamlit Secrets設定例
            
            ```toml
            [google_sheets]
            type = "service_account"
            project_id = "your-project-id"
            private_key_id = "your-private-key-id"
            private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
            client_email = "your-service-account@your-project.iam.gserviceaccount.com"
            client_id = "your-client-id"
            auth_uri = "https://accounts.google.com/o/oauth2/auth"
            token_uri = "https://oauth2.googleapis.com/token"
            ```
            """)
        
        return False
    
    return True

def login_page():
    """ログインページ"""
    st.markdown('<div class="main-header"><h1>🚀 FusionCRM - PicoCELA統合CRMシステム</h1><p>ENR企業データ最適化版 | Google Sheets統合</p></div>', unsafe_allow_html=True)
    
    # Google Sheets設定確認
    if not check_google_sheets_setup():
        return
    
    db_manager, email_service = get_managers()
    if not db_manager:
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("🔐 ログイン")
        st.info("🔑 デフォルトアカウント: admin / picocela2024")
        
        username = st.text_input("ユーザー名", value="admin")
        password = st.text_input("パスワード", type="password")
        
        if st.button("🚀 ログイン", type="primary", use_container_width=True):
            user = db_manager.authenticate_user(username, password)
            
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_role = user.get('role', 'user')
                st.success("✅ ログイン成功！")
                st.rerun()
            else:
                st.error("❌ ユーザー名またはパスワードが間違っています")

def dashboard_page():
    """ダッシュボードページ（ENR最適化版）"""
    st.markdown('<div class="main-header"><h1>📊 FusionCRM ダッシュボード</h1><p>ENR企業データ分析 | PicoCELA営業支援</p></div>', unsafe_allow_html=True)
    
    db_manager, email_service = get_managers()
    if not db_manager:
        return
    
    # 企業データ取得
    companies_df = db_manager.get_companies()
    email_history_df = db_manager.get_email_history()
    
    # 基本統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_companies = len(companies_df) if not companies_df.empty else 0
        st.metric("📊 ENR総企業数", total_companies)
    
    with col2:
        wifi_needed = len(companies_df[companies_df['needs_wifi'] == 'Yes']) if not companies_df.empty else 0
        st.metric("📶 Wi-Fi必要企業", wifi_needed)
    
    with col3:
        high_score = len(companies_df[companies_df['picocela_relevance_score'] >= 80]) if not companies_df.empty else 0
        st.metric("🎯 高関連度企業", high_score)
    
    with col4:
        email_available = len(companies_df[companies_df['email_address'].notna()]) if not companies_df.empty else 0
        st.metric("📧 メール配信可能", email_available)
    
    # PicoCELA関連度分布
    if not companies_df.empty:
        st.subheader("🎯 PicoCELA関連度スコア分布")
        
        score_ranges = {
            "80-100 (最高)": len(companies_df[companies_df['picocela_relevance_score'] >= 80]),
            "60-79 (高)": len(companies_df[(companies_df['picocela_relevance_score'] >= 60) & (companies_df['picocela_relevance_score'] < 80)]),
            "40-59 (中)": len(companies_df[(companies_df['picocela_relevance_score'] >= 40) & (companies_df['picocela_relevance_score'] < 60)]),
            "0-39 (低)": len(companies_df[companies_df['picocela_relevance_score'] < 40])
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            # スコア分布グラフ
            fig_pie = px.pie(
                values=list(score_ranges.values()),
                names=list(score_ranges.keys()),
                title="PicoCELA関連度スコア分布",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Wi-Fi必要性 vs スコア散布図
            if 'picocela_relevance_score' in companies_df.columns and 'needs_wifi' in companies_df.columns:
                fig_scatter = px.scatter(
                    companies_df,
                    x='keyword_match_count',
                    y='picocela_relevance_score',
                    color='needs_wifi',
                    title="キーワードマッチ数 vs 関連度スコア",
                    labels={'keyword_match_count': 'キーワードマッチ数', 'picocela_relevance_score': '関連度スコア'},
                    color_discrete_map={'Yes': '#ff6b6b', 'No': '#74b9ff'}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        # トップ企業一覧
        st.subheader("🏆 高優先度企業（トップ10）")
        top_companies = companies_df.nlargest(10, 'picocela_relevance_score')
        
        if not top_companies.empty:
            display_df = top_companies[['company_name', 'picocela_relevance_score', 'needs_wifi', 'keyword_match_count', 'email_address']].copy()
            display_df.columns = ['企業名', '関連度スコア', 'Wi-Fi必要', 'キーワードマッチ', 'メールアドレス']
            
            # スタイリング
            def highlight_high_priority(val):
                if isinstance(val, (int, float)) and val >= 80:
                    return 'background-color: #ff6b6b; color: white; font-weight: bold'
                elif val == 'Yes':
                    return 'background-color: #feca57; color: black; font-weight: bold'
                return ''
            
            styled_df = display_df.style.applymap(highlight_high_priority, subset=['関連度スコア', 'Wi-Fi必要'])
            st.dataframe(styled_df, use_container_width=True)
    
    # 今日の活動状況
    st.subheader("📈 本日の営業活動状況")
    
    if not email_history_df.empty:
        today = datetime.now().date()
        today_emails_df = email_history_df[email_history_df['sent_at'].dt.date == today] if 'sent_at' in email_history_df.columns else pd.DataFrame()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            today_count = len(today_emails_df)
            st.metric("📧 本日送信", today_count)
        
        with col2:
            success_count = len(today_emails_df[today_emails_df['status'] == 'success']) if not today_emails_df.empty else 0
            success_rate = (success_count / today_count * 100) if today_count > 0 else 0
            st.metric("✅ 成功率", f"{success_rate:.1f}%")
        
        with col3:
            contacted_today = len(companies_df[companies_df['status'] == 'Contacted']) if not companies_df.empty else 0
            st.metric("🤝 連絡済み企業", contacted_today)
    
    else:
        st.info("📭 まだ営業活動データがありません。メールキャンペーンを開始してください。")

def companies_page():
    """企業管理ページ（ENR最適化版）"""
    st.title("🏢 ENR企業管理")
    
    db_manager, email_service = get_managers()
    if not db_manager:
        return
    
    # フィルターセクション
    with st.expander("🔍 検索・フィルター", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_filter = st.selectbox("ステータスフィルター", ["すべて", "New", "Contacted", "Replied", "Qualified", "Lost"])
        
        with col2:
            priority_filter = st.selectbox("優先度フィルター", ["すべて", "Wi-Fi必要", "高スコア", "キーワードマッチ"])
        
        with col3:
            search_term = st.text_input("🔍 企業名検索")
        
        with col4:
            min_score = st.slider("最小関連度スコア", 0, 100, 0)
    
    # データ取得・表示
    companies_df = db_manager.get_companies(status_filter, search_term, min_score, priority_filter)
    
    if not companies_df.empty:
        st.write(f"📊 表示中: {len(companies_df)} 社")
        
        # データテーブル表示
        display_columns = ['company_name', 'picocela_relevance_score', 'needs_wifi', 'keyword_match_count', 'email_address', 'status']
        available_columns = [col for col in display_columns if col in companies_df.columns]
        
        if available_columns:
            display_df = companies_df[available_columns].copy()
            display_df.columns = ['企業名', '関連度スコア', 'Wi-Fi必要', 'キーワード数', 'メールアドレス', 'ステータス']
            
            # 優先度に基づく色分け
            def highlight_priority(row):
                if row['関連度スコア'] >= 80:
                    return ['background-color: #ff6b6b; color: white'] * len(row)
                elif row['Wi-Fi必要'] == 'Yes':
                    return ['background-color: #feca57; color: black'] * len(row)
                elif row['関連度スコア'] >= 60:
                    return ['background-color: #74b9ff; color: white'] * len(row)
                return [''] * len(row)
            
            styled_df = display_df.style.apply(highlight_priority, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(companies_df, use_container_width=True)
    else:
        st.warning("📭 条件に合致する企業が見つかりません")
    
    # ENRデータインポートセクション
    st.subheader("📥 ENRデータインポート")
    
    # ENRファイルアップロード
    uploaded_file = st.file_uploader(
        "ENR企業データファイル (Excel)", 
        type=['xlsx', 'xls'],
        help="ENR_Companies_Complete_Local.xlsx 形式のファイル"
    )
    
    if uploaded_file:
        try:
            import openpyxl
            df = pd.read_excel(uploaded_file)
            
            st.write("📊 ENRデータプレビュー:")
            st.dataframe(df.head(), use_container_width=True)
            
            # データ品質分析
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("企業数", len(df))
            with col2:
                email_count = len(df[df.iloc[:, 2].notna()]) if len(df.columns) > 2 else 0
                st.metric("メール有り", email_count)
            with col3:
                wifi_count = len(df[df.iloc[:, 6] == 'Yes']) if len(df.columns) > 6 else 0
                st.metric("Wi-Fi必要", wifi_count)
            
            if st.button("📥 ENRデータインポート実行", type="primary"):
                import_enr_data(uploaded_file, db_manager)
        
        except Exception as e:
            st.error(f"❌ ファイル読み込みエラー: {e}")

def import_enr_data(uploaded_file, db_manager):
    """ENRデータのインポート"""
    try:
        df = pd.read_excel(uploaded_file)
        
        imported = 0
        duplicates = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 既存企業名取得
        existing_companies = db_manager.get_companies()
        existing_names = set(existing_companies['company_name'].tolist()) if not existing_companies.empty else set()
        
        for i, row in df.iterrows():
            try:
                # ENRファイルの列構造に基づくマッピング
                company_name = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                if not company_name:
                    continue
                
                status_text.text(f"インポート中: {company_name} ({i+1}/{len(df)})")
                
                # 重複チェック
                if company_name in existing_names:
                    duplicates += 1
                    continue
                
                # ENRデータ構造に基づく企業データ準備
                company_data = {
                    'company_name': company_name,
                    'email_address': str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else "",
                    'website': str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else "",
                    'phone': str(row.iloc[4]).strip() if len(row) > 4 and pd.notna(row.iloc[4]) else "",
                    'address': str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else "",
                    'needs_wifi': str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else "No",
                    'description': str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else "",
                    'pdf_url': str(row.iloc[8]).strip() if len(row) > 8 and pd.notna(row.iloc[8]) else "",
                    'contact_info': str(row.iloc[9]).strip() if len(row) > 9 and pd.notna(row.iloc[9]) else "",
                    'source_url': str(row.iloc[10]).strip() if len(row) > 10 and pd.notna(row.iloc[10]) else "",
                    'keyword_match_count': int(row.iloc[11]) if len(row) > 11 and pd.notna(row.iloc[11]) else 0,
                    'status': 'New',
                    'industry_sector': '建設業',
                    'notes': f"ENRインポート: {datetime.now().strftime('%Y-%m-%d')}"
                }
                
                if db_manager.add_company(company_data):
                    imported += 1
                    existing_names.add(company_name)
                
            except Exception as e:
                st.warning(f"行のインポートエラー: {e}")
            
            progress_bar.progress((i + 1) / len(df))
        
        # 結果表示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ インポート成功", imported)
        with col2:
            st.metric("🔄 重複スキップ", duplicates) 
        with col3:
            st.metric("📊 処理済み", len(df))
        
        if imported > 0:
            st.success(f"🎉 {imported}件のENR企業データをGoogle Sheetsにインポートしました！")
            st.balloons()
            st.rerun()
        
    except Exception as e:
        st.error(f"❌ ENRインポートエラー: {e}")

def email_campaign_page():
    """メールキャンペーンページ（ENR最適化版）"""
    st.title("📧 ENR企業向けメールキャンペーン")
    
    db_manager, email_service = get_managers()
    if not db_manager or not email_service:
        return
    
    # Gmail設定確認
    gmail_config = st.session_state.get('gmail_config')
    
    if not gmail_config:
        st.warning("⚠️ Gmail設定が必要です")
        setup_gmail_config()
        return
    
    # 設定情報表示
    st.success(f"✅ Gmail設定済み: {gmail_config['email']} | 送信者名: {gmail_config['sender_name']}")
    
    # キャンペーンタブ
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 戦略的配信", "🧪 テスト送信", "📊 配信履歴", "📝 ENR専用テンプレート"])
    
    with tab1:
        strategic_email_campaign(db_manager, email_service)
    
    with tab2:
        test_email_send(db_manager, email_service)
    
    with tab3:
        email_history_view(db_manager)
    
    with tab4:
        template_management(email_service)

def strategic_email_campaign(db_manager, email_service):
    """戦略的メール配信（ENR最適化版）"""
    st.subheader("🎯 ENR企業向け戦略的メール配信")
    
    # 配信戦略選択
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 配信戦略")
        strategy = st.selectbox(
            "配信戦略を選択",
            [
                "Wi-Fi必要企業優先 (最高優先度)",
                "高関連度スコア企業 (80点以上)",
                "キーワードマッチ企業",
                "新規企業 (ステータス:New)",
                "カスタム条件"
            ]
        )
    
    with col2:
        st.markdown("### ⚙️ 配信設定")
        max_emails = st.number_input("最大配信数", min_value=1, max_value=100, value=20)
        delay_range = st.select_slider("送信間隔（秒）", options=[3, 5, 8, 10, 15], value=8)
    
    # 戦略別企業取得
    if strategy == "Wi-Fi必要企業優先 (最高優先度)":
        companies_df = db_manager.get_companies(priority_filter="Wi-Fi必要")
        template_suggestion = "wifi_focused"
    elif strategy == "高関連度スコア企業 (80点以上)":
        companies_df = db_manager.get_companies(min_score=80)
        template_suggestion = "initial_contact"
    elif strategy == "キーワードマッチ企業":
        companies_df = db_manager.get_companies(priority_filter="キーワードマッチ")
        template_suggestion = "initial_contact"
    elif strategy == "新規企業 (ステータス:New)":
        companies_df = db_manager.get_companies(status_filter="New")
        template_suggestion = "initial_contact"
    else:  # カスタム条件
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("ステータス", ["すべて", "New", "Contacted"])
        with col2:
            min_score = st.slider("最小スコア", 0, 100, 60)
        with col3:
            wifi_only = st.checkbox("Wi-Fi必要企業のみ")
        
        companies_df = db_manager.get_companies(status_filter, None, min_score)
        if wifi_only:
            companies_df = companies_df[companies_df['needs_wifi'] == 'Yes']
        template_suggestion = "initial_contact"
    
    # 配信対象企業表示
    if not companies_df.empty:
        # メールアドレスがある企業のみ
        email_companies = companies_df[companies_df['email_address'].notna() & (companies_df['email_address'] != '')]
        target_companies = email_companies.head(max_emails)
        
        if not target_companies.empty:
            st.markdown(f"### 📊 配信対象: {len(target_companies)}社")
            
            # 戦略分析
            col1, col2, col3 = st.columns(3)
            with col1:
                wifi_count = len(target_companies[target_companies['needs_wifi'] == 'Yes'])
                st.metric("📶 Wi-Fi必要企業", wifi_count)
            with col2:
                avg_score = target_companies['picocela_relevance_score'].mean()
                st.metric("📈 平均関連度スコア", f"{avg_score:.1f}")
            with col3:
                keyword_total = target_companies['keyword_match_count'].sum()
                st.metric("🔍 総キーワードマッチ", int(keyword_total))
            
            # 対象企業テーブル
            display_columns = ['company_name', 'picocela_relevance_score', 'needs_wifi', 'keyword_match_count', 'email_address']
            available_columns = [col for col in display_columns if col in target_companies.columns]
            
            if available_columns:
                display_df = target_companies[available_columns].copy()
                display_df.columns = ['企業名', '関連度スコア', 'Wi-Fi必要', 'キーワード数', 'メールアドレス']
                
                # 優先度色分け
                def highlight_priority(row):
                    if row['関連度スコア'] >= 80:
                        return ['background-color: #ff6b6b; color: white'] * len(row)
                    elif row['Wi-Fi必要'] == 'Yes':
                        return ['background-color: #feca57; color: black'] * len(row)
                    return [''] * len(row)
                
                styled_df = display_df.style.apply(highlight_priority, axis=1)
                st.dataframe(styled_df, use_container_width=True)
            
            # テンプレート選択
            templates = email_service.get_email_templates()
            template_name = st.selectbox(
                "📝 メールテンプレート", 
                list(templates.keys()),
                index=list(templates.keys()).index(template_suggestion) if template_suggestion in templates else 0
            )
            
            # プレビュー表示
            with st.expander("👀 メールプレビュー"):
                template = templates[template_name]
                sample_company = target_companies.iloc[0]['company_name']
                preview_body = template['body'].format(company_name=sample_company)
                
                st.write(f"**件名**: {template['subject']}")
                st.text_area("本文プレビュー", preview_body, height=300, disabled=True)
            
            # 配信実行
            st.markdown("### 🚀 配信実行")
            
            col1, col2 = st.columns(2)
            with col1:
                confirm_send = st.checkbox(f"✅ {len(target_companies)}社への配信を実行する")
            with col2:
                campaign_name = st.text_input("キャンペーン名", value=f"ENR_{strategy.split()[0]}_{datetime.now().strftime('%m%d')}")
            
            if confirm_send and st.button("📧 戦略的配信開始", type="primary", use_container_width=True):
                execute_strategic_campaign(target_companies, template_name, delay_range, campaign_name, db_manager, email_service)
        else:
            st.warning("📭 メールアドレスを持つ企業が見つかりません")
    else:
        st.warning("📭 配信対象企業が見つかりません")

def execute_strategic_campaign(target_companies, template_name, delay_range, campaign_name, db_manager, email_service):
    """戦略的キャンペーン実行"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_count = 0
    total = len(target_companies)
    
    results = []
    start_time = datetime.now()
    
    # キャンペーンID生成
    campaign_id = f"{campaign_name}_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    for i, (index, row) in enumerate(target_companies.iterrows()):
        company_name = row['company_name']
        email_address = row['email_address']
        
        status_text.text(f"📧 {company_name} に送信中... ({i+1}/{total})")
        
        success, message = email_service.send_email(email_address, company_name, template_name)
        
        if success:
            success_count += 1
            # ステータス更新
            db_manager.update_company_status(company_name, "Contacted")
            
            results.append({
                'company': company_name,
                'score': row.get('picocela_relevance_score', 0),
                'wifi_needed': row.get('needs_wifi', 'No'),
                'status': '✅ 成功',
                'message': '送信完了'
            })
        else:
            failed_count += 1
            results.append({
                'company': company_name,
                'score': row.get('picocela_relevance_score', 0),
                'wifi_needed': row.get('needs_wifi', 'No'),
                'status': '❌ 失敗',
                'message': message
            })
        
        progress_bar.progress((i + 1) / total)
        
        # 送信間隔
        if i < total - 1:
            time.sleep(delay_range)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 結果表示
    status_text.text("✅ 戦略的配信完了")
    
    # 結果メトリクス
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📧 総送信数", total)
    with col2:
        st.metric("✅ 成功", success_count)
    with col3:
        st.metric("❌ 失敗", failed_count)
    with col4:
        success_rate = (success_count / total * 100) if total > 0 else 0
        st.metric("📈 成功率", f"{success_rate:.1f}%")
    
    st.info(f"⏱️ 所要時間: {duration:.1f}秒 ({duration/60:.1f}分)")
    st.info(f"🏷️ キャンペーンID: {campaign_id}")
    
    # 詳細結果
    with st.expander("📋 詳細結果"):
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)
    
    # 成功時のお祝い
    if success_rate >= 90:
        st.balloons()
        st.success("🎉 素晴らしい成功率です！ENR企業への戦略的アプローチが成功しました！")

def test_email_send(db_manager, email_service):
    """テストメール送信（ENR最適化版）"""
    st.subheader("🧪 ENR企業向けテストメール送信")
    
    companies_df = db_manager.get_companies()
    
    if not companies_df.empty:
        # 高優先度企業を上位表示
        companies_df_sorted = companies_df.sort_values(['picocela_relevance_score', 'needs_wifi'], ascending=[False, False])
        email_companies = companies_df_sorted[companies_df_sorted['email_address'].notna() & (companies_df_sorted['email_address'] != '')]
        
        if not email_companies.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # 企業選択（優先度順）
                company_options = []
                for _, row in email_companies.head(20).iterrows():
                    wifi_icon = "📶" if row.get('needs_wifi') == 'Yes' else ""
                    score = row.get('picocela_relevance_score', 0)
                    priority_icon = "🔥" if score >= 80 else "⭐" if score >= 60 else ""
                    company_options.append(f"{priority_icon}{wifi_icon} {row['company_name']} (スコア:{score})")
                
                selected_option = st.selectbox("🏢 テスト対象企業", company_options)
                selected_company_name = selected_option.split("] ")[-1].split(" (スコア:")[0] if "] " in selected_option else selected_option.split(" (スコア:")[0].replace("🔥", "").replace("⭐", "").replace("📶", "").strip()
            
            with col2:
                templates = email_service.get_email_templates()
                template_name = st.selectbox("📝 テンプレート", list(templates.keys()))
            
            # 選択された企業の情報表示
            selected_company = email_companies[email_companies['company_name'] == selected_company_name].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**📧 送信先**: {selected_company['email_address']}")
            with col2:
                st.write(f"**🎯 関連度スコア**: {selected_company.get('picocela_relevance_score', 0)}")
            with col3:
                wifi_status = "✅ 必要" if selected_company.get('needs_wifi') == 'Yes' else "❌ 不要"
                st.write(f"**📶 Wi-Fi**: {wifi_status}")
            
            # 企業詳細情報
            if st.checkbox("📋 企業詳細情報を表示"):
                st.write(f"**🌐 ウェブサイト**: {selected_company.get('website', 'N/A')}")
                st.write(f"**📞 電話**: {selected_company.get('phone', 'N/A')}")
                st.write(f"**🔍 キーワードマッチ**: {selected_company.get('keyword_match_count', 0)}件")
                if selected_company.get('description'):
                    st.write(f"**📝 企業説明**: {selected_company.get('description', '')[:200]}...")
            
            # プレビュー
            template = templates[template_name]
            preview_body = template['body'].format(company_name=selected_company_name)
            
            with st.expander("👀 メールプレビュー"):
                st.write(f"**件名**: {template['subject']}")
                st.text_area("本文", preview_body, height=300, disabled=True)
            
            if st.button("🧪 テスト送信", type="primary"):
                with st.spinner("送信中..."):
                    success, message = email_service.send_email(
                        selected_company['email_address'], 
                        selected_company_name, 
                        template_name
                    )
                
                if success:
                    st.success(f"✅ テスト送信成功: {selected_company_name}")
                    st.info("📧 メール配信履歴に記録されました")
                    
                    # 送信後の推奨アクション
                    st.markdown("### 📈 次のアクション推奨")
                    if selected_company.get('needs_wifi') == 'Yes':
                        st.info("💡 この企業はWi-Fi必要企業です。フォローアップを優先してください。")
                    if selected_company.get('picocela_relevance_score', 0) >= 80:
                        st.info("💡 高関連度企業です。1週間以内にフォローアップメールを送信することを推奨します。")
                else:
                    st.error(f"❌ テスト送信失敗: {message}")
        else:
            st.warning("📭 メールアドレスを持つ企業が見つかりません")
    else:
        st.warning("🔍 テスト対象企業が見つかりません")

def email_history_view(db_manager):
    """メール配信履歴（ENR最適化版）"""
    st.subheader("📊 ENR企業向けメール配信履歴")
    
    # フィルター
    col1, col2, col3 = st.columns(3)
    with col1:
        days_back = st.selectbox("期間", [7, 30, 90, 365], index=1)
    with col2:
        status_filter = st.selectbox("ステータス", ["すべて", "success", "failed"])
    with col3:
        limit = st.selectbox("表示件数", [25, 50, 100], index=1)
    
    # データ取得
    history_df = db_manager.get_email_history(days_back, status_filter, limit)
    
    if not history_df.empty:
        # 統計情報
        total_emails = len(history_df)
        success_emails = len(history_df[history_df['status'] == 'success']) if 'status' in history_df.columns else 0
        success_rate = (success_emails / total_emails * 100) if total_emails > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📧 総送信数", total_emails)
        with col2:
            st.metric("✅ 成功数", success_emails)
        with col3:
            st.metric("📈 成功率", f"{success_rate:.1f}%")
        with col4:
            unique_companies = len(history_df['company_name'].unique()) if 'company_name' in history_df.columns else 0
            st.metric("🏢 送信企業数", unique_companies)
        
        # キャンペーン分析
        if 'template_used' in history_df.columns:
            st.subheader("📊 テンプレート別効果分析")
            template_stats = history_df.groupby('template_used')['status'].value_counts().unstack(fill_value=0)
            
            if 'success' in template_stats.columns:
                template_stats['success_rate'] = (template_stats['success'] / (template_stats.sum(axis=1)) * 100).round(1)
                st.dataframe(template_stats, use_container_width=True)
        
        # データテーブル
        st.subheader("📋 配信履歴詳細")
        display_columns = ['sent_at', 'company_name', 'template_used', 'status']
        available_columns = [col for col in display_columns if col in history_df.columns]
        
        if available_columns:
            display_df = history_df[available_columns].copy()
            display_df.columns = ['送信時刻', '企業名', 'テンプレート', 'ステータス']
            
            # ステータス色分け
            def highlight_status(val):
                if val == 'success':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'failed':
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            
            styled_df = display_df.style.applymap(highlight_status, subset=['ステータス'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(history_df, use_container_width=True)
        
    else:
        st.info("📭 指定期間の配信履歴がありません")

def template_management(email_service):
    """テンプレート管理（ENR特化版）"""
    st.subheader("📝 ENR企業向けメールテンプレート管理")
    
    templates = email_service.get_email_templates()
    
    # テンプレート一覧
    st.markdown("### 📋 利用可能テンプレート")
    
    for template_name, template_data in templates.items():
        with st.expander(f"📧 {template_name}"):
            st.write(f"**件名**: {template_data['subject']}")
            st.text_area("本文", template_data['body'], height=200, disabled=True, key=f"template_{template_name}")
            
            # テンプレート特徴
            if template_name == "initial_contact":
                st.info("💡 **用途**: 初回アプローチ用。一般的なENR企業向け")
            elif template_name == "wifi_focused":
                st.info("💡 **用途**: Wi-Fi必要企業向け。技術的なメリットを強調")
            elif template_name == "follow_up":
                st.info("💡 **用途**: フォローアップ用。既に接触した企業向け")
    
    # テンプレート使用分析
    st.markdown("### 📊 テンプレート効果分析")
    st.info("📈 実際の送信データに基づく効果分析（実装予定）")
    
    # 新しいテンプレート提案
    st.markdown("### 💡 ENR企業向け追加テンプレート案")
    
    additional_templates = {
        "construction_tech": {
            "name": "建設技術特化版",
            "description": "最新建設技術やDXに関心の高い企業向け",
            "target": "技術革新に積極的な建設会社"
        },
        "iot_integration": {
            "name": "IoT統合提案版", 
            "description": "IoTセンサーとの連携を重視する企業向け",
            "target": "スマート建設に取り組む企業"
        },
        "cost_efficiency": {
            "name": "コスト効率重視版",
            "description": "コスト削減効果を前面に出す企業向け",
            "target": "効率化・コスト削減を重視する企業"
        }
    }
    
    for template_id, template_info in additional_templates.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"**{template_info['name']}**")
        with col2:
            st.write(f"*{template_info['description']}*")
        with col3:
            if st.button("➕", key=f"add_{template_id}", help=f"{template_info['name']}を追加"):
                st.info("💡 カスタムテンプレート機能は次期バージョンで実装予定です")

def setup_gmail_config():
    """Gmail設定セットアップ（ENR最適化版）"""
    st.subheader("📧 Gmail SMTP設定（ENR営業用）")
    
    # 現在の設定表示
    current_config = st.session_state.get('gmail_config')
    if current_config:
        st.success("✅ Gmail設定済み")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📧 **メールアドレス**: {current_config['email']}")
        with col2:
            st.info(f"👤 **送信者名**: {current_config['sender_name']}")
    
    # 設定フォーム
    with st.form("gmail_config_form"):
        st.markdown("### 🔧 PicoCELA営業用Gmail設定")
        
        email = st.text_input(
            "📧 PicoCELA Gmailアドレス", 
            value=current_config.get('email', 'tokuda@picocela.com') if current_config else 'tokuda@picocela.com',
            help="PicoCELA公式営業用Gmailアドレス"
        )
        
        password = st.text_input(
            "🔑 アプリパスワード", 
            type="password",
            value=current_config.get('password', '') if current_config else '',
            help="Gmailの2段階認証で生成したアプリパスワード"
        )
        
        sender_name = st.text_input(
            "👤 送信者名", 
            value=current_config.get('sender_name', 'PicoCELA Inc.') if current_config else 'PicoCELA Inc.',
            help="ENR企業に表示される送信者名"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 設定保存", type="primary")
        with col2:
            test_button = st.form_submit_button("🧪 接続テスト")
        
        if save_button:
            if email and password and sender_name:
                config = {
                    "email": email,
                    "password": password,
                    "sender_name": sender_name,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587
                }
                st.session_state.gmail_config = config
                st.success("✅ Gmail設定を保存しました")
                st.rerun()
            else:
                st.error("❌ すべての項目を入力してください")
        
        if test_button:
            if email and password:
                test_config = {
                    "email": email,
                    "password": password,
                    "sender_name": sender_name,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587
                }
                test_gmail_connection(test_config)
            else:
                st.error("❌ メールアドレスとパスワードを入力してください")

def test_gmail_connection(config):
    """Gmail接続テスト"""
    try:
        with st.spinner("PicoCELA Gmail接続テスト中..."):
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email'], config['password'])
            server.quit()
        
        st.success("✅ PicoCELA Gmail接続テスト成功")
        st.balloons()
        
    except smtplib.SMTPAuthenticationError:
        st.error("❌ 認証エラー: メールアドレスまたはアプリパスワードが間違っています")
    except smtplib.SMTPException as e:
        st.error(f"❌ SMTP接続エラー: {e}")
    except Exception as e:
        st.error(f"❌ 接続テストエラー: {e}")

def settings_page():
    """設定ページ（ENR最適化版）"""
    st.title("⚙️ システム設定")
    
    tab1, tab2, tab3 = st.tabs(["📧 Gmail設定", "🔧 システム", "📊 ENRデータ管理"])
    
    with tab1:
        setup_gmail_config()
    
    with tab2:
        system_settings()
    
    with tab3:
        enr_data_management()

def system_settings():
    """システム設定（ENR最適化版）"""
    st.subheader("🔧 FusionCRM システム設定")
    
    db_manager, email_service = get_managers()
    if not db_manager:
        return
    
    # ENRデータ統計
    companies_df = db_manager.get_companies()
    email_history_df = db_manager.get_email_history()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        company_count = len(companies_df) if not companies_df.empty else 0
        st.metric("🏢 ENR企業データ", f"{company_count}件")
    
    with col2:
        email_count = len(email_history_df) if not email_history_df.empty else 0
        st.metric("📧 メール履歴", f"{email_count}件")
    
    with col3:
        wifi_companies = len(companies_df[companies_df['needs_wifi'] == 'Yes']) if not companies_df.empty else 0
        st.metric("📶 Wi-Fi必要企業", f"{wifi_companies}件")
    
    with col4:
        high_score_companies = len(companies_df[companies_df['picocela_relevance_score'] >= 80]) if not companies_df.empty else 0
        st.metric("🎯 高優先度企業", f"{high_score_companies}件")
    
    # システム情報
    st.subheader("ℹ️ システム情報")
    
    system_info = {
        "🐍 Python版": sys.version.split()[0],
        "📦 Streamlit版": st.__version__,
        "🗄️ データベース": "Google Sheets (ENR最適化)",
        "📧 メール送信": "Gmail SMTP",
        "🌐 展開環境": "Streamlit Cloud",
        "📊 データソース": "ENR Future Tech企業データ",
        "🎯 特化機能": "PicoCELA関連度スコア自動計算"
    }
    
    for key, value in system_info.items():
        st.write(f"**{key}**: {value}")
    
    # Google Sheets情報
    if db_manager and db_manager.spreadsheet:
        st.subheader("📊 Google Sheets情報")
        st.write(f"**スプレッドシート名**: {db_manager.spreadsheet.title}")
        st.write(f"**URL**: {db_manager.spreadsheet.url}")
        
        # ワークシート情報
        try:
            worksheets = db_manager.spreadsheet.worksheets()
            st.write("**ワークシート一覧**:")
            for ws in worksheets:
                row_count = ws.row_count
                col_count = ws.col_count
                st.write(f"  • {ws.title}: {row_count}行 × {col_count}列")
        except Exception as e:
            st.warning(f"ワークシート情報取得エラー: {e}")

def enr_data_management():
    """ENRデータ管理"""
    st.subheader("📊 ENRデータ管理・分析")
    
    db_manager, email_service = get_managers()
    if not db_manager:
        return
    
    companies_df = db_manager.get_companies()
    
    if not companies_df.empty:
        # ENRデータ品質分析
        st.markdown("### 📈 ENRデータ品質分析")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            email_rate = len(companies_df[companies_df['email_address'].notna()]) / len(companies_df) * 100
            st.metric("📧 メールアドレス保有率", f"{email_rate:.1f}%")
        
        with col2:
            wifi_rate = len(companies_df[companies_df['needs_wifi'] == 'Yes']) / len(companies_df) * 100
            st.metric("📶 Wi-Fi必要企業率", f"{wifi_rate:.1f}%")
        
        with col3:
            avg_keywords = companies_df['keyword_match_count'].mean()
            st.metric("🔍 平均キーワードマッチ", f"{avg_keywords:.1f}")
        
        # 関連度スコア分布
        st.markdown("### 🎯 PicoCELA関連度スコア分布")
        
        fig_hist = px.histogram(
            companies_df,
            x='picocela_relevance_score',
            nbins=20,
            title="PicoCELA関連度スコア分布",
            labels={'picocela_relevance_score': '関連度スコア', 'count': '企業数'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Wi-Fi vs スコアの関係
        if 'needs_wifi' in companies_df.columns:
            st.markdown("### 📊 Wi-Fi必要性と関連度スコアの関係")
            
            fig_box = px.box(
                companies_df,
                x='needs_wifi',
                y='picocela_relevance_score',
                title="Wi-Fi必要性別 関連度スコア分布",
                labels={'needs_wifi': 'Wi-Fi必要性', 'picocela_relevance_score': '関連度スコア'}
            )
            st.plotly_chart(fig_box, use_container_width=True)
        
        # データ最適化提案
        st.markdown("### 💡 データ最適化提案")
        
        low_score_companies = len(companies_df[companies_df['picocela_relevance_score'] < 40])
        if low_score_companies > 0:
            st.warning(f"⚠️ {low_score_companies}社が低関連度スコア（40未満）です。追加のキーワード分析を推奨します。")
        
        no_email_companies = len(companies_df[companies_df['email_address'].isna() | (companies_df['email_address'] == '')])
        if no_email_companies > 0:
            st.info(f"📧 {no_email_companies}社にメールアドレスがありません。企業ウェブサイトから追加取得を検討してください。")
        
        high_potential = len(companies_df[
            (companies_df['needs_wifi'] == 'Yes') & 
            (companies_df['picocela_relevance_score'] >= 70) &
            (companies_df['status'] == 'New')
        ])
        if high_potential > 0:
            st.success(f"🎯 {high_potential}社が高ポテンシャル企業（Wi-Fi必要+高スコア+未接触）です。優先的にアプローチしてください。")
    
    else:
        st.info("📭 ENRデータがまだインポートされていません。企業管理ページでデータをインポートしてください。")

def main():
    """メインアプリケーション（ENR最適化版）"""
    
    # 認証チェック
    if not st.session_state.get('logged_in', False):
        login_page()
        return
    
    # サイドバー
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.username}")
        st.markdown(f"**Role**: {st.session_state.get('user_role', 'user')}")
        
        # システム状態表示
        gmail_config = st.session_state.get('gmail_config')
        if gmail_config:
            st.success("✅ Gmail設定済み")
        else:
            st.warning("⚠️ Gmail未設定")
        
        # Google Sheets状態
        if check_google_sheets_setup():
            st.success("✅ Google Sheets接続済み")
        else:
            st.warning("⚠️ Google Sheets未設定")
        
        # ENRデータ状態
        db_manager, _ = get_managers()
        if db_manager:
            companies_df = db_manager.get_companies()
            company_count = len(companies_df) if not companies_df.empty else 0
            if company_count > 0:
                st.success(f"✅ ENRデータ: {company_count}社")
            else:
                st.warning("⚠️ ENRデータ未インポート")
        
        # ナビゲーション
        page = st.radio(
            "🧭 ページ選択",
            ["📊 ダッシュボード", "🏢 企業管理", "📧 メールキャンペーン", "⚙️ 設定"],
            key="navigation"
        )
        
        # クイック統計（ENR特化）
        if db_manager and not companies_df.empty:
            st.markdown("---")
            st.markdown("### 📈 ENRクイック統計")
            
            wifi_needed = len(companies_df[companies_df['needs_wifi'] == 'Yes'])
            high_score = len(companies_df[companies_df['picocela_relevance_score'] >= 80])
            
            st.metric("Wi-Fi必要", wifi_needed, delta=None)
            st.metric("高優先度", high_score, delta=None)
        
        # ログアウト
        st.markdown("---")
        if st.button("🚪 ログアウト", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # ページルーティング
    if page == "📊 ダッシュボード":
        dashboard_page()
    elif page == "🏢 企業管理":
        companies_page()
    elif page == "📧 メールキャンペーン":
        email_campaign_page()
    elif page == "⚙️ 設定":
        settings_page()

# アプリケーション起動
if __name__ == "__main__":
    main()
