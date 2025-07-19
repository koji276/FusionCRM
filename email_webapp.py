"""
統合メールシステム - 日本語個別生成 + 英語バッチ処理
既存のemail_webapp.pyに統合する完全版
"""

import openai
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
        if api_key:
            openai.api_key = api_key
        
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
        company_name = company_data.get('company_name', '')
        description = company_data.get('description', '')
        
        if not description or description.strip() == "":
            return self._create_fallback_email(company_name)
        
        try:
            # GPT-3.5でカスタマイズ部分のみ生成
            response = openai.ChatCompletion.create(
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
                generated_at TEXT,
                UNIQUE(company_id, language) ON CONFLICT REPLACE
            )
        """)
        
        # 送信履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrated_send_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT,
                company_name TEXT,
                language TEXT,
                subject TEXT,
                sent_at TEXT,
                status TEXT,
                email_address TEXT
            )
        """)
        
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
            'suggested_title': email_data.get('suggested_title')
        }
        
        cursor.execute("""
            INSERT OR REPLACE INTO integrated_emails 
            (company_id, company_name, language, subject, email_body, customization_data,
             api_cost, tokens_used, customization_method, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email_data.get('company_id'),
            email_data.get('company_name'),
            email_data.get('language', 'english'),
            email_data.get('subject'),
            email_data.get('customized_email'),
            json.dumps(customization_data),
            email_data.get('api_cost'),
            email_data.get('tokens_used'),
            email_data.get('customization_method'),
            email_data.get('generated_at')
        ))
        
        conn.commit()
        conn.close()
    
    def get_generated_email(self, company_id: str, language: str = 'english') -> Optional[Dict]:
        """生成済みメールを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM integrated_emails WHERE company_id = ? AND language = ?
        """, (company_id, language))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            email_data = dict(zip(columns, result))
            # JSONデータを展開
            if email_data['customization_data']:
                customization = json.loads(email_data['customization_data'])
                email_data.update(customization)
            return email_data
        return None

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

# ===== 瞬時送信システム =====
def send_pregenerated_emails(company_list: List[Dict], gmail_config: Dict, 
                            max_emails: int = 50, language: str = 'english') -> Dict:
    """事前生成メールの瞬時送信"""
    db = IntegratedEmailDatabase()
    
    st.write(f"📤 事前生成{language}メールの送信開始 (最大{max_emails}社)")
    
    sent_count = 0
    failed_count = 0
    target_companies = company_list[:max_emails]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, company in enumerate(target_companies):
        # 進捗更新
        progress = (i + 1) / len(target_companies)
        progress_bar.progress(progress)
        status_text.text(f"送信中: {company.get('company_name', 'Unknown')} ({i+1}/{len(target_companies)})")
        
        # データベースからメール取得
        company_id = company.get('company_id')
        stored_email = db.get_generated_email(company_id, language)
        
        if stored_email:
            try:
                # 瞬時送信
                success = send_email_smtp(
                    to_email=company.get('email'),
                    subject=stored_email['subject'],
                    body=stored_email['email_body'],
                    gmail_config=gmail_config
                )
                
                if success:
                    sent_count += 1
                    st.success(f"✅ {company.get('company_name')} - 送信成功")
                else:
                    failed_count += 1
                    st.error(f"❌ {company.get('company_name')} - 送信失敗")
                    
            except Exception as e:
                failed_count += 1
                st.error(f"❌ {company.get('company_name')} - エラー: {str(e)[:30]}")
        else:
            failed_count += 1
            st.warning(f"⚠️ {company.get('company_name')} - 事前生成メールなし")
        
        # 送信間隔
        if i < len(target_companies) - 1:
            time.sleep(60)
    
    summary = {
        'total_attempted': len(target_companies),
        'successful_sends': sent_count,
        'failed_sends': failed_count,
        'success_rate': (sent_count / len(target_companies)) * 100 if target_companies else 0
    }
    
    st.write(f"### 📊 送信完了")
    st.write(f"**成功**: {sent_count}/{len(target_companies)} ({summary['success_rate']:.1f}%)")
    
    return summary

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
                'phone': str(row.get('phone', '')).strip()
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
                'phone': ''
            }
        ]

# ===== メインUI =====
def render_integrated_email_system():
    """統合メールシステムのメインUI"""
    
    st.set_page_config(page_title="PicoCELA統合メールシステム", layout="wide")
    st.title("🌐 PicoCELA統合メールシステム")
    st.write("**日本語個別生成 + 英語バッチ処理システム**")
    
    # サイドバーでモード選択
    with st.sidebar:
        st.header("🔧 システム設定")
        
        # Gmail設定
        st.subheader("Gmail設定")
        gmail_user = st.text_input("Gmailアドレス", value="tokuda@picocela.com")
        gmail_password = st.text_input("アプリパスワード", type="password", value="bmzr lbrs cbbn jtmr")
        
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
        
        # OpenAI API設定
        st.subheader("OpenAI API設定")
        api_key = st.text_input("API Key", type="password")
        if api_key:
            openai.api_key = api_key
            st.success("✅ API設定完了")
        else:
            st.warning("⚠️ OpenAI API Keyが必要です")
    
    # メインタブ
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 英語バッチ生成", "📊 生成結果確認", "📤 瞬時送信", "📧 日本語メール"])
    
    with tab1:
        st.subheader("🌍 英語パートナーシップメール バッチ生成")
        
        st.write("**ベースメール特徴**:")
        st.write("- ✅ NASDAQ上場アピール + 技術仕様")
        st.write("- ✅ パートナーシップ提案（売り込みではない）")
        st.write("- ✅ 相手事業に特化した環境リスト")
        st.write("- ✅ 相互価値提案")
        
        col1, col2 = st.columns(2)
        with col1:
            max_companies = st.number_input("生成対象企業数", min_value=1, max_value=1000, value=100)
        with col2:
            estimated_cost = max_companies * 0.0004 * 150
            st.metric("予想コスト", f"約{estimated_cost:.0f}円")
        
        if st.button("🚀 英語バッチ生成開始", type="primary") and api_key:
            companies_data = get_companies_from_sheets()
            
            if companies_data:
                summary = generate_english_emails_batch(companies_data, max_companies)
                st.session_state['last_batch_summary'] = summary
            else:
                st.error("企業データが取得できませんでした")
    
    with tab2:
        st.subheader("📊 生成済みメール確認")
        
        db = IntegratedEmailDatabase()
        conn = sqlite3.connect(db.db_path)
        df = pd.read_sql_query("""
            SELECT company_name, language, customization_method, api_cost, generated_at 
            FROM integrated_emails ORDER BY generated_at DESC
        """, conn)
        conn.close()
        
        if not df.empty:
            st.write(f"**生成済みメール**: {len(df)}通")
            
            # 言語別フィルター
            language_filter = st.selectbox("言語フィルター", ["all", "english", "japanese"])
            if language_filter != "all":
                df_filtered = df[df['language'] == language_filter]
            else:
                df_filtered = df
            
            st.dataframe(df_filtered.head(20))
            
            # 詳細表示
            if st.button("サンプルメール表示"):
                sample_email = db.get_generated_email(df_filtered.iloc[0]['company_name'], 'english')
                if sample_email:
                    st.text_area("サンプルメール", sample_email['email_body'], height=400)
        else:
            st.warning("生成済みメールがありません")
    
    with tab3:
        st.subheader("📤 事前生成メール瞬時送信")
        
        if gmail_config:
            col1, col2 = st.columns(2)
            with col1:
                max_sends = st.number_input("最大送信数", min_value=1, max_value=100, value=20)
            with col2:
                language = st.selectbox("送信言語", ["english", "japanese"])
            
            if st.button("📤 瞬時送信開始", type="primary"):
                companies_data = get_companies_from_sheets()
                
                if companies_data:
                    summary = send_pregenerated_emails(companies_data, gmail_config, max_sends, language)
                    st.session_state['last_send_summary'] = summary
                else:
                    st.error("企業データが取得できませんでした")
        else:
            st.warning("Gmail設定を完了してください")
    
    with tab4:
        st.subheader("📧 日本語メール（個別生成）")
        st.write("既存の日本語個別生成システムをここに統合")
        st.info("日本語メール機能は既存システムを使用してください")
        
        # 簡易日本語メール機能（既存システム統合用）
        if st.button("日本語メール生成テスト"):
            st.write("日本語個別生成機能は既存のemail_webapp.pyシステムを使用してください")

# ===== 企業データ手動追加機能 =====
def render_company_data_management():
    """企業データ手動管理機能"""
    st.subheader("📝 企業データ管理")
    
    with st.expander("➕ 企業データ手動追加"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_company_name = st.text_input("企業名")
            new_email = st.text_input("メールアドレス")
        
        with col2:
            new_description = st.text_area("事業説明", height=100)
            new_website = st.text_input("ウェブサイト")
        
        if st.button("企業を追加") and new_company_name and new_email:
            # セッション状態に追加
            if 'manual_companies' not in st.session_state:
                st.session_state['manual_companies'] = []
            
            new_company = {
                'company_id': f"MANUAL_{len(st.session_state['manual_companies']):03d}",
                'company_name': new_company_name,
                'email': new_email,
                'description': new_description,
                'website': new_website,
                'phone': ''
            }
            
            st.session_state['manual_companies'].append(new_company)
            st.success(f"✅ {new_company_name} を追加しました")
    
    # 手動追加済み企業表示
    if 'manual_companies' in st.session_state and st.session_state['manual_companies']:
        st.write("**手動追加済み企業:**")
        for company in st.session_state['manual_companies']:
            st.write(f"- {company['company_name']} ({company['email']})")

# ===== システム統計表示 =====
def render_system_statistics():
    """システム統計表示"""
    st.subheader("📈 システム統計")
    
    db = IntegratedEmailDatabase()
    conn = sqlite3.connect(db.db_path)
    
    # 統計データ取得
    stats_query = """
        SELECT 
            language,
            customization_method,
            COUNT(*) as count,
            SUM(api_cost) as total_cost,
            AVG(api_cost) as avg_cost
        FROM integrated_emails 
        GROUP BY language, customization_method
    """
    
    try:
        stats_df = pd.read_sql_query(stats_query, conn)
        
        if not stats_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_emails = stats_df['count'].sum()
                st.metric("総生成数", f"{total_emails}通")
            
            with col2:
                total_cost = stats_df['total_cost'].sum()
                st.metric("総コスト", f"${total_cost:.3f}")
            
            with col3:
                avg_cost = stats_df['avg_cost'].mean()
                st.metric("平均コスト", f"${avg_cost:.4f}")
            
            # 詳細統計表
            st.write("**詳細統計:**")
            st.dataframe(stats_df)
        else:
            st.info("まだ生成されたメールがありません")
            
    except Exception as e:
        st.error(f"統計取得エラー: {str(e)}")
    
    finally:
        conn.close()

# ===== 設定管理 =====
def render_settings_management():
    """設定管理機能"""
    st.subheader("⚙️ システム設定")
    
    with st.expander("📧 メールテンプレート設定"):
        st.write("**現在のベースメール特徴:**")
        st.write("- NASDAQ上場アピール")
        st.write("- パートナーシップ提案")
        st.write("- 技術仕様明記")
        st.write("- 相手事業特化環境リスト")
        
        if st.button("テンプレート編集"):
            st.info("テンプレート編集機能は今後実装予定")
    
    with st.expander("🔧 API設定"):
        st.write("**OpenAI API使用量:**")
        
        # 今日の使用量計算
        db = IntegratedEmailDatabase()
        conn = sqlite3.connect(db.db_path)
        
        today = datetime.now().strftime('%Y-%m-%d')
        usage_query = f"""
            SELECT COUNT(*) as count, SUM(api_cost) as cost
            FROM integrated_emails 
            WHERE date(generated_at) = '{today}'
        """
        
        try:
            usage_df = pd.read_sql_query(usage_query, conn)
            if not usage_df.empty and usage_df.iloc[0]['count'] > 0:
                today_count = usage_df.iloc[0]['count']
                today_cost = usage_df.iloc[0]['cost'] or 0
                st.write(f"今日の生成数: {today_count}通")
                st.write(f"今日のコスト: ${today_cost:.4f}")
            else:
                st.write("今日はまだ生成していません")
        except:
            st.write("使用量データ取得エラー")
        finally:
            conn.close()

# ===== メインアプリケーション =====
def main():
    """メインアプリケーション"""
    
    # ページ設定
    st.set_page_config(
        page_title="PicoCELA統合メールシステム", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # タイトル
    st.title("🌐 PicoCELA統合メールシステム")
    st.markdown("**日本語個別生成 + 英語バッチ処理システム**")
    
    # サイドバー設定
    with st.sidebar:
        st.header("🔧 システム設定")
        
        # Gmail設定
        st.subheader("📧 Gmail設定")
        gmail_user = st.text_input("Gmailアドレス", value="tokuda@picocela.com")
        gmail_password = st.text_input("アプリパスワード", type="password", 
                                     help="既存のアプリパスワード: bmzr lbrs cbbn jtmr")
        
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
        
        # OpenAI API設定
        st.subheader("🤖 OpenAI API設定")
        api_key = st.text_input("API Key", type="password",
                               help="GPT-3.5使用のためのAPIキー")
        
        if api_key:
            openai.api_key = api_key
            st.success("✅ API設定完了")
        else:
            st.warning("⚠️ OpenAI API Keyが必要です")
        
        # システム統計（サイドバー表示）
        st.subheader("📊 クイック統計")
        try:
            db = IntegratedEmailDatabase()
            conn = sqlite3.connect(db.db_path)
            
            count_query = "SELECT COUNT(*) as total FROM integrated_emails"
            result = pd.read_sql_query(count_query, conn)
            total_generated = result.iloc[0]['total'] if not result.empty else 0
            
            cost_query = "SELECT SUM(api_cost) as total_cost FROM integrated_emails"
            cost_result = pd.read_sql_query(cost_query, conn)
            total_cost = cost_result.iloc[0]['total_cost'] if not cost_result.empty and cost_result.iloc[0]['total_cost'] else 0
            
            st.metric("生成済みメール", f"{total_generated}通")
            st.metric("総使用コスト", f"${total_cost:.3f}")
            
            conn.close()
        except:
            st.metric("生成済みメール", "0通")
            st.metric("総使用コスト", "$0.000")
    
    # メインコンテンツ
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌍 英語バッチ生成", 
        "📊 生成結果確認", 
        "📤 瞬時送信", 
        "📝 データ管理", 
        "⚙️ 設定"
    ])
    
    with tab1:
        st.subheader("🌍 英語パートナーシップメール バッチ生成")
        
        # システム説明
        with st.expander("ℹ️ システム概要"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**ベースメール特徴:**")
                st.write("- ✅ NASDAQ上場アピール")
                st.write("- ✅ 具体的技術仕様（10ホップ、2-3ms遅延）")
                st.write("- ✅ 数値効果（90%ケーブル削減）")
                st.write("- ✅ パートナーシップ提案（売り込みではない）")
            
            with col2:
                st.write("**カスタマイズ内容:**")
                st.write("- 🎯 相手事業に特化した環境リスト")
                st.write("- 🎯 相互価値提案の最適化")
                st.write("- 🎯 適切な宛先タイトル選択")
                st.write("- 🎯 業界理解の証明")
        
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
        if st.button("🚀 英語バッチ生成開始", type="primary") and api_key:
            if gmail_config:
                companies_data = get_companies_from_sheets()
                
                if companies_data and len(companies_data) > 0:
                    st.write(f"📋 {len(companies_data)}社のデータを取得しました")
                    summary = generate_english_emails_batch(companies_data, max_companies)
                    st.session_state['last_batch_summary'] = summary
                else:
                    st.error("❌ 企業データが取得できませんでした")
            else:
                st.error("❌ Gmail設定を完了してください")
        elif not api_key:
            st.warning("⚠️ OpenAI API Keyを設定してください")
    
    with tab2:
        st.subheader("📊 生成済みメール確認")
        
        db = IntegratedEmailDatabase()
        conn = sqlite3.connect(db.db_path)
        
        try:
            df = pd.read_sql_query("""
                SELECT company_name, language, customization_method, 
                       api_cost, generated_at, subject
                FROM integrated_emails 
                ORDER BY generated_at DESC
            """, conn)
            
            if not df.empty:
                st.write(f"**生成済みメール**: {len(df)}通")
                
                # フィルター
                col1, col2 = st.columns(2)
                with col1:
                    language_filter = st.selectbox("言語フィルター", ["all", "english", "japanese"])
                with col2:
                    method_filter = st.selectbox("生成方法", ["all", "gpt35", "fallback"])
                
                # フィルター適用
                df_filtered = df.copy()
                if language_filter != "all":
                    df_filtered = df_filtered[df_filtered['language'] == language_filter]
                if method_filter != "all":
                    df_filtered = df_filtered[df_filtered['customization_method'] == method_filter]
                
                # データ表示
                st.dataframe(df_filtered.head(20), use_container_width=True)
                
                # サンプルメール表示
                if len(df_filtered) > 0:
                    st.subheader("📧 サンプルメール表示")
                    
                    selected_company = st.selectbox(
                        "メール表示する企業を選択",
                        df_filtered['company_name'].tolist()
                    )
                    
                    if st.button("メール内容を表示"):
                        sample_email = db.get_generated_email(selected_company, 'english')
                        if sample_email:
                            st.write(f"**件名**: {sample_email['subject']}")
                            st.text_area("メール本文", sample_email['email_body'], height=400)
                            
                            # カスタマイズ詳細
                            with st.expander("カスタマイズ詳細"):
                                st.write(f"**環境リスト**: {sample_email.get('partnership_environments', 'N/A')}")
                                st.write(f"**価値提案**: {sample_email.get('partnership_value', 'N/A')}")
                                st.write(f"**推奨タイトル**: {sample_email.get('suggested_title', 'N/A')}")
            else:
                st.warning("⚠️ 生成済みメールがありません。まず「英語バッチ生成」タブで生成してください。")
                
        except Exception as e:
            st.error(f"❌ データベースエラー: {str(e)}")
        finally:
            conn.close()
    
    with tab3:
        st.subheader("📤 事前生成メール瞬時送信")
        
        if gmail_config:
            col1, col2 = st.columns(2)
            with col1:
                max_sends = st.number_input("最大送信数", min_value=1, max_value=100, value=20)
            with col2:
                language = st.selectbox("送信言語", ["english", "japanese"])
            
            # 送信可能メール数確認
            db = IntegratedEmailDatabase()
            conn = sqlite3.connect(db.db_path)
            
            try:
                available_query = f"""
                    SELECT COUNT(*) as count 
                    FROM integrated_emails 
                    WHERE language = '{language}'
                """
                available_df = pd.read_sql_query(available_query, conn)
                available_count = available_df.iloc[0]['count'] if not available_df.empty else 0
                
                st.info(f"📬 送信可能メール数: {available_count}通 ({language})")
                
                if available_count > 0:
                    estimated_send_time = max_sends * 1.1  # 60秒間隔 + 処理時間
                    st.write(f"⏱️ 予想送信時間: {estimated_send_time:.1f}分")
                    
                    if st.button("📤 瞬時送信開始", type="primary"):
                        companies_data = get_companies_from_sheets()
                        
                        if companies_data:
                            summary = send_pregenerated_emails(companies_data, gmail_config, max_sends, language)
                            st.session_state['last_send_summary'] = summary
                        else:
                            st.error("❌ 企業データが取得できませんでした")
                else:
                    st.warning(f"⚠️ {language}メールが生成されていません。まず生成してください。")
                    
            except Exception as e:
                st.error(f"❌ 送信可能数確認エラー: {str(e)}")
            finally:
                conn.close()
        else:
            st.warning("⚠️ Gmail設定を完了してください")
    
    with tab4:
        render_company_data_management()
    
    with tab5:
        render_settings_management()
        render_system_statistics()

if __name__ == "__main__":
    main()
