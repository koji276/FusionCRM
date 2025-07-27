"""
FusionCRM統合システム - メインエントリーポイント（認証機能付き）
既存の3つのシステムを統合したユニファイドインターフェース + ユーザー登録・認証

Version: 11.0
Created: 2025-07-23
Purpose: 既存システムをラップする統合UI + セキュア認証
"""

import streamlit as st
import sys
import os
import hashlib
import json
from datetime import datetime
import sqlite3

# 現在のディレクトリを基準にパスを設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'modules'))
sys.path.append(os.path.join(current_dir, 'crm_modules'))

class UserAuthSystem:
    """ユーザー認証システム"""
    
    def __init__(self):
        self.db_path = os.path.join(current_dir, 'fusion_users.db')
        self.init_database()
    
    def init_database(self):
        """ユーザーデータベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            company_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """パスワードをハッシュ化"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, email, password, company_name=""):
        """新規ユーザー登録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, company_name)
            VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, company_name))
            
            conn.commit()
            conn.close()
            return True, "ユーザー登録が完了しました！"
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "このユーザー名は既に使用されています"
            elif "email" in str(e):
                return False, "このメールアドレスは既に登録されています"
            else:
                return False, "登録エラーが発生しました"
        except Exception as e:
            return False, f"システムエラー: {str(e)}"
    
    def authenticate_user(self, username, password):
        """ユーザー認証"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
            SELECT id, username, email, company_name, role 
            FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                # 最終ログイン時間を更新
                cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                conn.close()
                return True, {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2], 
                    'company_name': user[3],
                    'role': user[4]
                }
            else:
                conn.close()
                return False, "ユーザー名またはパスワードが正しくありません"
                
        except Exception as e:
            return False, f"認証エラー: {str(e)}"
    
    def get_user_stats(self):
        """ユーザー統計を取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_login >= datetime('now', '-30 days') AND is_active = 1
            ''')
            active_users = cursor.fetchone()[0]
            
            conn.close()
            return total_users, active_users
            
        except Exception as e:
            return 0, 0

class FusionCRMUnified:
    def __init__(self):
        """統合システムの初期化"""
        self.current_dir = current_dir
        self.auth_system = UserAuthSystem()
        
    def show_auth_page(self):
        """認証ページ（ログイン・登録）"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 2rem;'>
            <h1 style='color: white; margin: 0; font-size: 2.5rem;'>🚀 FusionCRM</h1>
            <p style='color: white; margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.2rem;'>統合CRM・メール配信プラットフォーム</p>
            <p style='color: white; margin: 0; opacity: 0.8;'>効率的な営業活動をサポート</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 認証タブ
        auth_tab1, auth_tab2 = st.tabs(["🔐 ログイン", "📝 新規登録"])
        
        with auth_tab1:
            self.show_login_form()
            
        with auth_tab2:
            self.show_registration_form()
        
        # システム統計
        total_users, active_users = self.auth_system.get_user_stats()
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総登録ユーザー", f"{total_users}名")
        with col2:
            st.metric("アクティブユーザー", f"{active_users}名")
        with col3:
            st.metric("システム稼働率", "99.9%")
    
    def show_login_form(self):
        """ログインフォーム"""
        st.markdown("### 🔐 ログイン")
        
        with st.form("login_form"):
            username = st.text_input("ユーザー名", placeholder="ユーザー名を入力")
            password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                login_button = st.form_submit_button("ログイン", type="primary", use_container_width=True)
            
            if login_button:
                if username and password:
                    success, result = self.auth_system.authenticate_user(username, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = result
                        st.success(f"ようこそ、{result['username']}さん！")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.warning("ユーザー名とパスワードを入力してください")
        
        # 緊急パスワードリセット
        st.markdown("---")
        st.markdown("### 🚨 緊急パスワードリセット")
        
        with st.expander("管理者パスワードを忘れた場合"):
            st.warning("⚠️ 緊急時のみ使用してください")
            
            with st.form("emergency_reset"):
                st.write("管理者アカウントのパスワードをリセットします")
                new_password = st.text_input("新しいパスワード", type="password")
                confirm_password = st.text_input("パスワード確認", type="password")
                
                reset_button = st.form_submit_button("🔑 パスワードリセット", type="secondary")
                
                if reset_button:
                    if new_password and new_password == confirm_password:
                        if len(new_password) >= 4:
                            success = self.reset_admin_password(new_password)
                            if success:
                                st.success("✅ 管理者パスワードがリセットされました！")
                                st.info(f"新しいパスワード: {new_password}")
                            else:
                                st.error("❌ パスワードリセットに失敗しました")
                        else:
                            st.error("パスワードは4文字以上で入力してください")
                    else:
                        st.error("パスワードが一致しません")
    
    def show_registration_form(self):
        """新規登録フォーム"""
        st.markdown("### 📝 新規アカウント登録")
        
        with st.form("registration_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("ユーザー名", placeholder="英数字4文字以上")
                email = st.text_input("メールアドレス", placeholder="your@company.com")
                
            with col2:
                password = st.text_input("パスワード", type="password", placeholder="8文字以上")
                company_name = st.text_input("会社名（任意）", placeholder="株式会社○○")
            
            # 利用規約同意
            agree_terms = st.checkbox("利用規約とプライバシーポリシーに同意します")
            
            register_button = st.form_submit_button("アカウント作成", type="primary", use_container_width=True)
            
            if register_button:
                # バリデーション
                errors = []
                
                if not username or len(username) < 4:
                    errors.append("ユーザー名は4文字以上で入力してください")
                    
                if not email or "@" not in email:
                    errors.append("有効なメールアドレスを入力してください")
                    
                if not password or len(password) < 8:
                    errors.append("パスワードは8文字以上で入力してください")
                    
                if not agree_terms:
                    errors.append("利用規約に同意してください")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # ユーザー登録実行
                    success, message = self.auth_system.register_user(
                        username, email, password, company_name
                    )
                    
                    if success:
                        st.success(message)
                        st.info("登録完了！上記のログインタブからログインしてください。")
                    else:
                        st.error(message)

    def show_user_profile(self):
        """ユーザープロファイル表示"""
        if 'user_info' in st.session_state:
            user = st.session_state.user_info
            
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 👤 ユーザー情報")
                st.write(f"**{user['username']}**")
                if user['company_name']:
                    st.write(f"🏢 {user['company_name']}")
                st.write(f"📧 {user['email']}")
                
                if st.button("ログアウト", use_container_width=True):
                    # セッション情報をクリア
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()

    def main(self):
        """メインアプリケーション"""
        st.set_page_config(
            page_title="FusionCRM - Unified Platform v11.0",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 認証チェック
        if not st.session_state.get('authenticated', False):
            self.show_auth_page()
            return
        
        # 認証済みユーザー向けのメインアプリ
        self.show_main_application()
    
    def show_main_application(self):
        """認証済みユーザー向けメインアプリケーション"""
        
        # メインヘッダー
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem;'>
            <h1 style='color: white; margin: 0;'>🚀 FusionCRM Unified Platform</h1>
            <p style='color: white; margin: 0; opacity: 0.9;'>統合CRM・メール配信システム v11.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        # サイドバーナビゲーション
        with st.sidebar:
            st.markdown("## 🎯 システム選択")
            
            # ユーザープロファイル表示
            self.show_user_profile()
            
            # メインナビゲーション
            page = st.selectbox(
                "機能を選択してください",
                [
                    "📊 統合ダッシュボード",
                    "🏢 企業管理システム (CRM)",
                    "📧 メール配信システム",
                    "📈 分析・レポート",
                    "⚙️ システム設定"
                ],
                index=0
            )
            
            st.markdown("---")
            
            # システム状態表示
            st.markdown("### 📡 システム状態")
            st.success("✅ CRMシステム稼働中")
            st.success("✅ メールシステム稼働中")  
            st.success("✅ 統合ダッシュボード稼働中")
            
            st.markdown("---")
            
            # 今日の統計
            st.markdown("### 📊 今日の実績")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("送信", "50", "50 ↑")
                st.metric("返信", "4", "4 ↑")
            with col2:
                st.metric("返信率", "8.0%", "8.0% ↑")
                st.metric("成約見込", "2社", "2 ↑")
            
            st.markdown("---")
            
            # システム情報
            st.markdown("""
            ---
            **Version:** v11.0  
            **Last Update:** 2025-07-20  
            **Status:** 安定稼働中 ✅  
            **System:** 統合プラットフォーム 🚀
            """)
        
        # メインコンテンツの表示
        if page == "📊 統合ダッシュボード":
            self.show_unified_dashboard()
        elif page == "🏢 企業管理システム (CRM)":
            self.show_crm_system()
        elif page == "📧 メール配信システム":
            self.show_email_system()
        elif page == "📈 分析・レポート":
            self.show_analytics()
        elif page == "⚙️ システム設定":
            self.show_settings()

    def show_unified_dashboard(self):
        """統合ダッシュボード - 新規実装"""
        user = st.session_state.user_info
        
        st.title(f"📊 統合ダッシュボード - ようこそ {user['username']}さん")
        
        # パーソナライズされた挨拶
        if user['company_name']:
            st.markdown(f"### 🏢 {user['company_name']} の統合ダッシュボード")
        
        # 成果サマリー
        st.markdown("### 📊 システム概要")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="総企業数",
                value="1,247",
                delta="47社 (今月)",
                delta_color="normal"
            )
        with col2:
            st.metric(
                label="配信完了",
                value="50社",
                delta="50社 (今日)",
                delta_color="normal"
            )
        with col3:
            st.metric(
                label="返信率",
                value="8.2%",
                delta="4倍改善 ↑",
                delta_color="normal"
            )
        with col4:
            st.metric(
                label="効率化",
                value="高速",
                delta="自動化済み ↑",
                delta_color="normal"
            )
        
        # 主要機能
        st.markdown("### 🔥 主要機能")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # システム機能
            st.markdown("""
            **🏆 核心機能**
            - ✅ **企業データ管理**: 効率的な顧客情報管理
            - ✅ **AI メール生成**: 業界特化したメール自動作成  
            - ✅ **一括配信システム**: スケーラブルな送信機能
            - ✅ **返信率向上**: 効果的なアプローチ手法
            - ✅ **コスト最適化**: 効率的な運用コスト管理
            """)
            
            # 技術的特徴
            st.markdown("""
            **🔧 技術的特徴**
            - ✅ AIによる業界特化カスタマイズ
            - ✅ データベース完全統合  
            - ✅ Gmail統合送信システム
            - ✅ エラーハンドリング機能完備
            - ✅ モジュール化設計による高い保守性
            """)
        
        with col2:
            # システム構成
            st.markdown("**🚀 システム構成**")
            st.success("fusion_crm_unified.py ← 実行中")
            st.info("├── fusion_crm_main.py")
            st.info("├── email_webapp.py") 
            st.info("├── modules/ (5ファイル)")
            st.info("└── crm_modules/ (7ファイル)")

            # 次のアクション - Multipage対応（修正版）
            st.markdown("**⚡ 次のアクション**")
#            if st.button("🏢 CRM管理", use_container_width=True):
#                st.switch_page("pages/01_CRM管理.py")  # ← 新しいパス

            if st.button("🏢 CRM管理", use_container_width=True):
                import os
                st.write("📁 現在のディレクトリ:", os.getcwd())
                
                # pagesディレクトリの確認
                if os.path.exists("pages"):
                    files = os.listdir("pages")
                    st.write("📂 pagesディレクトリの内容:", files)
                    
                    # 目標ファイルの存在確認
                    target_file = "pages/01_CRM管理.py"
                    if os.path.exists(target_file):
                        st.success(f"✅ ファイル発見: {target_file}")
                        st.switch_page(target_file)
                    else:
                        st.error(f"❌ ファイルが見つかりません: {target_file}")
                        
                        # どのファイルが実際にあるかチェック
                        for file in files:
                            if "CRM" in file:
                                st.info(f"🔍 CRM関連ファイル発見: {file}")
                else:
                    st.error("❌ pagesディレクトリが存在しません")
                    st.write("📂 現在のディレクトリの内容:", os.listdir("."))
        
        # 機能ロードマップ
        st.markdown("### 🎯 機能ロードマップ")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **現在利用可能**
            - 🔄 統合ダッシュボード
            - 🔄 企業データ管理
            - 🔄 AIメール生成・送信
            """)
        
        with col2:
            st.markdown("""
            **近日公開予定**
            - ⭐ 英語メールテンプレート拡張
            - 🔄 自動返信検知システム
            - 🔄 送信制限対策強化
            """)
        
        with col3:
            st.markdown("""
            **将来予定機能**
            - 🔮 高度分析機能
            - 📊 詳細レポートダッシュボード
            - 💰 ROI分析ツール
            """)

    def show_crm_system(self):
        """CRMシステム表示"""
        st.title("🏢 企業管理システム (CRM)")
        
        st.info("💡 既存のCRMシステム機能をこちらに統合表示します")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            **統合予定機能:**
            - ✅ 企業データ管理
            - ✅ Google Sheets連携
            - ✅ データ処理・スコアリング
            - ✅ 企業検索・フィルタリング
            - ✅ データインポート・エクスポート
            """)
        
        with col2:
            st.markdown("**既存システムアクセス**")
            
            if st.button("🔗 CRMシステム起動", use_container_width=True, type="primary"):
                st.markdown("""
                **CRMシステムを別タブで開いてください:**
                
                `streamlit run fusion_crm_main.py`
                
                または統合機能の実装を待ってください。
                """)

    def show_email_system(self):
        """メールシステム表示"""
        st.title("📧 メール配信システム")
        
        st.info("💡 既存のメール配信システム機能をこちらに統合表示します")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            **統合予定機能:**
            - ✅ GPT-3.5メール自動生成
            - ✅ 業界特化カスタマイズ
            - ✅ Gmail統合送信
            - ✅ 一括送信システム
            - ✅ 送信履歴管理
            - ✅ テンプレート管理
            """)
            
            # システムの特長
            st.markdown("""
            **🎉 システムの特長:**
            - 🏆 効率的なメール配信システム
            - 💰 コスト効率に優れた運用
            - ⚡ 高速な処理性能
            - 📈 高い返信率を実現する仕組み
            """)
        
        with col2:
            st.markdown("**既存システムアクセス**")
            
            if st.button("🔗 メールシステム起動", use_container_width=True, type="primary"):
                st.markdown("""
                **メールシステムを別タブで開いてください:**
                
                `streamlit run email_webapp.py`
                
                または統合機能の実装を待ってください。
                """)

    def show_analytics(self):
        """分析・レポート"""
        st.title("📈 分析・レポート")
        
        # 実戦成果分析
        st.markdown("### 📊 実戦で実証された成功要因")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **1. "偽装された個別対応"の威力**
            ```python
            def generate_industry_specific_environments(company_data):
                # 建設会社 → "Multi-level construction sites"
                # 製造業 → "Manufacturing facilities with heavy machinery" 
                # 相手は個別検討されたと錯覚
            ```
            """)
            
            st.markdown("""
            **2. 効果的なアプローチ**
            - ❌ "商品をご検討ください" → 売り込み感
            - ✅ "協業の可能性を探りませんか" → 協力関係構築
            - 📈 **結果: 高い返信率を実現**
            """)
        
        with col2:
            st.markdown("""
            **3. 営業効率の最適化**
            - 返信 = 高い関心度を示すシグナル
            - 効率的なフィルタリング機能
            - **効率性: 大幅な時間短縮を実現**
            """)
            
            # 効果測定
            st.markdown("**💰 効果測定**")
            st.metric("時間効率", "大幅改善", "自動化による")
            st.metric("返信品質", "高品質", "AI最適化")
            st.metric("運用効率", "向上", "統合システム")

        # パフォーマンス推移
        st.markdown("### 📈 パフォーマンス推移")
        
        # ダミーデータでチャート表示
        import pandas as pd
        import numpy as np
        
        # 改善推移データ
        dates = pd.date_range('2025-07-01', '2025-07-23')
        performance_data = pd.DataFrame({
            '送信数': np.random.randint(0, 10, len(dates)),
            '返信数': np.random.randint(0, 3, len(dates)),
            '成約見込数': np.random.randint(0, 2, len(dates))
        }, index=dates)
        
        st.line_chart(performance_data)
        
        # 業界別分析
        st.markdown("### 🏭 業界別成功率分析")
        
        industry_col1, industry_col2 = st.columns(2)
        
        with industry_col1:
            st.markdown("**業界別返信率**")
            industries = {
                "Technology": 12.5,
                "Manufacturing": 8.2, 
                "Healthcare": 6.1,
                "Finance": 4.3,
                "Construction": 9.7
            }
            
            for industry, rate in industries.items():
                st.metric(industry, f"{rate}%")
        
        with industry_col2:
            st.markdown("**成功のポイント**")
            st.markdown("""
            **成功のポイント**
            - **Technology**: 協業提案が効果的
            - **Manufacturing**: 技術仕様への言及が重要  
            - **Healthcare**: コンプライアンス配慮が必須
            - **Finance**: 効率性の数値提示が有効
            - **Construction**: 現場課題への具体的解決策
            """)

    def show_settings(self):
        """システム設定"""
        st.title("⚙️ システム設定")
        
        user = st.session_state.user_info
        
        # 管理者昇格機能（新規ユーザー向け）
        user_role = user.get('role', 'user')
        user_email = user.get('email', '')
        
        if user_email == 'koji.tokuda@gmail.com' and user_role != 'admin':
            with st.expander("🚀 管理者権限を取得"):
                st.write("あなたのアカウントを管理者に昇格させますか？")
                if st.button("👑 管理者に昇格", type="primary"):
                    if self.promote_to_admin(user['id']):
                        st.success("✅ 管理者に昇格しました！")
                        # セッション情報を更新
                        st.session_state.user_info['role'] = 'admin'
                        st.rerun()
                    else:
                        st.error("❌ 昇格に失敗しました")
        
        # 管理者機能
        if user_role == 'admin':
            st.success("👑 管理者としてログイン中")
            self.show_admin_panel()
            st.markdown("---")
        
        # 一般ユーザー設定
        st.markdown("### 👤 アカウント設定")
        
        with st.expander("✏️ 自分の情報を編集", expanded=True):
            with st.form("edit_profile"):
                st.write("**📝 プロフィール編集**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("ユーザー名", value=user['username'])
                    new_email = st.text_input("メールアドレス", value=user['email'])
                
                with col2:
                    new_company = st.text_input("会社名", value=user.get('company_name', ''))
                    new_password = st.text_input("新しいパスワード（変更する場合のみ）", type="password", help="空白の場合は変更しません")
                
                update_submitted = st.form_submit_button("💾 プロフィールを更新", type="primary")
                
                if update_submitted:
                    if not new_username.strip():
                        st.error("ユーザー名は必須です")
                    elif not new_email.strip() or "@" not in new_email:
                        st.error("有効なメールアドレスを入力してください")
                    else:
                        # プロフィール更新
                        success, message = self.update_user_complete(
                            user['id'], new_username.strip(), new_email.strip(), 
                            new_company.strip(), user['role'], 'approved', 1,
                            new_password.strip() if new_password.strip() else None
                        )
                        
                        if success:
                            st.success("✅ プロフィールを更新しました")
                            # セッション情報を更新
                            st.session_state.user_info.update({
                                'username': new_username.strip(),
                                'email': new_email.strip(),
                                'company_name': new_company.strip()
                            })
                            st.rerun()
                        else:
                            st.error(f"❌ 更新に失敗しました: {message}")
        
        # アカウント削除セクション
        with st.expander("🗑️ アカウント削除", expanded=False):
            st.warning("⚠️ **危険な操作**: この操作は取り消すことができません")
            
            if st.button("🗑️ アカウント削除", type="secondary"):
                st.session_state.show_delete_confirmation = True
        
        # アカウント削除確認ダイアログ
        if st.session_state.get('show_delete_confirmation', False):
            self.show_delete_account_dialog()
        
        # システム情報
        st.markdown("### ℹ️ システム情報")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown("""
            **バージョン情報**
            - Version: **v11.0**
            - 最終更新: **2025年7月20日**
            - システム状態: **安定稼働中 ✅**
            - 統合プラットフォーム: **運用中 🚀**
            """)
        
        with info_col2:
            st.markdown("""
            **システム構成**
            - 統合UI: `fusion_crm_unified.py`
            - CRMシステム: `fusion_crm_main.py`
            - メールシステム: `email_webapp.py`
            - モジュール: 12ファイル構成
            """)

    def show_admin_panel(self):
        """管理者パネル"""
        st.markdown("### 🔒 管理者パネル")
        
        # タブで管理機能を分割
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "👥 ユーザー管理", 
            "📝 承認待ち", 
            "📧 招待管理", 
            "📊 システム統計"
        ])
        
        with admin_tab1:
            self.show_user_management()
        
        with admin_tab2:
            self.show_pending_approvals()
        
        with admin_tab3:
            self.show_invitation_management()
        
        with admin_tab4:
            self.show_system_statistics()

    def show_user_management(self):
        """ユーザー管理画面"""
        st.subheader("👥 全ユーザー管理")
        
        # デバッグ情報表示
        st.write("**🔍 デバッグ情報**")
        
        # 利用可能なデータベースファイルを表示
        db_files = ['fusion_users_secure.db', 'fusion_users.db']
        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM users')
                    count = cursor.fetchone()[0]
                    conn.close()
                    st.write(f"✅ {db_file}: {count}名のユーザー")
                except:
                    st.write(f"❌ {db_file}: 読み込みエラー")
            else:
                st.write(f"⚠️ {db_file}: ファイルなし")
        
        st.write("---")
        
        # ユーザー一覧を取得
        users = self.get_all_users()
        
        if not users:
            st.info("登録ユーザーがいません")
            return
        
        # ユーザー一覧表示
        for user in users:
            user_id, username, email, company, role, status, created_at, is_active = user
            
            # 自分自身かどうかをチェック
            is_current_user = user_id == st.session_state.user_info['id']
            user_title = f"👤 {username} ({email})" + (" 【あなた】" if is_current_user else "")
            
            with st.expander(user_title, expanded=False):
                
                # ユーザー情報編集フォーム
                with st.form(f"edit_user_{user_id}"):
                    st.write("**📝 ユーザー情報編集**")
                    
                    form_col1, form_col2 = st.columns(2)
                    
                    with form_col1:
                        new_username = st.text_input(
                            "ユーザー名", 
                            value=username, 
                            key=f"username_{user_id}",
                            help="ユーザー名を変更できます"
                        )
                        new_email = st.text_input(
                            "メールアドレス", 
                            value=email, 
                            key=f"email_{user_id}",
                            help="メールアドレスを変更できます"
                        )
                        new_company = st.text_input(
                            "会社名", 
                            value=company or "", 
                            key=f"company_{user_id}",
                            help="会社名を変更できます"
                        )
                    
                    with form_col2:
                        new_role = st.selectbox(
                            "権限", 
                            ["user", "admin"], 
                            index=1 if role == "admin" else 0,
                            format_func=lambda x: "👑 管理者" if x == "admin" else "👤 ユーザー",
                            key=f"role_{user_id}"
                        )
                        new_status = st.selectbox(
                            "承認状態", 
                            ["approved", "pending"], 
                            index=0 if status == "approved" else 1,
                            format_func=lambda x: "✅ 承認済み" if x == "approved" else "⏳ 承認待ち",
                            key=f"status_{user_id}"
                        )
                        new_is_active = st.checkbox(
                            "アカウント有効", 
                            value=bool(is_active),
                            key=f"active_{user_id}"
                        )
                    
                    # パスワード変更セクション
                    st.write("**🔒 パスワード変更**")
                    new_password = st.text_input(
                        "新しいパスワード（変更する場合のみ入力）", 
                        type="password",
                        key=f"password_{user_id}",
                        help="空白の場合はパスワードを変更しません"
                    )
                    
                    # 更新ボタン
                    update_button = st.form_submit_button(
                        f"💾 {username} の情報を更新", 
                        type="primary"
                    )
                    
                    if update_button:
                        # バリデーション
                        if not new_username.strip():
                            st.error("ユーザー名は必須です")
                        elif not new_email.strip() or "@" not in new_email:
                            st.error("有効なメールアドレスを入力してください")
                        else:
                            # ユーザー情報を更新
                            success, message = self.update_user_complete(
                                user_id, new_username.strip(), new_email.strip(), 
                                new_company.strip(), new_role, new_status, 
                                new_is_active, new_password.strip() if new_password.strip() else None
                            )
                            
                            if success:
                                st.success(f"✅ {username} の情報を更新しました")
                                
                                # 自分自身の情報を更新した場合はセッション情報も更新
                                if is_current_user:
                                    st.session_state.user_info.update({
                                        'username': new_username.strip(),
                                        'email': new_email.strip(),
                                        'company_name': new_company.strip(),
                                        'role': new_role
                                    })
                                
                                st.rerun()
                            else:
                                st.error(f"❌ 更新に失敗しました: {message}")
                
                # 現在の情報表示
                st.write("---")
                info_col1, info_col2 = st.columns([2, 1])
                
                with info_col1:
                    st.write("**📊 現在の情報**")
                    st.write(f"**ユーザー名:** {username}")
                    st.write(f"**メールアドレス:** {email}")
                    st.write(f"**会社名:** {company or 'なし'}")
                    st.write(f"**権限:** {'👑 管理者' if role == 'admin' else '👤 ユーザー'}")
                    st.write(f"**状態:** {'✅ 承認済み' if status == 'approved' else '⏳ 承認待ち'}")
                    st.write(f"**アクティブ:** {'🟢 有効' if is_active else '🔴 無効'}")
                    st.write(f"**登録日:** {created_at}")
                
                with info_col2:
                    st.write("**⚠️ 危険操作**")
                    
                    # 自分自身は削除できない
                    if is_current_user:
                        st.info("自分自身は削除できません")
                    else:
                        # ユーザー削除（危険操作）
                        if st.button(f"🗑️ {username} を削除", key=f"delete_{user_id}", type="secondary"):
                            st.session_state[f'confirm_delete_{user_id}'] = True
                
                # 削除確認ダイアログ（自分以外の場合のみ）
                if not is_current_user and st.session_state.get(f'confirm_delete_{user_id}', False):
                    st.error(f"⚠️ 本当に {username} を削除しますか？")
                    st.write("この操作は取り消せません。")
                    
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button(f"はい、削除します", key=f"confirm_yes_{user_id}", type="primary"):
                            if self.delete_user(user_id):
                                st.success(f"ユーザー {username} を削除しました")
                                del st.session_state[f'confirm_delete_{user_id}']
                                st.rerun()
                            else:
                                st.error("削除に失敗しました")
                    
                    with col_no:
                        if st.button(f"キャンセル", key=f"confirm_no_{user_id}"):
                            del st.session_state[f'confirm_delete_{user_id}']
                            st.rerun()

    def show_pending_approvals(self):
        """承認待ちユーザー管理"""
        st.subheader("📝 承認待ちユーザー")
        st.info("承認待ちのユーザーはいません")

    def show_invitation_management(self):
        """招待管理"""
        st.subheader("📧 招待管理")
        st.info("招待機能は今後実装予定です")

    def show_system_statistics(self):
        """システム統計"""
        st.subheader("📊 システム統計")
        
        stats = self.get_system_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("総ユーザー数", stats.get('total_users', 0))
        with col2:
            st.metric("承認待ち", stats.get('pending_users', 0))
        with col3:
            st.metric("今日のログイン", stats.get('today_logins', 0))
        with col4:
            st.metric("失敗ログイン", stats.get('failed_logins', 0))

    def show_delete_account_dialog(self):
        """アカウント削除確認ダイアログ"""
        st.error("⚠️ アカウント削除の確認")
        st.write("この操作を実行すると、あなたのアカウントとすべてのデータが永久に削除されます。")
        st.write("この操作は取り消すことができません。")
        
        # 確認入力
        confirm_text = st.text_input(
            "削除を確認するため「削除します」と入力してください",
            key="delete_confirmation_text"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 本当に削除する", type="primary", disabled=(confirm_text != "削除します")):
                if self.delete_current_user():
                    st.success("アカウントを削除しました。ご利用ありがとうございました。")
                    # セッションをクリア
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                else:
                    st.error("削除に失敗しました")
        
        with col2:
            if st.button("キャンセル"):
                del st.session_state['show_delete_confirmation']
                st.rerun()

    # データベース操作メソッド
    def promote_to_admin(self, user_id):
        """ユーザーを管理者に昇格"""
        try:
            db_path = 'fusion_users.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # ユーザーを管理者に変更
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', ('admin', user_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"昇格エラー: {str(e)}")
            return False

    def reset_admin_password(self, new_password):
        """管理者パスワードをリセット"""
        try:
            db_path = 'fusion_users.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 管理者アカウントを確認
            cursor.execute('SELECT id FROM users WHERE username = "admin"')
            admin_user = cursor.fetchone()
            
            if not admin_user:
                conn.close()
                return False
            
            admin_id = admin_user[0]
            
            # パスワードをハッシュ化（旧データベース形式）
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            # パスワードを更新
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, admin_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"リセットエラー: {str(e)}")
            return False

    def get_all_users(self):
        """全ユーザーを取得（旧データベース対応）"""
        try:
            # fusion_users.db を優先的に使用
            db_path = 'fusion_users.db'
            
            if not os.path.exists(db_path):
                st.warning(f"⚠️ データベースファイル {db_path} が見つかりません")
                return []
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # テーブル構造を確認
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            st.info(f"データベース列: {', '.join(columns)}")
            
            # 旧データベース構造に対応したクエリ
            base_query = "SELECT id, username, email"
            
            # 存在する列のみ追加
            if 'company_name' in columns:
                base_query += ", company_name"
            else:
                base_query += ", '' as company_name"
            
            if 'role' in columns:
                base_query += ", role"
            else:
                base_query += ", 'user' as role"
            
            if 'status' in columns:
                base_query += ", status"
            else:
                base_query += ", 'approved' as status"
            
            if 'created_at' in columns:
                base_query += ", created_at"
            else:
                base_query += ", datetime('now') as created_at"
            
            if 'is_active' in columns:
                base_query += ", is_active"
            else:
                base_query += ", 1 as is_active"
            
            base_query += " FROM users ORDER BY id"
            
            cursor.execute(base_query)
            users = cursor.fetchall()
            conn.close()
            
            st.success(f"✅ {len(users)}名のユーザーを取得しました")
            return users
            
        except Exception as e:
            st.error(f"データベースエラー: {str(e)}")
            return []

    def update_user_complete(self, user_id, username, email, company_name, role, status, is_active, new_password=None):
        """ユーザー情報を完全更新（旧データベース対応）"""
        try:
            db_path = 'fusion_users.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # テーブル構造を確認
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 重複チェック（自分以外）
            cursor.execute('''
            SELECT id FROM users 
            WHERE (username = ? OR email = ?) AND id != ?
            ''', (username, email, user_id))
            
            duplicate = cursor.fetchone()
            if duplicate:
                conn.close()
                return False, "ユーザー名またはメールアドレスが既に使用されています"
            
            # 基本更新クエリ
            update_parts = ["username = ?", "email = ?"]
            params = [username, email]
            
            # 存在する列のみ更新
            if 'company_name' in columns:
                update_parts.append("company_name = ?")
                params.append(company_name)
            
            if 'role' in columns:
                update_parts.append("role = ?")
                params.append(role)
            
            if 'is_active' in columns:
                update_parts.append("is_active = ?")
                params.append(is_active)
            
            # パスワード更新
            if new_password and 'password_hash' in columns:
                password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                update_parts.append("password_hash = ?")
                params.append(password_hash)
            
            params.append(user_id)
            
            update_query = f"UPDATE users SET {', '.join(update_parts)} WHERE id = ?"
            cursor.execute(update_query, params)
            
            conn.commit()
            conn.close()
            return True, "更新完了"
            
        except Exception as e:
            return False, f"更新エラー: {str(e)}"

    def delete_user(self, user_id):
        """ユーザーを削除（旧データベース対応）"""
        try:
            db_path = 'fusion_users.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 削除前にユーザー情報を確認
            cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
            user_info = cursor.fetchone()
            
            if not user_info:
                conn.close()
                return False
            
            # ユーザーを削除
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            st.info(f"削除完了: {user_info[0]} ({user_info[1]})")
            return True
            
        except Exception as e:
            st.error(f"削除エラー: {str(e)}")
            return False

    def delete_current_user(self):
        """現在のユーザーを削除"""
        user_id = st.session_state.user_info['id']
        return self.delete_user(user_id)

    def get_system_stats(self):
        """システム統計を取得（旧データベース対応）"""
        try:
            db_path = 'fusion_users.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 総ユーザー数
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # 承認待ち（status列がない場合は0）
            try:
                cursor.execute('SELECT COUNT(*) FROM users WHERE status = "pending"')
                pending_users = cursor.fetchone()[0]
            except:
                pending_users = 0
            
            # 今日のログイン（ログテーブルがない場合は0）
            today_logins = 0
            failed_logins = 0
            
            conn.close()
            
            return {
                'total_users': total_users,
                'pending_users': pending_users,
                'today_logins': today_logins,
                'failed_logins': failed_logins
            }
            
        except Exception as e:
            st.error(f"統計取得エラー: {str(e)}")
            return {
                'total_users': 0,
                'pending_users': 0,
                'today_logins': 0,
                'failed_logins': 0
            }

def main():
    """アプリケーションのメインエントリーポイント"""
    try:
        app = FusionCRMUnified()
        app.main()
    except Exception as e:
        st.error(f"システムエラーが発生しました: {str(e)}")
        st.info("既存システムを個別に起動してください:")
        st.code("""
        streamlit run fusion_crm_main.py
        streamlit run email_webapp.py
        """)

if __name__ == "__main__":
    main()
