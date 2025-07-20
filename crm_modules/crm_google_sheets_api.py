"""
Google Sheets API管理モジュール
fusion_crm_main.pyから抽出
"""

import streamlit as st
import requests
import json
import time

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
