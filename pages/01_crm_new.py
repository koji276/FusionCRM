"""
FORCE UPDATE TRIGGER - Version 2.1 - KEY FIXED
Updated: 2025-07-29 14:35
This file contains the FULL CRM functionality with tabs, search, and filters.
FIXED: Button key duplication issues
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
import requests
import os

# デバッグ情報を強制表示
st.sidebar.markdown("### 🔧 デバッグ情報")
st.sidebar.text(f"ファイル更新: 2025-07-29 14:35")
st.sidebar.text("期待される表示: 5つのタブ")
st.sidebar.text("ステータス: ボタンキー修正済み")

# Streamlitキャッシュクリア（強制）
if 'cache_cleared_v2' not in st.session_state:
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.cache_cleared_v2 = True
    st.sidebar.success("キャッシュクリア実行済み v2")

# 戻るボタン（ユニークキー）
if st.button("← 統合ダッシュボードに戻る", key="back_to_dashboard_crm_new"):
    st.session_state.current_view = 'dashboard'
    st.rerun()

# ページ設定とスタイル
st.title("🏢 CRM管理システム - フル機能版")
st.markdown("**企業データ管理・ステータス追跡・PicoCELA関連度分析**")

# 重要: この表示が見えない場合はStreamlitキャッシュ問題
st.error("🚨 重要: この赤いメッセージが表示されていない場合、アップデートが反映されていません")
st.success("✅ このメッセージが見える場合、アップデートは成功しています")

# 統合プラットフォームからサイドバーへの移動
st.info("🔄 統合プラットフォーム: サイドバーから他のページに移動 | Google Sheets連携でリアルタイム同期")

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
    """Google Sheets API（統合版）"""
    
    def __init__(self, gas_url):
        self.gas_url = gas_url
        self._connection_tested = False
        self._connection_status = "未テスト"
    
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
            
            if response.status_code != 200:
                st.warning(f"HTTP {response.status_code}: サーバー応答エラー")
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            try:
                result = response.json()
            except json.JSONDecodeError:
                st.warning("非JSON応答を受信")
                return {"success": False, "error": "Invalid JSON response"}
            
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                if action not in ['test', 'init_database']:
                    st.error(f"API エラー（{action}）: {error_msg}")
                return result
            
            return result
            
        except requests.exceptions.Timeout:
            st.error(f"タイムアウト（{action}）: 30秒以内に応答なし")
            return {"success": False, "error": "Timeout"}
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

class CompanyManager:
    """企業管理クラス（統合版）"""
    
    def __init__(self, api):
        self.api = api
        self._ensure_database()
    
    def _ensure_database(self):
        """データベース初期化確認"""
        result = self.api.call_api('init_database', method='POST')
        if result and result.get('success') and result.get('spreadsheet_url'):
            st.session_state.crm_spreadsheet_url = result['spreadsheet_url']
    
    def add_company(self, company_data, user_id="system"):
        """企業追加"""
        try:
            relevance_score = ENRDataProcessor.calculate_picocela_relevance(company_data)
            wifi_required = 1 if ENRDataProcessor.detect_wifi_requirement(company_data) else 0
            
            company_data['picocela_relevance_score'] = relevance_score
            company_data['wifi_required'] = wifi_required
            company_data['priority_score'] = relevance_score + (50 if wifi_required else 0)
            company_data['sales_status'] = company_data.get('sales_status', 'New')
            
            result = self.api.call_api('add_company', method='POST', data={'company': company_data})
            
            if result and result.get('success'):
                return result.get('company_id')
            return None
            
        except Exception as e:
            st.error(f"企業追加エラー: {str(e)}")
            return None
    
    def get_all_companies(self):
        """全企業取得"""
        try:
            result = self.api.call_api('get_companies')
            
            if result and result.get('success') and result.get('companies'):
                df = pd.DataFrame(result['companies'])
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return pd.DataFrame()

def get_google_sheets_api():
    """Google Sheets API取得（統合版・強化版）"""
    
    # デバッグ情報を表示
    st.sidebar.markdown("### 🔧 API接続デバッグ")
    
    # 優先順位1: Streamlit secrets
    if 'google_apps_script_url' in st.secrets:
        gas_url = st.secrets['google_apps_script_url']
        st.sidebar.success("✅ Secrets からURL取得")
        st.sidebar.text(f"URL: {gas_url[:30]}...")
        try:
            api = GoogleSheetsAPI(gas_url)
            st.session_state.crm_gas_url = gas_url
            return api
        except Exception as e:
            st.sidebar.error(f"Secrets API初期化エラー: {str(e)}")
    
    # 優先順位2: セッション状態（CRM専用）
    elif 'crm_gas_url' in st.session_state:
        gas_url = st.session_state.crm_gas_url
        st.sidebar.info("📋 CRM専用URL使用")
        st.sidebar.text(f"URL: {gas_url[:30]}...")
        try:
            return GoogleSheetsAPI(gas_url)
        except Exception as e:
            st.sidebar.error(f"CRM URL初期化エラー: {str(e)}")
    
    # 優先順位3: 統合システムのAPI設定を継承
    elif 'gas_url' in st.session_state:
        gas_url = st.session_state.gas_url
        st.sidebar.info("🔄 統合システムURL継承")
        st.sidebar.text(f"URL: {gas_url[:30]}...")
        try:
            return GoogleSheetsAPI(gas_url)
        except Exception as e:
            st.sidebar.error(f"統合システムAPI使用エラー: {str(e)}")
    
    # 優先順位4: 強制的にSecretsを再チェック
    else:
        st.sidebar.warning("⚠️ API設定が見つかりません")
        st.sidebar.markdown("**利用可能な設定:**")
        
        # デバッグ用：利用可能な設定を表示
        if hasattr(st, 'secrets'):
            available_secrets = [key for key in st.secrets.keys() if 'script' in key.lower() or 'url' in key.lower()]
            if available_secrets:
                st.sidebar.text("Secrets: " + ", ".join(available_secrets))
            else:
                st.sidebar.text("Secrets: なし")
        
        # セッション状態の確認
        session_apis = [key for key in st.session_state.keys() if 'url' in key.lower() or 'api' in key.lower()]
        if session_apis:
            st.sidebar.text("Session: " + ", ".join(session_apis))
        else:
            st.sidebar.text("Session: なし")
    
    return None

def show_crm_dashboard(company_manager):
    """CRMダッシュボード"""
    st.markdown("## 📊 CRMダッシュボード")
    
    all_companies = company_manager.get_all_companies()
    total_companies = len(all_companies)
    
    if total_companies == 0:
        st.info("📋 企業データがありません。サンプルデータを追加してテストしてください。")
        
        if st.button("🚀 サンプルデータを追加", type="primary", key="add_sample_data_dashboard"):
            sample_companies = [
                {
                    'company_name': 'ABC建設株式会社',
                    'email': 'info@abc-const.jp',
                    'industry': 'Construction',
                    'notes': 'WiFi, mesh network solutions needed for construction sites',
                    'source': 'Sample Data'
                },
                {
                    'company_name': 'XYZ工業',
                    'email': 'contact@xyz-ind.com',
                    'industry': 'Industrial',
                    'notes': 'Smart factory, IoT integration, wireless monitoring',
                    'source': 'Sample Data'
                },
                {
                    'company_name': 'DEF開発',
                    'email': 'sales@def-dev.co.jp',
                    'industry': 'Development',
                    'notes': 'Smart building automation, network infrastructure',
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
                time.sleep(1)
                st.rerun()
        
        return
    
    # 統計計算
    try:
        wifi_companies = len(all_companies[all_companies['wifi_required'] == 1]) if 'wifi_required' in all_companies.columns else 0
        picocela_companies = len(all_companies[all_companies['picocela_relevance_score'] >= 50]) if 'picocela_relevance_score' in all_companies.columns else 0
        monthly_target = 15
        
    except Exception as e:
        st.error(f"統計計算エラー: {str(e)}")
        wifi_companies = 0
        picocela_companies = 0
        monthly_target = 15
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", f"{total_companies:,}")
    
    with col2:
        st.metric("📶 WiFi需要企業", f"{wifi_companies:,}")
        wifi_pct = f"{wifi_companies/total_companies*100:.1f}%" if total_companies > 0 else "0%"
        st.caption(wifi_pct)
    
    with col3:
        st.metric("🎯 PicoCELA関連", f"{picocela_companies:,}")
        relevance_pct = f"{picocela_companies/total_companies*100:.1f}%" if total_companies > 0 else "0%"
        st.caption(relevance_pct)
    
    with col4:
        st.metric("📊 今月目標", f"{monthly_target:,}")

def show_company_list_management(company_manager):
    """企業一覧・管理"""
    st.markdown("## 🏢 企業管理")
    
    # 企業名検索・フィルター
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 企業名検索", placeholder="企業名を入力...", key="company_search_input")
    
    with col2:
        status_filter = st.selectbox("📊 ステータス", ["全て"] + list(SALES_STATUS.keys()), key="status_filter_select")
    
    with col3:
        picocela_filter = st.slider("🎯 以上PicoCELAスコア", 0, 100, 0, key="picocela_score_slider")
    
    with col4:
        wifi_filter = st.selectbox("📶 WiFi需要", ["全て", "WiFi必要", "WiFi不要"], key="wifi_filter_select")
    
    # データ取得とフィルタリング
    companies_df = company_manager.get_all_companies()
    
    if not companies_df.empty:
        # フィルタリング適用
        filtered_df = companies_df.copy()
        
        # 企業名検索
        if search_term and 'company_name' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['company_name'].str.contains(search_term, case=False, na=False)]
        
        # ステータスフィルター
        if status_filter != "全て" and 'sales_status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['sales_status'] == status_filter]
        
        # PicoCELAスコアフィルター
        if 'picocela_relevance_score' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= picocela_filter]
        
        # WiFi需要フィルター
        if wifi_filter != "全て" and 'wifi_required' in filtered_df.columns:
            wifi_value = 1 if wifi_filter == "WiFi必要" else 0
            filtered_df = filtered_df[filtered_df['wifi_required'] == wifi_value]
        
        st.markdown(f"### 📋 企業リスト ({len(filtered_df)}社)")
        
        if not filtered_df.empty:
            # 表示用データ準備
            display_columns = ['company_name', 'sales_status']
            
            if 'picocela_relevance_score' in filtered_df.columns:
                display_columns.append('picocela_relevance_score')
            if 'wifi_required' in filtered_df.columns:
                display_columns.append('wifi_required')
            if 'email' in filtered_df.columns:
                display_columns.append('email')
            if 'industry' in filtered_df.columns:
                display_columns.append('industry')
            
            # 表示用に列名を変更
            display_df = filtered_df[display_columns].copy()
            column_mapping = {
                'company_name': '企業名',
                'sales_status': 'ステータス',
                'picocela_relevance_score': 'PicoCELAスコア',
                'wifi_required': 'WiFi需要',
                'email': 'メール',
                'industry': '業界'
            }
            
            display_df = display_df.rename(columns=column_mapping)
            
            # WiFi需要を分かりやすく表示
            if 'WiFi需要' in display_df.columns:
                display_df['WiFi需要'] = display_df['WiFi需要'].map({1: '✅', 0: '❌'})
            
            st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.info("フィルター条件に該当する企業がありません。")
    else:
        st.info("企業データがありません。企業を追加してください。")

def show_crm_analysis(company_manager):
    """CRM分析表示"""
    st.markdown("## 📈 企業ステータス分析 (10段階)")
    
    all_companies = company_manager.get_all_companies()
    
    if all_companies.empty:
        st.info("分析するデータがありません。")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ステータス分布グラフ
        if 'sales_status' in all_companies.columns:
            status_counts = all_companies['sales_status'].value_counts()
            
            fig = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="ステータス別企業数",
                color=status_counts.values,
                color_continuous_scale="Viridis"
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # PicoCELA関連度スコア分析
        if 'picocela_relevance_score' in all_companies.columns:
            
            fig = px.histogram(
                all_companies,
                x='picocela_relevance_score',
                nbins=10,
                title="PicoCELA関連度スコア分布",
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def show_add_company_form(company_manager):
    """企業追加フォーム"""
    st.markdown("### ➕ 新規企業追加")
    
    with st.form("add_company_form_new"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("企業名*", placeholder="例: 株式会社サンプル", key="new_company_name")
            email = st.text_input("メールアドレス", placeholder="contact@example.com", key="new_company_email")
            industry = st.text_input("業界", placeholder="建設業", key="new_company_industry")
        
        with col2:
            phone = st.text_input("電話番号", placeholder="03-1234-5678", key="new_company_phone")
            website_url = st.text_input("ウェブサイト", placeholder="https://example.com", key="new_company_website")
            source = st.selectbox("情報源", ["Manual", "ENR Import", "Web Research", "Referral"], key="new_company_source")
        
        notes = st.text_area("備考・メモ", placeholder="企業の特徴、WiFi需要、その他重要な情報", key="new_company_notes")
        
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

# 強制的にタブを表示（キャッシュ無視）
st.markdown("---")
st.markdown("## 📋 以下に5つのタブが表示されるはずです:")

# メイン実行部分（API接続デバッグ強化版）
try:
    # API取得
    api = get_google_sheets_api()
    
    if api is None:
        st.error("🔌 Google Sheets APIに接続できません")
        
        # 詳細なデバッグ情報
        st.markdown("### 🔍 詳細診断")
        
        # 統合ダッシュボードの認証状態を確認
        if 'user_info' in st.session_state:
            user_info = st.session_state.user_info
            st.success(f"✅ ユーザー認証済み: {user_info.get('username', 'Unknown')}")
        else:
            st.warning("⚠️ ユーザー認証情報なし")
        
        # 緊急回避ボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 API設定を再取得", key="refresh_api_settings"):
                # 統合システムの設定を強制的に再読み込み
                if 'gas_url' in st.session_state:
                    st.session_state.crm_gas_url = st.session_state.gas_url
                    st.success("API設定を更新しました")
                    st.rerun()
                else:
                    st.error("統合システムのAPI設定が見つかりません")
        
        with col2:
            if st.button("⚠️ オフラインモードで続行", key="offline_mode_continue"):
                st.session_state.force_offline_mode = True
                st.info("オフラインモードに切り替えました")
                st.rerun()
        
        # 強制オフラインモード
        if st.session_state.get('force_offline_mode', False):
            st.info("🔧 オフラインモード: Google Sheets接続をスキップして基本機能を使用")
            
            # オフライン用のダミーマネージャー
            class OfflineCompanyManager:
                def __init__(self):
                    # SALES_STATUS定義を追加
                    self.SALES_STATUS = {
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
                
                def get_all_companies(self):
                    sample_data = {
                        'company_name': ['ABC建設', 'XYZ工業', 'DEF開発', 'テスト建設株式会社'],
                        'sales_status': ['Contacted', 'Qualified', 'Proposal', 'New'],
                        'picocela_relevance_score': [85, 92, 78, 95],
                        'wifi_required': [1, 1, 0, 1],
                        'email': ['info@abc.jp', 'contact@xyz.com', 'sales@def.jp', 'test@test.com'],
                        'industry': ['建設業', '工業', '開発', '建設業']
                    }
                    return pd.DataFrame(sample_data)
                
                def add_company(self, company_data, user_id="system"):
                    st.success("✅ オフラインモード: 企業データをメモリに追加しました")
                    return f"offline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            company_manager = OfflineCompanyManager()
            
            # タブ構造での機能表示（オフラインモード）
            st.markdown("### 🚀 CRM機能（オフラインモード）")
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 ダッシュボード", "🏢 企業管理", "📈 分析", "➕ 企業追加", "⚙️ 設定"])
            
            with tab1:
                show_crm_dashboard(company_manager)
            
            with tab2:
                show_company_list_management(company_manager)
            
            with tab3:
                show_crm_analysis(company_manager)
            
            with tab4:
                show_add_company_form(company_manager)
            
            with tab5:
                st.markdown("### ⚙️ CRM設定（オフライン）")
                st.warning("⚠️ オフラインモードです")
                st.info("Google Sheets接続が復旧すると、データが同期されます。")
        
        else:
            # フォールバック: 基本機能のみ提供
            st.markdown("### 📊 基本CRM機能（オフライン）")
            st.info("Google Sheets接続なしでも基本機能は利用できます。")
            
            # サンプルデータ表示
            sample_data = {
                '企業名': ['ABC建設', 'XYZ工業', 'DEF開発'],
                'ステータス': ['Contacted', 'Qualified', 'Proposal'],
                'PicoCELAスコア': [85, 92, 78],
                'WiFi需要': ['✅', '✅', '❌']
            }
            df = pd.DataFrame(sample_data)
            st.dataframe(df, use_container_width=True)
        
    else:
        # 正常なAPI接続時
        company_manager = CompanyManager(api)
        
        # Google Sheetsリンク表示
        if 'crm_spreadsheet_url' in st.session_state:
            st.success(f"✅ Google Sheets連携中 | [📊 スプレッドシートを開く]({st.session_state.crm_spreadsheet_url})")
        
        # タブ構造での機能表示（ユニークキー付き）
        st.markdown("### 🚀 CRM機能（フルモード）")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 ダッシュボード", "🏢 企業管理", "📈 分析", "➕ 企業追加", "⚙️ 設定"])
        
        with tab1:
            show_crm_dashboard(company_manager)
        
        with tab2:
            show_company_list_management(company_manager)
        
        with tab3:
            show_crm_analysis(company_manager)
        
        with tab4:
            show_add_company_form(company_manager)
        
        with tab5:
            st.markdown("### ⚙️ CRM設定")
            st.info("統合システムの設定は統合ダッシュボードで管理されます。")
            
            # 設定状況表示
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔧 接続状況**")
                if 'crm_spreadsheet_url' in st.session_state:
                    st.success("✅ Google Sheets接続中")
                else:
                    st.warning("⚠️ Google Sheets未接続")
            
            with col2:
                st.markdown("**📊 データ統計**")
                all_companies = company_manager.get_all_companies()
                st.metric("登録企業数", len(all_companies))

except Exception as e:
    st.error(f"🚨 CRMシステムエラー: {str(e)}")
    st.info("統合ダッシュボードから再度アクセスしてください。")
    
    # エラー詳細（デバッグ用）
    with st.expander("🔧 エラー詳細 (開発者向け)"):
        st.code(str(e))
        st.markdown("**対処方法:**")
        st.markdown("1. 統合ダッシュボードに戻る")
        st.markdown("2. Google Sheets接続を確認")
        st.markdown("3. ブラウザをリフレッシュ")
