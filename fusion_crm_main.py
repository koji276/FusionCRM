"""
FusionCRM - PicoCELA営業管理システム（Google Sheets専用版）
完全にGoogle Sheetsに対応、SQLite削除
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import requests

# メール関連のインポート（正しい大文字小文字）
EMAIL_AVAILABLE = True
EMAIL_ERROR_MESSAGE = ""

try:
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
except ImportError as e:
    EMAIL_AVAILABLE = False
    EMAIL_ERROR_MESSAGE = f"メールライブラリのインポートエラー: {str(e)}"

# ページ設定
st.set_page_config(
    page_title="FusionCRM - PicoCELA営業管理システム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 拡張ステータス定義
SALES_STATUS = {
    'New': '新規企業',
    'Contacted': '初回連絡済み', 
    'Replied': '返信あり',
    'Engaged': '継続対話中',
    'Qualified': '有望企業確定',
    'Proposal': '提案書提出済み',
    'Negotiation': '契約交渉中',
    'Won': '受注成功',
    'Lost': '失注',
    'Dormant': '休眠中'
}

# PicoCELA関連キーワード
PICOCELA_KEYWORDS = [
    'network', 'mesh', 'wireless', 'wifi', 'connectivity',
    'iot', 'smart', 'digital', 'automation', 'sensor', 'ai',
    'construction', 'building', 'site', 'industrial', 'management',
    'platform', 'solution', 'integration', 'control', 'monitoring'
]

class GoogleSheetsAPI:
    """Google Sheets API（Google Apps Script経由）"""
    
    def __init__(self, gas_url):
        self.gas_url = gas_url
        self._test_connection()
    
    def _test_connection(self):
        """接続テスト"""
        try:
            response = requests.get(f"{self.gas_url}?action=test", timeout=10)
            result = response.json()
            if not result.get('success'):
                raise Exception("Google Apps Script接続エラー")
        except Exception as e:
            st.error(f"接続エラー: {str(e)}")
            raise
    
    def call_api(self, action, method='GET', data=None):
        """API呼び出しの共通メソッド"""
        try:
            if method == 'GET':
                response = requests.get(f"{self.gas_url}?action={action}", timeout=30)
            else:
                response = requests.post(
                    self.gas_url,
                    json={"action": action, **data} if data else {"action": action},
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
            
            result = response.json()
            if not result.get('success'):
                raise Exception(result.get('error', 'Unknown error'))
            
            return result
        except Exception as e:
            st.error(f"API呼び出しエラー（{action}）: {str(e)}")
            return None

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
        """優先度スコア計算"""
        relevance = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        
        priority = relevance
        if wifi_required:
            priority += 50
        
        return min(priority, 150)

class CompanyManager:
    """企業管理クラス（Google Sheets専用版）"""
    
    def __init__(self, api):
        self.api = api
        self._ensure_database()
    
    def _ensure_database(self):
        """データベース初期化確認"""
        result = self.api.call_api('init_database', method='POST')
        if result and result.get('spreadsheet_url'):
            st.session_state.spreadsheet_url = result['spreadsheet_url']
    
    def add_company(self, company_data, user_id="system"):
        """企業追加"""
        try:
            # PicoCELA関連度とWiFi需要を自動計算
            relevance_score = ENRDataProcessor.calculate_picocela_relevance(company_data)
            wifi_required = 1 if ENRDataProcessor.detect_wifi_requirement(company_data) else 0
            priority_score = ENRDataProcessor.calculate_priority_score(company_data)
            
            company_data['picocela_relevance_score'] = relevance_score
            company_data['wifi_required'] = wifi_required
            company_data['priority_score'] = priority_score
            company_data['sales_status'] = company_data.get('sales_status', 'New')
            
            result = self.api.call_api('add_company', method='POST', data={'company': company_data})
            
            if result:
                return result.get('company_id')
            return None
            
        except Exception as e:
            st.error(f"企業追加エラー: {str(e)}")
            return None
    
    def update_status(self, company_id, new_status, user_id, reason="", notes=""):
        """ステータス更新"""
        try:
            result = self.api.call_api('update_status', method='POST', data={
                'company_id': company_id,
                'new_status': new_status,
                'note': f"{reason} - {notes}" if reason else notes
            })
            
            return result is not None
            
        except Exception as e:
            st.error(f"ステータス更新エラー: {str(e)}")
            return False
    
    def get_companies_by_status(self, status=None, wifi_required=None):
        """ステータス別企業取得"""
        try:
            result = self.api.call_api('get_companies')
            
            if result and result.get('companies'):
                df = pd.DataFrame(result['companies'])
                
                # 安全なフィルタリング（カラムの存在確認）
                if status and not df.empty and 'sales_status' in df.columns:
                    df = df[df['sales_status'] == status]
                
                if wifi_required is not None and not df.empty and 'wifi_required' in df.columns:
                    df = df[df['wifi_required'] == wifi_required]
                
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return pd.DataFrame()
    
    def get_all_companies(self):
        """全企業取得"""
        return self.get_companies_by_status()

class EmailCampaignManager:
    """メールキャンペーン管理（Google Sheets版）"""
    
    def __init__(self, api):
        self.api = api
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
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_settings['smtp_server'], self.smtp_settings['smtp_port']) as server:
                if self.smtp_settings['use_tls']:
                    server.starttls(context=context)
                server.login(from_email, from_password)
                server.send_message(msg)
            
            return True, "メール送信成功"
            
        except Exception as e:
            return False, f"メール送信エラー: {str(e)}"
    
    def get_email_templates(self):
        """メールテンプレート"""
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

貴社の事業にお役立ていただけるソリューションがあるかもしれません。
ぜひ一度お話をお聞かせください。

株式会社PicoCELA
営業部"""
            }
        }

