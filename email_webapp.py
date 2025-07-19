"""
統合メールシステム - 日本語個別生成 + 英語バッチ処理
既存のemail_webapp.pyに統合する完全版（機能削除なし）
"""

import json
import time
import sqlite3
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# OpenAI クライアントの安全な初期化
def get_openai_client():
    """OpenAI クライアントを安全に取得"""
    try:
        from openai import OpenAI
        
        # Streamlit Secrets からAPIキー取得を優先
        if "OPENAI_API_KEY" in st.secrets:
            return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        else:
            st.error("❌ OPENAI_API_KEY が .streamlit/secrets.toml に設定されていません")
            return None
    except ImportError:
        st.error("❌ OpenAI ライブラリがインストールされていません")
        return None
    except Exception as e:
        st.error(f"❌ OpenAI クライアント初期化エラー: {e}")
        return None

# ===== 既存のGmail送信機能 =====
def send_email_smtp(to_email: str, subject: str, body: str, gmail_config: Dict) -> bool:
    """Gmail SMTP経由でメール送信"""
    try:
        # SMTP設定
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # MIMEメッセージ作成
        msg = MIMEMultipart()
        msg['From'] = f"{gmail_config['sender_name']} <{gmail_config['email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 本文添付
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP接続・送信
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_config['email'], gmail_config['password'])
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        st.error(f"メール送信エラー: {str(e)}")
        return False

