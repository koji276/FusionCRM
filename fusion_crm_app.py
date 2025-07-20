"""
FusionCRM - Streamlit Cloud エントリーポイント
Version: 6.1 (2025年7月20日)
"""

import streamlit as st
import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def main():
    """メインアプリケーション選択"""
    
    st.set_page_config(
        page_title="FusionCRM Suite",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🚀 FusionCRM Suite")
    st.markdown("**統合営業管理システム**")
    
    # システム選択
    st.subheader("🎯 システム選択")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 CRMメインシステム")
        st.markdown("企業管理・ダッシュボード・分析")
        
        if st.button("🚀 CRMシステムを開く", type="primary", use_container_width=True):
            # CRMメインシステムの起動
            try:
                from fusion_crm_main import main as crm_main
                st.session_state.app_mode = 'crm'
                crm_main()
                return
            except ImportError as e:
                st.error(f"CRMシステム読み込みエラー: {e}")
                st.info("fusion_crm_main.py が見つかりません")
    
    with col2:
        st.markdown("### 📧 メール配信システム")
        st.markdown("AI生成・バッチ送信・履歴管理")
        
        if st.button("📧 メールシステムを開く", type="secondary", use_container_width=True):
            # メールシステムの起動
            try:
                from email_webapp import main as email_main
                st.session_state.app_mode = 'email'
                email_main()
                return
            except ImportError as e:
                st.error(f"メールシステム読み込みエラー: {e}")
                st.info("email_webapp.py が見つかりません")
    
    # システム状態表示
    st.markdown("---")
    st.subheader("📊 システム状態")
    
    # ファイル存在確認
    col1, col2, col3 = st.columns(3)
    
    with col1:
        crm_exists = os.path.exists("fusion_crm_main.py")
        status = "✅ 利用可能" if crm_exists else "❌ ファイルなし"
        st.metric("CRMシステム", status)
    
    with col2:
        email_exists = os.path.exists("email_webapp.py")
        status = "✅ 利用可能" if email_exists else "❌ ファイルなし"
        st.metric("メールシステム", status)
    
    with col3:
        modules_exist = os.path.exists("modules/")
        status = "✅ 利用可能" if modules_exist else "❌ ディレクトリなし"
        st.metric("モジュール", status)
    
    # ファイル一覧表示（デバッグ用）
    if st.checkbox("🔍 ファイル一覧を表示（デバッグ）"):
        st.subheader("📁 リポジトリ内容")
        
        try:
            files = []
            for root, dirs, filenames in os.walk("."):
                for filename in filenames:
                    if filename.endswith(('.py', '.toml', '.txt', '.md')):
                        files.append(os.path.join(root, filename))
            
            if files:
                st.write("**見つかったファイル:**")
                for file in sorted(files):
                    st.text(f"• {file}")
            else:
                st.warning("Pythonファイルが見つかりません")
                
        except Exception as e:
            st.error(f"ファイル一覧取得エラー: {e}")
    
    # 直接起動オプション
    st.markdown("---")
    st.subheader("🔧 直接起動オプション")
    
    if st.button("🏢 fusion_crm_main.py を直接実行"):
        try:
            import fusion_crm_main
            fusion_crm_main.main()
        except Exception as e:
            st.error(f"直接実行エラー: {e}")
    
    if st.button("📧 email_webapp.py を直接実行"):
        try:
            import email_webapp
            email_webapp.main()
        except Exception as e:
            st.error(f"直接実行エラー: {e}")
    
    # 緊急フォールバック
    st.markdown("---")
    st.subheader("🚨 緊急フォールバック")
    st.info("上記でエラーが発生する場合は、個別システムのURLに直接アクセスしてください")
    
    email_system_url = "https://aiplusagents-4j4kitm3mapdvaxkhi3npk.streamlit.app/"
    st.markdown(f"📧 [メール配信システム（独立版）]({email_system_url})")

if __name__ == "__main__":
    # セッション状態確認
    if 'app_mode' in st.session_state:
        # 既に選択されたアプリがある場合
        if st.session_state.app_mode == 'crm':
            try:
                from fusion_crm_main import main as crm_main
                crm_main()
            except:
                st.error("CRMシステム起動失敗 - メイン選択画面に戻ります")
                del st.session_state.app_mode
                st.rerun()
        elif st.session_state.app_mode == 'email':
            try:
                from email_webapp import main as email_main
                email_main()
            except:
                st.error("メールシステム起動失敗 - メイン選択画面に戻ります")
                del st.session_state.app_mode
                st.rerun()
    else:
        # メイン選択画面
        main()
