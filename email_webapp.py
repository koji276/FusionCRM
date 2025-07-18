#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Streamlit Cloud対応 メール配信システム
ファイル保存なしでセッション状態のみで動作
"""

import streamlit as st
import sqlite3
import pandas as pd
import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ページ設定
st.set_page_config(
    page_title="📧 FusionCRM メール配信システム",
    page_icon="📧",
    layout="wide"
)

# セッション状態の初期化
if 'gmail_config' not in st.session_state:
    st.session_state.gmail_config = None
if 'setup_completed' not in st.session_state:
    st.session_state.setup_completed = False

class StreamlitEmailWebApp:
    """Streamlit Cloud対応メール配信Webアプリケーション"""
    
    def __init__(self):
        # ファイルシステムを使わずセッション状態のみで動作
        pass
    
    def is_gmail_configured(self):
        """Gmail設定状況確認（セッション状態ベース）"""
        return st.session_state.gmail_config is not None and st.session_state.setup_completed
    
    def save_gmail_config_to_session(self, config):
        """Gmail設定をセッション状態に保存"""
        try:
            st.session_state.gmail_config = config
            st.session_state.setup_completed = True
            return True
        except Exception as e:
            st.error(f"設定保存エラー: {e}")
            return False
    
    def test_gmail_connection(self, config):
        """Gmail接続テスト"""
        try:
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email'], config['password'])
            server.quit()
            return True, "接続成功"
        except Exception as e:
            return False, f"接続エラー: {str(e)}"
    
    def send_email(self, to_email, company_name, subject, body):
        """メール送信"""
        if not self.is_gmail_configured():
            return False, "Gmail設定が無効です"
        
        try:
            config = st.session_state.gmail_config
            
            msg = MIMEMultipart()
            msg['From'] = f"{config['sender_name']} <{config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 会社名の置換
            formatted_body = body.replace('{company_name}', company_name)
            msg.attach(MIMEText(formatted_body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email'], config['password'])
            
            text = msg.as_string()
            server.sendmail(config['email'], to_email, text)
            server.quit()
            
            return True, "送信成功"
            
        except Exception as e:
            return False, f"送信エラー: {str(e)}"

def get_companies_data():
    """企業データ取得（サンプルデータ使用）"""
    # Streamlit Cloudでは外部データベースにアクセスできないため、サンプルデータを使用
    sample_data = {
        'id': [1, 2, 3, 4, 5, 6, 7, 8],
        'company_name': [
            'テストコンストラクション株式会社',
            'スマートビルディング合同会社', 
            'Wyebot',
            'Delta Electronics (Americas)',
            'Energous Corporation',
            'Lyngsoe Systems',
            'Corvus Robotics, Inc.',
            'Interlake Mecalux Inc.'
        ],
        'email_address': [
            'contact@test-construction.com',
            'info@smart-building.co.jp',
            'contact@wyebot.com',
            'contact@delta-americas.com',
            'contact@energous.com',
            'contact@lyngsoe.com',
            'contact@corvusrobotics.com',
            'contact@mecalux.com'
        ],
        'website': [
            'https://test-construction.com',
            'https://smart-building.co.jp',
            'https://wyebot.com',
            'https://delta-americas.com',
            'https://energous.com',
            'https://lyngsoe.com',
            'https://corvusrobotics.com',
            'https://mecalux.com'
        ],
        'status': ['New', 'New', 'New', 'New', 'New', 'New', 'New', 'New'],
        'picocela_relevance_score': [115, 120, 100, 20, 110, 80, 20, 90]
    }
    
    return pd.DataFrame(sample_data)

def render_header():
    """ヘッダー"""
    st.title("📧 FusionCRM メール配信システム")
    st.markdown("**独立メール配信アプリケーション**")
    
    # メインシステムへのリンク
    st.info("🔗 [メインシステムに戻る](https://aiplusagents-4j4kitm3mapdvaxkhi3npk.streamlit.app/) （別タブで開く）")

def render_gmail_setup():
    """Gmail設定"""
    st.header("⚙️ Gmail設定")
    
    app = StreamlitEmailWebApp()
    
    # 現在の設定表示
    if app.is_gmail_configured():
        st.success("✅ Gmail設定済み")
        config = st.session_state.gmail_config
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**メール**: {config['email']}")
        with col2:
            st.info(f"**送信者名**: {config['sender_name']}")
        
        # 設定クリア
        if st.button("🔄 設定をクリア"):
            st.session_state.gmail_config = None
            st.session_state.setup_completed = False
            st.rerun()
    else:
        st.error("❌ Gmail設定が必要です")
    
    # 設定フォーム
    with st.expander("🔧 Gmail設定・変更"):
        st.markdown("### 📋 Googleアプリパスワード取得方法")
        st.markdown("""
        1. [Googleアカウント管理](https://myaccount.google.com) → セキュリティ
        2. 2段階認証プロセスを有効化
        3. アプリパスワード → メール → その他「FusionCRM」
        4. 生成された16文字パスワードをコピー
        """)
        
        with st.form("gmail_setup"):
            email = st.text_input(
                "Gmailアドレス", 
                value=st.session_state.gmail_config['email'] if app.is_gmail_configured() else "tokuda@picocela.com"
            )
            password = st.text_input("アプリパスワード", type="password")
            sender_name = st.text_input(
                "送信者名", 
                value=st.session_state.gmail_config['sender_name'] if app.is_gmail_configured() else "PicoCELA Inc."
            )
            
            if st.form_submit_button("💾 設定保存"):
                if email and password and sender_name:
                    config = {
                        "email": email,
                        "password": password,
                        "sender_name": sender_name,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587
                    }
                    
                    with st.spinner("接続テスト中..."):
                        success, message = app.test_gmail_connection(config)
                    
                    if success:
                        app.save_gmail_config_to_session(config)
                        st.success("✅ 設定保存完了")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("すべての項目を入力してください")

def render_email_campaign():
    """メール配信"""
    st.header("📧 メール配信")
    
    app = StreamlitEmailWebApp()
    
    if not app.is_gmail_configured():
        st.error("❌ Gmail設定が必要です。上記で設定してください。")
        return
    
    # 企業データ取得
    df = get_companies_data()
    
    # 配信設定
    st.subheader("🎯 配信対象")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("ステータス", ["全て"] + list(df['status'].unique()))
    with col2:
        min_score = st.number_input("最小スコア", min_value=0, value=0)
    with col3:
        max_count = st.number_input("最大送信数", min_value=1, max_value=50, value=5)
    
    # フィルター適用
    filtered_df = df.copy()
    
    if status_filter != "全て":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= min_score]
    filtered_df = filtered_df.head(max_count)
    
    st.info(f"📊 配信対象: {len(filtered_df)}社")
    
    if len(filtered_df) > 0:
        # 対象企業表示
        with st.expander("📋 配信対象企業"):
            st.dataframe(filtered_df[['company_name', 'email_address', 'status', 'picocela_relevance_score']])
        
        # メール内容
        st.subheader("✉️ メール内容")
        
        template_type = st.selectbox("テンプレート", ["初回提案", "フォローアップ", "カスタム"])
        
        if template_type == "初回提案":
            default_subject = "PicoCELA メッシュネットワークソリューションのご案内"
            default_body = """Dear {company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

建設現場でのワイヤレス通信にお困りではありませんか？

弊社のメッシュネットワーク技術により、以下のメリットを提供いたします：

• 建設現場での安定したワイヤレス通信
• 既存インフラに依存しない独立ネットワーク
• IoTセンサー・モニタリング機器との連携
• 現場安全性向上・デジタル化推進

詳細な資料をお送りいたしますので、お時間をいただけますでしょうか。

株式会社PicoCELA
営業部"""
        elif template_type == "フォローアップ":
            default_subject = "PicoCELA メッシュネットワーク - フォローアップ"
            default_body = """Dear {company_name} 様

先日はお時間をいただき、ありがとうございました。

弊社のメッシュネットワークソリューションについて、
追加でご質問やご相談がございましたら、お気軽にお声がけください。

株式会社PicoCELA
営業部"""
        else:
            default_subject = ""
            default_body = ""
        
        subject = st.text_input("件名", value=default_subject)
        body = st.text_area("本文", value=default_body, height=200)
        
        # 送信設定
        send_interval = st.slider("送信間隔（秒）", 1, 30, 5)
        
        # 送信実行
        if st.button("🚀 メール配信開始", type="primary"):
            if subject and body:
                if st.checkbox("✅ 配信実行を確認"):
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    failed_count = 0
                    
                    for i, (idx, company) in enumerate(filtered_df.iterrows()):
                        company_name = company['company_name']
                        email_address = company['email_address']
                        
                        status_text.text(f"送信中: {company_name}")
                        
                        success, message = app.send_email(email_address, company_name, subject, body)
                        
                        if success:
                            success_count += 1
                            st.success(f"✅ {company_name} - 送信成功")
                        else:
                            failed_count += 1
                            st.error(f"❌ {company_name}: {message}")
                        
                        progress_bar.progress((i + 1) / len(filtered_df))
                        
                        if i < len(filtered_df) - 1:
                            time.sleep(send_interval)
                    
                    status_text.success("🎉 配信完了！")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("送信成功", success_count)
                    col2.metric("送信失敗", failed_count)
                    col3.metric("成功率", f"{success_count/(success_count+failed_count)*100:.1f}%" if (success_count+failed_count) > 0 else "0%")
                
                else:
                    st.warning("確認チェックボックスにチェックしてください")
            else:
                st.error("件名と本文を入力してください")

def main():
    """メイン関数"""
    
    # ヘッダー
    render_header()
    
    # Gmail設定
    render_gmail_setup()
    
    # メール配信
    render_email_campaign()
    
    # フッター
    st.markdown("---")
    st.markdown("**💡 注意**: この設定はセッション中のみ有効です。ブラウザを閉じると設定がリセットされます。")

if __name__ == "__main__":
    main()
