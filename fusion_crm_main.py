"""
FusionCRM - PicoCELA営業管理システム（Google Sheets専用版）
完全修正版 - 接続問題解決、自動接続、拡張ステータス管理対応
Version: 6.0 (2025年7月18日)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import requests
import os  # 既存インポートの後に1行追加

# メール関連のインポート
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
    """Google Sheets API（Google Apps Script経由）- 完全修正版"""
    
    def __init__(self, gas_url):
        self.gas_url = gas_url
        self._connection_tested = False
        self._connection_status = "未テスト"
    
    def _lazy_test_connection(self):
        """遅延接続テスト（実際の使用時に実行）"""
        if self._connection_tested:
            return True
            
        try:
            # シンプルなPOSTリクエストでテスト
            response = requests.post(
                self.gas_url,
                json={"action": "init_database"},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self._connection_tested = True
                self._connection_status = "接続成功"
                return True
            else:
                self._connection_status = f"HTTP {response.status_code}"
                return False
                
        except Exception as e:
            self._connection_status = f"エラー: {str(e)}"
            return False
    
    def call_api(self, action, method='GET', data=None):
        """API呼び出しの共通メソッド（完全修正版）"""
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
            
            # レスポンス確認
            if response.status_code != 200:
                st.warning(f"HTTP {response.status_code}: サーバー応答エラー")
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            # JSON解析
            try:
                result = response.json()
            except json.JSONDecodeError:
                st.warning("非JSON応答を受信 - Google Apps Scriptの設定を確認してください")
                return {"success": False, "error": "Invalid JSON response"}
            
            # 成功確認
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                if action not in ['test', 'init_database']:  # テスト系は警告のみ
                    st.error(f"API エラー（{action}）: {error_msg}")
                return result
            
            return result
            
        except requests.exceptions.Timeout:
            st.error(f"タイムアウト（{action}）: 30秒以内に応答なし")
            return {"success": False, "error": "Timeout"}
        except requests.exceptions.RequestException as e:
            st.error(f"ネットワークエラー（{action}）: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            st.error(f"予期しないエラー（{action}）: {str(e)}")
            return {"success": False, "error": str(e)}

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
        if result and result.get('success') and result.get('spreadsheet_url'):
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
            
            if result and result.get('success'):
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
            
            return result and result.get('success')
            
        except Exception as e:
            st.error(f"ステータス更新エラー: {str(e)}")
            return False
    
    def get_companies_by_status(self, status=None, wifi_required=None):
        """ステータス別企業取得"""
        try:
            result = self.api.call_api('get_companies')
            
            if result and result.get('success') and result.get('companies'):
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
    """Google Sheets API取得（完全修正版）"""
    
    # 優先順位1: Streamlit secrets
    if 'google_apps_script_url' in st.secrets:
        gas_url = st.secrets['google_apps_script_url']
        try:
            # 接続テストなしでAPIオブジェクトを作成
            api = GoogleSheetsAPI(gas_url)
            st.session_state.gas_url = gas_url
            return api
        except Exception as e:
            st.error(f"Secrets設定のURL初期化エラー: {str(e)}")
    
    # 優先順位2: セッション状態
    elif 'gas_url' in st.session_state:
        gas_url = st.session_state.gas_url
        try:
            return GoogleSheetsAPI(gas_url)
        except Exception as e:
            st.error(f"保存済みURL初期化エラー: {str(e)}")
            del st.session_state.gas_url
    
    # 優先順位3: 手動設定が必要
    return None

def setup_google_sheets_connection():
    """Google Sheets接続設定UI（完全修正版）"""
    st.markdown("## 🚀 Google Sheets接続設定")
    
    # 既存のSecrets設定を確認
    if 'google_apps_script_url' in st.secrets:
        st.success("✅ Streamlit Secretsに設定済み")
        st.info("管理者によってURLが設定されているため、手動設定は不要です。")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 基本接続テスト
            if st.button("🔗 基本接続テスト", type="primary", use_container_width=True):
                with st.spinner("接続テスト中..."):
                    try:
                        api = GoogleSheetsAPI(st.secrets['google_apps_script_url'])
                        
                        # 実際のAPI呼び出しでテスト
                        result = api.call_api('init_database', method='POST')
                        
                        if result and result.get('success'):
                            st.success("✅ 接続成功！Google Sheetsとの連携が正常に動作しています。")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ 接続は可能ですが、Google Apps Scriptの応答に問題があります。")
                            st.info("アプリは使用可能です。問題が続く場合は管理者にお問い合わせください。")
                            
                    except Exception as e:
                        st.error(f"❌ 接続テストエラー: {str(e)}")
                        st.info("💡 強制的にアプリを開始することも可能です。")
        
        with col2:
            # 強制開始オプション
            if st.button("🚀 強制的にアプリを開始", type="secondary", use_container_width=True):
                # 強制的にセッションに保存
                st.session_state.gas_url = st.secrets['google_apps_script_url']
                st.success("🚀 強制的にアプリを開始しました。")
                st.info("接続に問題がある場合でも、基本機能は使用できます。")
                time.sleep(1)
                st.rerun()
        
        # 設定詳細表示
        with st.expander("🔧 設定詳細"):
            st.code(f"URL: {st.secrets['google_apps_script_url'][:50]}...", language="text")
            st.markdown("**管理者向け**: Streamlit Cloud Secretsで設定済み")
        
        return
    
    # 手動設定UI
    st.info("初回セットアップ：Google Apps Script URLを設定してください")
    
    default_url = st.session_state.get('last_attempted_url', '')
    
    gas_url = st.text_input(
        "Google Apps Script URL",
        value=default_url,
        placeholder="https://script.google.com/macros/s/xxx/exec",
        help="Google Apps Scriptをデプロイして取得したURLを入力"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔗 接続テスト", type="primary", use_container_width=True):
            if gas_url:
                st.session_state.last_attempted_url = gas_url
                
                with st.spinner("接続テスト中..."):
                    try:
                        api = GoogleSheetsAPI(gas_url)
                        result = api.call_api('init_database', method='POST')
                        
                        if result and result.get('success'):
                            st.success("✅ 接続成功！")
                            st.session_state.gas_url = gas_url
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning("⚠️ 接続テストに問題がありますが、アプリは使用可能です。")
                            if st.button("続行する"):
                                st.session_state.gas_url = gas_url
                                st.rerun()
                                
                    except Exception as e:
                        st.error(f"❌ 接続失敗: {str(e)}")
                        if st.button("エラーを無視して続行"):
                            st.session_state.gas_url = gas_url
                            st.rerun()
            else:
                st.warning("URLを入力してください")
    
    with col2:
        if st.button("📖 セットアップガイド", use_container_width=True):
            show_setup_guide()

def show_setup_guide():
    """セットアップガイド表示"""
    st.markdown("""
    ### 📋 Google Apps Script設定手順
    
    #### 🔧 管理者向け（推奨）
    1. Google Apps Scriptを設定後、Streamlit Cloud Secretsに保存
    2. 全ユーザーが自動的に接続できるようになります
    
    #### 👤 個人ユーザー向け
    1. [Google Apps Script](https://script.google.com/)にアクセス
    2. 新しいプロジェクトを作成
    3. 提供されたコードをコピー&ペースト
    4. デプロイ → 新しいデプロイ
    5. ウェブアプリとして公開（全員にアクセス許可）
    6. URLをコピーして上記に貼り付け
    
    #### 🔒 セキュリティ注意
    - URLは機密情報として扱ってください
    - 共有環境では管理者設定を推奨します
    """)

def show_connection_status():
    """接続状況表示"""
    if 'google_apps_script_url' in st.secrets:
        st.sidebar.success("🔒 管理者設定済み")
    elif 'gas_url' in st.session_state:
        st.sidebar.success("✅ 接続済み")
        if st.sidebar.button("🔌 切断"):
            del st.session_state.gas_url
            if 'last_attempted_url' in st.session_state:
                del st.session_state.last_attempted_url
            st.rerun()
    else:
        st.sidebar.warning("⚠️ 未接続")

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
        st.subheader("📋 企業一覧（最新10社）")
        
        # 表示用データ準備
        display_columns = ['company_name', 'sales_status']
        if 'industry' in all_companies.columns:
            display_columns.append('industry')
        if 'wifi_required' in all_companies.columns:
            display_columns.append('wifi_required')
        if 'priority_score' in all_companies.columns:
            display_columns.append('priority_score')
        
        display_df = all_companies[display_columns].tail(10) if all(col in all_companies.columns for col in display_columns) else all_companies.tail(10)
        
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
                    
                    with st.spinner("企業を追加中..."):
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
                st.subheader("📈 ステータス更新")
                
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
                            
                            with st.spinner("ステータス更新中..."):
                                success = company_manager.update_status(company_id, new_status, 'user', notes=notes)
                            
                            if success:
                                st.success(f"✅ {selected_company}のステータスを{SALES_STATUS[new_status]}に更新しました")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ ステータス更新に失敗しました")
        else:
            st.info("企業データがありません。まず企業を追加してください。")

def add_email_distribution_link():
    """メール配信システムへのリンクを追加（最小限）"""
    st.markdown("---")
    st.subheader("📧 メール配信システム")
    
    gmail_configured = os.path.exists('config/gmail_config.json')
    
    if gmail_configured:
        st.success("✅ Gmail設定済み")
    else:
        st.warning("⚠️ Gmail設定が必要です")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌐 Web版起動"):
            st.info("ターミナル: streamlit run email_campaign_streamlit.py --server.port 8502")
    
    with col2:
        if st.button("💻 CLI版起動"):
            st.info("ターミナル: python email_distribution.py")


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
    
    st.text_area("件名", value=selected_template["subject"], disabled=True, height=50)
    st.text_area("本文", value=selected_template["body"], height=300, disabled=True)

def show_analytics(company_manager):
    """分析・レポート"""
    st.header("📈 分析・レポート")
    
    companies_df = company_manager.get_all_companies()
    
    if companies_df.empty:
        st.info("分析するデータがありません。企業データを追加してください。")
        return
    
    # 基本統計
    st.subheader("📊 基本統計")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ステータス分布
        if 'sales_status' in companies_df.columns:
            status_counts = companies_df['sales_status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title="ステータス分布")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # WiFi需要分布
        if 'wifi_required' in companies_df.columns:
            wifi_counts = companies_df['wifi_required'].map({1: 'WiFi必要', 0: 'WiFi不要'}).value_counts()
            fig = px.bar(x=wifi_counts.index, y=wifi_counts.values, 
                        title="WiFi需要分布")
            st.plotly_chart(fig, use_container_width=True)

def show_data_import(company_manager):
    """データインポート機能（完全実装版）"""
    st.header("📁 データインポート")
    
    tab1, tab2, tab3 = st.tabs(["📤 ファイルアップロード", "📊 データプレビュー", "📋 インポート履歴"])
    
    with tab1:
        st.subheader("📤 企業データのインポート")
        st.info("Excel (XLSX)、CSV、TSVファイルに対応しています。")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "ファイルを選択してください",
            type=['xlsx', 'xls', 'csv', 'tsv'],
            help="企業データを含むファイルをアップロードしてください"
        )
        
        if uploaded_file is not None:
            try:
                # ファイルタイプに応じた処理
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                elif uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.tsv'):
                    df = pd.read_csv(uploaded_file, sep='\t')
                
                st.success(f"✅ ファイル読み込み成功: {len(df)}行のデータ")
                
                # データプレビュー
                st.subheader("📊 データプレビュー")
                st.dataframe(df.head(10), use_container_width=True)
                
                # カラムマッピング設定
                st.subheader("🔄 カラムマッピング")
                st.info("アップロードファイルのカラムを FusionCRM の項目にマッピングしてください")
                
                # FusionCRMの標準カラム
                fusion_columns = {
                    'company_name': '企業名（必須）',
                    'email': 'メールアドレス',
                    'phone': '電話番号',
                    'website_url': 'ウェブサイト',
                    'industry': '業界',
                    'notes': '備考・説明',
                    'source': '情報源'
                }
                
                # 自動マッピング提案
                auto_mapping = suggest_column_mapping(df.columns.tolist())
                
                # マッピング設定UI
                mapping = {}
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**FusionCRM項目**")
                    for fusion_col, description in fusion_columns.items():
                        st.markdown(f"• **{description}**")
                
                with col2:
                    st.markdown("**ファイルのカラム**")
                    for fusion_col, description in fusion_columns.items():
                        suggested = auto_mapping.get(fusion_col, '')
                        options = ['（マッピングしない）'] + df.columns.tolist()
                        
                        default_index = 0
                        if suggested and suggested in df.columns:
                            default_index = options.index(suggested)
                        
                        selected = st.selectbox(
                            description,
                            options,
                            index=default_index,
                            key=f"mapping_{fusion_col}"
                        )
                        
                        if selected != '（マッピングしない）':
                            mapping[fusion_col] = selected
                
                # 詳細設定
                st.subheader("⚙️ インポート設定")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    import_mode = st.radio(
                        "インポートモード",
                        ["新規追加のみ", "重複チェック（メールアドレス基準）", "すべて追加"]
                    )
                    
                    batch_size = st.number_input(
                        "バッチサイズ",
                        min_value=1,
                        max_value=100,
                        value=10,
                        help="一度に処理する企業数"
                    )
                
                with col2:
                    auto_wifi_detection = st.checkbox(
                        "WiFi需要の自動判定",
                        value=True,
                        help="企業名・説明からWiFi需要を自動判定"
                    )
                    
                    auto_picocela_scoring = st.checkbox(
                        "PicoCELA関連度の自動計算",
                        value=True,
                        help="キーワードマッチングによる関連度計算"
                    )
                
                # プレビュー変換
                if st.button("🔍 変換プレビュー", type="secondary"):
                    if 'company_name' not in mapping:
                        st.error("❌ 企業名のマッピングは必須です")
                    else:
                        preview_df = create_import_preview(df, mapping, auto_wifi_detection, auto_picocela_scoring)
                        st.subheader("📋 変換後データプレビュー（最初の5行）")
                        st.dataframe(preview_df.head(), use_container_width=True)
                        
                        # 統計情報
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            wifi_count = len(preview_df[preview_df['wifi_required'] == 1]) if 'wifi_required' in preview_df.columns else 0
                            st.metric("WiFi需要企業", wifi_count)
                        
                        with col2:
                            high_relevance = len(preview_df[preview_df['picocela_relevance_score'] >= 50]) if 'picocela_relevance_score' in preview_df.columns else 0
                            st.metric("高関連度企業", high_relevance)
                        
                        with col3:
                            total_valid = len(preview_df[preview_df['company_name'].notna() & (preview_df['company_name'] != '')])
                            st.metric("有効データ", total_valid)
                
                # インポート実行
                st.subheader("🚀 インポート実行")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 データインポート開始", type="primary", use_container_width=True):
                        if 'company_name' not in mapping:
                            st.error("❌ 企業名のマッピングは必須です")
                        else:
                            execute_data_import(
                                df, mapping, company_manager, 
                                import_mode, batch_size,
                                auto_wifi_detection, auto_picocela_scoring
                            )
                
                with col2:
                    if st.button("📄 CSVエクスポート", type="secondary", use_container_width=True):
                        if 'company_name' in mapping:
                            export_df = create_import_preview(df, mapping, auto_wifi_detection, auto_picocela_scoring)
                            csv = export_df.to_csv(index=False)
                            st.download_button(
                                label="📥 変換後データをダウンロード",
                                data=csv,
                                file_name=f"fusioncrm_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.error("❌ まず企業名のマッピングを設定してください")
                            
            except Exception as e:
                st.error(f"❌ ファイル読み込みエラー: {str(e)}")
    
    with tab2:
        st.subheader("📊 データプレビュー・検証")
        st.info("アップロードしたデータの詳細分析を行います")
        
        # 既存のアップロードファイルがあるかチェック
        if 'uploaded_file' in locals() and uploaded_file is not None:
            # データ品質チェック
            show_data_quality_analysis(df)
        else:
            st.info("📤 まずファイルをアップロードしてください")
    
    with tab3:
        st.subheader("📋 インポート履歴")
        show_import_history()

def suggest_column_mapping(file_columns):
    """カラムマッピングの自動提案"""
    mapping_rules = {
        'company_name': ['company name', 'company_name', 'name', 'organization', 'business name'],
        'email': ['email', 'email address', 'e-mail', 'mail', 'contact email'],
        'phone': ['phone', 'telephone', 'tel', 'contact phone', 'phone number'],
        'website_url': ['website', 'url', 'web', 'homepage', 'site'],
        'industry': ['industry', 'sector', 'business type', 'category'],
        'notes': ['description', 'notes', 'comment', 'remarks', 'details'],
        'source': ['source', 'origin', 'lead source', 'channel']
    }
    
    suggestions = {}
    
    for fusion_col, patterns in mapping_rules.items():
        for file_col in file_columns:
            if any(pattern.lower() in file_col.lower() for pattern in patterns):
                suggestions[fusion_col] = file_col
                break
    
    return suggestions

def create_import_preview(df, mapping, auto_wifi_detection, auto_picocela_scoring):
    """インポートプレビューデータの作成"""
    preview_data = []
    
    for _, row in df.iterrows():
        company_data = {}
        
        # マッピングに基づいてデータを変換
        for fusion_col, file_col in mapping.items():
            if file_col in df.columns:
                value = row[file_col]
                if pd.isna(value):
                    value = ''
                company_data[fusion_col] = str(value)
        
        # 必須フィールドの確認
        if not company_data.get('company_name'):
            continue
        
        # WiFi需要の自動判定
        if auto_wifi_detection:
            company_data['wifi_required'] = detect_wifi_need_from_data(company_data)
        else:
            company_data['wifi_required'] = 0
        
        # PicoCELA関連度の自動計算
        if auto_picocela_scoring:
            company_data['picocela_relevance_score'] = calculate_picocela_relevance_from_data(company_data)
        else:
            company_data['picocela_relevance_score'] = 0
        
        # 優先度スコア計算
        company_data['priority_score'] = calculate_priority_from_data(company_data)
        
        # デフォルト値設定
        company_data['sales_status'] = 'New'
        company_data['source'] = company_data.get('source', 'Data Import')
        
        preview_data.append(company_data)
    
    return pd.DataFrame(preview_data)

def detect_wifi_need_from_data(company_data):
    """データからWiFi需要を判定"""
    wifi_indicators = [
        'wifi', 'wireless', 'network', 'connectivity', 'mesh',
        'iot', 'smart', 'digital', 'automation', 'sensor',
        'monitoring', 'tracking', 'communication'
    ]
    
    text_fields = [
        company_data.get('company_name', ''),
        company_data.get('notes', ''),
        company_data.get('industry', '')
    ]
    
    full_text = ' '.join(text_fields).lower()
    
    for indicator in wifi_indicators:
        if indicator in full_text:
            return 1
    
    return 0

def calculate_picocela_relevance_from_data(company_data):
    """データからPicoCELA関連度を計算"""
    score = 0
    
    # キーワードスコアリング
    keywords = {
        'network': 15, 'mesh': 20, 'wireless': 15, 'wifi': 15,
        'connectivity': 10, 'iot': 10, 'smart': 8, 'automation': 8,
        'construction': 12, 'building': 10, 'industrial': 8
    }
    
    text_fields = [
        company_data.get('company_name', ''),
        company_data.get('notes', ''),
        company_data.get('industry', '')
    ]
    
    full_text = ' '.join(text_fields).lower()
    
    for keyword, points in keywords.items():
        if keyword in full_text:
            score += points
    
    return min(score, 100)

def calculate_priority_from_data(company_data):
    """優先度スコアを計算"""
    base_score = company_data.get('picocela_relevance_score', 0)
    
    if company_data.get('wifi_required', 0) == 1:
        base_score += 50
    
    # メールアドレスがある場合のボーナス
    if company_data.get('email'):
        base_score += 10
    
    # ウェブサイトがある場合のボーナス
    if company_data.get('website_url'):
        base_score += 5
    
    return min(base_score, 150)

def execute_data_import(df, mapping, company_manager, import_mode, batch_size, auto_wifi, auto_picocela):
    """データインポートの実行"""
    
    # プログレスバーの初期化
    progress_bar = st.progress(0)
    status_text = st.empty()
    stats_container = st.container()
    
    # 統計情報の初期化
    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # 変換後データの作成
    import_df = create_import_preview(df, mapping, auto_wifi, auto_picocela)
    total_rows = len(import_df)
    
    if total_rows == 0:
        st.error("❌ インポート可能なデータがありません")
        return
    
    status_text.text(f"📥 {total_rows}社のデータをインポート中...")
    
    # バッチ処理でインポート
    for i in range(0, total_rows, batch_size):
        batch_df = import_df.iloc[i:i+batch_size]
        
        for idx, row in batch_df.iterrows():
            try:
                # 企業データの準備
                company_data = row.to_dict()
                
                # 重複チェック（メールアドレス基準）
                if import_mode == "重複チェック（メールアドレス基準）" and company_data.get('email'):
                    # 既存企業の確認
                    existing_companies = company_manager.get_all_companies()
                    if not existing_companies.empty and 'email' in existing_companies.columns:
                        if company_data['email'] in existing_companies['email'].values:
                            stats['skipped'] += 1
                            continue
                
                # 企業追加
                result = company_manager.add_company(company_data, user_id='data_import')
                
                if result:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"企業追加失敗: {company_data.get('company_name', 'Unknown')}")
                
                stats['total'] += 1
                
                # プログレスバー更新
                progress = (stats['total']) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"📥 処理中... {stats['total']}/{total_rows} ({stats['success']}成功, {stats['failed']}失敗, {stats['skipped']}スキップ)")
                
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"エラー: {str(e)} (企業: {company_data.get('company_name', 'Unknown')})")
        
        # バッチ間の小休止
        time.sleep(0.1)
    
    # 完了メッセージ
    progress_bar.progress(1.0)
    
    if stats['success'] > 0:
        st.success(f"✅ インポート完了! {stats['success']}社を正常に追加しました")
    
    # 詳細統計
    with stats_container:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("✅ 成功", stats['success'])
        with col2:
            st.metric("❌ 失敗", stats['failed'])
        with col3:
            st.metric("⏭️ スキップ", stats['skipped'])
        with col4:
            st.metric("📊 処理総数", stats['total'])
    
    # エラー詳細
    if stats['errors']:
        with st.expander(f"❌ エラー詳細 ({len(stats['errors'])}件)"):
            for error in stats['errors'][:10]:  # 最初の10件のみ表示
                st.text(error)
            if len(stats['errors']) > 10:
                st.text(f"... その他 {len(stats['errors']) - 10} 件のエラー")
    
    # インポート履歴の保存
    save_import_history(stats, mapping, import_mode)

def show_data_quality_analysis(df):
    """データ品質分析の表示"""
    st.subheader("🔍 データ品質分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 基本統計**")
        st.metric("総行数", len(df))
        st.metric("列数", len(df.columns))
        
        # 欠損値チェック
        missing_data = df.isnull().sum()
        if missing_data.sum() > 0:
            st.markdown("**⚠️ 欠損値**")
            for col, count in missing_data[missing_data > 0].items():
                st.text(f"• {col}: {count}行 ({count/len(df)*100:.1f}%)")
        else:
            st.success("✅ 欠損値なし")
    
    with col2:
        st.markdown("**📈 データ分析**")
        
        # メールアドレスの有効性
        if 'Email Address' in df.columns or any('email' in col.lower() for col in df.columns):
            email_col = next((col for col in df.columns if 'email' in col.lower()), None)
            if email_col:
                valid_emails = df[email_col].notna().sum()
                st.metric("有効メールアドレス", f"{valid_emails}/{len(df)}")
        
        # WiFi関連企業の予測
        text_columns = df.select_dtypes(include=['object']).columns
        wifi_count = 0
        for col in text_columns:
            wifi_count += df[col].astype(str).str.contains('wifi|wireless|network', case=False, na=False).sum()
        
        if wifi_count > 0:
            st.metric("WiFi関連キーワード検出", f"{wifi_count}件")

def save_import_history(stats, mapping, import_mode):
    """インポート履歴の保存"""
    if 'import_history' not in st.session_state:
        st.session_state.import_history = []
    
    history_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stats': stats,
        'mapping': mapping,
        'import_mode': import_mode
    }
    
    st.session_state.import_history.append(history_entry)

def show_import_history():
    """インポート履歴の表示"""
    if 'import_history' not in st.session_state or not st.session_state.import_history:
        st.info("📋 インポート履歴がありません")
        return
    
    st.markdown("**📊 最近のインポート履歴**")
    
    for i, entry in enumerate(reversed(st.session_state.import_history[-10:])):
        with st.expander(f"📅 {entry['timestamp']} - {entry['stats']['success']}社追加"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**統計情報**")
                st.json(entry['stats'])
            
            with col2:
                st.markdown("**設定情報**")
                st.text(f"インポートモード: {entry['import_mode']}")
                st.markdown("**カラムマッピング:**")
                for fusion_col, file_col in entry['mapping'].items():
                    st.text(f"• {fusion_col} ← {file_col}")
    
    # 履歴クリア
    if st.button("🗑️ 履歴をクリア"):
        st.session_state.import_history = []
        st.rerun()

# メイン関数
def main():
    st.title("🚀 FusionCRM - PicoCELA営業管理システム")
    st.markdown("**☁️ Google Sheets版（クラウド対応）- Version 6.0**")
    
    # Google Sheets API取得
    api = get_google_sheets_api()
    
    if api is None:
        setup_google_sheets_connection()
        return
    
    # 接続成功時の処理
    try:
        # マネージャー初期化
        company_manager = CompanyManager(api)
        email_manager = EmailCampaignManager(api)
        
        # Google Sheetsリンク表示
        if 'spreadsheet_url' in st.session_state:
            st.success(f"✅ Google Sheets接続中 | [📊 スプレッドシートを開く]({st.session_state.spreadsheet_url})")
        else:
            st.info("🔄 Google Sheetsとの接続を確立中...")
        
        # サイドバー
        st.sidebar.title("🌟 FusionCRM")
        st.sidebar.markdown("☁️ **Google Sheets版 v6.0**")
        
        # 接続状況表示
        show_connection_status()
        
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
            
    except Exception as e:
        st.error(f"アプリケーションエラー: {str(e)}")
        st.error("Google Sheets接続に問題がある可能性があります。")
        
        # エラー時の対処オプション
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 接続をリセット", type="primary"):
                if 'gas_url' in st.session_state:
                    del st.session_state.gas_url
                if 'spreadsheet_url' in st.session_state:
                    del st.session_state.spreadsheet_url
                st.rerun()
        
        with col2:
            if st.button("🚀 強制継続", type="secondary"):
                st.info("エラーを無視してアプリケーションを継続します。")
                # 基本的なダッシュボードを表示
                st.subheader("📊 基本ダッシュボード")
                st.info("接続に問題がありますが、アプリケーションは利用可能です。")

add_email_distribution_link()  # 既存main()の最後に追加

if __name__ == "__main__":
    main()
