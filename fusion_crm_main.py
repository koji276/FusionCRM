"""
FusionCRM - PicoCELA営業管理システム（Google Sheets専用版）
SQLiteを削除し、Google Sheetsのみに対応
"""

import streamlit as st
import pandas as pd
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import requests

# メール関連のインポート（既存のまま）
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

# 拡張ステータス定義（既存のまま）
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

# ステータス優先度
STATUS_PRIORITY = {
    'Won': 10, 'Negotiation': 9, 'Proposal': 8, 'Qualified': 7,
    'Engaged': 6, 'Replied': 5, 'Contacted': 4, 'New': 3,
    'Dormant': 2, 'Lost': 1
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
            response = requests.get(f"{self.gas_url}?action=test")
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
                response = requests.get(f"{self.gas_url}?action={action}")
            else:
                response = requests.post(
                    self.gas_url,
                    json={"action": action, **data} if data else {"action": action},
                    headers={'Content-Type': 'application/json'}
                )
            
            result = response.json()
            if not result.get('success'):
                raise Exception(result.get('error', 'Unknown error'))
            
            return result
        except Exception as e:
            st.error(f"API呼び出しエラー（{action}）: {str(e)}")
            return None

class ENRDataProcessor:
    """ENRデータ処理クラス（既存のまま）"""
    
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
                
                # フィルタリング
                if status and not df.empty:
                    df = df[df['sales_status'] == status]
                
                if wifi_required is not None and not df.empty:
                    df = df[df['wifi_required'] == wifi_required]
                
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return pd.DataFrame()
    
    def get_status_analytics(self):
        """ステータス分析データ取得"""
        try:
            result = self.api.call_api('get_analytics')
            
            if result and result.get('analytics'):
                analytics = result['analytics']
                
                # ステータス別データフレーム作成
                status_data = []
                for status, count in analytics.get('status_breakdown', {}).items():
                    status_data.append({
                        'status': status,
                        'count': count,
                        'avg_relevance': 0,  # TODO: APIで平均値も返すように修正
                        'wifi_count': 0
                    })
                status_df = pd.DataFrame(status_data)
                
                # WiFi需要データフレーム作成
                wifi_data = []
                for wifi_need, count in analytics.get('wifi_needs_breakdown', {}).items():
                    wifi_data.append({
                        'wifi_required': 1 if wifi_need == 'High' else 0,
                        'count': count,
                        'avg_relevance': 0
                    })
                wifi_df = pd.DataFrame(wifi_data)
                
                return status_df, wifi_df
            
            return pd.DataFrame(), pd.DataFrame()
            
        except Exception as e:
            st.error(f"分析データ取得エラー: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

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
        """単一メール送信（既存のまま）"""
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
    
    def send_bulk_email(self, targets_df, subject, body_template, from_email, from_password, from_name="PicoCELA Inc."):
        """一括メール送信"""
        results = []
        success_count = 0
        error_count = 0
        
        for idx, target in targets_df.iterrows():
            try:
                personalized_body = body_template.replace('{company_name}', str(target.get('company_name', '御社')))
                
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
                
                time.sleep(2)  # Gmail制限対応
                
            except Exception as e:
                error_count += 1
                results.append({
                    'company_name': target.get('company_name', 'Unknown'),
                    'email': target.get('email', 'Unknown'),
                    'status': f"処理エラー: {str(e)}",
                    'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        summary = f"送信完了: 成功 {success_count}件, 失敗 {error_count}件"
        return results, summary
    
    def get_campaign_targets(self, target_status, wifi_required=None, min_relevance=0):
        """キャンペーンターゲット取得"""
        result = self.api.call_api('get_companies')
        
        if result and result.get('companies'):
            df = pd.DataFrame(result['companies'])
            
            # フィルタリング
            if not df.empty:
                df = df[df['sales_status'] == target_status]
                df = df[df['email'].notna() & (df['email'] != '')]
                df = df[df['picocela_relevance_score'] >= min_relevance]
                
                if wifi_required is not None:
                    df = df[df['wifi_required'] == wifi_required]
            
            return df
        
        return pd.DataFrame()
    
    def get_email_templates(self):
        """メールテンプレート（既存のまま）"""
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

# 既存の画面関数はそのまま使用（show_dashboard、show_company_managementなど）
# ただし、SQLite関連の処理は削除

def show_analytics(company_manager):
    """📈 分析・レポート － まだ未実装のためのプレースホルダ"""
    st.header("📈 分析・レポート (準備中)")
    st.info("この機能は現在準備中です。")

def show_dashboard(company_manager):
    """ダッシュボード（Google Sheets版）"""
    st.header("📊 ダッシュボード")
    
    # 基本統計
    all_companies = company_manager.get_companies_by_status()
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
    
    # 統計計算
    try:
        wifi_companies = len(all_companies[all_companies['wifi_required'] == 1])
        high_priority = len(all_companies[all_companies['priority_score'] >= 100])
        engaged_plus = len(all_companies[all_companies['sales_status'].isin(['Engaged', 'Qualified', 'Proposal', 'Negotiation'])])
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
    
    # 分析グラフ
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

# その他の関数（show_company_management、show_email_campaignsなど）も
# 同様にSQLite関連の処理を削除してGoogle Sheets APIを使用するように修正

if __name__ == "__main__":
    main()
