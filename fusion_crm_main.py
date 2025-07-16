import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import importlib.util
import time
import re

# メール関連のimportをtry-except文で安全に処理
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    st.warning("⚠️ メール機能は現在利用できません（Streamlit Cloud環境）")

# ページ設定
st.set_page_config(
    page_title="FusionCRM - PicoCELA営業管理システム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 拡張ステータス定義（ENR最適化対応）
SALES_STATUS = {
    'New': '新規企業',
    'Contacted': '初回連絡済み', 
    'Replied': '返信あり',
    'Engaged': '継続対話中',      # 🆕 オンラインミーティング段階
    'Qualified': '有望企業確定',
    'Proposal': '提案書提出済み',  # 🆕 提案段階
    'Negotiation': '契約交渉中',  # 🆕 条件調整段階
    'Won': '受注成功',            # 🆕 成約
    'Lost': '失注',
    'Dormant': '休眠中'           # 🆕 再活性化対象
}

# ステータス優先度（ENR戦略対応）
STATUS_PRIORITY = {
    'Won': 10, 'Negotiation': 9, 'Proposal': 8, 'Qualified': 7,
    'Engaged': 6, 'Replied': 5, 'Contacted': 4, 'New': 3,
    'Dormant': 2, 'Lost': 1
}

# PicoCELA関連キーワード（ENRデータ分析用）
PICOCELA_KEYWORDS = [
    'network', 'mesh', 'wireless', 'wifi', 'connectivity',
    'iot', 'smart', 'digital', 'automation', 'sensor', 'ai',
    'construction', 'building', 'site', 'industrial', 'management',
    'platform', 'solution', 'integration', 'control', 'monitoring'
]

def hash_password(password):
    """パスワードハッシュ化（Streamlit Cloud対応）"""
    # SHA256 + ソルトによる安全なハッシュ化
    salt = "picocela_fusion_crm_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password, hashed):
    """パスワード検証"""
    return hash_password(password) == hashed

class DatabaseManager:
    """データベース管理クラス（認証システム修正版）"""
    
    def __init__(self, db_name="fusion_crm.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """データベース初期化（認証システム修正版）"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # ユーザーテーブル（ハッシュ化方式変更）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # 企業テーブル（拡張フィールド追加）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                website_url TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                industry TEXT,
                employees_count TEXT,
                revenue_range TEXT,
                status TEXT DEFAULT 'New',
                picocela_relevance_score INTEGER DEFAULT 0,
                keywords_matched TEXT,
                wifi_required BOOLEAN DEFAULT 0,
                priority_score INTEGER DEFAULT 0,
                source TEXT DEFAULT 'Manual',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact_date TIMESTAMP,
                next_action TEXT,
                next_action_date TIMESTAMP
            )
        ''')
        
        # ステータス履歴テーブル（新規追加）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY,
                company_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                changed_by TEXT,
                change_reason TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # メール送信履歴テーブル（拡張）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY,
                company_id INTEGER,
                template_name TEXT,
                subject TEXT,
                body TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                error_message TEXT,
                opened BOOLEAN DEFAULT 0,
                replied BOOLEAN DEFAULT 0,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # 既存テーブルのカラム追加（安全な実装）
        self._add_missing_columns(cursor)
        
        conn.commit()
        conn.close()
    
    def _add_missing_columns(self, cursor):
        """既存データベースに新しいカラムを安全に追加"""
        new_columns = [
            ('companies', 'wifi_required', 'BOOLEAN DEFAULT 0'),
            ('companies', 'priority_score', 'INTEGER DEFAULT 0'),
            ('companies', 'source', 'TEXT DEFAULT "Manual"'),
            ('companies', 'notes', 'TEXT'),
            ('companies', 'last_contact_date', 'TIMESTAMP'),
            ('companies', 'next_action', 'TEXT'),
            ('companies', 'next_action_date', 'TIMESTAMP'),
            ('users', 'last_login', 'TIMESTAMP'),
            ('users', 'is_active', 'BOOLEAN DEFAULT 1')
        ]
        
        for table, column, definition in new_columns:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
            except sqlite3.OperationalError:
                # カラムが既に存在する場合は無視
                pass

class ENRDataProcessor:
    """ENRデータ処理クラス"""
    
    @staticmethod
    def calculate_picocela_relevance(company_data):
        """PicoCELA関連度スコア計算"""
        score = 0
        text_fields = [
            company_data.get('company_name', ''),
            company_data.get('website_url', ''),
            company_data.get('notes', ''),
            str(company_data.get('industry', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for keyword in PICOCELA_KEYWORDS:
            if keyword.lower() in full_text:
                score += 10
        
        return min(score, 100)  # 最大100点
    
    @staticmethod
    def detect_wifi_requirement(company_data):
        """WiFi需要判定"""
        wifi_indicators = [
            'wifi', 'wireless', 'network', 'connectivity', 
            'iot', 'smart building', 'construction tech'
        ]
        
        text_fields = [
            company_data.get('company_name', ''),
            company_data.get('notes', ''),
            str(company_data.get('industry', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for indicator in wifi_indicators:
            if indicator in full_text:
                return True
        return False
    
    @staticmethod
    def calculate_priority_score(company_data):
        """優先度スコア計算（WiFi需要 + 関連度）"""
        relevance = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        
        priority = relevance
        if wifi_required:
            priority += 50  # WiFi必要企業にボーナス
        
        return min(priority, 150)  # 最大150点

class CompanyManager:
    """企業管理クラス（拡張ステータス対応）"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_company(self, company_data, user_id="system"):
        """企業追加（ENR最適化対応）"""
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        
        # PicoCELA関連度とWiFi需要を自動計算
        relevance_score = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        priority_score = ENRDataProcessor.calculate_priority_score(company_data)
        
        cursor.execute('''
            INSERT INTO companies (
                company_name, website_url, email, phone, address, 
                industry, employees_count, revenue_range, status,
                picocela_relevance_score, wifi_required, priority_score,
                source, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            company_data.get('company_name'),
            company_data.get('website_url'),
            company_data.get('email'),
            company_data.get('phone'),
            company_data.get('address'),
            company_data.get('industry'),
            company_data.get('employees_count'),
            company_data.get('revenue_range'),
            company_data.get('status', 'New'),
            relevance_score,
            wifi_required,
            priority_score,
            company_data.get('source', 'Manual'),
            company_data.get('notes', '')
        ))
        
        company_id = cursor.lastrowid
        
        # ステータス履歴記録
        self._log_status_change(cursor, company_id, None, 'New', user_id, "企業登録")
        
        conn.commit()
        conn.close()
        return company_id
    
    def update_status(self, company_id, new_status, user_id, reason="", notes=""):
        """ステータス更新（履歴記録付き）"""
        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        
        # 現在のステータス取得
        cursor.execute('SELECT status FROM companies WHERE id = ?', (company_id,))
        result = cursor.fetchone()
        old_status = result[0] if result else None
        
        # ステータス更新
        cursor.execute('''
            UPDATE companies 
            SET status = ?, updated_at = CURRENT_TIMESTAMP, last_contact_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, company_id))
        
        # 履歴記録
        self._log_status_change(cursor, company_id, old_status, new_status, user_id, reason, notes)
        
        conn.commit()
        conn.close()
    
    def _log_status_change(self, cursor, company_id, old_status, new_status, user_id, reason="", notes=""):
        """ステータス変更履歴記録"""
        cursor.execute('''
            INSERT INTO status_history (
                company_id, old_status, new_status, changed_by, change_reason, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (company_id, old_status, new_status, user_id, reason, notes))
    
    def get_companies_by_status(self, status=None, wifi_required=None):
        """ステータス別企業取得（フィルタ拡張）"""
        conn = sqlite3.connect(self.db.db_name)
        
        query = 'SELECT * FROM companies WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if wifi_required is not None:
            query += ' AND wifi_required = ?'
            params.append(wifi_required)
        
        query += ' ORDER BY priority_score DESC, updated_at DESC'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_status_analytics(self):
        """ステータス分析データ取得"""
        conn = sqlite3.connect(self.db.db_name)
        
        # ステータス別企業数
        status_df = pd.read_sql_query('''
            SELECT status, COUNT(*) as count, 
                   AVG(picocela_relevance_score) as avg_relevance,
                   SUM(wifi_required) as wifi_count
            FROM companies 
            GROUP BY status
        ''', conn)
        
        # WiFi需要企業の分析
        wifi_df = pd.read_sql_query('''
            SELECT wifi_required, COUNT(*) as count,
                   AVG(picocela_relevance_score) as avg_relevance
            FROM companies 
            GROUP BY wifi_required
        ''', conn)
        
        conn.close()
        return status_df, wifi_df

class EmailCampaignManager:
    """メールキャンペーン管理（Streamlit Cloud対応）"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.email_available = EMAIL_AVAILABLE
    
    def get_campaign_targets(self, target_status, wifi_required=None, min_relevance=0):
        """キャンペーンターゲット取得"""
        conn = sqlite3.connect(self.db.db_name)
        
        query = '''
            SELECT * FROM companies 
            WHERE status = ? AND email IS NOT NULL AND email != ''
              AND picocela_relevance_score >= ?
        '''
        params = [target_status, min_relevance]
        
        if wifi_required is not None:
            query += ' AND wifi_required = ?'
            params.append(wifi_required)
        
        query += ' ORDER BY priority_score DESC'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

# 認証関数（修正版）
def authenticate_user(db_manager, username, password):
    """ユーザー認証（修正版）"""
    try:
        conn = sqlite3.connect(db_manager.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT password_hash, is_active FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result:
            stored_hash, is_active = result
            
            if not is_active:
                conn.close()
                return False, "アカウントが無効化されています"
            
            if verify_password(password, stored_hash):
                # 最終ログイン時刻更新
                cursor.execute(
                    'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?', 
                    (username,)
                )
                conn.commit()
                conn.close()
                return True, "ログイン成功"
            else:
                conn.close()
                return False, "パスワードが正しくありません"
        else:
            conn.close()
            return False, "ユーザーが存在しません"
            
    except Exception as e:
        return False, f"認証エラー: {str(e)}"

def create_user(db_manager, username, password, email, role="user"):
    """ユーザー作成（修正版）"""
    try:
        conn = sqlite3.connect(db_manager.db_name)
        cursor = conn.cursor()
        
        # パスワードハッシュ化
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, role)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, email, role))
        
        conn.commit()
        conn.close()
        return True, "ユーザー作成成功"
        
    except sqlite3.IntegrityError:
        return False, "ユーザー名が既に存在します"
    except Exception as e:
        return False, f"ユーザー作成エラー: {str(e)}"

def ensure_default_user(db_manager):
    """デフォルトユーザーの確保（修正版）"""
    try:
        conn = sqlite3.connect(db_manager.db_name)
        cursor = conn.cursor()
        
        # ユーザー数確認
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # ユーザーが存在しない場合、デフォルトユーザー作成
        if user_count == 0:
            default_password = "picocela2024"
            password_hash = hash_password(default_password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin", password_hash, "admin@picocela.com", "admin"))
            
            conn.commit()
            return True, "デフォルトユーザーを作成しました"
        
        conn.close()
        return True, "既存ユーザーがあります"
        
    except Exception as e:
        return False, f"デフォルトユーザー作成エラー: {str(e)}"

# Streamlitアプリメイン部分
def main():
    st.title("🚀 FusionCRM - PicoCELA営業管理システム")
    st.markdown("**ENR最適化・拡張ステータス対応版 (Streamlit Cloud)**")
    
    # 環境情報表示
    if not EMAIL_AVAILABLE:
        st.info("ℹ️ Streamlit Cloud環境で動作中 - メール機能は制限されています")
    
    # セッション状態初期化
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # データベース初期化
    db_manager = DatabaseManager()
    
    # デフォルトユーザー確保（初回実行用）
    success, message = ensure_default_user(db_manager)
    if not success:
        st.error(f"初期化エラー: {message}")
        return
    
    company_manager = CompanyManager(db_manager)
    email_manager = EmailCampaignManager(db_manager)
    
    # 認証確認
    if not st.session_state.logged_in:
        show_login_page(db_manager)
        return
    
    # サイドバーナビゲーション
    st.sidebar.title(f"👋 {st.session_state.username}")
    st.sidebar.markdown("🌐 **Streamlit Cloud版**")
    
    page = st.sidebar.selectbox(
        "📋 メニュー",
        ["📊 ダッシュボード", "🏢 企業管理", "📧 メールキャンペーン", 
         "📈 分析・レポート", "⚙️ 設定", "📁 データインポート"]
    )
    
    # ページルーティング
    if page == "📊 ダッシュボード":
        show_dashboard(company_manager)
    elif page == "🏢 企業管理":
        show_company_management(company_manager)
    elif page == "📧 メールキャンペーン":
        show_email_campaigns(email_manager, company_manager)
    elif page == "📈 分析・レポート":
        show_analytics(company_manager)
    elif page == "⚙️ 設定":
        show_settings()
    elif page == "📁 データインポート":
        show_data_import(company_manager)
    
    # ログアウト
    if st.sidebar.button("🚪 ログアウト"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

def show_login_page(db_manager):
    """ログインページ（認証システム修正版）"""
    st.markdown("## 🔐 FusionCRM ログイン")
    st.markdown("**PicoCELA営業管理システム - Streamlit Cloud版**")
    
    # デフォルトユーザー情報表示
    st.success("💡 **デフォルトログイン**: admin / picocela2024")
    
    tab1, tab2 = st.tabs(["🔑 ログイン", "👤 新規登録"])
    
    with tab1:
        st.subheader("🔑 ログイン")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            username = st.text_input("ユーザー名", value="admin", placeholder="ユーザー名を入力")
            password = st.text_input("パスワード", value="picocela2024", type="password", placeholder="パスワードを入力")
            
            if st.button("🚀 ログイン", type="primary", use_container_width=True):
                if username and password:
                    success, message = authenticate_user(db_manager, username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("✅ ログインしました！")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ ユーザー名とパスワードを入力してください")
        
        with col2:
            st.markdown("**💡 クイックアクセス**")
            st.markdown("デフォルトユーザー情報が\n自動入力されています")
            
            if st.button("🎯 即座ログイン", use_container_width=True):
                success, message = authenticate_user(db_manager, "admin", "picocela2024")
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = "admin"
                    st.success("✅ ログインしました！")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with tab2:
        st.subheader("👤 新規ユーザー登録")
        
        new_username = st.text_input("新しいユーザー名", placeholder="例: yamada")
        new_password = st.text_input("新しいパスワード", type="password", placeholder="6文字以上")
        new_email = st.text_input("メールアドレス", placeholder="例: yamada@picocela.com")
        
        if st.button("📝 ユーザー登録", type="primary"):
            if new_username and new_password and new_email:
                if len(new_password) >= 6:
                    success, message = create_user(db_manager, new_username, new_password, new_email)
                    if success:
                        st.success(f"✅ {message} ログインしてください。")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ パスワードは6文字以上で入力してください")
            else:
                st.warning("⚠️ すべての項目を入力してください")

def show_dashboard(company_manager):
    """ダッシュボード（ENR分析強化）"""
    st.header("📊 ダッシュボード")
    
    # 基本統計
    all_companies = company_manager.get_companies_by_status()
    total_companies = len(all_companies)
    
    if total_companies == 0:
        st.info("📋 企業データがありません。「データインポート」から企業情報を追加してください。")
        
        # クイックスタートボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 サンプルデータを追加", type="primary"):
                # サンプルデータ追加
                sample_companies = [
                    {
                        'company_name': 'テストコンストラクション株式会社',
                        'email': 'contact@test-construction.com',
                        'industry': 'Construction',
                        'notes': 'WiFi, IoT, wireless network solutions needed',
                        'source': 'Sample Data'
                    },
                    {
                        'company_name': 'スマートビルディング合同会社',
                        'email': 'info@smart-building.co.jp',
                        'industry': 'Smart Building',
                        'notes': 'mesh network, construction tech, digital solutions',
                        'source': 'Sample Data'
                    }
                ]
                
                for company in sample_companies:
                    company_manager.add_company(company, st.session_state.username)
                
                st.success("✅ サンプルデータを追加しました！")
                st.rerun()
        
        with col2:
            st.markdown("**📁 または**")
            st.markdown("「データインポート」から\nENRファイルをアップロード")
        
        return
    
    wifi_companies = len(all_companies[all_companies['wifi_required'] == 1])
    high_priority = len(all_companies[all_companies['priority_score'] >= 100])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", total_companies)
    
    with col2:
        st.metric("📶 WiFi必要企業", wifi_companies, 
                 f"{wifi_companies/total_companies*100:.1f}%" if total_companies > 0 else "0%")
    
    with col3:
        st.metric("🎯 高優先度企業", high_priority,
                 f"{high_priority/total_companies*100:.1f}%" if total_companies > 0 else "0%")
    
    with col4:
        engaged_plus = len(all_companies[all_companies['status'].isin(['Engaged', 'Qualified', 'Proposal', 'Negotiation'])])
        st.metric("🔥 商談中企業", engaged_plus)
    
    # ステータス分析
    status_analytics, wifi_analytics = company_manager.get_status_analytics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 ステータス別分布")
        if not status_analytics.empty:
            fig = px.pie(status_analytics, values='count', names='status',
                        title="企業ステータス分布")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📶 WiFi需要分析")
        if not wifi_analytics.empty:
            wifi_labels = ['WiFi不要', 'WiFi必要']
            fig = px.bar(x=wifi_labels, y=wifi_analytics['count'],
                        title="WiFi需要別企業数")
            st.plotly_chart(fig, use_container_width=True)
    
    # 優先アクション企業
    st.subheader("🎯 優先アクション企業（上位10社）")
    priority_companies = all_companies.nlargest(10, 'priority_score')[
        ['company_name', 'status', 'priority_score', 'wifi_required', 'picocela_relevance_score']
    ]
    st.dataframe(priority_companies, use_container_width=True)

def show_company_management(company_manager):
    """企業管理（拡張ステータス対応）"""
    st.header("🏢 企業管理")
    
    # フィルター
    col1, col2, col3 = st.columns(3)
    
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
    
    with col3:
        sort_option = st.selectbox(
            "ソート順",
            ["優先度順", "更新日順", "関連度順", "企業名順"]
        )
    
    # データ取得
    if status_filter == "すべて":
        companies_df = company_manager.get_companies_by_status()
    else:
        companies_df = company_manager.get_companies_by_status(status_filter)
    
    # WiFiフィルター適用
    if wifi_filter == "WiFi必要":
        companies_df = companies_df[companies_df['wifi_required'] == 1]
    elif wifi_filter == "WiFi不要":
        companies_df = companies_df[companies_df['wifi_required'] == 0]
    
    # 企業リスト表示
    if not companies_df.empty:
        st.subheader(f"📋 企業一覧 ({len(companies_df)}社)")
        
        for idx, company in companies_df.iterrows():
            with st.expander(
                f"🏢 {company['company_name']} | "
                f"📊 {SALES_STATUS.get(company['status'], company['status'])} | "
                f"🎯 優先度: {company['priority_score']}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**📧 Email**: {company['email'] or 'N/A'}")
                    st.write(f"**📞 電話**: {company['phone'] or 'N/A'}")
                    st.write(f"**🌐 Website**: {company['website_url'] or 'N/A'}")
                    st.write(f"**🏭 業界**: {company['industry'] or 'N/A'}")
                
                with col2:
                    st.write(f"**📶 WiFi需要**: {'🟢 あり' if company['wifi_required'] else '⚪ なし'}")
                    st.write(f"**⭐ 関連度**: {company['picocela_relevance_score']}/100")
                    st.write(f"**🎯 優先度**: {company['priority_score']}/150")
                    st.write(f"**📅 更新日**: {company['updated_at']}")
                
                # ステータス更新
                new_status = st.selectbox(
                    "ステータス変更",
                    list(SALES_STATUS.keys()),
                    index=list(SALES_STATUS.keys()).index(company['status']),
                    key=f"status_{company['id']}"
                )
                
                reason = st.text_input(
                    "変更理由",
                    key=f"reason_{company['id']}"
                )
                
                if st.button(f"ステータス更新", key=f"update_{company['id']}"):
                    if new_status != company['status']:
                        company_manager.update_status(
                            company['id'], 
                            new_status, 
                            st.session_state.username,
                            reason
                        )
                        st.success(f"ステータスを {SALES_STATUS[new_status]} に更新しました")
                        st.rerun()
    else:
        st.info("条件に一致する企業がありません。")

def show_email_campaigns(email_manager, company_manager):
    """メールキャンペーン（Streamlit Cloud対応）"""
    st.header("📧 メールキャンペーン")
    
    if not email_manager.email_available:
        st.warning("📧 Streamlit Cloud環境ではメール送信機能が制限されています")
        st.info("💡 代替案：メールアドレスリストをダウンロードして、Gmailで一括送信してください")
    
    tab1, tab2 = st.tabs(["🎯 戦略的配信", "📊 配信履歴"])
    
    with tab1:
        st.subheader("🎯 ターゲット企業選定")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_status = st.selectbox(
                "対象ステータス",
                list(SALES_STATUS.keys()),
                index=0
            )
        
        with col2:
            wifi_required = st.selectbox(
                "WiFi需要",
                ["すべて", "WiFi必要のみ", "WiFi不要のみ"]
            )
        
        with col3:
            min_relevance = st.slider(
                "最小関連度スコア",
                0, 100, 50
            )
        
        # ターゲット企業取得
        wifi_filter = None
        if wifi_required == "WiFi必要のみ":
            wifi_filter = True
        elif wifi_required == "WiFi不要のみ":
            wifi_filter = False
        
        targets = email_manager.get_campaign_targets(
            target_status, wifi_filter, min_relevance
        )
        
        st.write(f"📊 対象企業数: **{len(targets)}社**")
        
        if not targets.empty:
            st.dataframe(
                targets[['company_name', 'email', 'priority_score', 'wifi_required']],
                use_container_width=True
            )
            
            # CSVダウンロード
            csv = targets[['company_name', 'email', 'priority_score', 'wifi_required']].to_csv(index=False)
            st.download_button(
                label="📁 ターゲットリストをダウンロード",
                data=csv,
                file_name=f"campaign_targets_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.subheader("📊 配信履歴・効果分析")
        st.info("配信履歴機能は実装予定です。")

def show_analytics(company_manager):
    """分析・レポート"""
    st.header("📈 分析・レポート")
    
    all_companies = company_manager.get_companies_by_status()
    
    if all_companies.empty:
        st.warning("分析するデータがありません。")
        return
    
    # ENR戦略分析
    st.subheader("🎯 ENR戦略分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # WiFi vs 関連度相関
        fig = px.scatter(
            all_companies,
            x='picocela_relevance_score',
            y='priority_score',
            color='wifi_required',
            size='priority_score',
            title="WiFi需要 vs PicoCELA関連度",
            labels={
                'picocela_relevance_score': 'PicoCELA関連度',
                'priority_score': '優先度スコア'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ステータス別平均関連度
        status_relevance = all_companies.groupby('status')['picocela_relevance_score'].mean().reset_index()
        fig = px.bar(
            status_relevance,
            x='status',
            y='picocela_relevance_score',
            title="ステータス別平均関連度"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_settings():
    """設定"""
    st.header("⚙️ 設定")
    
    tab1, tab2 = st.tabs(["📧 メール設定", "🎯 ステータス管理"])
    
    with tab1:
        st.subheader("📧 メール設定")
        if EMAIL_AVAILABLE:
            st.info("メール機能は利用可能ですが、設定はローカル版で行ってください。")
        else:
            st.warning("Streamlit Cloud環境ではメール機能は制限されています。")
            st.info("💡 代替案：CSVダウンロード機能を活用してください。")
    
    with tab2:
        st.subheader("🎯 ステータス管理")
        st.write("**現在の営業ステータス:**")
        
        for status_code, status_name in SALES_STATUS.items():
            priority = STATUS_PRIORITY.get(status_code, 0)
            st.write(f"• **{status_code}**: {status_name} (優先度: {priority})")

def show_data_import(company_manager):
    """データインポート（ENR対応）"""
    st.header("📁 データインポート")
    
    st.subheader("📊 ENRデータインポート")
    st.info("💡 ENR_Companies_Complete_Local.xlsx または任意のCSV/Excelファイルをアップロードできます")
    
    uploaded_file = st.file_uploader(
        "ファイルをアップロード",
        type=['xlsx', 'csv'],
        help="企業データファイルを選択してください"
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            st.write(f"📊 読み込みデータ: {len(df)}行")
            st.dataframe(df.head(), use_container_width=True)
            
            # カラムマッピング
            st.subheader("📋 カラムマッピング")
            col1, col2 = st.columns(2)
            
            with col1:
                name_col = st.selectbox("企業名", df.columns, index=0)
                email_col = st.selectbox("メールアドレス", ['None'] + list(df.columns), index=1 if len(df.columns) > 1 else 0)
                
            with col2:
                url_col = st.selectbox("ウェブサイト", ['None'] + list(df.columns), index=2 if len(df.columns) > 2 else 0)
                industry_col = st.selectbox("業界", ['None'] + list(df.columns), index=3 if len(df.columns) > 3 else 0)
            
            if st.button("🚀 インポート実行"):
                progress_bar = st.progress(0)
                success_count = 0
                
                for idx, row in df.iterrows():
                    try:
                        company_data = {
                            'company_name': str(row[name_col]) if pd.notna(row[name_col]) else f"Company_{idx}",
                            'email': str(row[email_col]) if email_col != 'None' and pd.notna(row[email_col]) else '',
                            'website_url': str(row[url_col]) if url_col != 'None' and pd.notna(row[url_col]) else '',
                            'industry': str(row[industry_col]) if industry_col != 'None' and pd.notna(row[industry_col]) else 'Construction',
                            'source': f'{uploaded_file.name} Import',
                            'notes': f"インポート日: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                        
                        company_manager.add_company(company_data, st.session_state.username)
                        success_count += 1
                        
                    except Exception as e:
                        st.error(f"行 {idx+1} でエラー: {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(df))
                
                st.success(f"✅ {success_count}社のインポートが完了しました！")
                st.balloons()
                
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {str(e)}")

if __name__ == "__main__":
    main()
