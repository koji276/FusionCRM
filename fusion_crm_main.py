"""
FusionCRM - PicoCELA営業管理システム（Google Sheets版）
既存モジュールとの完全統合版
"""

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import re

# 既存モジュールの定数を統合
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

STATUS_PRIORITY = {
    'Won': 10, 'Negotiation': 9, 'Proposal': 8, 'Qualified': 7,
    'Engaged': 6, 'Replied': 5, 'Contacted': 4, 'New': 3,
    'Dormant': 2, 'Lost': 1
}

PICOCELA_KEYWORDS = [
    'network', 'mesh', 'wireless', 'wifi', 'connectivity',
    'iot', 'smart', 'digital', 'automation', 'sensor', 'ai',
    'construction', 'building', 'site', 'industrial', 'management',
    'platform', 'solution', 'integration', 'control', 'monitoring',
    'infrastructure', 'communication', 'technology', 'system',
    'device', 'data', 'cloud', 'edge', 'real-time', 'remote'
]

# ページ設定
st.set_page_config(
    page_title="FusionCRM - PicoCELA営業管理システム",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .strategy-box {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ENRDataProcessor:
    """ENRデータ処理・分析クラス（既存ロジック使用）"""
    
    @staticmethod
    def calculate_picocela_relevance(company_data):
        """PicoCELA関連度スコア計算（ENR企業向け最適化）"""
        score = 0
        text_fields = [
            str(company_data.get('name', '')),
            str(company_data.get('company_name', '')),
            str(company_data.get('website', '')),
            str(company_data.get('website_url', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', '')),
            str(company_data.get('description', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        # キーワードマッチング
        matched_keywords = []
        for keyword in PICOCELA_KEYWORDS:
            if keyword.lower() in full_text:
                score += 10
                matched_keywords.append(keyword)
        
        # 建設業界ボーナス
        construction_terms = ['construction', 'building', 'contractor', 'engineering']
        for term in construction_terms:
            if term in full_text:
                score += 5
        
        return min(score, 100), matched_keywords
    
    @staticmethod
    def detect_wifi_requirement(company_data):
        """WiFi・ワイヤレス需要判定（建設業界特化）"""
        wifi_indicators = [
            'wifi', 'wireless', 'network', 'connectivity', 'mesh',
            'iot', 'smart building', 'construction tech', 'digital construction',
            'site management', 'remote monitoring', 'sensor network',
            'communication system', 'field connectivity'
        ]
        
        text_fields = [
            str(company_data.get('name', '')),
            str(company_data.get('company_name', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', '')),
            str(company_data.get('description', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for indicator in wifi_indicators:
            if indicator in full_text:
                return True
        
        return False
    
    @staticmethod
    def calculate_priority_score(company_data):
        """戦略的優先度スコア計算"""
        relevance, _ = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        
        priority = relevance
        
        # WiFi必要企業に大幅ボーナス
        if wifi_required:
            priority += 50
        
        # ENR企業ボーナス
        if str(company_data.get('source', '')).lower().find('enr') >= 0:
            priority += 20
        
        # 企業規模による調整
        employees = str(company_data.get('employees_count', '')).lower()
        if any(size in employees for size in ['large', '1000+', 'enterprise']):
            priority += 15
        elif any(size in employees for size in ['medium', '100-1000', 'mid']):
            priority += 10
        
        return min(priority, 150)

class CompanyManager:
    """企業管理クラス（Google Sheets専用版）"""
    
    def __init__(self, script_url):
        self.script_url = script_url
        self.is_connected = False
        
    def test_connection(self):
        """接続テスト"""
        if not self.script_url:
            return False, "Google Apps Script URLが設定されていません"
            
        try:
            response = requests.post(
                self.script_url,
                json={"action": "ping"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.is_connected = True
                    return True, "接続成功！"
                else:
                    return False, f"エラー: {result.get('message', '不明なエラー')}"
            else:
                return False, f"HTTP エラー: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "接続タイムアウト（10秒）"
        except requests.exceptions.RequestException as e:
            return False, f"接続エラー: {str(e)}"
        except Exception as e:
            return False, f"予期しないエラー: {str(e)}"
    
    def get_companies(self):
        """企業データを取得"""
        if not self.is_connected:
            return []
            
        try:
            response = requests.post(
                self.script_url,
                json={"action": "getCompanies"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return result.get("data", [])
            return []
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return []
    
    def add_company(self, company_data):
        """企業追加（ENR最適化・自動分析付き）"""
        if not self.is_connected:
            return False, "接続されていません"
        
        # PicoCELA関連度とWiFi需要を自動計算
        relevance_score, matched_keywords = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        priority_score = ENRDataProcessor.calculate_priority_score(company_data)
        
        # データ拡張
        enhanced_data = company_data.copy()
        enhanced_data.update({
            'picoCela_score': relevance_score,
            'keywords_matched': ','.join(matched_keywords),
            'wifi_required': wifi_required,
            'priority_score': priority_score,
            'status': company_data.get('status', 'New'),
            'source': company_data.get('source', 'Manual'),
            'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
            
        try:
            response = requests.post(
                self.script_url,
                json={
                    "action": "addCompany",
                    "data": enhanced_data
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"追加エラー: {str(e)}"
    
    def update_company_status(self, company_id, new_status, note=""):
        """企業ステータス更新（次のアクション提案付き）"""
        if not self.is_connected:
            return False, "接続されていません"
        
        # 次のアクション推奨
        next_action = self._suggest_next_action(new_status)
        enhanced_note = f"{note} - 推奨次アクション: {next_action}" if note else f"推奨次アクション: {next_action}"
            
        try:
            response = requests.post(
                self.script_url,
                json={
                    "action": "updateStatus",
                    "companyId": company_id,
                    "status": new_status,
                    "note": enhanced_note
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"更新エラー: {str(e)}"
    
    def _suggest_next_action(self, status):
        """ステータス別次アクション推奨"""
        action_map = {
            'New': '初回メール送信',
            'Contacted': 'フォローアップメール（1週間後）',
            'Replied': 'オンラインミーティング設定',
            'Engaged': '現場訪問・詳細ニーズ確認',
            'Qualified': '提案書作成・カスタマイズ',
            'Proposal': '社内検討状況確認',
            'Negotiation': '条件調整・最終提案',
            'Won': '契約履行・導入支援',
            'Lost': '関係維持・将来機会確認',
            'Dormant': '再活性化キャンペーン'
        }
        return action_map.get(status, '')

    def import_bulk_data(self, companies_list):
        """複数企業データを一括インポート（ENR最適化）"""
        if not self.is_connected:
            return False, "接続されていません"
        
        # 各企業データにENR分析を適用
        enhanced_companies = []
        for company_data in companies_list:
            relevance_score, matched_keywords = ENRDataProcessor.calculate_picocela_relevance(company_data)
            wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
            priority_score = ENRDataProcessor.calculate_priority_score(company_data)
            
            enhanced_data = company_data.copy()
            enhanced_data.update({
                'picoCela_score': relevance_score,
                'keywords_matched': ','.join(matched_keywords),
                'wifi_required': wifi_required,
                'priority_score': priority_score,
                'status': company_data.get('status', 'New'),
                'source': company_data.get('source', 'Import'),
                'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            enhanced_companies.append(enhanced_data)
            
        try:
            response = requests.post(
                self.script_url,
                json={
                    "action": "bulkImport",
                    "companies": enhanced_companies
                },
                timeout=60  # 大量データ用にタイムアウト延長
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "success", result.get("message", "")
            return False, f"HTTP エラー: {response.status_code}"
            
        except Exception as e:
            return False, f"一括インポートエラー: {str(e)}"
    
    def get_companies_by_criteria(self, status=None, wifi_required=None, 
                                min_priority=0, min_relevance=0, limit=None):
        """条件別企業取得（戦略的フィルタリング）"""
        companies = self.get_companies()
        if not companies:
            return pd.DataFrame()
        
        df = pd.DataFrame(companies)
        
        # 数値型に変換
        for col in ['priority_score', 'picoCela_score', 'wifi_required']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # フィルタリング
        if 'priority_score' in df.columns:
            df = df[df['priority_score'] >= min_priority]
        if 'picoCela_score' in df.columns:
            df = df[df['picoCela_score'] >= min_relevance]
        
        if status:
            if isinstance(status, list):
                df = df[df['status'].isin(status)]
            else:
                df = df[df['status'] == status]
        
        if wifi_required is not None and 'wifi_required' in df.columns:
            df = df[df['wifi_required'] == (1 if wifi_required else 0)]
        
        # ソート
        if 'priority_score' in df.columns:
            df = df.sort_values('priority_score', ascending=False)
        
        if limit:
            df = df.head(limit)
        
        return df
    
    def get_strategic_pipeline(self):
        """戦略的パイプライン分析"""
        companies = self.get_companies()
        if not companies:
            return {
                'pipeline': pd.DataFrame(),
                'wifi_strategy_targets': pd.DataFrame(),
                'total_companies': 0,
                'wifi_required_total': 0
            }
        
        df = pd.DataFrame(companies)
        
        # パイプライン分析
        pipeline_data = []
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            for status, count in status_counts.items():
                status_df = df[df['status'] == status]
                pipeline_data.append({
                    'status': status,
                    'status_jp': SALES_STATUS.get(status, status),
                    'company_count': count,
                    'avg_relevance': status_df['picoCela_score'].mean() if 'picoCela_score' in status_df.columns else 0,
                    'avg_priority': status_df['priority_score'].mean() if 'priority_score' in status_df.columns else 0,
                    'wifi_companies': len(status_df[status_df['wifi_required'] == 1]) if 'wifi_required' in status_df.columns else 0
                })
        
        pipeline_df = pd.DataFrame(pipeline_data)
        
        # WiFi戦略企業取得
        wifi_companies = self.get_companies_by_criteria(wifi_required=True, limit=20)
        
        wifi_total = len(df[df['wifi_required'] == 1]) if 'wifi_required' in df.columns else 0
        
        return {
            'pipeline': pipeline_df,
            'wifi_strategy_targets': wifi_companies,
            'total_companies': len(df),
            'wifi_required_total': wifi_total
        }

def init_session_state():
    """セッション状態を初期化"""
    if 'company_manager' not in st.session_state:
        st.session_state.company_manager = None
    if 'companies_data' not in st.session_state:
        st.session_state.companies_data = []
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None

def show_connection_setup():
    """Google Apps Script接続設定画面"""
    st.markdown('<h1 class="main-header">🚀 FusionCRM - PicoCELA営業管理システム</h1>', unsafe_allow_html=True)
    st.markdown("### ☁️ Google Sheets版（ENR統合対応）")
    
    if st.session_state.company_manager and st.session_state.company_manager.is_connected:
        st.markdown("""
        <div class="success-box">
            ✅ <strong>Google Sheets接続中</strong> - ENR最適化システム準備完了
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("""
    <div class="info-box">
        📋 <strong>PicoCELA特化セットアップ</strong><br>
        建設業界ENRデータに最適化されたGoogle Apps Scriptとの接続を設定します。
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("🔧 Google Apps Script接続設定", expanded=True):
        st.markdown("""
        **📋 セットアップ手順:**
        1. [Google Apps Script](https://script.google.com/) にアクセス
        2. 新しいプロジェクト「FusionCRM PicoCELA Backend」を作成
        3. 提供されたコードを貼り付け
        4. デプロイして Web アプリURLを取得
        5. 下記にURLを入力して接続テスト
        """)
        
        # 既知のURLを事前入力
        default_url = "https://script.google.com/macros/s/AKfycbw3nXJ0vQGBDr_RfZGmYRy2rWH4Jv02ZfelpMCC-oKk1sgkiDB0RYIrh2Ym3De1_aKv/exec"
        
        script_url = st.text_input(
            "📍 Google Apps Script Web アプリ URL:",
            value=default_url,
            placeholder="https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec",
            help="FusionCRM用にデプロイしたGoogle Apps ScriptのURLを入力してください"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔗 接続テスト", type="primary"):
                if script_url:
                    with st.spinner("PicoCELA専用システムに接続中..."):
                        manager = CompanyManager(script_url)
                        success, message = manager.test_connection()
                        
                        if success:
                            st.session_state.company_manager = manager
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("URLを入力してください")
        
        with col2:
            if script_url:
                st.info("💡 PicoCELA営業管理システム用URL設定済み")

def show_dashboard():
    """メインダッシュボード（PicoCELA戦略特化）"""
    if not st.session_state.company_manager or not st.session_state.company_manager.is_connected:
        show_connection_setup()
        return
    
    st.markdown('<h1 class="main-header">📊 PicoCELA戦略ダッシュボード</h1>', unsafe_allow_html=True)
    
    # データ更新
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 データ更新", type="secondary"):
            with st.spinner("ENRデータを分析中..."):
                st.session_state.companies_data = st.session_state.company_manager.get_companies()
                st.session_state.last_refresh = datetime.now()
                st.success("戦略的分析完了！")
    
    with col2:
        if st.session_state.last_refresh:
            st.info(f"最終更新: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # データ取得
    if not st.session_state.companies_data:
        with st.spinner("PicoCELA関連企業を分析中..."):
            st.session_state.companies_data = st.session_state.company_manager.get_companies()
    
    companies = st.session_state.companies_data
    
    if not companies:
        st.warning("📋 企業データがありません。ENRデータをインポートしてください。")
        
        # サンプル戦略企業データ
        with st.expander("🎯 PicoCELA戦略企業サンプルを追加"):
            if st.button("📊 戦略的サンプル企業を追加", type="primary"):
                sample_companies = [
                    {
                        "name": "スマート建設テクノロジー株式会社",
                        "industry": "建設業",
                        "website": "https://smart-construction-tech.com",
                        "contact_person": "田中智也",
                        "email": "tanaka@smart-construction-tech.com",
                        "phone": "03-1234-5678",
                        "notes": "IoTセンサーネットワークと建設現場のWiFiメッシュソリューションに特化。大規模建設プロジェクトでの無線通信システム導入実績多数。",
                        "status": "New",
                        "source": "ENR_Sample",
                        "description": "construction site wireless mesh network IoT smart building"
                    },
                    {
                        "name": "デジタル建築ソリューション株式会社",
                        "industry": "建設技術",
                        "website": "https://digital-architecture-solutions.com",
                        "contact_person": "山田花子",
                        "email": "yamada@digital-architecture.com",
                        "phone": "06-9876-5432",
                        "notes": "建設現場のデジタル化とワイヤレス通信インフラに関するコンサルティング。メッシュネットワーク技術の導入支援。",
                        "status": "Contacted",
                        "source": "ENR_Sample",
                        "description": "digital construction mesh network wireless infrastructure smart technology"
                    },
                    {
                        "name": "コネクテッド建設株式会社",
                        "industry": "建設業",
                        "website": "https://connected-construction.com",
                        "contact_person": "佐藤次郎",
                        "email": "sato@connected-construction.com",
                        "phone": "052-1111-2222",
                        "notes": "建設現場でのIoTデバイス接続とリアルタイム監視システム。WiFi環境とセンサーネットワークの統合ソリューション提供。",
                        "status": "Replied",
                        "source": "ENR_Sample",
                        "description": "connected construction IoT real-time monitoring wifi sensor network"
                    }
                ]
                
                with st.spinner("PicoCELA戦略企業データを追加中..."):
                    success_count = 0
                    for company in sample_companies:
                        success, message = st.session_state.company_manager.add_company(company)
                        if success:
                            success_count += 1
                        else:
                            st.error(f"追加失敗: {message}")
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count}社の戦略企業を追加しました！")
                        st.session_state.companies_data = st.session_state.company_manager.get_companies()
                        st.rerun()
        return
    
    # 戦略的KPIメトリクス
    df = pd.DataFrame(companies)
    
    # 数値型変換
    for col in ['picoCela_score', 'priority_score', 'wifi_required']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    st.markdown("### 🎯 PicoCELA戦略KPI")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏢 総企業数", len(df))
    
    with col2:
        if 'wifi_required' in df.columns:
            wifi_count = len(df[df['wifi_required'] == 1])
            wifi_rate = (wifi_count / len(df) * 100) if len(df) > 0 else 0
            st.metric("📶 WiFi需要企業", f"{wifi_count}社", f"{wifi_rate:.1f}%")
        else:
            st.metric("📶 WiFi需要企業", "0社")
    
    with col3:
        if 'picoCela_score' in df.columns:
            high_relevance = len(df[df['picoCela_score'] >= 70])
            st.metric("⭐ 高関連度企業", f"{high_relevance}社", "70点以上")
        else:
            st.metric("⭐ 高関連度企業", "0社")
    
    with col4:
        if 'priority_score' in df.columns:
            strategic_targets = len(df[df['priority_score'] >= 100])
            st.metric("🎯 戦略ターゲット", f"{strategic_targets}社", "100点以上")
        else:
            st.metric("🎯 戦略ターゲット", "0社")
    
    # 戦略的パイプライン分析
    st.markdown("### 📈 戦略的パイプライン分析")
    
    pipeline_data = st.session_state.company_manager.get_strategic_pipeline()
    pipeline_df = pipeline_data['pipeline']
    
    if not pipeline_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # ステータス分布
            fig_pie = px.pie(
                pipeline_df,
                values='company_count',
                names='status_jp',
                title="営業ステータス分布",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # WiFi需要分析
            if 'wifi_companies' in pipeline_df.columns:
                fig_wifi = px.bar(
                    pipeline_df,
                    x='status_jp',
                    y=['company_count', 'wifi_companies'],
                    title="ステータス別WiFi需要分析",
                    barmode='group'
                )
                st.plotly_chart(fig_wifi, use_container_width=True)
    
    # 戦略ターゲット企業リスト
    st.markdown("### 🎯 戦略ターゲット企業（優先度順）")
    
    strategic_targets = st.session_state.company_manager.get_companies_by_criteria(
        min_priority=80, limit=10
    )
    
    if not strategic_targets.empty:
        # 重要カラムのみ表示
        display_columns = ['name', 'industry', 'status', 'picoCela_score', 'priority_score', 'wifi_required', 'contact_person']
        available_columns = [col for col in display_columns if col in strategic_targets.columns]
        
        # WiFi需要を視覚的に表示
        if 'wifi_required' in strategic_targets.columns:
            strategic_targets['WiFi需要'] = strategic_targets['wifi_required'].apply(
                lambda x: "🔥 高需要" if x == 1 else "📊 通常"
            )
        
        st.dataframe(
            strategic_targets[available_columns + (['WiFi需要'] if 'wifi_required' in strategic_targets.columns else [])],
            use_container_width=True,
            column_config={
                "name": "企業名",
                "industry": "業界",
                "status": "ステータス",
                "picoCela_score": st.column_config.NumberColumn("関連度", format="%.0f点"),
                "priority_score": st.column_config.NumberColumn("優先度", format="%.0f点"),
                "contact_person": "担当者",
                "WiFi需要": "WiFi需要"
            }
        )
    else:
        st.info("戦略ターゲット基準を満たす企業がありません。条件を調整してください。")

def show_company_management():
    """企業管理画面（PicoCELA戦略特化）"""
    if not st.session_state.company_manager or not st.session_state.company_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 🏢 PicoCELA戦略企業管理")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ 企業追加", "✏️ ステータス管理", "📋 企業一覧", "🎯 戦略分析"])
    
    with tab1:
        show_add_company()
    
    with tab2:
        show_status_management()
    
    with tab3:
        show_company_list()
    
    with tab4:
        show_strategic_analysis()

def show_add_company():
    """企業追加画面（ENR最適化）"""
    st.markdown("#### ➕ 新規企業追加（PicoCELA関連度自動分析）")
    
    with st.form("add_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("🏢 企業名*", placeholder="例: スマート建設テクノロジー株式会社")
            industry = st.selectbox(
                "🏗️ 業界",
                ["建設業", "建設技術", "製造業", "IT・通信", "不動産", "エネルギー", "運輸・物流", "その他"]
            )
            website = st.text_input("🌐 ウェブサイト", placeholder="https://example.com")
        
        with col2:
            contact_person = st.text_input("👤 担当者名", placeholder="田中太郎")
            email = st.text_input("📧 メールアドレス", placeholder="tanaka@example.com")
            phone = st.text_input("📞 電話番号", placeholder="03-1234-5678")
        
        notes = st.text_area(
            "📝 備考・技術情報", 
            placeholder="IoT、WiFi、メッシュネットワーク、建設現場での技術活用など、PicoCELA関連技術について記載してください。関連度スコアの自動計算に使用されます。",
            height=100
        )
        
        source = st.selectbox(
            "📊 データソース",
            ["Manual", "ENR_Import", "Exhibition", "Referral", "Web_Search", "Other"]
        )
        
        submitted = st.form_submit_button("✅ 企業を追加（自動分析実行）", type="primary")
        
        if submitted:
            if not company_name:
                st.error("❌ 企業名は必須です")
            else:
                company_data = {
                    "name": company_name,
                    "industry": industry,
                    "website": website,
                    "contact_person": contact_person,
                    "email": email,
                    "phone": phone,
                    "notes": notes,
                    "status": "New",
                    "source": source,
                    "description": notes  # ENR分析用
                }
                
                with st.spinner("PicoCELA関連度を自動分析中..."):
                    # 事前分析表示
                    relevance_score, keywords = ENRDataProcessor.calculate_picocela_relevance(company_data)
                    wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
                    priority_score = ENRDataProcessor.calculate_priority_score(company_data)
                    
                    st.info(f"🤖 自動分析結果: 関連度 {relevance_score}点, WiFi需要 {'有' if wifi_required else '無'}, 優先度 {priority_score}点")
                    
                    success, message = st.session_state.company_manager.add_company(company_data)
                    
                    if success:
                        st.success(f"✅ {company_name} を追加しました！")
                        st.session_state.companies_data = st.session_state.company_manager.get_companies()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ 追加失敗: {message}")

def show_status_management():
    """ステータス管理画面（次アクション提案付き）"""
    st.markdown("#### ✏️ ステータス管理（戦略的営業フロー）")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 企業データがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 企業選択
    company_names = df['name'].tolist() if 'name' in df.columns else []
    if not company_names:
        st.warning("表示可能な企業がありません")
        return
        
    selected_company = st.selectbox("🏢 ステータス更新する企業を選択:", company_names)
    
    if selected_company:
        company_row = df[df['name'] == selected_company].iloc[0]
        
        # 現在の戦略情報を表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 現在の戦略情報")
            current_status = company_row.get('status', 'New')
            st.info(f"**ステータス:** {SALES_STATUS.get(current_status, current_status)}")
            
            if 'picoCela_score' in company_row:
                st.info(f"**PicoCELA関連度:** {company_row['picoCela_score']:.0f}点")
            
            if 'priority_score' in company_row:
                st.info(f"**戦略優先度:** {company_row['priority_score']:.0f}点")
            
            if 'wifi_required' in company_row:
                wifi_status = "🔥 高需要" if company_row['wifi_required'] == 1 else "📊 通常"
                st.info(f"**WiFi需要:** {wifi_status}")
        
        with col2:
            st.markdown("#### 🎯 ステータス更新")
            
            # 戦略的ステータス選択
            status_options = list(SALES_STATUS.keys())
            current_index = status_options.index(current_status) if current_status in status_options else 0
            
            new_status = st.selectbox(
                "新しいステータス:",
                status_options,
                index=current_index,
                format_func=lambda x: f"{SALES_STATUS[x]} ({x})"
            )
            
            # 戦略的理由選択
            reason_options = {
                "initial_contact": "初回コンタクト完了",
                "positive_response": "前向きな反応あり",
                "meeting_scheduled": "ミーティング設定",
                "needs_confirmed": "WiFi需要確認済み",
                "proposal_ready": "提案準備完了",
                "budget_confirmed": "予算確認済み",
                "decision_pending": "意思決定待ち",
                "won_contract": "契約獲得",
                "lost_competition": "競合に敗北",
                "dormant_timing": "タイミング不適切"
            }
            
            reason = st.selectbox("更新理由:", list(reason_options.keys()), format_func=lambda x: reason_options[x])
            
            notes = st.text_area("追加メモ:", placeholder="具体的な状況や次回アクションについて記載")
            
            if st.button("🔄 ステータス更新", type="primary"):
                company_id = company_row.get('id', selected_company)
                full_note = f"{reason_options[reason]}. {notes}"
                
                with st.spinner("戦略的ステータス更新中..."):
                    success, message = st.session_state.company_manager.update_company_status(
                        company_id, new_status, full_note
                    )
                    
                    if success:
                        st.success(f"✅ {selected_company} のステータスを更新しました！")
                        
                        # 次のアクション提案を表示
                        next_action = st.session_state.company_manager._suggest_next_action(new_status)
                        if next_action:
                            st.markdown(f"""
                            <div class="strategy-box">
                                <strong>🎯 推奨次アクション:</strong><br>
                                {next_action}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.session_state.companies_data = st.session_state.company_manager.get_companies()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ 更新失敗: {message}")

def show_company_list():
    """企業一覧表示（戦略的フィルタリング）"""
    st.markdown("#### 📋 企業一覧（戦略フィルタリング）")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 企業データがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 戦略的フィルター
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input("🔍 企業名検索:", placeholder="企業名を入力")
    
    with col2:
        if 'status' in df.columns:
            status_filter = st.selectbox("📊 ステータス:", ["全て"] + list(df['status'].unique()))
        else:
            status_filter = "全て"
    
    with col3:
        wifi_filter = st.selectbox("📶 WiFi需要:", ["全て", "需要あり", "需要なし"])
    
    with col4:
        priority_threshold = st.slider("🎯 優先度しきい値:", 0, 150, 50)
    
    # フィルター適用
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]
    
    if status_filter != "全て" and 'status' in df.columns:
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if wifi_filter != "全て" and 'wifi_required' in df.columns:
        wifi_value = 1 if wifi_filter == "需要あり" else 0
        filtered_df = filtered_df[filtered_df['wifi_required'] == wifi_value]
    
    if 'priority_score' in df.columns:
        filtered_df = filtered_df[pd.to_numeric(filtered_df['priority_score'], errors='coerce') >= priority_threshold]
    
    # ソート
    if 'priority_score' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('priority_score', ascending=False)
    
    # 結果表示
    st.markdown(f"**検索結果: {len(filtered_df)}件**")
    
    if not filtered_df.empty:
        # 戦略的表示用カラム
        display_columns = ['name', 'industry', 'status', 'picoCela_score', 'priority_score', 'wifi_required', 'contact_person', 'email']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        # WiFi需要を視覚化
        if 'wifi_required' in filtered_df.columns:
            filtered_df['WiFi需要'] = filtered_df['wifi_required'].apply(
                lambda x: "🔥" if x == 1 else "📊"
            )
            available_columns.append('WiFi需要')
        
        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True,
            column_config={
                "name": "企業名",
                "industry": "業界",
                "status": "ステータス",
                "picoCela_score": st.column_config.NumberColumn("関連度", format="%.0f"),
                "priority_score": st.column_config.NumberColumn("優先度", format="%.0f"),
                "contact_person": "担当者",
                "email": "メール",
                "WiFi需要": "WiFi"
            }
        )
    else:
        st.info("フィルター条件に一致する企業がありません。")

def show_strategic_analysis():
    """戦略分析画面"""
    st.markdown("#### 🎯 PicoCELA戦略分析")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 分析するデータがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 戦略的分析メトリクス
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'picoCela_score' in df.columns:
            avg_relevance = pd.to_numeric(df['picoCela_score'], errors='coerce').mean()
            st.metric("平均関連度", f"{avg_relevance:.1f}点")
        
        if 'wifi_required' in df.columns:
            wifi_rate = (df['wifi_required'].sum() / len(df) * 100)
            st.metric("WiFi需要率", f"{wifi_rate:.1f}%")
    
    with col2:
        if 'priority_score' in df.columns:
            high_priority = len(df[pd.to_numeric(df['priority_score'], errors='coerce') >= 100])
            st.metric("戦略ターゲット数", f"{high_priority}社")
        
        if 'status' in df.columns:
            qualified_plus = len(df[df['status'].isin(['Qualified', 'Proposal', 'Negotiation', 'Won'])])
            conversion_rate = (qualified_plus / len(df) * 100) if len(df) > 0 else 0
            st.metric("有望化率", f"{conversion_rate:.1f}%")
    
    with col3:
        if 'status' in df.columns:
            won_count = len(df[df['status'] == 'Won'])
            win_rate = (won_count / len(df) * 100) if len(df) > 0 else 0
            st.metric("受注率", f"{win_rate:.1f}%")
    
    # 戦略的ビジュアライゼーション
    tab1, tab2, tab3 = st.tabs(["📊 関連度分析", "📶 WiFi戦略分析", "🎯 優先度マトリクス"])
    
    with tab1:
        if 'picoCela_score' in df.columns:
            st.markdown("##### PicoCELA関連度分布")
            
            relevance_scores = pd.to_numeric(df['picoCela_score'], errors='coerce').dropna()
            
            fig_hist = px.histogram(
                x=relevance_scores,
                nbins=20,
                title="PicoCELA関連度スコア分布",
                labels={'x': '関連度スコア', 'y': '企業数'},
                color_discrete_sequence=['#FF6B6B']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 高関連度企業
            high_relevance = df[pd.to_numeric(df['picoCela_score'], errors='coerce') >= 70]
            if not high_relevance.empty:
                st.markdown("##### 🌟 高関連度企業（70点以上）")
                display_cols = ['name', 'industry', 'status', 'picoCela_score', 'priority_score']
                available_cols = [col for col in display_cols if col in high_relevance.columns]
                st.dataframe(high_relevance[available_cols], use_container_width=True)
    
    with tab2:
        if 'wifi_required' in df.columns and 'status' in df.columns:
            st.markdown("##### WiFi需要企業の営業ステータス分析")
            
            wifi_status_analysis = df.groupby(['status', 'wifi_required']).size().reset_index(name='count')
            
            fig_wifi = px.bar(
                wifi_status_analysis,
                x='status',
                y='count',
                color='wifi_required',
                title="ステータス別WiFi需要分析",
                color_discrete_map={0: '#95a5a6', 1: '#e74c3c'},
                labels={'wifi_required': 'WiFi需要', 'count': '企業数'}
            )
            st.plotly_chart(fig_wifi, use_container_width=True)
            
            # WiFi戦略企業リスト
            wifi_companies = df[df['wifi_required'] == 1]
            if not wifi_companies.empty:
                st.markdown("##### 🔥 WiFi需要企業リスト")
                display_cols = ['name', 'industry', 'status', 'picoCela_score', 'contact_person']
                available_cols = [col for col in display_cols if col in wifi_companies.columns]
                st.dataframe(wifi_companies[available_cols], use_container_width=True)
    
    with tab3:
        if 'picoCela_score' in df.columns and 'priority_score' in df.columns:
            st.markdown("##### 戦略的優先度マトリクス")
            
            # 散布図で関連度 vs 優先度
            fig_scatter = px.scatter(
                df,
                x='picoCela_score',
                y='priority_score',
                color='status',
                size='wifi_required',
                hover_data=['name'],
                title="PicoCELA関連度 vs 戦略優先度マトリクス",
                labels={'picoCela_score': 'PicoCELA関連度', 'priority_score': '戦略優先度'}
            )
            
            # 戦略ゾーンの線を追加
            fig_scatter.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="高優先度ライン")
            fig_scatter.add_vline(x=70, line_dash="dash", line_color="orange", annotation_text="高関連度ライン")
            
            st.plotly_chart(fig_scatter, use_container_width=True)

def show_data_import():
    """データインポート画面（ENR最適化）"""
    if not st.session_state.company_manager or not st.session_state.company_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 📁 ENRデータインポート（PicoCELA自動分析）")
    
    st.markdown("""
    **📋 ENR対応フォーマット:**
    - CSV ファイル（ENRエクスポート対応）
    - Excel ファイル (.xlsx, .xls)
    
    **🤖 自動分析機能:**
    - PicoCELA関連度スコア自動計算
    - WiFi需要自動判定
    - 戦略優先度自動設定
    
    **📝 推奨カラム:**
    - 企業名 (company_name, name, 会社名)
    - 業界 (industry, 業界)
    - ウェブサイト (website, website_url)
    - 説明・技術情報 (description, notes, 備考)
    """)
    
    uploaded_file = st.file_uploader(
        "📎 ENRファイルを選択してください",
        type=['csv', 'xlsx', 'xls'],
        help="ENRデータまたは企業リストファイルをアップロードしてください"
    )
    
    if uploaded_file is not None:
        try:
            # ファイル読み込み
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.markdown("#### 📊 データプレビュー")
            st.dataframe(df.head(10), use_container_width=True)
            
            # 自動カラム推定
            st.markdown("#### 🔗 カラムマッピング（自動推定）")
            
            def auto_detect_column(df, candidates):
                """カラム名の自動推定"""
                for candidate in candidates:
                    for col in df.columns:
                        if candidate.lower() in col.lower():
                            return col
                return ''
            
            col1, col2 = st.columns(2)
            
            with col1:
                name_candidates = ['company_name', 'name', '会社名', '企業名', 'company']
                auto_name = auto_detect_column(df, name_candidates)
                name_col = st.selectbox("企業名カラム:", df.columns.tolist(), 
                                      index=df.columns.tolist().index(auto_name) if auto_name else 0)
                
                industry_candidates = ['industry', '業界', 'sector']
                auto_industry = auto_detect_column(df, industry_candidates)
                industry_col = st.selectbox("業界カラム:", [''] + df.columns.tolist(),
                                          index=df.columns.tolist().index(auto_industry) + 1 if auto_industry else 0)
                
                email_candidates = ['email', 'mail', 'メール']
                auto_email = auto_detect_column(df, email_candidates)
                email_col = st.selectbox("メールカラム:", [''] + df.columns.tolist(),
                                       index=df.columns.tolist().index(auto_email) + 1 if auto_email else 0)
            
            with col2:
                contact_candidates = ['contact', 'person', '担当者', 'representative']
                auto_contact = auto_detect_column(df, contact_candidates)
                contact_col = st.selectbox("担当者カラム:", [''] + df.columns.tolist(),
                                         index=df.columns.tolist().index(auto_contact) + 1 if auto_contact else 0)
                
                website_candidates = ['website', 'url', 'web', 'ウェブサイト']
                auto_website = auto_detect_column(df, website_candidates)
                website_col = st.selectbox("ウェブサイトカラム:", [''] + df.columns.tolist(),
                                         index=df.columns.tolist().index(auto_website) + 1 if auto_website else 0)
                
                desc_candidates = ['description', 'notes', '備考', 'details', 'technology']
                auto_desc = auto_detect_column(df, desc_candidates)
                description_col = st.selectbox("説明・技術情報カラム:", [''] + df.columns.tolist(),
                                             index=df.columns.tolist().index(auto_desc) + 1 if auto_desc else 0)
            
            # ENR分析プレビュー
            if st.button("🤖 PicoCELA関連度プレビュー（先頭5社）", type="secondary"):
                preview_companies = []
                for i, (_, row) in enumerate(df.head(5).iterrows()):
                    company_data = {
                        "name": str(row[name_col]) if pd.notna(row[name_col]) else "",
                        "industry": str(row[industry_col]) if industry_col and pd.notna(row[industry_col]) else "",
                        "description": str(row[description_col]) if description_col and pd.notna(row[description_col]) else "",
                        "website": str(row[website_col]) if website_col and pd.notna(row[website_col]) else ""
                    }
                    
                    if company_data["name"]:
                        relevance, keywords = ENRDataProcessor.calculate_picocela_relevance(company_data)
                        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
                        priority = ENRDataProcessor.calculate_priority_score(company_data)
                        
                        preview_companies.append({
                            "企業名": company_data["name"],
                            "関連度": f"{relevance}点",
                            "WiFi需要": "🔥 有" if wifi_required else "📊 無",
                            "優先度": f"{priority}点",
                            "マッチキーワード": ", ".join(keywords[:3]) if keywords else "なし"
                        })
                
                if preview_companies:
                    st.markdown("##### 🤖 自動分析プレビュー")
                    st.dataframe(pd.DataFrame(preview_companies), use_container_width=True)
            
            # 一括インポート
            if st.button("📥 ENRデータ一括インポート（PicoCELA分析実行）", type="primary"):
                with st.spinner("ENRデータをPicoCELA戦略分析中..."):
                    companies_to_import = []
                    
                    progress_bar = st.progress(0)
                    total_rows = len(df)
                    
                    for i, (_, row) in enumerate(df.iterrows()):
                        company_data = {
                            "name": str(row[name_col]) if pd.notna(row[name_col]) else "",
                            "industry": str(row[industry_col]) if industry_col and pd.notna(row[industry_col]) else "",
                            "email": str(row[email_col]) if email_col and pd.notna(row[email_col]) else "",
                            "contact_person": str(row[contact_col]) if contact_col and pd.notna(row[contact_col]) else "",
                            "website": str(row[website_col]) if website_col and pd.notna(row[website_col]) else "",
                            "description": str(row[description_col]) if description_col and pd.notna(row[description_col]) else "",
                            "notes": str(row[description_col]) if description_col and pd.notna(row[description_col]) else "",
                            "status": "New",
                            "source": "ENR_Import"
                        }
                        
                        if company_data["name"]:
                            companies_to_import.append(company_data)
                        
                        progress_bar.progress((i + 1) / total_rows)
                    
                    if companies_to_import:
                        success, message = st.session_state.company_manager.import_bulk_data(companies_to_import)
                        
                        if success:
                            st.success(f"✅ {len(companies_to_import)}社のENRデータをPicoCELA分析付きでインポートしました！")
                            
                            # 分析結果サマリー
                            analysis_summary = []
                            for company in companies_to_import:
                                relevance, _ = ENRDataProcessor.calculate_picocela_relevance(company)
                                wifi_required = ENRDataProcessor.detect_wifi_requirement(company)
                                if relevance >= 70:
                                    analysis_summary.append(f"🌟 {company['name']}: 関連度{relevance}点")
                                if wifi_required:
                                    analysis_summary.append(f"🔥 {company['name']}: WiFi需要あり")
                            
                            if analysis_summary:
                                st.markdown("##### 🎯 注目企業（自動抽出）")
                                for item in analysis_summary[:10]:  # 上位10社
                                    st.info(item)
                            
                            st.session_state.companies_data = st.session_state.company_manager.get_companies()
                        else:
                            st.error(f"❌ インポート失敗: {message}")
                    else:
                        st.warning("⚠️ インポート可能なデータがありません")
        
        except Exception as e:
            st.error(f"❌ ファイル処理エラー: {str(e)}")

def show_analytics():
    """分析・レポート画面（PicoCELA戦略特化）"""
    if not st.session_state.company_manager or not st.session_state.company_manager.is_connected:
        st.error("❌ Google Sheetsに接続されていません")
        return
    
    st.markdown("### 📈 PicoCELA戦略分析・レポート")
    
    companies = st.session_state.companies_data
    if not companies:
        st.warning("📋 分析するデータがありません")
        return
    
    df = pd.DataFrame(companies)
    
    # 数値型変換
    for col in ['picoCela_score', 'priority_score', 'wifi_required']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # エグゼクティブサマリー
    st.markdown("### 📊 エグゼクティブサマリー")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_companies = len(df)
        st.metric("総企業数", total_companies)
    
    with col2:
        if 'picoCela_score' in df.columns:
            avg_relevance = df['picoCela_score'].mean()
            st.metric("平均関連度", f"{avg_relevance:.1f}点")
        else:
            st.metric("平均関連度", "N/A")
    
    with col3:
        if 'wifi_required' in df.columns:
            wifi_companies = len(df[df['wifi_required'] == 1])
            wifi_rate = (wifi_companies / total_companies * 100) if total_companies > 0 else 0
            st.metric("WiFi需要企業", f"{wifi_companies}社", f"{wifi_rate:.1f}%")
        else:
            st.metric("WiFi需要企業", "N/A")
    
    with col4:
        if 'priority_score' in df.columns:
            strategic_targets = len(df[df['priority_score'] >= 100])
            strategic_rate = (strategic_targets / total_companies * 100) if total_companies > 0 else 0
            st.metric("戦略ターゲット", f"{strategic_targets}社", f"{strategic_rate:.1f}%")
        else:
            st.metric("戦略ターゲット", "N/A")
    
    # 詳細分析タブ
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 戦略分析", "📊 セグメント分析", "📈 パフォーマンス分析", "📋 レポート出力"])
    
    with tab1:
        show_strategic_deep_analysis(df)
    
    with tab2:
        show_segment_analysis(df)
    
    with tab3:
        show_performance_analysis(df)
    
    with tab4:
        show_report_export(df)

def show_strategic_deep_analysis(df):
    """戦略的詳細分析"""
    st.markdown("#### 🎯 PicoCELA戦略的詳細分析")
    
    if 'picoCela_score' in df.columns and 'priority_score' in df.columns:
        # 戦略マトリクス
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 戦略ポジショニングマトリクス")
            
            # 4象限分析
            high_rel_high_pri = df[(df['picoCela_score'] >= 70) & (df['priority_score'] >= 100)]
            high_rel_low_pri = df[(df['picoCela_score'] >= 70) & (df['priority_score'] < 100)]
            low_rel_high_pri = df[(df['picoCela_score'] < 70) & (df['priority_score'] >= 100)]
            low_rel_low_pri = df[(df['picoCela_score'] < 70) & (df['priority_score'] < 100)]
            
            st.write(f"🟢 **スターターゲット** (高関連度・高優先度): {len(high_rel_high_pri)}社")
            st.write(f"🟡 **育成対象** (高関連度・低優先度): {len(high_rel_low_pri)}社")
            st.write(f"🟠 **機会探索** (低関連度・高優先度): {len(low_rel_high_pri)}社")
            st.write(f"⚪ **低優先度** (低関連度・低優先度): {len(low_rel_low_pri)}社")
        
        with col2:
            # 戦略的推奨アクション
            st.markdown("##### 🎯 戦略的推奨アクション")
            
            if len(high_rel_high_pri) > 0:
                st.success(f"**即座アプローチ**: {len(high_rel_high_pri)}社のスターターゲットに集中営業")
            
            if len(high_rel_low_pri) > 0:
                st.info(f"**関係構築**: {len(high_rel_low_pri)}社との長期的関係構築")
            
            if len(low_rel_high_pri) > 0:
                st.warning(f"**ニーズ発掘**: {len(low_rel_high_pri)}社の潜在ニーズ確認")
            
            # WiFi戦略
            if 'wifi_required' in df.columns:
                wifi_stars = high_rel_high_pri[high_rel_high_pri['wifi_required'] == 1]
                if len(wifi_stars) > 0:
                    st.error(f"**最優先**: {len(wifi_stars)}社のWiFi需要スターターゲット")
        
        # マトリクス散布図
        fig_matrix = px.scatter(
            df,
            x='picoCela_score',
            y='priority_score',
            color='status',
            size='wifi_required',
            hover_data=['name'] if 'name' in df.columns else [],
            title="PicoCELA戦略ポジショニングマトリクス",
            labels={'picoCela_score': 'PicoCELA関連度', 'priority_score': '戦略優先度'},
            width=800,
            height=500
        )
        
        # 戦略ゾーンライン
        fig_matrix.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="高優先度ライン (100点)")
        fig_matrix.add_vline(x=70, line_dash="dash", line_color="orange", annotation_text="高関連度ライン (70点)")
        
        # 背景色で4象限を表示
        fig_matrix.add_shape(type="rect", x0=70, y0=100, x1=100, y1=150, 
                           fillcolor="green", opacity=0.1, line_width=0)
        fig_matrix.add_annotation(x=85, y=125, text="スター<br>ターゲット", showarrow=False, 
                                font=dict(size=12, color="green"))
        
        st.plotly_chart(fig_matrix, use_container_width=True)

def show_segment_analysis(df):
    """セグメント分析"""
    st.markdown("#### 📊 セグメント別戦略分析")
    
    # 業界別分析
    if 'industry' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🏗️ 業界別分析")
            
            industry_analysis = df.groupby('industry').agg({
                'name': 'count',
                'picoCela_score': 'mean',
                'priority_score': 'mean',
                'wifi_required': 'sum'
            }).round(2)
            industry_analysis.columns = ['企業数', '平均関連度', '平均優先度', 'WiFi需要数']
            
            st.dataframe(industry_analysis, use_container_width=True)
        
        with col2:
            # 業界別関連度
            industry_avg = df.groupby('industry')['picoCela_score'].mean().sort_values(ascending=True)
            
            fig_industry = px.bar(
                x=industry_avg.values,
                y=industry_avg.index,
                orientation='h',
                title="業界別平均PicoCELA関連度",
                labels={'x': '平均関連度', 'y': '業界'},
                color=industry_avg.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_industry, use_container_width=True)
    
    # ステータス別分析
    if 'status' in df.columns:
        st.markdown("##### 📈 営業ステータス別戦略分析")
        
        status_analysis = df.groupby('status').agg({
            'name': 'count',
            'picoCela_score': 'mean',
            'priority_score': 'mean',
            'wifi_required': 'sum'
        }).round(2)
        status_analysis.columns = ['企業数', '平均関連度', '平均優先度', 'WiFi需要数']
        
        # ステータス日本語化
        status_analysis.index = [SALES_STATUS.get(idx, idx) for idx in status_analysis.index]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(status_analysis, use_container_width=True)
        
        with col2:
            # ステータス別進捗
            fig_funnel = px.funnel(
                x=status_analysis['企業数'],
                y=status_analysis.index,
                title="営業ファネル分析"
            )
            st.plotly_chart(fig_funnel, use_container_width=True)

def show_performance_analysis(df):
    """パフォーマンス分析"""
    st.markdown("#### 📈 営業パフォーマンス分析")
    
    if 'status' in df.columns:
        # コンバージョン分析
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🎯 コンバージョン率分析")
            
            total = len(df)
            contacted = len(df[df['status'].isin(['Contacted', 'Replied', 'Engaged', 'Qualified', 'Proposal', 'Negotiation', 'Won'])])
            engaged = len(df[df['status'].isin(['Engaged', 'Qualified', 'Proposal', 'Negotiation', 'Won'])])
            qualified = len(df[df['status'].isin(['Qualified', 'Proposal', 'Negotiation', 'Won'])])
            won = len(df[df['status'] == 'Won'])
            
            conversion_data = {
                'ステージ': ['総企業数', 'コンタクト済み', 'エンゲージ済み', '有望企業', '受注'],
                '企業数': [total, contacted, engaged, qualified, won],
                'コンバージョン率': [100, (contacted/total*100) if total > 0 else 0, 
                              (engaged/total*100) if total > 0 else 0,
                              (qualified/total*100) if total > 0 else 0,
                              (won/total*100) if total > 0 else 0]
            }
            
            conversion_df = pd.DataFrame(conversion_data)
            st.dataframe(conversion_df, use_container_width=True)
        
        with col2:
            # WiFi特化パフォーマンス
            if 'wifi_required' in df.columns:
                st.markdown("##### 🔥 WiFi需要企業パフォーマンス")
                
                wifi_df = df[df['wifi_required'] == 1]
                non_wifi_df = df[df['wifi_required'] == 0]
                
                wifi_metrics = {
                    'メトリクス': ['企業数', '平均関連度', '有望化率', '受注率'],
                    'WiFi需要あり': [
                        len(wifi_df),
                        wifi_df['picoCela_score'].mean() if len(wifi_df) > 0 else 0,
                        len(wifi_df[wifi_df['status'].isin(['Qualified', 'Proposal', 'Negotiation', 'Won'])]) / len(wifi_df) * 100 if len(wifi_df) > 0 else 0,
                        len(wifi_df[wifi_df['status'] == 'Won']) / len(wifi_df) * 100 if len(wifi_df) > 0 else 0
                    ],
                    'WiFi需要なし': [
                        len(non_wifi_df),
                        non_wifi_df['picoCela_score'].mean() if len(non_wifi_df) > 0 else 0,
                        len(non_wifi_df[non_wifi_df['status'].isin(['Qualified', 'Proposal', 'Negotiation', 'Won'])]) / len(non_wifi_df) * 100 if len(non_wifi_df) > 0 else 0,
                        len(non_wifi_df[non_wifi_df['status'] == 'Won']) / len(non_wifi_df) * 100 if len(non_wifi_df) > 0 else 0
                    ]
                }
                
                wifi_metrics_df = pd.DataFrame(wifi_metrics)
                st.dataframe(wifi_metrics_df, use_container_width=True)
    
    # トレンド分析（作成日時がある場合）
    if 'created_date' in df.columns:
        st.markdown("##### 📅 時系列トレンド分析")
        
        try:
            df['created_date'] = pd.to_datetime(df['created_date'])
            df['月'] = df['created_date'].dt.to_period('M')
            
            monthly_trend = df.groupby('月').agg({
                'name': 'count',
                'picoCela_score': 'mean',
                'wifi_required': 'sum'
            }).reset_index()
            
            monthly_trend['月'] = monthly_trend['月'].astype(str)
            
            fig_trend = px.line(
                monthly_trend,
                x='月',
                y=['name', 'wifi_required'],
                title="月別企業追加数とWiFi需要企業数",
                labels={'value': '企業数', '月': '月'}
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
        except Exception as e:
            st.info("時系列分析: 日付データの形式を確認できませんでした")

def show_report_export(df):
    """レポート出力"""
    st.markdown("#### 📋 戦略レポート出力")
    
    # レポート生成オプション
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📊 出力オプション")
        
        report_type = st.selectbox(
            "レポート種類:",
            ["エグゼクティブサマリー", "詳細分析レポート", "戦略ターゲットリスト", "WiFi戦略レポート"]
        )
        
        format_type = st.selectbox(
            "出力形式:",
            ["CSV", "Excel"]
        )
        
        if st.button("📥 レポート生成", type="primary"):
            if report_type == "エグゼクティブサマリー":
                export_data = generate_executive_summary(df)
            elif report_type == "詳細分析レポート":
                export_data = generate_detailed_analysis(df)
            elif report_type == "戦略ターゲットリスト":
                export_data = generate_strategic_targets(df)
            else:  # WiFi戦略レポート
                export_data = generate_wifi_strategy_report(df)
            
            if format_type == "CSV":
                csv_data = export_data.to_csv(index=False)
                st.download_button(
                    label="📁 CSVダウンロード",
                    data=csv_data,
                    file_name=f"picocela_{report_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                # Excelの場合はバイト形式で出力
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    export_data.to_excel(writer, sheet_name='PicoCELA戦略分析', index=False)
                
                st.download_button(
                    label="📁 Excelダウンロード",
                    data=buffer.getvalue(),
                    file_name=f"picocela_{report_type}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        st.markdown("##### 🎯 アクションアイテム")
        
        # 自動生成されたアクションアイテム
        action_items = generate_action_items(df)
        
        for i, item in enumerate(action_items, 1):
            st.markdown(f"**{i}.** {item}")

def generate_executive_summary(df):
    """エグゼクティブサマリー生成"""
    summary_data = []
    
    if 'status' in df.columns:
        for status in df['status'].unique():
            status_df = df[df['status'] == status]
            summary_data.append({
                'ステータス': SALES_STATUS.get(status, status),
                '企業数': len(status_df),
                '平均関連度': status_df['picoCela_score'].mean() if 'picoCela_score' in status_df.columns else 0,
                '平均優先度': status_df['priority_score'].mean() if 'priority_score' in status_df.columns else 0,
                'WiFi需要企業数': status_df['wifi_required'].sum() if 'wifi_required' in status_df.columns else 0
            })
    
    return pd.DataFrame(summary_data)

def generate_detailed_analysis(df):
    """詳細分析レポート生成"""
    # 重要カラムを選択
    columns = ['name', 'industry', 'status', 'picoCela_score', 'priority_score', 'wifi_required', 'contact_person', 'email']
    available_columns = [col for col in columns if col in df.columns]
    
    detailed_df = df[available_columns].copy()
    
    # 日本語化
    if 'status' in detailed_df.columns:
        detailed_df['status'] = detailed_df['status'].map(SALES_STATUS)
    
    if 'wifi_required' in detailed_df.columns:
        detailed_df['wifi_required'] = detailed_df['wifi_required'].apply(lambda x: 'あり' if x == 1 else 'なし')
    
    return detailed_df

def generate_strategic_targets(df):
    """戦略ターゲットリスト生成"""
    if 'priority_score' in df.columns:
        strategic_df = df[pd.to_numeric(df['priority_score'], errors='coerce') >= 100].copy()
        strategic_df = strategic_df.sort_values('priority_score', ascending=False)
        
        columns = ['name', 'industry', 'status', 'picoCela_score', 'priority_score', 'wifi_required', 'contact_person', 'email']
        available_columns = [col for col in columns if col in strategic_df.columns]
        
        return strategic_df[available_columns]
    else:
        return pd.DataFrame()

def generate_wifi_strategy_report(df):
    """WiFi戦略レポート生成"""
    if 'wifi_required' in df.columns:
        wifi_df = df[df['wifi_required'] == 1].copy()
        wifi_df = wifi_df.sort_values('picoCela_score', ascending=False) if 'picoCela_score' in wifi_df.columns else wifi_df
        
        columns = ['name', 'industry', 'status', 'picoCela_score', 'priority_score', 'contact_person', 'email', 'notes']
        available_columns = [col for col in columns if col in wifi_df.columns]
        
        return wifi_df[available_columns]
    else:
        return pd.DataFrame()

def generate_action_items(df):
    """アクションアイテム自動生成"""
    action_items = []
    
    # 戦略ターゲットのアクション
    if 'priority_score' in df.columns:
        high_priority = df[pd.to_numeric(df['priority_score'], errors='coerce') >= 100]
        if len(high_priority) > 0:
            action_items.append(f"**優先度100点以上の{len(high_priority)}社に即座アプローチ開始**")
    
    # WiFi需要企業のアクション
    if 'wifi_required' in df.columns:
        wifi_companies = df[df['wifi_required'] == 1]
        new_wifi = wifi_companies[wifi_companies['status'] == 'New'] if 'status' in wifi_companies.columns else wifi_companies
        if len(new_wifi) > 0:
            action_items.append(f"**WiFi需要{len(new_wifi)}社への初回コンタクト実施**")
    
    # ステータス別アクション
    if 'status' in df.columns:
        replied_companies = df[df['status'] == 'Replied']
        if len(replied_companies) > 0:
            action_items.append(f"**返信済み{len(replied_companies)}社とのミーティング設定**")
        
        engaged_companies = df[df['status'] == 'Engaged']
        if len(engaged_companies) > 0:
            action_items.append(f"**継続対話中{len(engaged_companies)}社への提案書準備**")
    
    # 業界特化アクション
    if 'industry' in df.columns and 'picoCela_score' in df.columns:
        construction_high = df[(df['industry'] == '建設業') & (pd.to_numeric(df['picoCela_score'], errors='coerce') >= 70)]
        if len(construction_high) > 0:
            action_items.append(f"**建設業界高関連度{len(construction_high)}社への業界特化提案作成**")
    
    if not action_items:
        action_items.append("**データの蓄積を継続し、戦略的分析の精度向上を図る**")
    
    return action_items

def main():
    """メイン関数"""
    # セッション状態初期化
    init_session_state()
    
    # サイドバーメニュー
    with st.sidebar:
        st.markdown("### 🚀 FusionCRM - PicoCELA")
        st.markdown("**建設業界ENR特化営業管理**")
        
        menu_options = [
            "📊 戦略ダッシュボード",
            "🏢 企業管理",
            "📁 ENRデータインポート",
            "📈 戦略分析・レポート",
            "⚙️ システム設定"
        ]
        
        selected_menu = st.radio("メニュー選択:", menu_options)
        
        st.markdown("---")
        
        # 接続状態表示
        if st.session_state.company_manager and st.session_state.company_manager.is_connected:
            st.success("✅ Google Sheets 接続中")
            
            # PicoCELA戦略統計
            if st.session_state.companies_data:
                st.markdown("### 🎯 PicoCELA戦略統計")
                df = pd.DataFrame(st.session_state.companies_data)
                
                # 数値型変換
                for col in ['picoCela_score', 'priority_score', 'wifi_required']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                st.metric("総企業数", len(df))
                
                if 'wifi_required' in df.columns:
                    wifi_count = len(df[df['wifi_required'] == 1])
                    st.metric("WiFi需要企業", wifi_count)
                
                if 'priority_score' in df.columns:
                    strategic_count = len(df[df['priority_score'] >= 100])
                    st.metric("戦略ターゲット", strategic_count)
                
                if 'picoCela_score' in df.columns:
                    avg_relevance = df['picoCela_score'].mean()
                    st.metric("平均関連度", f"{avg_relevance:.1f}")
        else:
            st.error("❌ 未接続")
            st.markdown("⚙️ システム設定から接続してください")
    
    # メイン画面表示
    try:
        if selected_menu == "📊 戦略ダッシュボード":
            show_dashboard()
        elif selected_menu == "🏢 企業管理":
            show_company_management()
        elif selected_menu == "📁 ENRデータインポート":
            show_data_import()
        elif selected_menu == "📈 戦略分析・レポート":
            show_analytics()
        elif selected_menu == "⚙️ システム設定":
            show_connection_setup()
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("💡 システム設定で接続を確認してください")
        
        # デバッグ情報
        with st.expander("🔧 デバッグ情報"):
            st.text(f"エラー詳細: {str(e)}")
            st.text(f"接続状態: {st.session_state.company_manager is not None}")
            if st.session_state.company_manager:
                st.text(f"接続確認: {st.session_state.company_manager.is_connected}")

if __name__ == "__main__":
    main()
