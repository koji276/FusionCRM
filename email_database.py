"""
統合メールデータベース管理
企業データ、生成メール、送信履歴の管理機能
"""

import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime


class IntegratedEmailDatabase:
    """統合メールデータベース（日本語・英語対応）"""
    
    def __init__(self, db_path: str = "picocela_integrated_emails.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 企業データテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT UNIQUE,
                company_name TEXT,
                email TEXT,
                website TEXT,
                phone TEXT,
                description TEXT,
                industry TEXT,
                country TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # 統合メールテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrated_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT,
                company_name TEXT,
                language TEXT,
                subject TEXT,
                email_body TEXT,
                customization_data TEXT,
                api_cost REAL,
                tokens_used INTEGER,
                customization_method TEXT,
                template_type TEXT,
                generated_at TEXT,
                UNIQUE(company_name, language, template_type) ON CONFLICT REPLACE
            )
        """)
        
        # 送信履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrated_send_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT,
                company_name TEXT,
                recipient_email TEXT,
                language TEXT,
                subject TEXT,
                sent_at TEXT,
                status TEXT,
                smtp_response TEXT,
                template_type TEXT
            )
        """)
        
        # テンプレートテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE,
                language TEXT,
                subject_template TEXT,
                body_template TEXT,
                template_type TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # システム設定テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE,
                setting_value TEXT,
                setting_type TEXT,
                updated_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_company(self, company_data: Dict):
        """企業データを保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO companies 
            (company_id, company_name, email, website, phone, description, industry, country, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_data.get('company_id'),
            company_data.get('company_name'),
            company_data.get('email'),
            company_data.get('website'),
            company_data.get('phone'),
            company_data.get('description'),
            company_data.get('industry'),
            company_data.get('country', 'Unknown'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def save_generated_email(self, email_data: Dict):
        """生成メールをデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # カスタマイズデータをJSONで保存
        customization_data = {
            'partnership_environments': email_data.get('partnership_environments'),
            'partnership_value': email_data.get('partnership_value'),
            'suggested_title': email_data.get('suggested_title'),
            'custom_content': email_data.get('custom_content'),
            'industry_specific_benefits': email_data.get('industry_specific_benefits'),
            'call_to_action': email_data.get('call_to_action')
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO integrated_emails 
            (company_id, company_name, language, subject, email_body, customization_data,
             api_cost, tokens_used, customization_method, template_type, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_data.get('company_id'),
            email_data.get('company_name'),
            email_data.get('language', 'english'),
            email_data.get('subject'),
            email_data.get('customized_email') or email_data.get('email_content'),
            json.dumps(customization_data),
            email_data.get('api_cost'),
            email_data.get('tokens_used'),
            email_data.get('customization_method'),
            email_data.get('template_type', 'standard'),
            email_data.get('generated_at')
        ))
        
        conn.commit()
        conn.close()
    
    def get_generated_email(self, company_name: str, language: str = 'english', template_type: str = 'standard') -> Optional[Dict]:
        """生成済みメールを取得 - company_nameベース検索"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM integrated_emails 
            WHERE company_name = ? AND language = ? AND template_type = ?
        """, (company_name, language, template_type))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'company_id', 'company_name', 'language', 'subject', 'email_body', 
                      'customization_data', 'api_cost', 'tokens_used', 'customization_method', 
                      'template_type', 'generated_at']
            email_data = dict(zip(columns, result))
            # JSONデータを展開
            if email_data['customization_data']:
                try:
                    customization = json.loads(email_data['customization_data'])
                    email_data.update(customization)
                except:
                    pass
            return email_data
        return None
    
    def save_send_history(self, send_data: Dict):
        """送信履歴を保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO integrated_send_history 
            (company_id, company_name, recipient_email, language, subject, sent_at, status, smtp_response, template_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            send_data.get('company_id'),
            send_data.get('company_name'),
            send_data.get('recipient_email'),
            send_data.get('language'),
            send_data.get('subject'),
            datetime.now().isoformat(),
            send_data.get('status'),
            send_data.get('smtp_response'),
            send_data.get('template_type', 'standard')
        ))
        
        conn.commit()
        conn.close()
    
    def get_companies(self, limit: int = 100) -> List[Dict]:
        """企業データ一覧を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM companies ORDER BY updated_at DESC LIMIT {limit}")
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'company_id', 'company_name', 'email', 'website', 'phone', 
                  'description', 'industry', 'country', 'created_at', 'updated_at']
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_send_history(self, limit: int = 50) -> List[Dict]:
        """送信履歴を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT * FROM integrated_send_history 
            ORDER BY sent_at DESC LIMIT {limit}
        """)
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'company_id', 'company_name', 'recipient_email', 'language', 
                  'subject', 'sent_at', 'status', 'smtp_response', 'template_type']
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_already_sent_companies(self, language: str, template_type: str) -> List[str]:
        """送信済み企業名リストを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 成功送信済みの企業名を取得
        cursor.execute("""
            SELECT DISTINCT company_name 
            FROM integrated_send_history 
            WHERE language = ? AND template_type = ? AND status = 'success'
            AND DATE(sent_at) = DATE('now')
        """, (language, template_type))
        
        sent_companies = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return sent_companies