# ===== 英語カスタマイズエンジン =====
class EnglishEmailCustomizer:
    """英語パートナーシップメールのカスタマイゼーション"""
    
    def __init__(self, api_key: str = None):
        self.openai_client = get_openai_client()
        
        # 高品質ベースメール（提供されたもの）
        self.base_email_template = """Subject: Exploring Strategic Partnership for Industrial Mesh Wi-Fi Solutions

Dear {title},

I hope this message finds you well.

My name is Koji Tokuda from PicoCELA Inc. (NASDAQ: PCLA), a NASDAQ-listed company specializing in advanced Industrial multi-hop mesh Wi-Fi access point solutions.

PicoCELA's unique technology enables:
• Ultra-stable, multi-hop wireless connectivity over wide areas (10 hops available)
• Video, Voice, Robotics control traffic available even if mesh (2-3m sec/hop latency)  
• Reduced installation costs and deployment time (Maximum 90% LAN cable reduction)
• Reliable coverage in challenging environments such as:
{industry_specific_environments}

{custom_value_proposition}

As we continue to expand globally, we are eager to establish partnerships that deliver mutual value. Beyond offering our technology, we support partners in expanding their business into the Japanese and broader Asian markets. By combining your solutions with our technology, we believe we can create differentiated offerings and new business opportunities in both regions.

For more information about PicoCELA and our solutions, please visit our website: https://picocela.com/en/

Would you be open to a brief call to discuss potential collaboration?

If you prefer not to receive further communication regarding potential business collaboration, please let me know, and I will remove you from our contact list.

Thank you very much for your time.

Best regards,
Koji Tokuda
Business Development Manager
PicoCELA Inc. (NASDAQ: PCLA)
tokuda@picocela.com
1-408-850-5058
4F SANOS Nihombashi Building,
2−34−5 Nihombashi-Ningyocho,
Chuo-ku, Tokyo 103-0013, Japan
https://picocela.com/en/"""

        # パートナーシップ特化カスタマイズプロンプト
        self.customization_prompt = """
Customize PicoCELA partnership proposal for specific company.

Company: {company_name}
Business: {description}

This is a PARTNERSHIP proposal (not sales). Focus on mutual business opportunities.

Current generic environments:
• Industrial facilities
• Construction sites  
• Mines
• Disaster recovery and temporary networks
• Warehouses

Task: Replace with 4-5 challenging environments specific to this company's target markets/customers.

Requirements:
- Match their industry expertise and customer base
- Emphasize technical RF/networking challenges PicoCELA solves
- Show you understand their business domain
- Use professional technical language

Output JSON:
{{
  "partnership_environments": "• [Environment 1 specific to their customers]\\n• [Environment 2]\\n• [Environment 3]\\n• [Environment 4]\\n• [Environment 5 if relevant]",
  "partnership_value": "2-3 sentences about mutual partnership benefits for their business and customer base",
  "suggested_title": "Business Development Manager/Partnership Manager/CEO etc"
}}

Focus on THEIR CUSTOMERS' challenges that PicoCELA can help solve.
"""
    
    def customize_email_gpt35(self, company_data: Dict) -> Dict:
        """GPT-3.5による英語メールカスタマイズ"""
        if not self.openai_client:
            return self._create_fallback_email(company_data.get('company_name', ''), error="OpenAI API未設定")
            
        company_name = company_data.get('company_name', '')
        description = company_data.get('description', '')
        
        if not description or description.strip() == "":
            return self._create_fallback_email(company_name)
        
        try:
            # GPT-3.5でカスタマイズ部分のみ生成
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": self.customization_prompt.format(
                        company_name=company_name,
                        description=description
                    )}
                ],
                max_tokens=300,
                temperature=0.3,
                timeout=30
            )
            
            # コスト計算
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.0015 + output_tokens * 0.002) / 1000
            
            # レスポンス解析
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '')
            
            customization = json.loads(result_text)
            
            # ベースメールにカスタマイズを適用
            customized_email = self.base_email_template.format(
                title=customization.get('suggested_title', 'Business Development Manager'),
                industry_specific_environments=customization.get('partnership_environments', ''),
                custom_value_proposition=customization.get('partnership_value', '')
            )
            
            return {
                'company_id': company_data.get('company_id'),
                'company_name': company_name,
                'customized_email': customized_email,
                'subject': 'Exploring Strategic Partnership for Industrial Mesh Wi-Fi Solutions',
                'partnership_environments': customization.get('partnership_environments'),
                'partnership_value': customization.get('partnership_value'),
                'suggested_title': customization.get('suggested_title'),
                'api_cost': cost,
                'tokens_used': input_tokens + output_tokens,
                'customization_method': 'gpt35',
                'language': 'english',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._create_fallback_email(company_name, error=str(e))
    
    def _create_fallback_email(self, company_name: str, error: str = None) -> Dict:
        """フォールバックメール（元の汎用版）"""
        customized_email = self.base_email_template.format(
            title='Business Development Manager',
            industry_specific_environments='• Industrial facilities\n• Construction sites\n• Mines\n• Disaster recovery and temporary networks\n• Warehouses',
            custom_value_proposition='Our technology can significantly enhance your wireless infrastructure capabilities while reducing deployment costs and complexity.'
        )
        
        return {
            'company_name': company_name,
            'customized_email': customized_email,
            'subject': 'Exploring Strategic Partnership for Industrial Mesh Wi-Fi Solutions',
            'partnership_environments': '• Industrial facilities\n• Construction sites\n• Mines\n• Disaster recovery and temporary networks\n• Warehouses',
            'partnership_value': 'Our technology can significantly enhance your wireless infrastructure capabilities while reducing deployment costs and complexity.',
            'suggested_title': 'Business Development Manager',
            'api_cost': 0.0,
            'customization_method': 'fallback',
            'language': 'english',
            'error': error,
            'generated_at': datetime.now().isoformat()
        }

# ===== 日本語メールカスタマイズエンジン =====
class JapaneseEmailCustomizer:
    """日本語営業メールのカスタマイゼーション"""
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # 日本語ベーステンプレート
        self.base_template = """件名: {subject}

{company_name} 御中

いつもお世話になっております。
PicoCELA株式会社の{sender_name}と申します。

この度、貴社の{business_description}に関連して、弊社のワイヤレスソリューションがお役に立てる可能性があると考え、ご連絡させていただきました。

{custom_content}

PicoCELA独自の技術特徴：
• 最大10ホップの安定したメッシュ通信
• 低遅延（ホップあたり2-3ms）でリアルタイム制御対応
• 配線工事を最大90%削減可能
• {industry_specific_benefits}

{call_to_action}

ご多忙中恐れ入りますが、ご検討のほど、よろしくお願い申し上げます。

{signature}
"""
    
    def customize_japanese_email(self, company_data: Dict, template_type: str = "partnership") -> Dict:
        """日本語メールのカスタマイズ"""
        if not self.openai_client:
            return self._create_fallback_japanese_email(company_data)
        
        try:
            prompt = f"""
以下の企業向けに、PicoCELAの無線技術を紹介する営業メールをカスタマイズしてください。

企業名: {company_data.get('company_name', '')}
事業内容: {company_data.get('description', '')}
業界: {company_data.get('industry', '')}

要求:
1. 相手企業の事業に特化した技術的課題を理解していることを示す
2. PicoCELAの技術がどのように解決できるかを具体的に説明
3. 日本のビジネス文化に適した丁寧な文章
4. パートナーシップの可能性を示唆

JSON形式で回答:
{{
  "subject": "件名",
  "custom_content": "カスタマイズされた本文（2-3段落）",
  "industry_specific_benefits": "業界特化の技術メリット",
  "call_to_action": "具体的な提案・次のステップ"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.4
            )
            
            customization = json.loads(response.choices[0].message.content)
            
            # テンプレートに適用
            email_content = self.base_template.format(
                subject=customization.get('subject', 'PicoCELAワイヤレスソリューションのご提案'),
                company_name=company_data.get('company_name', ''),
                sender_name='徳田',
                business_description=company_data.get('description', '事業'),
                custom_content=customization.get('custom_content', ''),
                industry_specific_benefits=customization.get('industry_specific_benefits', ''),
                call_to_action=customization.get('call_to_action', ''),
                signature=self._get_japanese_signature()
            )
            
            return {
                'company_id': company_data.get('company_id'),
                'company_name': company_data.get('company_name'),
                'email_content': email_content,
                'subject': customization.get('subject'),
                'language': 'japanese',
                'customization_method': 'gpt35',
                'api_cost': (response.usage.total_tokens * 0.00175) / 1000,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._create_fallback_japanese_email(company_data, error=str(e))
    
    def _create_fallback_japanese_email(self, company_data: Dict, error: str = None) -> Dict:
        """日本語フォールバックメール"""
        email_content = self.base_template.format(
            subject='PicoCELAワイヤレスソリューションのご提案',
            company_name=company_data.get('company_name', ''),
            sender_name='徳田',
            business_description=company_data.get('description', '事業'),
            custom_content='貴社の事業展開において、安定したワイヤレス通信環境の構築が重要な要素となっているのではないでしょうか。',
            industry_specific_benefits='厳しい環境での安定通信',
            call_to_action='もしご興味をお持ちいただけましたら、15分程度のお電話でご説明させていただければと思います。',
            signature=self._get_japanese_signature()
        )
        
        return {
            'company_id': company_data.get('company_id'),
            'company_name': company_data.get('company_name'),
            'email_content': email_content,
            'subject': 'PicoCELAワイヤレスソリューションのご提案',
            'language': 'japanese',
            'customization_method': 'fallback',
            'api_cost': 0.0,
            'error': error,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_japanese_signature(self) -> str:
        """日本語署名"""
        return """――――――――――――――――――――
PicoCELA株式会社
ビジネス開発部
徳田 幸次
〒103-0013 
東京都中央区日本橋人形町2-34-5
SANOS日本橋ビル4F
TEL: 1-408-850-5058
Email: tokuda@picocela.com
URL: https://picocela.com/
――――――――――――――――――――"""

# ===== データベース管理 =====
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
        """生成済みメールを取得 - company_nameベース検索に修正"""
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

# ===== バッチ処理システム =====
def generate_english_emails_batch(companies_data: List[Dict], max_companies: int = None) -> Dict:
    """英語メールバッチ生成"""
    customizer = EnglishEmailCustomizer()
    db = IntegratedEmailDatabase()
    
    companies_to_process = companies_data[:max_companies] if max_companies else companies_data
    total_companies = len(companies_to_process)
    
    st.write(f"🌍 {total_companies}社の英語パートナーシップメール生成中...")
    
    # 処理予測
    estimated_time_minutes = (total_companies * 2) / 60
    estimated_cost = total_companies * 0.0004
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("処理対象", f"{total_companies}社")
    with col2:
        st.metric("予想時間", f"{estimated_time_minutes:.1f}分")
    with col3:
        st.metric("予想コスト", f"${estimated_cost:.3f}")
    
    # バッチ処理実行
    results = []
    total_cost = 0.0
    success_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_tracker = st.empty()
    
    start_time = time.time()
    
    for i, company in enumerate(companies_to_process):
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        # 進捗更新
        progress = (i + 1) / total_companies
        progress_bar.progress(progress)
        status_text.text(f"生成中: {company.get('company_name', 'Unknown')} ({i+1}/{total_companies})")
        
        # 時間予測
        if i > 0:
            avg_time = elapsed_time / i
            remaining_time = (total_companies - i) * avg_time / 60
            time_tracker.text(f"経過: {elapsed_time/60:.1f}分 | 残り: {remaining_time:.1f}分")
        
        # 企業データ保存
        db.save_company(company)
        
        # メール生成
        result = customizer.customize_email_gpt35(company)
        results.append(result)
        
        # データベース保存
        db.save_generated_email(result)
        
        if result.get('customization_method') == 'gpt35':
            success_count += 1
            total_cost += result.get('api_cost', 0.0)
        
        # 5社ごとに進捗表示
        if (i + 1) % 5 == 0:
            success_rate = (success_count / (i + 1)) * 100
            st.success(f"✅ {i+1}社完了 (GPT成功率: {success_rate:.1f}%)")
        
        # API制限対応
        time.sleep(1)
    
    # 完了サマリー
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    summary = {
        'total_processed': total_companies,
        'gpt35_success': success_count,
        'fallback_used': total_companies - success_count,
        'success_rate': (success_count / total_companies) * 100,
        'total_cost_usd': total_cost,
        'total_cost_jpy': total_cost * 150,
        'total_time_minutes': total_elapsed / 60,
        'avg_cost_per_email': total_cost / total_companies if total_companies > 0 else 0
    }
    
    st.balloons()
    st.success(f"🎉 英語メールバッチ生成完了！")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("GPT成功", f"{success_count}社", f"{summary['success_rate']:.1f}%")
    with col2:
        st.metric("総コスト", f"¥{summary['total_cost_jpy']:.0f}")
    with col3:
        st.metric("処理時間", f"{summary['total_time_minutes']:.1f}分")
    with col4:
        st.metric("平均コスト", f"${summary['avg_cost_per_email']:.4f}")
    
    return summary

def generate_japanese_emails_individual(companies_data: List[Dict], template_type: str = "partnership") -> Dict:
    """日本語メール個別生成"""
    customizer = JapaneseEmailCustomizer()
    db = IntegratedEmailDatabase()
    
    st.write(f"🇯🇵 日本語メール個別生成開始...")
    
    results = []
    total_cost = 0.0
    
    for i, company in enumerate(companies_data):
        st.write(f"処理中: {company.get('company_name')} ({i+1}/{len(companies_data)})")
        
        # 企業データ保存
        db.save_company(company)
        
        # メール生成
        result = customizer.customize_japanese_email(company, template_type)
        results.append(result)
        
        # データベース保存
        result['template_type'] = template_type
        db.save_generated_email(result)
        
        total_cost += result.get('api_cost', 0.0)
        
        # 結果表示
        with st.expander(f"📧 {company.get('company_name')} - 生成結果"):
            st.write(f"**件名**: {result.get('subject')}")
            st.text_area("内容", result.get('email_content'), height=300, key=f"email_{i}")
    
    summary = {
        'total_processed': len(companies_data),
        'total_cost_usd': total_cost,
        'total_cost_jpy': total_cost * 150
    }
    
    st.success(f"✅ 日本語メール {len(companies_data)}件生成完了")
    
    return summary

# ===== 重複なし再開機能付き送信システム =====
def get_already_sent_companies(db: IntegratedEmailDatabase, language: str, template_type: str) -> List[str]:
    """送信済み企業名リストを取得"""
    conn = sqlite3.connect(db.db_path)
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

def send_email_smtp_with_retry(to_email: str, subject: str, body: str, gmail_config: Dict, max_retries: int = 3) -> bool:
    """リトライ機能付きメール送信"""
    for attempt in range(max_retries):
        try:
            # SMTP設定
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            
            # MIMEメッセージ作成
            msg = MIMEMultipart()
            msg['From'] = f"{gmail_config['sender_name']} <{gmail_config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 本文添付
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP接続・送信
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(gmail_config['email'], gmail_config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(30)  # 30秒待機してリトライ
                continue
            else:
                raise e
    
    return False

def send_pregenerated_emails_with_resume(company_list: List[Dict], gmail_config: Dict, 
                                        max_emails: int = 50, language: str = 'english',
                                        template_type: str = 'standard', send_interval: int = 60,
                                        resume_mode: bool = False) -> Dict:
    """重複なし再開機能付き瞬時送信"""
    db = IntegratedEmailDatabase()
    
    # 送信済み企業を除外
    if resume_mode:
        already_sent = get_already_sent_companies(db, language, template_type)
        remaining_companies = [c for c in company_list if c.get('company_name') not in already_sent]
        st.info(f"📧 送信済み: {len(already_sent)}社 | 残り: {len(remaining_companies)}社")
    else:
        remaining_companies = company_list
        already_sent = []
    
    target_companies = remaining_companies[:max_emails]
    
    if not target_companies:
        st.success("✅ 全企業への送信が完了しています！")
        return {'all_completed': True}
    
    st.write(f"📤 {'再開' if resume_mode else '開始'}: {len(target_companies)}社への送信")
    
    sent_count = 0
    failed_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_remaining_text = st.empty()
    
    start_time = time.time()
    
    for i, company in enumerate(target_companies):
        # 進捗更新
        progress = (i + 1) / len(target_companies)
        progress_bar.progress(progress)
        status_text.text(f"送信中: {company.get('company_name', 'Unknown')} ({i+1}/{len(target_companies)})")
        
        # 残り時間表示
        if i > 0:
            elapsed = time.time() - start_time
            estimated_total = elapsed / i * len(target_companies)
            remaining = estimated_total - elapsed
            time_remaining_text.text(f"⏱️ 残り時間: {remaining/60:.1f}分")
        
        # 送信前に再度確認（他のプロセスで送信済みの場合）
        company_name = company.get('company_name')
        if company_name in get_already_sent_companies(db, language, template_type):
            st.info(f"⚠️ {company_name} - 既に送信済みのためスキップ")
            continue
        
        # データベースからメール取得
        stored_email = db.get_generated_email(company_name, language, template_type)
        
        if stored_email:
            try:
                # Gmail制限対策: より長い間隔
                if i > 0:
                    time.sleep(send_interval)
                
                # 送信実行（リトライ機能付き）
                success = send_email_smtp_with_retry(
                    to_email=company.get('email'),
                    subject=stored_email['subject'],
                    body=stored_email['email_body'],
                    gmail_config=gmail_config,
                    max_retries=3
                )
                
                # 送信履歴保存
                send_record = {
                    'company_id': company.get('company_id', ''),
                    'company_name': company_name,
                    'recipient_email': company.get('email'),
                    'language': language,
                    'subject': stored_email['subject'],
                    'status': 'success' if success else 'failed',
                    'smtp_response': 'OK' if success else 'SMTP Error',
                    'template_type': template_type
                }
                db.save_send_history(send_record)
                
                if success:
                    sent_count += 1
                    st.success(f"✅ {company.get('company_name')} - 送信成功")
                else:
                    failed_count += 1
                    st.error(f"❌ {company.get('company_name')} - 送信失敗")
                    
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                st.error(f"❌ {company.get('company_name')} - エラー: {error_msg[:50]}")
                
                # Gmail制限検知
                if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "authentication" in error_msg.lower():
                    st.error("🚫 Gmail送信制限に達しました。24時間後に再開してください。")
                    break
                
                # エラー履歴保存
                send_record = {
                    'company_id': company.get('company_id', ''),
                    'company_name': company_name,
                    'recipient_email': company.get('email'),
                    'language': language,
                    'subject': stored_email.get('subject', 'Unknown'),
                    'status': 'error',
                    'smtp_response': error_msg[:100],
                    'template_type': template_type
                }
                db.save_send_history(send_record)
        else:
            failed_count += 1
            st.warning(f"⚠️ {company.get('company_name')} - 事前生成メールなし")
    
    # 完了処理
    total_time = time.time() - start_time
    total_sent_today = len(already_sent) + sent_count
    
    summary = {
        'total_attempted': len(target_companies),
        'successful_sends': sent_count,
        'failed_sends': failed_count,
        'total_sent_today': total_sent_today,
        'success_rate': (sent_count / len(target_companies)) * 100 if target_companies else 0,
        'total_time_minutes': total_time / 60,
        'remaining_companies': len(remaining_companies) - len(target_companies)
    }
    
    st.success(f"🎉 送信{'再開' if resume_mode else ''}完了！")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今回送信", f"{sent_count}通")
    with col2:
        st.metric("本日総送信", f"{total_sent_today}通")
    with col3:
        st.metric("成功率", f"{summary['success_rate']:.1f}%")
    with col4:
        st.metric("残り企業", f"{summary['remaining_companies']}社")
    
    return summary

# ===== 互換性のための旧関数 =====
def send_pregenerated_emails(company_list: List[Dict], gmail_config: Dict, 
                            max_emails: int = 50, language: str = 'english',
                            template_type: str = 'standard') -> Dict:
    """旧バージョン互換性のための関数"""
    return send_pregenerated_emails_with_resume(
        company_list, gmail_config, max_emails, language, template_type, 60, False
    )

# ===== 企業データ取得（Google Sheets連携） =====
def get_companies_from_sheets() -> List[Dict]:
    """Google Sheetsから企業データを取得"""
    try:
        # 既存のGoogle Sheets URL使用
        sheet_url = "https://docs.google.com/spreadsheets/d/1ySS3zLbEwq3U54pzIRAbKLyhOWR2YdBUSdK_xr_7WNY"
        csv_url = f"{sheet_url}/export?format=csv&gid=580124806"
        
        # データ読み込み
        df = pd.read_csv(csv_url)
        
        # 必要な列のみ抽出・整形
        companies = []
        for index, row in df.iterrows():
            company_data = {
                'company_id': f"COMP_{index:03d}",
                'company_name': str(row.get('company_name', '')).strip(),
                'email': str(row.get('email', '')).strip(),
                'description': str(row.get('description', '')).strip(),
                'website': str(row.get('website', '')).strip(),
                'phone': str(row.get('phone', '')).strip(),
                'industry': str(row.get('industry', '')).strip(),
                'country': str(row.get('country', '')).strip()
            }
            
            # 有効なデータのみ追加
            if company_data['company_name'] and company_data['email']:
                companies.append(company_data)
        
        st.success(f"✅ Google Sheetsから{len(companies)}社のデータを取得")
        return companies
        
    except Exception as e:
        st.error(f"Google Sheets接続エラー: {str(e)}")
        
        # フォールバックデータ
        return [
            {
                'company_id': 'FUSION_001',
                'company_name': 'FUSIONDRIVER',
                'email': 'koji@fusiondriver.biz',
                'description': 'WiFi solution for construction sites with wireless communication integration',
                'website': 'https://www.fusiondriver.biz',
                'phone': '',
                'industry': 'Technology',
                'country': 'Japan'
            }
        ]

# ===== 企業データ手動追加機能 =====
def render_company_data_management():
    """企業データ手動管理機能"""
    st.subheader("📝 企業データ管理")
    
    db = IntegratedEmailDatabase()
    
    # データ追加フォーム
    with st.expander("➕ 企業データ手動追加"):
        with st.form("add_company_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_company_name = st.text_input("企業名*")
                new_email = st.text_input("メールアドレス*")
                new_website = st.text_input("ウェブサイト")
                new_phone = st.text_input("電話番号")
            
            with col2:
                new_description = st.text_area("事業説明", height=100)
                new_industry = st.text_input("業界")
                new_country = st.selectbox("国", ["Japan", "USA", "UK", "Germany", "Other"])
            
            submitted = st.form_submit_button("企業を追加")
            
            if submitted and new_company_name and new_email:
                new_company = {
                    'company_id': f"MANUAL_{int(time.time())}",
                    'company_name': new_company_name,
                    'email': new_email,
                    'description': new_description,
                    'website': new_website,
                    'phone': new_phone,
                    'industry': new_industry,
                    'country': new_country
                }
                
                db.save_company(new_company)
                st.success(f"✅ {new_company_name} を追加しました")
                st.rerun()
    
    # 既存企業データ表示
    st.subheader("💼 登録済み企業データ")
    
    companies = db.get_companies(50)
    if companies:
        # フィルター
        col1, col2 = st.columns(2)
        with col1:
            country_filter = st.selectbox("国フィルター", 
                                        ["All"] + list(set(c.get('country', 'Unknown') for c in companies)))
        with col2:
            industry_filter = st.selectbox("業界フィルター", 
                                         ["All"] + list(set(c.get('industry', 'Unknown') for c in companies)))
        
        # フィルター適用
        filtered_companies = companies
        if country_filter != "All":
            filtered_companies = [c for c in filtered_companies if c.get('country') == country_filter]
        if industry_filter != "All":
            filtered_companies = [c for c in filtered_companies if c.get('industry') == industry_filter]
        
        # データ表示
        df = pd.DataFrame(filtered_companies)
        if not df.empty:
            df = df[['company_name', 'email', 'industry', 'country', 'updated_at']]
            st.dataframe(df, use_container_width=True)
        
        st.info(f"表示中: {len(filtered_companies)}社 / 総数: {len(companies)}社")
    else:
        st.warning("⚠️ 登録済み企業データがありません")

# ===== システム統計表示 =====
def render_system_statistics():
    """システム統計表示"""
    st.subheader("📈 システム統計")
    
    db = IntegratedEmailDatabase()
    conn = sqlite3.connect(db.db_path)
    
    # 生成統計
    try:
        stats_query = """
            SELECT 
                language,
                customization_method,
                template_type,
                COUNT(*) as count,
                SUM(api_cost) as total_cost,
                AVG(api_cost) as avg_cost
            FROM integrated_emails 
            GROUP BY language, customization_method, template_type
        """
        
        stats_df = pd.read_sql_query(stats_query, conn)
        
        if not stats_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_emails = stats_df['count'].sum()
                st.metric("総生成数", f"{total_emails}通")
            
            with col2:
                total_cost = stats_df['total_cost'].sum()
                st.metric("総コスト", f"${total_cost:.3f}")
            
            with col3:
                avg_cost = stats_df['avg_cost'].mean()
                st.metric("平均コスト", f"${avg_cost:.4f}")
            
            with col4:
                english_count = stats_df[stats_df['language'] == 'english']['count'].sum()
                st.metric("英語メール", f"{english_count}通")
            
            # 詳細統計表
            st.write("**詳細統計:**")
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("まだ生成されたメールがありません")
        
        # 送信統計
        st.subheader("📤 送信統計")
        send_stats_query = """
            SELECT 
                language,
                status,
                COUNT(*) as count
            FROM integrated_send_history 
            GROUP BY language, status
        """
        
        send_stats_df = pd.read_sql_query(send_stats_query, conn)
        
        if not send_stats_df.empty:
            col1, col2, col3 = st.columns(3)
            
            total_sent = send_stats_df['count'].sum()
            success_sent = send_stats_df[send_stats_df['status'] == 'success']['count'].sum()
            success_rate = (success_sent / total_sent * 100) if total_sent > 0 else 0
            
            with col1:
                st.metric("総送信数", f"{total_sent}通")
            with col2:
                st.metric("成功送信", f"{success_sent}通")
            with col3:
                st.metric("成功率", f"{success_rate:.1f}%")
            
            st.dataframe(send_stats_df, use_container_width=True)
        else:
            st.info("まだ送信履歴がありません")
            
    except Exception as e:
        st.error(f"統計取得エラー: {str(e)}")
    
    finally:
        conn.close()

# ===== 設定管理 =====
def render_settings_management():
    """設定管理機能"""
    st.subheader("⚙️ システム設定")
    
    # API設定状態
    with st.expander("🔧 API設定状態"):
        if "OPENAI_API_KEY" in st.secrets:
            st.success("✅ OpenAI API Key: 設定済み (Streamlit Secrets)")
        else:
            st.warning("⚠️ OpenAI API Key: 未設定")
            st.info("`.streamlit/secrets.toml` に `OPENAI_API_KEY` を設定してください")
    
    # テンプレート管理
    with st.expander("📧 メールテンプレート管理"):
        st.write("**英語テンプレート特徴:**")
        st.write("- ✅ NASDAQ上場アピール")
        st.write("- ✅ パートナーシップ提案")
        st.write("- ✅ 技術仕様明記（10ホップ、2-3ms遅延）")
        st.write("- ✅ 相手事業特化環境リスト")
        
        st.write("**日本語テンプレート特徴:**")
        st.write("- ✅ 日本のビジネス文化に適した丁寧な文章")
        st.write("- ✅ 技術的課題への理解を示す内容")
        st.write("- ✅ 具体的な次のステップ提案")
        
        if st.button("カスタムテンプレート追加"):
            st.info("カスタムテンプレート機能は今後実装予定")
    
    # システム情報
    with st.expander("ℹ️ システム情報"):
        st.write("**データベース**: SQLite")
        st.write("**メール送信**: Gmail SMTP")
        st.write("**AI生成**: OpenAI GPT-3.5-turbo")
        st.write("**データソース**: Google Sheets")
        
        # データベースサイズ
        try:
            import os
            db_path = "picocela_integrated_emails.db"
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / 1024  # KB
                st.write(f"**データベースサイズ**: {db_size:.1f} KB")
        except:
            st.write("**データベースサイズ**: 取得できませんでした")

# ===== 送信履歴表示 =====
def render_send_history():
    """送信履歴表示"""
    st.subheader("📧 送信履歴")
    
    db = IntegratedEmailDatabase()
    history = db.get_send_history(100)
    
    if history:
        # フィルター
        col1, col2, col3 = st.columns(3)
        with col1:
            language_filter = st.selectbox("言語", ["All", "english", "japanese"], key="history_lang")
        with col2:
            status_filter = st.selectbox("ステータス", ["All", "success", "failed", "error"], key="history_status")
        with col3:
            show_limit = st.number_input("表示件数", min_value=10, max_value=200, value=50)
        
        # フィルター適用
        filtered_history = history[:show_limit]
        if language_filter != "All":
            filtered_history = [h for h in filtered_history if h.get('language') == language_filter]
        if status_filter != "All":
            filtered_history = [h for h in filtered_history if h.get('status') == status_filter]
        
        # データ表示
        if filtered_history:
            df = pd.DataFrame(filtered_history)
            df = df[['company_name', 'recipient_email', 'language', 'status', 'sent_at', 'subject']]
            st.dataframe(df, use_container_width=True)
            
            # 詳細表示
            selected_index = st.selectbox("詳細表示", range(len(filtered_history)), 
                                        format_func=lambda x: f"{filtered_history[x]['company_name']} - {filtered_history[x]['status']}")
            
            if st.button("詳細を表示"):
                selected_record = filtered_history[selected_index]
                st.json(selected_record)
        else:
            st.info("フィルター条件に一致する履歴がありません")
    else:
        st.warning("⚠️ 送信履歴がありません")

# ===== メインアプリケーション =====
def main():
    """メインアプリケーション"""
    
    # ページ設定
    st.set_page_config(
        page_title="PicoCELA統合メールシステム完全版", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # タイトル
    st.title("🌐 PicoCELA統合メールシステム完全版")
    st.markdown("**日本語個別生成 + 英語バッチ処理システム - 全機能搭載**")
    
    # API設定状態確認
    api_configured = "OPENAI_API_KEY" in st.secrets
    if api_configured:
        st.success("✅ OpenAI API Key 設定済み (Streamlit Secrets)")
    else:
        st.error("❌ OpenAI API Key が設定されていません (.streamlit/secrets.toml)")
    
    # サイドバー設定
    with st.sidebar:
        st.header("🔧 システム設定")
        
        # API設定状態表示
        st.subheader("🤖 OpenAI API設定")
        if api_configured:
            st.success("✅ API設定完了")
        else:
            st.error("❌ API未設定")
            st.info("Secretsファイルを確認してください")
        
        # Gmail設定
        st.subheader("📧 Gmail設定")
        gmail_user = st.text_input("Gmailアドレス", value="tokuda@picocela.com")
        gmail_password = st.text_input("アプリパスワード", type="password", 
                                     help="Gmail 2段階認証のアプリパスワード")
        
        # Gmail設定状態
        if gmail_user and gmail_password:
            gmail_config = {
                'email': gmail_user,
                'password': gmail_password,
                'sender_name': 'PicoCELA Inc.'
            }
            st.success("✅ Gmail設定完了")
        else:
            gmail_config = None
            st.warning("⚠️ Gmail設定が必要です")
        
        # クイック統計
        st.subheader("📊 クイック統計")
        try:
            db = IntegratedEmailDatabase()
            conn = sqlite3.connect(db.db_path)
            
            # 生成数
            count_query = "SELECT COUNT(*) as total FROM integrated_emails"
            result = pd.read_sql_query(count_query, conn)
            total_generated = result.iloc[0]['total'] if not result.empty else 0
            
            # コスト
            cost_query = "SELECT SUM(api_cost) as total_cost FROM integrated_emails"
            cost_result = pd.read_sql_query(cost_query, conn)
            total_cost = cost_result.iloc[0]['total_cost'] if not cost_result.empty and cost_result.iloc[0]['total_cost'] else 0
            
            # 送信数
            send_query = "SELECT COUNT(*) as total_sent FROM integrated_send_history"
            send_result = pd.read_sql_query(send_query, conn)
            total_sent = send_result.iloc[0]['total_sent'] if not send_result.empty else 0
            
            st.metric("生成済み", f"{total_generated}通")
            st.metric("送信済み", f"{total_sent}通")
            st.metric("総コスト", f"${total_cost:.3f}")
            
            conn.close()
        except:
            st.metric("生成済み", "0通")
            st.metric("送信済み", "0通")
            st.metric("総コスト", "$0.000")
    
    # メインコンテンツ
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🌍 英語バッチ生成", 
        "🇯🇵 日本語個別生成",
        "📊 生成結果確認", 
        "📤 瞬時送信",
        "📧 送信履歴",
        "📝 データ管理", 
        "⚙️ 設定"
    ])
    
    with tab1:
        st.subheader("🌍 英語パートナーシップメール バッチ生成")
        
        # システム説明
        with st.expander("ℹ️ バッチ生成システム概要"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**ベースメール特徴:**")
                st.write("- ✅ NASDAQ上場企業アピール")
                st.write("- ✅ 具体的技術仕様（10ホップ、2-3ms遅延）")
                st.write("- ✅ 数値効果（90%ケーブル削減）")
                st.write("- ✅ パートナーシップ提案（売り込みではない）")
            
            with col2:
                st.write("**GPT-3.5カスタマイズ:**")
                st.write("- 🎯 相手企業の顧客層に特化した環境リスト")
                st.write("- 🎯 相互ビジネス価値提案の最適化")
                st.write("- 🎯 適切な宛先タイトル自動選択")
                st.write("- 🎯 業界専門知識の証明")
        
        # 生成設定
        col1, col2, col3 = st.columns(3)
        with col1:
            max_companies = st.number_input("生成対象企業数", min_value=1, max_value=1000, value=100)
        with col2:
            estimated_cost = max_companies * 0.0004 * 150
            st.metric("予想コスト", f"約{estimated_cost:.0f}円")
        with col3:
            estimated_time = max_companies * 2 / 60
            st.metric("予想時間", f"{estimated_time:.1f}分")
        
        # 生成実行
        if api_configured:
            if st.button("🚀 英語バッチ生成開始", type="primary"):
                companies_data = get_companies_from_sheets()
                
                if companies_data and len(companies_data) > 0:
                    st.write(f"📋 {len(companies_data)}社のデータを取得しました")
                    summary = generate_english_emails_batch(companies_data, max_companies)
                    st.session_state['last_batch_summary'] = summary
                else:
                    st.error("❌ 企業データが取得できませんでした")
        else:
            st.error("❌ OpenAI API設定を完了してください")
    
    with tab2:
        st.subheader("🇯🇵 日本語営業メール 個別生成")
        
        # テンプレートタイプ選択
        template_type = st.selectbox("メールタイプ", 
                                   ["partnership", "introduction", "follow_up"],
                                   format_func=lambda x: {
                                       "partnership": "パートナーシップ提案",
                                       "introduction": "初回紹介",
                                       "follow_up": "フォローアップ"
                                   }[x])
        
        # 企業選択
        companies_data = get_companies_from_sheets()
        if companies_data:
            selected_companies = st.multiselect(
                "生成対象企業を選択",
                companies_data,
                format_func=lambda x: f"{x['company_name']} ({x.get('industry', 'Unknown')})"
            )
            
            if api_configured and selected_companies:
                if st.button("🇯🇵 日本語メール生成開始", type="primary"):
                    summary = generate_japanese_emails_individual(selected_companies, template_type)
                    st.session_state['last_japanese_summary'] = summary
            elif not api_configured:
                st.error("❌ OpenAI API設定を完了してください")
            elif not selected_companies:
                st.warning("⚠️ 生成対象企業を選択してください")
        else:
            st.error("❌ 企業データが取得できませんでした")
    
    with tab3:
        st.subheader("📊 生成済みメール確認・編集")
        
        db = IntegratedEmailDatabase()
        conn = sqlite3.connect(db.db_path)
        
        try:
            # フィルター
            col1, col2, col3 = st.columns(3)
            with col1:
                language_filter = st.selectbox("言語フィルター", ["all", "english", "japanese"])
            with col2:
                method_filter = st.selectbox("生成方法", ["all", "gpt35", "fallback"])
            with col3:
                template_filter = st.selectbox("テンプレート", ["all", "standard", "partnership", "introduction", "follow_up"])
            
            # データ取得
            where_clauses = []
            if language_filter != "all":
                where_clauses.append(f"language = '{language_filter}'")
            if method_filter != "all":
                where_clauses.append(f"customization_method = '{method_filter}'")
            if template_filter != "all":
                where_clauses.append(f"template_type = '{template_filter}'")
            
            where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT company_name, language, customization_method, template_type,
                       api_cost, generated_at, subject
                FROM integrated_emails 
                {where_clause}
                ORDER BY generated_at DESC
                LIMIT 50
            """
            
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                st.write(f"**生成済みメール**: {len(df)}通")
                st.dataframe(df, use_container_width=True)
                
                # 詳細表示・編集
                st.subheader("📧 メール詳細表示・編集")
                
                selected_company = st.selectbox(
                    "メール表示する企業を選択",
                    df['company_name'].tolist()
                )
                
                selected_language = st.selectbox("言語", ["english", "japanese"], key="detail_lang")
                selected_template = st.selectbox("テンプレート", ["standard", "partnership", "introduction", "follow_up"], key="detail_template")
                
                if st.button("メール内容を表示・編集"):
                    stored_email = db.get_generated_email(selected_company, selected_language, selected_template)
                    if stored_email:
                        st.write(f"**件名**: {stored_email['subject']}")
                        
                        # 編集可能なテキストエリア
                        edited_content = st.text_area(
                            "メール本文（編集可能）", 
                            stored_email['email_body'], 
                            height=400,
                            key="edit_email_content"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 変更を保存"):
                                # 編集内容を保存
                                stored_email['email_body'] = edited_content
                                db.save_generated_email(stored_email)
                                st.success("✅ メール内容を更新しました")
                        
                        with col2:
                            if st.button("📋 クリップボードにコピー"):
                                st.code(edited_content)
                                st.info("💡 上記テキストを手動でコピーしてください")
                        
                        # カスタマイズ詳細
                        with st.expander("🔍 カスタマイズ詳細"):
                            st.write(f"**生成方法**: {stored_email.get('customization_method', 'N/A')}")
                            st.write(f"**APIコスト**: ${stored_email.get('api_cost', 0):.4f}")
                            st.write(f"**生成日時**: {stored_email.get('generated_at', 'N/A')}")
                            
                            if stored_email.get('partnership_environments'):
                                st.write(f"**環境リスト**: {stored_email.get('partnership_environments', 'N/A')}")
                            if stored_email.get('partnership_value'):
                                st.write(f"**価値提案**: {stored_email.get('partnership_value', 'N/A')}")
                            if stored_email.get('suggested_title'):
                                st.write(f"**推奨タイトル**: {stored_email.get('suggested_title', 'N/A')}")
                    else:
                        st.warning("⚠️ 指定された条件のメールが見つかりません")
            else:
                st.warning("⚠️ 生成済みメールがありません。まず生成タブで実行してください。")
                
        except Exception as e:
            st.error(f"❌ データベースエラー: {str(e)}")
        finally:
            conn.close()
    
    with tab4:
        st.subheader("📤 事前生成メール瞬時送信")
        
        if gmail_config:
            # 送信状況確認
            db = IntegratedEmailDatabase()
            conn = sqlite3.connect(db.db_path)
            
            # 本日の送信統計
            today_stats_query = """
                SELECT 
                    language,
                    template_type,
                    COUNT(*) as sent_count
                FROM integrated_send_history 
                WHERE DATE(sent_at) = DATE('now') AND status = 'success'
                GROUP BY language, template_type
            """
            
            today_stats = pd.read_sql_query(today_stats_query, conn)
            
            # 送信状況表示
            if not today_stats.empty:
                st.subheader("📊 本日の送信状況")
                for _, row in today_stats.iterrows():
                    st.info(f"✅ {row['language']}/{row['template_type']}: {row['sent_count']}通送信済み")
            
            # 新規送信 vs 再開送信
            st.subheader("🚀 送信モード選択")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🆕 新規送信開始**")
                if st.button("新規送信設定", key="new_send"):
                    st.session_state['send_mode'] = 'new'
            
            with col2:
                st.write("**🔄 送信再開**")
                if st.button("再開設定", key="resume_send"):
                    st.session_state['send_mode'] = 'resume'
            
            # デフォルト設定
            if 'send_mode' not in st.session_state:
                st.session_state['send_mode'] = 'new'
            
            # 送信設定
            st.subheader(f"⚙️ {'再開' if st.session_state['send_mode'] == 'resume' else '新規'}送信設定")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                max_sends = st.number_input("最大送信数", min_value=1, max_value=100, value=20)
            with col2:
                send_language = st.selectbox("送信言語", ["english", "japanese"], key="send_lang")
            with col3:
                send_template = st.selectbox("テンプレート", ["standard", "partnership", "introduction", "follow_up"], key="send_template")
            
            # 送信間隔設定（Gmail制限対策）
            st.subheader("⏱️ 送信制限対策")
            col1, col2 = st.columns(2)
            with col1:
                send_interval = st.slider("送信間隔（秒）", min_value=60, max_value=300, value=120, 
                                        help="Gmail制限対策のため60秒以上推奨")
            with col2:
                max_daily_sends = st.number_input("1日最大送信数", min_value=50, max_value=500, value=200,
                                                help="Gmailアカウント制限に応じて調整")
            
            # 送信可能数確認
            try:
                available_query = f"""
                    SELECT COUNT(*) as count 
                    FROM integrated_emails 
                    WHERE language = '{send_language}' AND template_type = '{send_template}'
                """
                available_df = pd.read_sql_query(available_query, conn)
                available_count = available_df.iloc[0]['count'] if not available_df.empty else 0
                
                # 今日の送信数確認
                daily_sent_query = f"""
                    SELECT COUNT(*) as count 
                    FROM integrated_send_history 
                    WHERE DATE(sent_at) = DATE('now') AND status = 'success'
                """
                daily_sent_df = pd.read_sql_query(daily_sent_query, conn)
                daily_sent = daily_sent_df.iloc[0]['count'] if not daily_sent_df.empty else 0
                
                # 残り送信可能数
                remaining_daily = max_daily_sends - daily_sent
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("生成済みメール", f"{available_count}通")
                with col2:
                    st.metric("本日送信済み", f"{daily_sent}通")
                with col3:
                    st.metric("本日残り可能", f"{remaining_daily}通")
                
                if remaining_daily <= 0:
                    st.error("🚫 本日の送信制限に達しています。明日再開してください。")
                else:
                    if available_count > 0:
                        # 送信対象企業の確認
                        companies_data = get_companies_from_sheets()
                        
                        if st.session_state['send_mode'] == 'resume':
                            # 再開モード: 送信済み企業を除外
                            already_sent = get_already_sent_companies(db, send_language, send_template)
                            remaining_companies = [c for c in companies_data if c.get('company_name') not in already_sent]
                            
                            st.info(f"📧 送信済み: {len(already_sent)}社 | 未送信: {len(remaining_companies)}社")
                            
                            if not remaining_companies:
                                st.success("✅ 全企業への送信が完了しています！")
                            else:
                                target_count = min(max_sends, len(remaining_companies), remaining_daily)
                                estimated_time = target_count * (send_interval + 10) / 60
                                
                                st.write(f"⏱️ 予想送信時間: {estimated_time:.1f}分 ({target_count}社)")
                                
                                # 送信プレビュー
                                with st.expander("👀 再開送信対象プレビュー"):
                                    preview_companies = remaining_companies[:min(target_count, 5)]
                                    for company in preview_companies:
                                        st.write(f"• {company['company_name']} ({company['email']})")
                                    if len(remaining_companies) > 5:
                                        st.write(f"... 他 {len(remaining_companies)-5}社")
                                
                                # 送信確認
                                st.subheader("✅ 送信確認")
                                confirm_send = st.checkbox("📤 送信内容を確認し、Gmail制限を理解しました")
                                
                                if confirm_send and st.button("🔄 送信再開", type="primary"):
                                    summary = send_pregenerated_emails_with_resume(
                                        companies_data, 
                                        gmail_config, 
                                        max_sends, 
                                        send_language, 
                                        send_template, 
                                        send_interval,
                                        resume_mode=True
                                    )
                                    st.session_state['last_send_summary'] = summary
                                elif not confirm_send:
                                    st.warning("⚠️ 送信確認チェックボックスをチェックしてください")
                        else:
                            # 新規モード
                            target_count = min(max_sends, len(companies_data), remaining_daily)
                            estimated_time = target_count * (send_interval + 10) / 60
                            
                            st.write(f"⏱️ 予想送信時間: {estimated_time:.1f}分 ({target_count}社)")
                            
                            # 送信プレビュー
                            with st.expander("👀 送信対象プレビュー"):
                                preview_companies = companies_data[:min(target_count, 5)]
                                for company in preview_companies:
                                    st.write(f"• {company['company_name']} ({company['email']})")
                                if len(companies_data) > 5:
                                    st.write(f"... 他 {len(companies_data)-5}社")
                            
                            # 送信確認
                            st.subheader("✅ 送信確認")
                            confirm_send = st.checkbox("📤 送信内容を確認し、Gmail制限を理解しました")
                            
                            if confirm_send and st.button("🚀 瞬時送信開始", type="primary"):
                                summary = send_pregenerated_emails_with_resume(
                                    companies_data, 
                                    gmail_config, 
                                    max_sends, 
                                    send_language, 
                                    send_template, 
                                    send_interval,
                                    resume_mode=False
                                )
                                st.session_state['last_send_summary'] = summary
                            elif not confirm_send:
                                st.warning("⚠️ 送信確認チェックボックスをチェックしてください")
                    else:
                        st.warning(f"⚠️ {send_language}/{send_template}メールが生成されていません。まず生成してください。")
                        
            except Exception as e:
                st.error(f"❌ 送信可能数確認エラー: {str(e)}")
            finally:
                conn.close()
        else:
            st.warning("⚠️ Gmail設定を完了してください")
            
            # Gmail設定ヘルプ
            with st.expander("📧 Gmail設定ヘルプ"):
                st.write("**Gmail設定手順:**")
                st.write("1. Googleアカウントで2段階認証を有効化")
                st.write("2. アプリパスワードを生成")
                st.write("3. サイドバーにGmailアドレスとアプリパスワードを入力")
                st.write("4. 設定完了後、送信機能が利用可能になります")
                
                st.write("**Gmail制限について:**")
                st.write("- 通常アカウント: 500通/日")
                st.write("- G Suite: 2000通/日")
                st.write("- 推奨送信間隔: 120秒")
                st.write("- 制限に達した場合: 24時間待機が必要")
    
    with tab5:
        render_send_history()
    
    with tab6:
        render_company_data_management()
        
        # 一括データインポート
        st.subheader("📥 CSV一括インポート")
        
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type=['csv'])
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file)
                st.write("**アップロードデータプレビュー:**")
                st.dataframe(import_df.head())
                
                # カラムマッピング
                st.write("**カラムマッピング:**")
                col1, col2 = st.columns(2)
                
                required_fields = ['company_name', 'email', 'description']
                optional_fields = ['website', 'phone', 'industry', 'country']
                
                mapping = {}
                
                with col1:
                    st.write("**必須フィールド:**")
                    for field in required_fields:
                        mapping[field] = st.selectbox(
                            f"{field} ← CSV列", 
                            [""] + list(import_df.columns),
                            key=f"map_{field}"
                        )
                
                with col2:
                    st.write("**オプションフィールド:**")
                    for field in optional_fields:
                        mapping[field] = st.selectbox(
                            f"{field} ← CSV列",
                            [""] + list(import_df.columns),
                            key=f"map_{field}"
                        )
                
                # インポート実行
                if all(mapping[field] for field in required_fields):
                    if st.button("📥 データをインポート"):
                        db = IntegratedEmailDatabase()
                        import_count = 0
                        
                        for _, row in import_df.iterrows():
                            company_data = {
                                'company_id': f"IMPORT_{int(time.time())}_{import_count}",
                            }
                            
                            for field, csv_col in mapping.items():
                                if csv_col:
                                    company_data[field] = str(row[csv_col]).strip()
                            
                            if company_data.get('company_name') and company_data.get('email'):
                                db.save_company(company_data)
                                import_count += 1
                        
                        st.success(f"✅ {import_count}社のデータをインポートしました")
                        st.rerun()
                else:
                    st.warning("⚠️ 必須フィールド（company_name, email, description）のマッピングを完了してください")
                    
            except Exception as e:
                st.error(f"❌ CSVインポートエラー: {str(e)}")
    
    with tab7:
        render_settings_management()
        render_system_statistics()
        
        # 詳細システム情報
        st.subheader("🔧 詳細システム情報")
        
        with st.expander("📊 データベーステーブル情報"):
            db = IntegratedEmailDatabase()
            conn = sqlite3.connect(db.db_path)
            
            try:
                # テーブル一覧
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables_df = pd.read_sql_query(tables_query, conn)
                st.write("**データベーステーブル:**")
                
                for table in tables_df['name']:
                    count_query = f"SELECT COUNT(*) as count FROM {table}"
                    count_result = pd.read_sql_query(count_query, conn)
                    record_count = count_result.iloc[0]['count']
                    st.write(f"• {table}: {record_count}レコード")
                    
            except Exception as e:
                st.error(f"データベース情報取得エラー: {str(e)}")
            finally:
                conn.close()
        
        # データエクスポート
        with st.expander("📤 データエクスポート"):
            export_table = st.selectbox("エクスポートテーブル", 
                                      ["integrated_emails", "companies", "integrated_send_history"])
            
            if st.button("CSV形式でエクスポート"):
                db = IntegratedEmailDatabase()
                conn = sqlite3.connect(db.db_path)
                
                try:
                    export_df = pd.read_sql_query(f"SELECT * FROM {export_table}", conn)
                    csv_data = export_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 CSVファイルをダウンロード",
                        data=csv_data,
                        file_name=f"{export_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    st.success(f"✅ {export_table}テーブルのデータを準備しました")
                    
                except Exception as e:
                    st.error(f"エクスポートエラー: {str(e)}")
                finally:
                    conn.close()

# ===== 送信間隔カスタマイズ対応（旧バージョン互換性） =====
def send_pregenerated_emails_with_interval(company_list: List[Dict], gmail_config: Dict, 
                                          max_emails: int = 50, language: str = 'english',
                                          template_type: str = 'standard', send_interval: int = 60) -> Dict:
    """旧バージョン互換性のための関数 - 新しい再開機能にリダイレクト"""
    return send_pregenerated_emails_with_resume(
        company_list, gmail_config, max_emails, language, template_type, send_interval, False
    )

if __name__ == "__main__":
    main()
