#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Simple & Reliable Version
PicoCELA社専用統合CRMシステム（シンプル確実版）
SQLiteベース - クラウド展開対応
"""

import streamlit as st
import pandas as pd
import sqlite3
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
    .success-metric {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class DatabaseManager:
    """データベース管理クラス（シンプル版）"""
    
    def __init__(self, db_path="fusion_crm.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ユーザーテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 企業テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                email_address TEXT,
                website TEXT,
                phone TEXT,
                address TEXT,
                status TEXT DEFAULT 'New',
                priority INTEGER DEFAULT 0,
                last_contact_date TIMESTAMP,
                next_followup_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                picocela_relevance_score INTEGER DEFAULT 50,
                keywords_matched TEXT DEFAULT 'construction,network'
            )
        """)
        
        # メール履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY,
                company_id INTEGER,
                email_type TEXT,
                subject TEXT,
                content TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                error_message TEXT,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)
        
        # デフォルト管理者ユーザーの作成
        try:
            default_password_hash = hashlib.sha256("picocela2024".encode()).hexdigest()
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password_hash, email, role)
                VALUES ('admin', ?, 'tokuda@picocela.com', 'admin')
            """, (default_password_hash,))
        except:
            pass
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """データベース接続の取得"""
        return sqlite3.connect(self.db_path)

class EmailService:
    """メール配信サービス（シンプル版）"""
    
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
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # company_idの取得
            cursor.execute("SELECT id FROM companies WHERE company_name = ?", (company_name,))
            result = cursor.fetchone()
            company_id = result[0] if result else None
            
            # 履歴記録
            cursor.execute("""
                INSERT INTO email_history (company_id, email_type, subject, content, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (company_id, template_name, f"Campaign to {company_name}", f"Email sent to {email}", status, error_msg))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.warning(f"履歴記録エラー: {e}")
    
    def get_email_templates(self):
        """メールテンプレートの取得"""
        return {
            "initial_contact": {
                "subject": "【PicoCELA】メッシュネットワークソリューションのご案内",
                "body": """Dear {company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

建設現場でのワイヤレス通信にお困りではありませんか？

弊社のメッシュネットワーク技術により、以下のメリットを提供いたします：

• 建設現場での安定したワイヤレス通信
• 既存インフラに依存しない独立ネットワーク  
• IoTセンサー・モニタリング機器との連携
• 現場安全性向上・デジタル化推進

詳細な資料をお送りいたしますので、お時間をいただけますでしょうか。

何かご質問がございましたら、お気軽にお声がけください。

どうぞよろしくお願いいたします。

---
株式会社PicoCELA
営業部
Email: tokuda@picocela.com
Tel: [お電話番号]
Web: https://www.picocela.com"""
            },
            "follow_up": {
                "subject": "【PicoCELA】フォローアップ - メッシュネットワーク技術について",
                "body": """Dear {company_name} 様

先日はお忙しい中、お時間をいただき
ありがとうございました。

弊社のメッシュネットワークソリューションについて、
追加でご質問やご相談がございましたら、
お気軽にお声がけください。

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
    db_manager = DatabaseManager()
    email_service = EmailService(db_manager)
    return db_manager, email_service

db_manager, email_service = get_managers()

def hash_password(password):
    """パスワードのハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    """パスワードの確認"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def login_page():
    """ログインページ"""
    st.markdown('<div class="main-header"><h1>🚀 FusionCRM - PicoCELA統合CRMシステム</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 ログイン", "👥 ユーザー登録"])
        
        with tab1:
            st.subheader("ログイン")
            
            # デフォルトログイン情報表示
            st.info("🔑 デフォルトアカウント: admin / picocela2024")
            
            username = st.text_input("ユーザー名", value="admin")
            password = st.text_input("パスワード", type="password")
            
            if st.button("🚀 ログイン", type="primary", use_container_width=True):
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                conn.close()
                
                if result and check_password(password, result[0]):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = result[1]
                    st.success("✅ ログイン成功！")
                    st.rerun()
                else:
                    st.error("❌ ユーザー名またはパスワードが間違っています")
        
        with tab2:
            st.subheader("新規ユーザー登録")
            new_username = st.text_input("新しいユーザー名")
            new_email = st.text_input("メールアドレス", value="tokuda@picocela.com")
            new_password = st.text_input("新しいパスワード", type="password")
            
            if st.button("👥 登録", use_container_width=True):
                if len(new_password) < 6:
                    st.error("❌ パスワードは6文字以上で入力してください")
                else:
                    try:
                        conn = db_manager.get_connection()
                        cursor = conn.cursor()
                        
                        hashed_password = hash_password(new_password)
                        cursor.execute("""
                            INSERT INTO users (username, password_hash, email, role)
                            VALUES (?, ?, ?, ?)
                        """, (new_username, hashed_password, new_email, "admin"))
                        
                        conn.commit()
                        conn.close()
                        st.success("✅ ユーザー登録が完了しました！ログインしてください。")
                        
                    except sqlite3.IntegrityError:
                        st.error("❌ このユーザー名は既に使用されています")

def dashboard_page():
    """ダッシュボードページ"""
    st.markdown('<div class="main-header"><h1>📊 FusionCRM ダッシュボード</h1></div>', unsafe_allow_html=True)
    
    conn = db_manager.get_connection()
    
    # 基本統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_companies = pd.read_sql("SELECT COUNT(*) as count FROM companies", conn).iloc[0]['count']
        st.metric("📊 総企業数", total_companies)
    
    with col2:
        new_companies = pd.read_sql("SELECT COUNT(*) as count FROM companies WHERE status = 'New'", conn).iloc[0]['count']
        st.metric("🆕 新規企業", new_companies)
    
    with col3:
        contacted = pd.read_sql("SELECT COUNT(*) as count FROM companies WHERE status = 'Contacted'", conn).iloc[0]['count']
        st.metric("📞 連絡済み", contacted)
    
    with col4:
        email_available = pd.read_sql("SELECT COUNT(*) as count FROM companies WHERE email_address IS NOT NULL AND email_address != ''", conn).iloc[0]['count']
        st.metric("📧 メール配信可能", email_available)
    
    # 今日の活動状況
    st.subheader("📈 本日の活動状況")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        today_emails = pd.read_sql("SELECT COUNT(*) as count FROM email_history WHERE DATE(sent_at) = DATE('now')", conn).iloc[0]['count']
        st.metric("📧 本日送信", today_emails)
    
    with col2:
        success_emails = pd.read_sql("SELECT COUNT(*) as count FROM email_history WHERE DATE(sent_at) = DATE('now') AND status = 'success'", conn).iloc[0]['count']
        success_rate = (success_emails / today_emails * 100) if today_emails > 0 else 0
        st.metric("✅ 成功率", f"{success_rate:.1f}%")
    
    with col3:
        high_priority = pd.read_sql("SELECT COUNT(*) as count FROM companies WHERE picocela_relevance_score >= 70", conn).iloc[0]['count']
        st.metric("🎯 高優先度企業", high_priority)
    
    # グラフ表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 企業ステータス分布")
        status_data = pd.read_sql("SELECT status, COUNT(*) as count FROM companies GROUP BY status", conn)
        
        if not status_data.empty:
            fig = px.pie(
                status_data, 
                values='count', 
                names='status', 
                title="企業ステータス分布",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 データがありません")
    
    with col2:
        st.subheader("📈 メール送信トレンド（過去7日）")
        email_trend = pd.read_sql("""
            SELECT DATE(sent_at) as date, COUNT(*) as count, status
            FROM email_history 
            WHERE sent_at >= DATE('now', '-7 days')
            GROUP BY DATE(sent_at), status
            ORDER BY date DESC
        """, conn)
        
        if not email_trend.empty:
            fig = px.line(
                email_trend, 
                x='date', 
                y='count', 
                color='status',
                title="過去7日のメール送信状況",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 メール送信履歴がありません")
    
    # 最近のメール配信履歴
    st.subheader("📧 最近のメール配信履歴")
    recent_emails = pd.read_sql("""
        SELECT 
            datetime(eh.sent_at, 'localtime') as 送信時刻,
            c.company_name as 企業名,
            eh.status as ステータス,
            eh.email_type as テンプレート
        FROM email_history eh
        LEFT JOIN companies c ON eh.company_id = c.id
        ORDER BY eh.sent_at DESC
        LIMIT 10
    """, conn)
    
    if not recent_emails.empty:
        st.dataframe(recent_emails, use_container_width=True)
    else:
        st.info("📭 メール配信履歴がありません")
    
    conn.close()

def companies_page():
    """企業管理ページ"""
    st.title("🏢 企業管理")
    
    # フィルターセクション
    with st.expander("🔍 検索・フィルター", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("ステータスフィルター", ["すべて", "New", "Contacted", "Replied", "Qualified", "Lost"])
        
        with col2:
            search_term = st.text_input("🔍 企業名検索")
        
        with col3:
            min_score = st.slider("最小関連度スコア", 0, 100, 0)
    
    # データ取得
    conn = db_manager.get_connection()
    
    query = """
        SELECT 
            id, company_name, email_address, website, phone, 
            status, picocela_relevance_score, last_contact_date,
            created_at
        FROM companies WHERE 1=1
    """
    params = []
    
    if status_filter != "すべて":
        query += " AND status = ?"
        params.append(status_filter)
    
    if search_term:
        query += " AND company_name LIKE ?"
        params.append(f"%{search_term}%")
    
    if min_score > 0:
        query += " AND picocela_relevance_score >= ?"
        params.append(min_score)
    
    query += " ORDER BY picocela_relevance_score DESC, created_at DESC"
    
    companies_df = pd.read_sql(query, conn, params=params)
    
    if not companies_df.empty:
        st.write(f"📊 表示中: {len(companies_df)} 社")
        
        # データテーブル表示
        display_columns = ['company_name', 'email_address', 'status', 'picocela_relevance_score', 'last_contact_date']
        display_df = companies_df[display_columns].copy()
        display_df.columns = ['企業名', 'メールアドレス', 'ステータス', '関連度スコア', '最終連絡日']
        
        st.dataframe(display_df, use_container_width=True)
        
    else:
        st.warning("📭 条件に合致する企業が見つかりません")
    
    # データインポートセクション
    st.subheader("📥 データインポート")
    uploaded_file = st.file_uploader(
        "企業データファイル (Excel/CSV)", 
        type=['xlsx', 'xls', 'csv'],
        help="company_name, email_address, website, phone の列を含むファイル"
    )
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                preview_df = pd.read_csv(uploaded_file)
            else:
                preview_df = pd.read_excel(uploaded_file)
            
            st.write("📊 プレビュー:")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            if st.button("📥 インポート実行", type="primary"):
                import_companies_data(uploaded_file)
        
        except Exception as e:
            st.error(f"❌ ファイル読み込みエラー: {e}")
    
    conn.close()

def import_companies_data(uploaded_file):
    """企業データのインポート"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 列名のマッピング
        column_mapping = {
            'Company Name': 'company_name',
            'company_name': 'company_name',
            'Company': 'company_name',
            'Email': 'email_address', 
            'email': 'email_address',
            'Email Address': 'email_address',
            'Website': 'website',
            'website': 'website',
            'URL': 'website',
            'Phone': 'phone',
            'phone': 'phone',
            'Tel': 'phone'
        }
        
        # 列名を標準化
        df_renamed = df.rename(columns=column_mapping)
        
        conn = db_manager.get_connection()
        imported = 0
        duplicates = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, row in df_renamed.iterrows():
            try:
                company_name = row.get('company_name', '').strip()
                if not company_name:
                    continue
                
                status_text.text(f"インポート中: {company_name} ({i+1}/{len(df_renamed)})")
                
                cursor = conn.cursor()
                
                # 重複チェック
                cursor.execute("SELECT COUNT(*) FROM companies WHERE company_name = ?", (company_name,))
                if cursor.fetchone()[0] > 0:
                    duplicates += 1
                    continue
                
                cursor.execute("""
                    INSERT INTO companies 
                    (company_name, email_address, website, phone, status, picocela_relevance_score, keywords_matched)
                    VALUES (?, ?, ?, ?, 'New', ?, 'construction,network')
                """, (
                    company_name,
                    row.get('email_address', '').strip(),
                    row.get('website', '').strip(),
                    row.get('phone', '').strip(),
                    random.randint(40, 80)
                ))
                imported += 1
                
            except Exception as e:
                st.warning(f"行のインポートエラー: {e}")
            
            progress_bar.progress((i + 1) / len(df_renamed))
        
        conn.commit()
        conn.close()
        
        # 結果表示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ インポート成功", imported)
        with col2:
            st.metric("🔄 重複スキップ", duplicates) 
        with col3:
            st.metric("📊 処理済み", len(df_renamed))
        
        if imported > 0:
            st.success(f"🎉 {imported}件の企業データをインポートしました！")
            st.rerun()
        
    except Exception as e:
        st.error(f"❌ インポートエラー: {e}")

def email_campaign_page():
    """メールキャンペーンページ"""
    st.title("📧 メールキャンペーン")
    
    # Gmail設定確認
    gmail_config = st.session_state.get('gmail_config')
    
    if not gmail_config:
        st.warning("⚠️ Gmail設定が必要です")
        setup_gmail_config()
        return
    
    # 設定情報表示
    st.success(f"✅ Gmail設定済み: {gmail_config['email']} | 送信者名: {gmail_config['sender_name']}")
    
    # キャンペーンタブ
    tab1, tab2, tab3 = st.tabs(["🚀 一括配信", "🧪 テスト送信", "📊 配信履歴"])
    
    with tab1:
        bulk_email_campaign()
    
    with tab2:
        test_email_send()
    
    with tab3:
        email_history_view()

def bulk_email_campaign():
    """一括メール配信"""
    st.subheader("🚀 一括メール配信")
    
    # 配信設定
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("配信対象ステータス", ["New", "Contacted", "Replied"], key="bulk_status")
    with col2:
        max_emails = st.number_input("最大配信数", min_value=1, max_value=100, value=20)
    with col3:
        min_score = st.slider("最小関連度スコア", 0, 100, 50)
    
    # 対象企業の取得と表示
    conn = db_manager.get_connection()
    target_companies = pd.read_sql("""
        SELECT id, company_name, email_address, picocela_relevance_score, website
        FROM companies 
        WHERE status = ? AND email_address IS NOT NULL AND email_address != ''
        AND picocela_relevance_score >= ?
        ORDER BY picocela_relevance_score DESC
        LIMIT ?
    """, conn, params=[status_filter, min_score, max_emails])
    
    if not target_companies.empty:
        st.markdown(f"### 📊 配信対象: {len(target_companies)}社")
        
        # 対象企業テーブル
        display_df = target_companies[['company_name', 'email_address', 'picocela_relevance_score']].copy()
        display_df.columns = ['企業名', 'メールアドレス', '関連度スコア']
        st.dataframe(display_df, use_container_width=True)
        
        # テンプレート選択
        templates = email_service.get_email_templates()
        template_name = st.selectbox("📝 メールテンプレート", list(templates.keys()))
        
        # プレビュー表示
        with st.expander("👀 メールプレビュー"):
            template = templates[template_name]
            sample_company = target_companies.iloc[0]['company_name']
            preview_body = template['body'].format(company_name=sample_company)
            
            st.write(f"**件名**: {template['subject']}")
            st.text_area("本文プレビュー", preview_body, height=200, disabled=True)
        
        # 配信確認と実行
        st.markdown("### 🚀 配信実行")
        
        col1, col2 = st.columns(2)
        with col1:
            confirm_send = st.checkbox(f"✅ {len(target_companies)}社への配信を実行する")
        with col2:
            delay_range = st.select_slider(
                "送信間隔（秒）", 
                options=[1, 3, 5, 8, 10], 
                value=5,
                help="送信間隔を設定（スパム防止）"
            )
        
        if confirm_send and st.button("📧 配信開始", type="primary", use_container_width=True):
            execute_bulk_campaign(target_companies, template_name, delay_range, conn)
    
    else:
        st.warning("📭 配信対象企業が見つかりません")
        st.info(f"条件: ステータス={status_filter}, 関連度スコア>={min_score}")
    
    conn.close()

def execute_bulk_campaign(target_companies, template_name, delay_range, conn):
    """バルクキャンペーンの実行"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_count = 0
    total = len(target_companies)
    
    results = []
    start_time = datetime.now()
    
    for i, row in target_companies.iterrows():
        company_name = row['company_name']
        email_address = row['email_address']
        
        status_text.text(f"📧 {company_name} に送信中... ({i+1}/{total})")
        
        success, message = email_service.send_email(email_address, company_name, template_name)
        
        if success:
            success_count += 1
            # ステータス更新
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE companies 
                SET status = 'Contacted', last_contact_date = ?, updated_at = ?
                WHERE id = ?
            """, (datetime.now(), datetime.now(), row['id']))
            conn.commit()
            
            results.append({
                'company': company_name,
                'status': '✅ 成功',
                'message': '送信完了'
            })
        else:
            failed_count += 1
            results.append({
                'company': company_name,
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
    status_text.text("✅ 配信完了")
    
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
    
    # 所要時間
    st.info(f"⏱️ 所要時間: {duration:.1f}秒 ({duration/60:.1f}分)")
    
    # 詳細結果
    with st.expander("📋 詳細結果"):
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)
    
    # 成功時のお祝いメッセージ
    if success_rate >= 90:
        st.balloons()
        st.success("🎉 素晴らしい成功率です！")

def test_email_send():
    """テストメール送信"""
    st.subheader("🧪 テストメール送信")
    
    conn = db_manager.get_connection()
    companies = pd.read_sql("""
        SELECT company_name, email_address, picocela_relevance_score
        FROM companies 
        WHERE email_address IS NOT NULL AND email_address != ''
        ORDER BY picocela_relevance_score DESC
        LIMIT 20
    """, conn)
    
    if not companies.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.selectbox("🏢 テスト対象企業", companies['company_name'].tolist())
        
        with col2:
            templates = email_service.get_email_templates()
            template_name = st.selectbox("📝 テンプレート", list(templates.keys()))
        
        selected_company = companies[companies['company_name'] == company_name].iloc[0]
        
        st.write(f"**📧 送信先**: {selected_company['email_address']}")
        st.write(f"**🎯 関連度スコア**: {selected_company['picocela_relevance_score']}")
        
        # プレビュー
        template = templates[template_name]
        preview_body = template['body'].format(company_name=company_name)
        
        with st.expander("👀 メールプレビュー"):
            st.write(f"**件名**: {template['subject']}")
            st.text_area("本文", preview_body, height=200, disabled=True)
        
        if st.button("🧪 テスト送信", type="primary"):
            with st.spinner("送信中..."):
                success, message = email_service.send_email(
                    selected_company['email_address'], 
                    company_name, 
                    template_name
                )
            
            if success:
                st.success(f"✅ テスト送信成功: {company_name}")
                st.info("📧 メール配信履歴に記録されました")
            else:
                st.error(f"❌ テスト送信失敗: {message}")
    
    else:
        st.warning("🔍 テスト対象企業が見つかりません")
        st.info("企業データをインポートしてください")
    
    conn.close()

def email_history_view():
    """メール配信履歴"""
    st.subheader("📊 メール配信履歴")
    
    conn = db_manager.get_connection()
    
    # フィルター
    col1, col2, col3 = st.columns(3)
    with col1:
        days_back = st.selectbox("期間", [7, 30, 90, 365], index=1)
    with col2:
        status_filter = st.selectbox("ステータス", ["すべて", "success", "failed"])
    with col3:
        limit = st.selectbox("表示件数", [25, 50, 100], index=1)
    
    # クエリ構築
    query = """
        SELECT 
            datetime(eh.sent_at, 'localtime') as 送信時刻,
            c.company_name as 企業名,
            eh.email_type as テンプレート,
            eh.subject as 件名,
            eh.status as ステータス,
            eh.error_message as エラーメッセージ
        FROM email_history eh
        LEFT JOIN companies c ON eh.company_id = c.id
        WHERE eh.sent_at >= datetime('now', '-{} days')
    """.format(days_back)
    
    if status_filter != "すべて":
        query += f" AND eh.status = '{status_filter}'"
    
    query += " ORDER BY eh.sent_at DESC LIMIT {}".format(limit)
    
    history = pd.read_sql(query, conn)
    
    if not history.empty:
        # 統計情報
        total_emails = len(history)
        success_emails = len(history[history['ステータス'] == 'success'])
        success_rate = (success_emails / total_emails * 100) if total_emails > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📧 総送信数", total_emails)
        with col2:
            st.metric("✅ 成功数", success_emails)
        with col3:
            st.metric("📈 成功率", f"{success_rate:.1f}%")
        
        # データテーブル
        st.dataframe(history, use_container_width=True)
        
    else:
        st.info("📭 指定期間の配信履歴がありません")
    
    conn.close()

def setup_gmail_config():
    """Gmail設定セットアップ"""
    st.subheader("📧 Gmail SMTP設定")
    
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
        st.markdown("### 🔧 Gmail設定")
        
        email = st.text_input(
            "📧 Gmailアドレス", 
            value=current_config.get('email', 'tokuda@picocela.com') if current_config else 'tokuda@picocela.com',
            help="PicoCELAの公式Gmailアドレス"
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
            help="メール受信者に表示される送信者名"
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
        with st.spinner("Gmail接続テスト中..."):
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email'], config['password'])
            server.quit()
        
        st.success("✅ Gmail接続テスト成功")
        st.balloons()
        
    except smtplib.SMTPAuthenticationError:
        st.error("❌ 認証エラー: メールアドレスまたはアプリパスワードが間違っています")
    except smtplib.SMTPException as e:
        st.error(f"❌ SMTP接続エラー: {e}")
    except Exception as e:
        st.error(f"❌ 接続テストエラー: {e}")

def settings_page():
    """設定ページ"""
    st.title("⚙️ システム設定")
    
    tab1, tab2 = st.tabs(["📧 Gmail設定", "🔧 システム"])
    
    with tab1:
        setup_gmail_config()
    
    with tab2:
        system_settings()

def system_settings():
    """システム設定"""
    st.subheader("🔧 システム設定")
    
    # データベース統計
    conn = db_manager.get_connection()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        company_count = pd.read_sql("SELECT COUNT(*) as count FROM companies", conn).iloc[0]['count']
        st.metric("🏢 企業データ", f"{company_count}件")
    
    with col2:
        email_count = pd.read_sql("SELECT COUNT(*) as count FROM email_history", conn).iloc[0]['count']
        st.metric("📧 メール履歴", f"{email_count}件")
    
    with col3:
        user_count = pd.read_sql("SELECT COUNT(*) as count FROM users", conn).iloc[0]['count']
        st.metric("👥 ユーザー数", f"{user_count}名")
    
    # システム情報
    st.subheader("ℹ️ システム情報")
    
    system_info = {
        "🐍 Python版": sys.version.split()[0],
        "📦 Streamlit版": st.__version__,
        "🗄️ データベース": "SQLite3",
        "📧 メール送信": "Gmail SMTP",
        "🌐 展開環境": "Streamlit Cloud対応"
    }
    
    for key, value in system_info.items():
        st.write(f"**{key}**: {value}")
    
    conn.close()

def main():
    """メインアプリケーション"""
    
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
        
        # ナビゲーション
        page = st.radio(
            "🧭 ページ選択",
            ["📊 ダッシュボード", "🏢 企業管理", "📧 メールキャンペーン", "⚙️ 設定"],
            key="navigation"
        )
        
        # クイック統計
        st.markdown("---")
        st.markdown("### 📈 クイック統計")
        
        try:
            conn = db_manager.get_connection()
            
            total_companies = pd.read_sql("SELECT COUNT(*) as count FROM companies", conn).iloc[0]['count']
            today_emails = pd.read_sql("SELECT COUNT(*) as count FROM email_history WHERE DATE(sent_at) = DATE('now')", conn).iloc[0]['count']
            
            st.metric("企業数", total_companies, delta=None)
            st.metric("今日の送信", today_emails, delta=None)
            
            conn.close()
        except:
            st.error("データベース接続エラー")
        
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