def get_google_sheets_api():
    """Google Sheets API取得"""
    # Streamlit secretsから取得を試みる
    if 'google_apps_script_url' in st.secrets:
        gas_url = st.secrets['google_apps_script_url']
    # セッション状態から取得
    elif 'gas_url' in st.session_state:
        gas_url = st.session_state.gas_url
    else:
        gas_url = None
    
    if gas_url:
        try:
            return GoogleSheetsAPI(gas_url)
        except:
            return None
    
    return None

def setup_google_sheets_connection():
    """Google Sheets接続設定UI"""
    st.markdown("## 🚀 Google Sheets接続設定")
    st.info("Google Apps Script URLを設定してください")
    
    gas_url = st.text_input(
        "Google Apps Script URL",
        placeholder="https://script.google.com/macros/s/xxx/exec",
        help="Google Apps Scriptをデプロイして取得したURLを入力"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔗 接続テスト", type="primary", use_container_width=True):
            if gas_url:
                try:
                    api = GoogleSheetsAPI(gas_url)
                    st.success("✅ 接続成功！")
                    st.session_state.gas_url = gas_url
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 接続失敗: {str(e)}")
            else:
                st.warning("URLを入力してください")
    
    with col2:
        if st.button("📖 セットアップガイド", use_container_width=True):
            st.markdown("""
            ### 📋 Google Apps Script設定手順
            1. [Google Apps Script](https://script.google.com/)にアクセス
            2. 新しいプロジェクトを作成
            3. 提供されたコードをコピー&ペースト
            4. デプロイ → 新しいデプロイ
            5. ウェブアプリとして公開（全員にアクセス許可）
            6. URLをコピーして上記に貼り付け
            """)

def show_dashboard(company_manager):
    """ダッシュボード"""
    st.header("📊 ダッシュボード")
    
    # 基本統計
    all_companies = company_manager.get_all_companies()
    total_companies = len(all_companies)
    
    if total_companies == 0:
        st.info("📋 企業データがありません。サンプルデータを追加してテストしてください。")
        
        if st.button("🚀 サンプルデータを追加", type="primary"):
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
                    'notes': 'mesh network, construction tech, digital solutions',
                    'source': 'Sample Data'
                }
            ]
            
            success_count = 0
            for company in sample_companies:
                result = company_manager.add_company(company, 'system')
                if result:
                    success_count += 1
            
            if success_count > 0:
                st.success(f"✅ {success_count}社のサンプルデータを追加しました！")
                st.rerun()
        
        return
    
    # 統計計算（安全にカラム確認）
    try:
        wifi_companies = len(all_companies[all_companies['wifi_required'] == 1]) if 'wifi_required' in all_companies.columns else 0
        high_priority = len(all_companies[all_companies['priority_score'] >= 100]) if 'priority_score' in all_companies.columns else 0
        engaged_plus = len(all_companies[all_companies['sales_status'].isin(['Engaged', 'Qualified', 'Proposal', 'Negotiation'])]) if 'sales_status' in all_companies.columns else 0
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
    
    # 企業一覧表示
    if not all_companies.empty:
        st.subheader("📋 企業一覧")
        
        # 表示用データ準備
        display_columns = ['company_name', 'sales_status', 'industry']
        if 'wifi_required' in all_companies.columns:
            display_columns.append('wifi_required')
        if 'priority_score' in all_companies.columns:
            display_columns.append('priority_score')
        
        display_df = all_companies[display_columns] if all(col in all_companies.columns for col in display_columns) else all_companies
        
        st.dataframe(display_df, use_container_width=True)

