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

# メール関連のimport（Streamlit Cloud対応強化版）
EMAIL_AVAILABLE = True
EMAIL_ERROR_MESSAGE = ""

try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    import ssl
    
    # メール送信テスト関数
    def test_email_functionality():
        """メール機能のテスト"""
        try:
            # 基本的なMIMEオブジェクト作成テスト
            msg = MimeMultipart()
            msg['Subject'] = "Test"
            return True, "メール機能は利用可能です"
        except Exception as e:
            return False, f"メール機能エラー: {str(e)}"
    
    email_test_result, email_test_message = test_email_functionality()
    if not email_test_result:
        EMAIL_AVAILABLE = False
        EMAIL_ERROR_MESSAGE = email_test_message
        
except ImportError as e:
    EMAIL_AVAILABLE = False
    EMAIL_ERROR_MESSAGE = f"メールライブラリのインポートエラー: {str(e)}"
except Exception as e:
    EMAIL_AVAILABLE = False
    EMAIL_ERROR_MESSAGE = f"メール機能初期化エラー: {str(e)}"

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
    salt = "picocela_fusion_crm_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password, hashed):
    """パスワード検証"""
    return hash_password(password) == hashed

class DatabaseManager:
    """データベース管理クラス（Streamlit Cloud互換性強化版）"""
    
    def __init__(self, db_name="fusion_crm.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_table_columns(self, table_name):
        """テーブルのカラム一覧を取得"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            return columns
        except:
            return []
    
    def safe_add_column(self, table_name, column_name, column_definition):
        """カラムを安全に追加"""
        try:
            existing_columns = self.get_table_columns(table_name)
            if column_name not in existing_columns:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}')
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            st.error(f"カラム追加エラー ({table_name}.{column_name}): {str(e)}")
            return False
        return False
    
    def rebuild_companies_table_if_needed(self):
        """企業テーブルの再構築（必要に応じて）"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # 既存データのバックアップ
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies'")
            if cursor.fetchone():
                try:
                    # 既存データを取得
                    cursor.execute("SELECT * FROM companies")
                    existing_data = cursor.fetchall()
                    
                    # 既存のカラム名を取得
                    cursor.execute("PRAGMA table_info(companies)")
                    old_columns = [row[1] for row in cursor.fetchall()]
                    
                    # 新しいテーブル作成
                    cursor.execute("DROP TABLE IF EXISTS companies_backup")
                    cursor.execute("ALTER TABLE companies RENAME TO companies_backup")
                    
                    # 完全なスキーマで新テーブル作成
                    self.create_companies_table_full_schema(cursor)
                    
                    # データ移行（カラムが存在するもののみ）
                    if existing_data:
                        self.migrate_company_data(cursor, existing_data, old_columns)
                    
                    # バックアップテーブル削除
                    cursor.execute("DROP TABLE IF EXISTS companies_backup")
                    
                except Exception as e:
                    st.warning(f"データ移行中にエラー: {str(e)} - 新しいテーブルを作成します")
                    cursor.execute("DROP TABLE IF EXISTS companies")
                    self.create_companies_table_full_schema(cursor)
            else:
                # テーブルが存在しない場合は新規作成
                self.create_companies_table_full_schema(cursor)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"テーブル再構築エラー: {str(e)}")
            return False
    
    def create_companies_table_full_schema(self, cursor):
        """完全なスキーマで企業テーブルを作成"""
        cursor.execute('''
            CREATE TABLE companies (
                id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                website_url TEXT DEFAULT '',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                address TEXT DEFAULT '',
                industry TEXT DEFAULT '',
                employees_count TEXT DEFAULT '',
                revenue_range TEXT DEFAULT '',
                status TEXT DEFAULT 'New',
                picocela_relevance_score INTEGER DEFAULT 0,
                keywords_matched TEXT DEFAULT '',
                wifi_required INTEGER DEFAULT 0,
                priority_score INTEGER DEFAULT 0,
                source TEXT DEFAULT 'Manual',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact_date TIMESTAMP,
                next_action TEXT DEFAULT '',
                next_action_date TIMESTAMP
            )
        ''')
    
    def migrate_company_data(self, cursor, old_data, old_columns):
        """既存データを新しいテーブルに移行"""
        # 基本的なカラムマッピング
        basic_columns = ['id', 'company_name', 'website_url', 'email', 'phone', 
                        'address', 'industry', 'employees_count', 'revenue_range', 'status']
        
        for row in old_data:
            try:
                # 基本データの準備
                company_data = {}
                for i, col in enumerate(old_columns):
                    if i < len(row) and col in basic_columns:
                        company_data[col] = row[i] if row[i] is not None else ''
                
                # デフォルト値設定
                company_data.setdefault('company_name', 'Unknown Company')
                company_data.setdefault('status', 'New')
                company_data.setdefault('wifi_required', 0)
                company_data.setdefault('priority_score', 0)
                company_data.setdefault('picocela_relevance_score', 0)
                company_data.setdefault('source', 'Migrated')
                
                # データ挿入
                placeholders = ', '.join(['?' for _ in range(len(company_data))])
                columns = ', '.join(company_data.keys())
                values = list(company_data.values())
                
                cursor.execute(f'''
                    INSERT INTO companies ({columns})
                    VALUES ({placeholders})
                ''', values)
                
            except Exception as e:
                st.warning(f"データ行の移行エラー: {str(e)}")
                continue
    
    def init_database(self):
        """データベース初期化（Streamlit Cloud最適化版）"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # ユーザーテーブル（シンプル版）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT DEFAULT '',
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # ステータス履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY,
                company_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                changed_by TEXT,
                change_reason TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # メール送信履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY,
                company_id INTEGER,
                template_name TEXT DEFAULT '',
                subject TEXT DEFAULT '',
                body TEXT DEFAULT '',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT '',
                error_message TEXT DEFAULT ''
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 企業テーブルの安全な再構築
        self.rebuild_companies_table_if_needed()

class ENRDataProcessor:
    """ENRデータ処理クラス"""
    
    @staticmethod
    def calculate_picocela_relevance(company_data):
        """PicoCELA関連度スコア計算"""
        score = 0
        text_fields = [
            str(company_data.get('company_name', '')),
            str(company_data.get('website_url', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for keyword in PICOCELA_KEYWORDS:
            if keyword.lower() in full_text:
                score += 10
        
        return min(score, 100)
    
    @staticmethod
    def detect_wifi_requirement(company_data):
        """WiFi需要判定"""
        wifi_indicators = [
            'wifi', 'wireless', 'network', 'connectivity', 
            'iot', 'smart building', 'construction tech'
        ]
        
        text_fields = [
            str(company_data.get('company_name', '')),
            str(company_data.get('notes', '')),
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
            priority += 50
        
        return min(priority, 150)

class CompanyManager:
    """企業管理クラス（エラー対応強化版）"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def add_company(self, company_data, user_id="system"):
        """企業追加（エラーハンドリング強化版）"""
        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            
            # 必須フィールドの設定
            company_name = str(company_data.get('company_name', 'Unknown Company'))
            website_url = str(company_data.get('website_url', ''))
            email = str(company_data.get('email', ''))
            phone = str(company_data.get('phone', ''))
            address = str(company_data.get('address', ''))
            industry = str(company_data.get('industry', ''))
            source = str(company_data.get('source', 'Manual'))
            notes = str(company_data.get('notes', ''))
            
            # PicoCELA関連度とWiFi需要を自動計算
            relevance_score = ENRDataProcessor.calculate_picocela_relevance(company_data)
            wifi_required = 1 if ENRDataProcessor.detect_wifi_requirement(company_data) else 0
            priority_score = ENRDataProcessor.calculate_priority_score(company_data)
            
            cursor.execute('''
                INSERT INTO companies (
                    company_name, website_url, email, phone, address, 
                    industry, status, picocela_relevance_score, wifi_required, 
                    priority_score, source, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_name, website_url, email, phone, address,
                industry, 'New', relevance_score, wifi_required,
                priority_score, source, notes
            ))
            
            company_id = cursor.lastrowid
            
            # ステータス履歴記録
            cursor.execute('''
                INSERT INTO status_history (
                    company_id, old_status, new_status, changed_by, change_reason
                ) VALUES (?, ?, ?, ?, ?)
            ''', (company_id, None, 'New', user_id, "企業登録"))
            
            conn.commit()
            conn.close()
            return company_id
            
        except Exception as e:
            st.error(f"企業追加エラー: {str(e)}")
            return None
    
    def update_status(self, company_id, new_status, user_id, reason="", notes=""):
        """ステータス更新（エラーハンドリング強化版）"""
        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            
            # 現在のステータス取得
            cursor.execute('SELECT status FROM companies WHERE id = ?', (company_id,))
            result = cursor.fetchone()
            old_status = result[0] if result else None
            
            # ステータス更新
            cursor.execute('''
                UPDATE companies 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, company_id))
            
            # 履歴記録
            cursor.execute('''
                INSERT INTO status_history (
                    company_id, old_status, new_status, changed_by, change_reason, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (company_id, old_status, new_status, user_id, reason, notes))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"ステータス更新エラー: {str(e)}")
            return False
    
    def get_companies_by_status(self, status=None, wifi_required=None):
        """ステータス別企業取得（エラーハンドリング強化版）"""
        try:
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
            
            # NaN値を適切なデフォルト値に置換
            df = df.fillna({
                'website_url': '',
                'email': '',
                'phone': '',
                'address': '',
                'industry': '',
                'notes': '',
                'wifi_required': 0,
                'priority_score': 0,
                'picocela_relevance_score': 0
            })
            
            return df
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return pd.DataFrame()
    
    def get_status_analytics(self):
        """ステータス分析データ取得（エラーハンドリング強化版）"""
        try:
            conn = sqlite3.connect(self.db.db_name)
            
            # ステータス別企業数
            status_df = pd.read_sql_query('''
                SELECT 
                    status, 
                    COUNT(*) as count, 
                    AVG(COALESCE(picocela_relevance_score, 0)) as avg_relevance,
                    SUM(COALESCE(wifi_required, 0)) as wifi_count
                FROM companies 
                GROUP BY status
            ''', conn)
            
            # WiFi需要企業の分析
            wifi_df = pd.read_sql_query('''
                SELECT 
                    COALESCE(wifi_required, 0) as wifi_required, 
                    COUNT(*) as count,
                    AVG(COALESCE(picocela_relevance_score, 0)) as avg_relevance
                FROM companies 
                GROUP BY wifi_required
            ''', conn)
            
            conn.close()
            return status_df, wifi_df
            
        except Exception as e:
            st.error(f"分析データ取得エラー: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

class EmailCampaignManager:
    """メールキャンペーン管理（完全機能版）"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.email_available = EMAIL_AVAILABLE
        self.smtp_settings = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True
        }
    
    def send_single_email(self, to_email, subject, body, from_email, from_password, from_name="PicoCELA Inc."):
        """単一メール送信"""
        if not self.email_available:
            return False, f"メール機能が利用できません: {EMAIL_ERROR_MESSAGE}"
        
        try:
            # メッセージ作成
            msg = MimeMultipart()
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 本文追加
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            # SMTP接続・送信
            with smtplib.SMTP(self.smtp_settings['smtp_server'], self.smtp_settings['smtp_port']) as server:
                if self.smtp_settings['use_tls']:
                    server.starttls()
                server.login(from_email, from_password)
                server.send_message(msg)
            
            return True, "メール送信成功"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Gmail認証エラー：アプリパスワードを確認してください"
        except smtplib.SMTPRecipientsRefused:
            return False, f"受信者エラー：{to_email} は無効なアドレスです"
        except smtplib.SMTPServerDisconnected:
            return False, "SMTP接続エラー：ネットワーク接続を確認してください"
        except Exception as e:
            return False, f"メール送信エラー: {str(e)}"
    
    def send_bulk_email(self, targets_df, subject, body_template, from_email, from_password, from_name="PicoCELA Inc."):
        """一括メール送信"""
        if not self.email_available:
            return [], f"メール機能が利用できません: {EMAIL_ERROR_MESSAGE}"
        
        results = []
        success_count = 0
        error_count = 0
        
        for idx, target in targets_df.iterrows():
            try:
                # 会社名を本文に挿入
                personalized_body = body_template.replace('{company_name}', str(target.get('company_name', '御社')))
                
                # メール送信
                success, message = self.send_single_email(
                    target['email'], subject, personalized_body, 
                    from_email, from_password, from_name
                )
                
                if success:
                    success_count += 1
                    status = "送信成功"
                else:
                    error_count += 1
                    status = f"送信失敗: {message}"
                
                results.append({
                    'company_name': target['company_name'],
                    'email': target['email'],
                    'status': status,
                    'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # 送信履歴をデータベースに記録
                self.log_email_send(target.get('id'), subject, personalized_body, status)
                
                # 送信間隔（Gmail制限対応）
                time.sleep(2)
                
            except Exception as e:
                error_count += 1
                error_message = f"処理エラー: {str(e)}"
                results.append({
                    'company_name': target.get('company_name', 'Unknown'),
                    'email': target.get('email', 'Unknown'),
                    'status': error_message,
                    'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        summary = f"送信完了: 成功 {success_count}件, 失敗 {error_count}件"
        return results, summary
    
    def log_email_send(self, company_id, subject, body, status):
        """メール送信履歴記録"""
        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO email_history (
                    company_id, subject, body, status, sent_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (company_id, subject, body, status))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.warning(f"送信履歴記録エラー: {str(e)}")
    
    def get_email_templates(self):
        """メールテンプレート取得"""
        return {
            "wifi_needed": {
                "subject": "建設現場のワイヤレス通信課題解決のご提案 - PicoCELA",
                "body": """{company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

建設現場でのワイヤレス通信にお困りではありませんか？

弊社のメッシュネットワーク技術により、以下のメリットを提供いたします：

• 既存インフラに依存しない独立ネットワーク構築
• IoTセンサー・モニタリング機器との安定した連携
• 現場安全性向上・リアルタイム状況把握
• 通信エリアの柔軟な拡張・移設対応

建設業界での豊富な導入実績がございます。
詳細な資料をお送りいたしますので、15分程度お時間をいただけますでしょうか。

何かご質問がございましたら、お気軽にお声かけください。

株式会社PicoCELA
営業部"""
            },
            "general": {
                "subject": "PicoCELA メッシュネットワークソリューションのご案内",
                "body": """{company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

弊社は建設・産業分野向けのワイヤレス通信ソリューションを提供しております。

【PicoCELAの特徴】
• メッシュネットワーク技術による安定通信
• 厳しい環境での高い耐久性
• 簡単設置・運用コスト削減
• 24時間サポート体制

貴社の事業にお役立ていただけるソリューションがあるかもしれません。
ぜひ一度お話をお聞かせください。

株式会社PicoCELA
営業部"""
            },
            "follow_up": {
                "subject": "PicoCELAソリューション - フォローアップのご連絡",
                "body": """{company_name} 様

いつもお世話になっております。
株式会社PicoCELAです。

先日ご案内させていただきました、メッシュネットワークソリューションの件はいかがでしょうか。

ご検討状況をお聞かせいただければ、より具体的なご提案をさせていただくことも可能です。

引き続きどうぞよろしくお願いいたします。

株式会社PicoCELA
営業部"""
            }
        }
    
    def get_campaign_targets(self, target_status, wifi_required=None, min_relevance=0):
        """キャンペーンターゲット取得（エラーハンドリング強化版）"""
        try:
            conn = sqlite3.connect(self.db.db_name)
            
            query = '''
                SELECT * FROM companies 
                WHERE status = ? 
                  AND email IS NOT NULL 
                  AND email != ''
                  AND COALESCE(picocela_relevance_score, 0) >= ?
            '''
            params = [target_status, min_relevance]
            
            if wifi_required is not None:
                query += ' AND COALESCE(wifi_required, 0) = ?'
                params.append(wifi_required)
            
            query += ' ORDER BY COALESCE(priority_score, 0) DESC'
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df.fillna('')
            
        except Exception as e:
            st.error(f"ターゲット取得エラー: {str(e)}")
            return pd.DataFrame()

# 認証関数（安定版）
def authenticate_user(db_manager, username, password):
    """ユーザー認証（エラーハンドリング強化版）"""
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
    """ユーザー作成（エラーハンドリング強化版）"""
    try:
        conn = sqlite3.connect(db_manager.db_name)
        cursor = conn.cursor()
        
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
    """デフォルトユーザーの確保（強制作成版）"""
    try:
        conn = sqlite3.connect(db_manager.db_name)
        cursor = conn.cursor()
        
        # adminユーザーを削除（存在する場合）
        cursor.execute('DELETE FROM users WHERE username = ?', ("admin",))
        
        # デフォルトユーザー作成
        password_hash = hash_password("picocela2024")
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', ("admin", password_hash, "admin@picocela.com", "admin", 1))
        
        conn.commit()
        conn.close()
        return True, "認証システム準備完了"
        
    except Exception as e:
        return False, f"認証システムエラー: {str(e)}"

# Streamlitアプリメイン部分
def main():
    st.title("🚀 FusionCRM - PicoCELA営業管理システム")
    st.markdown("**ENR最適化・拡張ステータス対応版 (Streamlit Cloud)**")
    
    # 環境情報表示
    if EMAIL_AVAILABLE:
        st.success("📧 メール機能: 利用可能（Gmail SMTP対応）")
    else:
        st.error(f"⚠️ メール機能エラー: {EMAIL_ERROR_MESSAGE}")
        st.info("💡 Gmail設定を確認してください：アプリパスワードが必要です")
    
    # セッション状態初期化
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # データベース初期化
    with st.spinner("🔄 データベース初期化中..."):
        db_manager = DatabaseManager()
        
        # 認証システム準備
        success, message = ensure_default_user(db_manager)
        if not success:
            st.error(f"認証システムエラー: {message}")
            return
    
    company_manager = CompanyManager(db_manager)
    email_manager = EmailCampaignManager(db_manager)
    
    # 認証確認
    if not st.session_state.logged_in:
        show_login_page(db_manager)
        return
    
    # メインアプリ
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
    """ログインページ（簡潔版）"""
    st.markdown("## 🔐 FusionCRM ログイン")
    st.markdown("**PicoCELA営業管理システム - Streamlit Cloud版**")
    
    st.success("💡 **デフォルトログイン**: admin / picocela2024")
    
    tab1, tab2 = st.tabs(["🔑 ログイン", "👤 新規登録"])
    
    with tab1:
        username = st.text_input("ユーザー名", value="admin")
        password = st.text_input("パスワード", value="picocela2024", type="password")
        
        if st.button("🚀 ログイン", type="primary"):
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
    
    with tab2:
        new_username = st.text_input("新しいユーザー名")
        new_password = st.text_input("新しいパスワード", type="password")
        new_email = st.text_input("メールアドレス")
        
        if st.button("📝 ユーザー登録"):
            if new_username and new_password and new_email:
                if len(new_password) >= 6:
                    success, message = create_user(db_manager, new_username, new_password, new_email)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ パスワードは6文字以上で入力してください")
            else:
                st.warning("⚠️ すべての項目を入力してください")

def show_dashboard(company_manager):
    """ダッシュボード（エラー対応強化版）"""
    st.header("📊 ダッシュボード")
    
    # 基本統計
    all_companies = company_manager.get_companies_by_status()
    total_companies = len(all_companies)
    
    if total_companies == 0:
        st.info("📋 企業データがありません。サンプルデータを追加してテストしてください。")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 サンプルデータを追加", type="primary"):
                # サンプルデータ追加（エラーハンドリング強化）
                sample_companies = [
                    {
                        'company_name': 'テストコンストラクション株式会社',
                        'email': 'contact@test-construction.com',
                        'industry': 'Construction',
                        'notes': 'WiFi, IoT, wireless network solutions needed for construction sites',
                        'source': 'Sample Data'
                    },
                    {
                        'company_name': 'スマートビルディング合同会社',
                        'email': 'info@smart-building.co.jp',
                        'industry': 'Smart Building',
                        'notes': 'mesh network, construction tech, digital solutions, smart building management',
                        'source': 'Sample Data'
                    }
                ]
                
                success_count = 0
                for company in sample_companies:
                    result = company_manager.add_company(company, st.session_state.username)
                    if result:
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"✅ {success_count}社のサンプルデータを追加しました！")
                    st.rerun()
                else:
                    st.error("❌ サンプルデータの追加に失敗しました")
        
        with col2:
            st.markdown("**📁 または**")
            st.markdown("「データインポート」から\nENRファイルをアップロード")
        
        return
    
    # 統計計算（エラーハンドリング付き）
    try:
        wifi_companies = len(all_companies[all_companies['wifi_required'] == 1])
        high_priority = len(all_companies[all_companies['priority_score'] >= 100])
        engaged_plus = len(all_companies[all_companies['status'].isin(['Engaged', 'Qualified', 'Proposal', 'Negotiation'])])
    except:
        wifi_companies = 0
        high_priority = 0
        engaged_plus = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", total_companies)
    
    with col2:
        wifi_pct = f"{wifi_companies/total_companies*100:.1f}%" if total_companies > 0 else "0%"
        st.metric("📶 WiFi必要企業", wifi_companies, wifi_pct)
    
    with col3:
        high_pct = f"{high_priority/total_companies*100:.1f}%" if total_companies > 0 else "0%"
        st.metric("🎯 高優先度企業", high_priority, high_pct)
    
    with col4:
        st.metric("🔥 商談中企業", engaged_plus)
    
    # 分析グラフ（エラーハンドリング付き）
    try:
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
    except Exception as e:
        st.warning(f"グラフ表示エラー: {str(e)}")
    
    # 優先企業リスト
    if not all_companies.empty:
        st.subheader("🎯 優先アクション企業（上位10社）")
        try:
            priority_companies = all_companies.nlargest(10, 'priority_score')[
                ['company_name', 'status', 'priority_score', 'wifi_required', 'picocela_relevance_score']
            ]
            st.dataframe(priority_companies, use_container_width=True)
        except Exception as e:
            st.warning(f"優先企業リスト表示エラー: {str(e)}")

def show_company_management(company_manager):
    """企業管理"""
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
    if wifi_filter == "WiFi必要" and not companies_df.empty:
        companies_df = companies_df[companies_df['wifi_required'] == 1]
    elif wifi_filter == "WiFi不要" and not companies_df.empty:
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
                    wifi_status = '🟢 あり' if company['wifi_required'] else '⚪ なし'
                    st.write(f"**📶 WiFi需要**: {wifi_status}")
                    st.write(f"**⭐ 関連度**: {company['picocela_relevance_score']}/100")
                    st.write(f"**🎯 優先度**: {company['priority_score']}/150")
                    st.write(f"**📅 更新日**: {company.get('updated_at', 'N/A')}")
                
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
                        if company_manager.update_status(
                            company['id'], new_status, st.session_state.username, reason
                        ):
                            st.success(f"ステータスを {SALES_STATUS[new_status]} に更新しました")
                            st.rerun()
    else:
        st.info("条件に一致する企業がありません。")

def show_email_campaigns(email_manager, company_manager):
    """メールキャンペーン（完全機能版）"""
    st.header("📧 メールキャンペーン")
    
    # メール機能状態表示
    if EMAIL_AVAILABLE:
        st.success("✅ メール送信機能: 利用可能")
    else:
        st.error(f"❌ メール機能エラー: {EMAIL_ERROR_MESSAGE}")
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["🎯 戦略的配信", "📧 Gmail設定", "📊 配信履歴"])
    
    with tab1:
        st.subheader("🎯 ターゲット企業選定")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_status = st.selectbox("対象ステータス", list(SALES_STATUS.keys()))
        
        with col2:
            wifi_required = st.selectbox("WiFi需要", ["すべて", "WiFi必要のみ", "WiFi不要のみ"])
        
        with col3:
            min_relevance = st.slider("最小関連度スコア", 0, 100, 50)
        
        # ターゲット企業取得
        wifi_filter = None
        if wifi_required == "WiFi必要のみ":
            wifi_filter = True
        elif wifi_required == "WiFi不要のみ":
            wifi_filter = False
        
        targets = email_manager.get_campaign_targets(target_status, wifi_filter, min_relevance)
        
        st.write(f"📊 対象企業数: **{len(targets)}社**")
        
        if not targets.empty:
            st.dataframe(targets[['company_name', 'email', 'priority_score', 'wifi_required']], use_container_width=True)
            
            # メールテンプレート選択
            st.subheader("📝 メールテンプレート")
            templates = email_manager.get_email_templates()
            
            template_names = {
                "wifi_needed": "🔌 WiFi必要企業向け",
                "general": "📋 一般企業向け", 
                "follow_up": "🔄 フォローアップ"
            }
            
            selected_template = st.selectbox(
                "テンプレート選択",
                options=list(template_names.keys()),
                format_func=lambda x: template_names[x]
            )
            
            template = templates[selected_template]
            
            # メール内容編集
            col1, col2 = st.columns(2)
            
            with col1:
                subject = st.text_input("件名", value=template["subject"])
            
            with col2:
                from_name = st.text_input("送信者名", value="PicoCELA Inc.")
            
            body = st.text_area(
                "本文（{company_name}は自動置換されます）", 
                value=template["body"], 
                height=300
            )
            
            # Gmail設定
            st.subheader("📧 Gmail送信設定")
            
            # セッション状態でGmail設定を保持
            if 'gmail_email' not in st.session_state:
                st.session_state.gmail_email = ""
            if 'gmail_password' not in st.session_state:
                st.session_state.gmail_password = ""
            
            col1, col2 = st.columns(2)
            
            with col1:
                gmail_email = st.text_input(
                    "Gmailアドレス", 
                    value=st.session_state.gmail_email,
                    placeholder="例: your-email@gmail.com"
                )
                st.session_state.gmail_email = gmail_email
            
            with col2:
                gmail_password = st.text_input(
                    "Gmailアプリパスワード", 
                    type="password",
                    value=st.session_state.gmail_password,
                    placeholder="16文字のアプリパスワード"
                )
                st.session_state.gmail_password = gmail_password
            
            st.info("💡 Gmailアプリパスワードの取得方法：Googleアカウント設定 → セキュリティ → 2段階認証 → アプリパスワード")
            
            # メール送信ボタン
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 テストメール送信", type="secondary"):
                    if gmail_email and gmail_password:
                        # 最初の企業にテストメール送信
                        if not targets.empty:
                            test_target = targets.iloc[0]
                            test_body = body.replace('{company_name}', test_target['company_name'])
                            
                            with st.spinner("テストメール送信中..."):
                                success, message = email_manager.send_single_email(
                                    test_target['email'], 
                                    f"[テスト] {subject}", 
                                    test_body, 
                                    gmail_email, 
                                    gmail_password,
                                    from_name
                                )
                            
                            if success:
                                st.success(f"✅ テストメール送信成功: {test_target['email']}")
                            else:
                                st.error(f"❌ テストメール送信失敗: {message}")
                    else:
                        st.warning("⚠️ Gmail設定を入力してください")
            
            with col2:
                # CSVダウンロード
                csv = targets[['company_name', 'email', 'priority_score', 'wifi_required']].to_csv(index=False)
                st.download_button(
                    label="📁 リストダウンロード",
                    data=csv,
                    file_name=f"campaign_targets_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            with col3:
                if st.button("🚀 一括メール送信", type="primary"):
                    if gmail_email and gmail_password:
                        if len(targets) > 0:
                            # 送信確認
                            if st.session_state.get('confirm_bulk_send', False):
                                with st.spinner(f"{len(targets)}社への一括メール送信中..."):
                                    results, summary = email_manager.send_bulk_email(
                                        targets, subject, body, gmail_email, gmail_password, from_name
                                    )
                                
                                st.success(f"📧 {summary}")
                                
                                # 送信結果表示
                                results_df = pd.DataFrame(results)
                                st.dataframe(results_df, use_container_width=True)
                                
                                # 送信確認状態をリセット
                                st.session_state.confirm_bulk_send = False
                            else:
                                st.warning(f"⚠️ {len(targets)}社に一括送信します。本当によろしいですか？")
                                if st.button("🔥 送信実行", type="primary"):
                                    st.session_state.confirm_bulk_send = True
                                    st.rerun()
                        else:
                            st.warning("⚠️ 送信対象企業がありません")
                    else:
                        st.warning("⚠️ Gmail設定を入力してください")
            
        else:
            st.info("📋 条件に一致する企業がありません")
    
    with tab2:
        st.subheader("📧 Gmail設定ガイド")
        
        st.markdown("""
        ### 🔧 Gmail SMTP設定手順
        
        1. **Googleアカウントにログイン**
        2. **Google アカウント設定** → **セキュリティ**
        3. **2段階認証を有効化**（未設定の場合）
        4. **アプリパスワード**を生成
        5. **生成された16文字のパスワード**をコピー
        6. **上記の「Gmail送信設定」に入力**
        
        ### ⚙️ 推奨設定
        - **送信者名**: PicoCELA Inc.
        - **送信間隔**: 2秒（Gmail制限対応）
        - **1日の送信上限**: 500通
        
        ### 🛡️ セキュリティ注意事項
        - アプリパスワードは他人に教えないでください
        - 定期的にパスワードを更新してください
        """)
        
        # Gmail設定テスト
        st.subheader("🧪 Gmail接続テスト")
        
        test_email = st.text_input("テスト用Gmailアドレス")
        test_password = st.text_input("テスト用アプリパスワード", type="password")
        
        if st.button("🔍 接続テスト"):
            if test_email and test_password:
                with st.spinner("Gmail接続テスト中..."):
                    success, message = email_manager.send_single_email(
                        test_email,  # 自分宛てに送信
                        "FusionCRM 接続テスト",
                        "FusionCRMからのテストメールです。この メールが届いた場合、Gmail設定は正常です。",
                        test_email,
                        test_password
                    )
                
                if success:
                    st.success("✅ Gmail接続成功！設定は正常です。")
                else:
                    st.error(f"❌ Gmail接続失敗: {message}")
            else:
                st.warning("⚠️ テスト用の情報を入力してください")
    
    with tab3:
        st.subheader("📊 配信履歴・効果分析")
        
        try:
            conn = sqlite3.connect(email_manager.db.db_name)
            
            # 送信履歴取得
            history_df = pd.read_sql_query('''
                SELECT 
                    eh.sent_at,
                    c.company_name,
                    eh.subject,
                    eh.status,
                    c.status as current_status
                FROM email_history eh
                LEFT JOIN companies c ON eh.company_id = c.id
                ORDER BY eh.sent_at DESC
                LIMIT 50
            ''', conn)
            
            conn.close()
            
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True)
                
                # 送信統計
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_sent = len(history_df)
                    st.metric("📧 総送信数", total_sent)
                
                with col2:
                    success_count = len(history_df[history_df['status'] == '送信成功'])
                    success_rate = f"{success_count/total_sent*100:.1f}%" if total_sent > 0 else "0%"
                    st.metric("✅ 送信成功率", success_rate)
                
                with col3:
                    recent_sends = len(history_df[history_df['sent_at'] >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')])
                    st.metric("📅 今週の送信", recent_sends)
            else:
                st.info("📋 送信履歴がありません")
                
        except Exception as e:
            st.error(f"履歴取得エラー: {str(e)}")

def show_analytics(company_manager):
    """分析・レポート"""
    st.header("📈 分析・レポート")
    
    all_companies = company_manager.get_companies_by_status()
    
    if all_companies.empty:
        st.warning("分析するデータがありません。")
        return
    
    st.subheader("🎯 ENR戦略分析")
    
    try:
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
    except Exception as e:
        st.warning(f"分析グラフ表示エラー: {str(e)}")

def show_settings():
    """設定"""
    st.header("⚙️ 設定")
    
    tab1, tab2 = st.tabs(["📧 メール設定", "🎯 ステータス管理"])
    
    with tab1:
        st.subheader("📧 メール設定")
        st.warning("Streamlit Cloud環境ではメール機能は制限されています。")
        st.info("💡 代替案：CSVダウンロード機能を活用してください。")
    
    with tab2:
        st.subheader("🎯 ステータス管理")
        st.write("**現在の営業ステータス:**")
        
        for status_code, status_name in SALES_STATUS.items():
            priority = STATUS_PRIORITY.get(status_code, 0)
            st.write(f"• **{status_code}**: {status_name} (優先度: {priority})")

def show_data_import(company_manager):
    """データインポート"""
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
                error_count = 0
                
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
                        
                        result = company_manager.add_company(company_data, st.session_state.username)
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:  # 最初の5つのエラーのみ表示
                            st.warning(f"行 {idx+1} でエラー: {str(e)}")
                    
                    progress_bar.progress((idx + 1) / len(df))
                
                st.success(f"✅ {success_count}社のインポートが完了しました！")
                if error_count > 0:
                    st.warning(f"⚠️ {error_count}社でエラーが発生しました")
                st.balloons()
                
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {str(e)}")

if __name__ == "__main__":
    main()