def show_company_management(company_manager):
    """企業管理"""
    st.header("🏢 企業管理")
    
    tab1, tab2 = st.tabs(["📝 企業追加", "📋 企業一覧"])
    
    with tab1:
        st.subheader("新規企業追加")
        
        with st.form("add_company_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("企業名*", placeholder="例: 株式会社サンプル")
                email = st.text_input("メールアドレス", placeholder="contact@example.com")
                industry = st.text_input("業界", placeholder="建設業")
            
            with col2:
                phone = st.text_input("電話番号", placeholder="03-1234-5678")
                website_url = st.text_input("ウェブサイト", placeholder="https://example.com")
                source = st.selectbox("情報源", ["Manual", "ENR Import", "Web Research", "Referral"])
            
            notes = st.text_area("備考・メモ", placeholder="企業の特徴、WiFi需要、その他重要な情報")
            
            submitted = st.form_submit_button("🏢 企業を追加", type="primary", use_container_width=True)
            
            if submitted:
                if company_name:
                    company_data = {
                        'company_name': company_name,
                        'email': email,
                        'phone': phone,
                        'website_url': website_url,
                        'industry': industry,
                        'notes': notes,
                        'source': source
                    }
                    
                    company_id = company_manager.add_company(company_data, 'user')
                    
                    if company_id:
                        st.success(f"✅ 企業「{company_name}」を追加しました！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 企業追加に失敗しました")
                else:
                    st.error("❌ 企業名は必須です")
    
    with tab2:
        st.subheader("企業一覧")
        
        companies_df = company_manager.get_all_companies()
        
        if not companies_df.empty:
            # フィルター
            col1, col2 = st.columns(2)
            
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
            
            # フィルタリング適用
            filtered_df = companies_df.copy()
            
            if status_filter != "すべて" and 'sales_status' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['sales_status'] == status_filter]
            
            if wifi_filter != "すべて" and 'wifi_required' in filtered_df.columns:
                wifi_value = 1 if wifi_filter == "WiFi必要" else 0
                filtered_df = filtered_df[filtered_df['wifi_required'] == wifi_value]
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # ステータス更新機能
            if not filtered_df.empty:
                st.subheader("ステータス更新")
                
                with st.form("update_status_form"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        company_options = filtered_df['company_name'].tolist() if 'company_name' in filtered_df.columns else []
                        selected_company = st.selectbox("企業選択", company_options)
                    
                    with col2:
                        new_status = st.selectbox("新しいステータス", list(SALES_STATUS.keys()))
                    
                    with col3:
                        notes = st.text_input("更新理由・備考")
                    
                    if st.form_submit_button("📈 ステータス更新", type="primary"):
                        if selected_company:
                            # 企業IDを取得
                            company_row = filtered_df[filtered_df['company_name'] == selected_company].iloc[0]
                            company_id = company_row.get('company_id', company_row.get('id'))
                            
                            if company_manager.update_status(company_id, new_status, 'user', notes=notes):
                                st.success(f"✅ {selected_company}のステータスを{SALES_STATUS[new_status]}に更新しました")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ ステータス更新に失敗しました")
        else:
            st.info("企業データがありません。まず企業を追加してください。")

def show_email_campaigns(email_manager, company_manager):
    """メールキャンペーン"""
    st.header("📧 メールキャンペーン")
    st.info("Google Sheets版では基本的なメール機能のみ提供します")
    
    templates = email_manager.get_email_templates()
    
    st.subheader("📝 メールテンプレート")
    
    template_choice = st.selectbox(
        "テンプレート選択",
        list(templates.keys()),
        format_func=lambda x: "WiFi需要企業向け" if x == "wifi_needed" else "一般企業向け"
    )
    
    selected_template = templates[template_choice]
    
    st.text_area("件名", value=selected_template["subject"], disabled=True)
    st.text_area("本文", value=selected_template["body"], height=300, disabled=True)

def show_analytics(company_manager):
    """分析・レポート"""
    st.header("📈 分析・レポート")
    st.info("この機能は現在準備中です。")

def show_data_import(company_manager):
    """データインポート"""
    st.header("📁 データインポート")
    st.info("この機能は現在準備中です。")

# メイン関数
def main():
    st.title("🚀 FusionCRM - PicoCELA営業管理システム")
    st.markdown("**☁️ Google Sheets版（クラウド対応）**")
    
    # Google Sheets API取得
    api = get_google_sheets_api()
    
    if api is None:
        setup_google_sheets_connection()
        return
    
    # マネージャー初期化
    company_manager = CompanyManager(api)
    email_manager = EmailCampaignManager(api)
    
    # Google Sheetsリンク表示
    if 'spreadsheet_url' in st.session_state:
        st.success(f"✅ Google Sheets接続中 | [📊 スプレッドシートを開く]({st.session_state.spreadsheet_url})")
    
    # サイドバー
    st.sidebar.title("🌟 FusionCRM")
    st.sidebar.markdown("☁️ **Google Sheets版**")
    
    # 接続情報表示
    if 'gas_url' in st.session_state:
        st.sidebar.success("✅ 接続済み")
        if st.sidebar.button("🔌 切断"):
            del st.session_state.gas_url
            st.rerun()
    
    page = st.sidebar.selectbox(
        "📋 メニュー",
        ["📊 ダッシュボード", "🏢 企業管理", "📧 メールキャンペーン", 
         "📈 分析・レポート", "📁 データインポート"]
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
    elif page == "📁 データインポート":
        show_data_import(company_manager)

if __name__ == "__main__":
    main()
