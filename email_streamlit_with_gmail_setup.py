#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Web版メール配信システム（Gmail設定機能付き）
ブラウザ上でGmail設定から配信まで完結
"""

import streamlit as st
import sqlite3
import pandas as pd
import json
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import plotly.express as px

# ページ設定
st.set_page_config(
    page_title="📧 FusionCRM メール配信システム",
    page_icon="📧",
    layout="wide"
)

# セッション状態の初期化
if 'gmail_config' not in st.session_state:
    st.session_state.gmail_config = None
if 'setup_step' not in st.session_state:
    st.session_state.setup_step = 1

class WebEmailDistribution:
    """Web版メール配信クラス"""
    
    def __init__(self):
        self.config_path = "config"
        self.ensure_config_dir()
        self.load_gmail_config()
    
    def ensure_config_dir(self):
        """設定ディレクトリの確保"""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
    
    def load_gmail_config(self):
        """Gmail設定の読み込み"""
        try:
            config_file = os.path.join(self.config_path, "gmail_config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                st.session_state.gmail_config = config
                return config
        except FileNotFoundError:
            st.session_state.gmail_config = None
            return None
        except Exception as e:
            st.error(f"設定読み込みエラー: {e}")
            return None
    
    def save_gmail_config(self, config):
        """Gmail設定の保存"""
        try:
            config_file = os.path.join(self.config_path, "gmail_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            st.session_state.gmail_config = config
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
        if not st.session_state.gmail_config:
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
    """企業データの取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        query = """
            SELECT id, company_name, email_address, website, phone, status, 
                   picocela_relevance_score, created_at
            FROM companies 
            WHERE email_address IS NOT NULL AND email_address != ''
            ORDER BY picocela_relevance_score DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"企業データ取得エラー: {e}")
        return pd.DataFrame()

def render_gmail_setup():
    """Gmail設定画面"""
    st.title("⚙️ Gmail設定")
    
    email_dist = WebEmailDistribution()
    
    # 現在の設定状況
    if st.session_state.gmail_config:
        st.success("✅ Gmail設定済み")
        
        with st.expander("現在の設定を確認"):
            config = st.session_state.gmail_config
            st.info(f"**メールアドレス**: {config['email']}")
            st.info(f"**送信者名**: {config['sender_name']}")
            st.info(f"**SMTPサーバー**: {config['smtp_server']}")
    else:
        st.error("❌ Gmail設定が必要です")
    
    # セットアップウィザード
    st.subheader("🔧 Gmail設定ウィザード")
    
    # ステップインジケーター
    steps = ["📧 Gmailアドレス", "🔑 アプリパスワード取得", "✅ 設定完了"]
    
    # ステップ表示
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        if i + 1 <= st.session_state.setup_step:
            col.success(f"**{i+1}. {step}**")
        else:
            col.info(f"{i+1}. {step}")
    
    st.markdown("---")
    
    # Step 1: メールアドレス確認
    if st.session_state.setup_step >= 1:
        st.subheader("📧 Step 1: Gmailアドレス")
        
        email = st.text_input(
            "Gmailアドレスを入力してください",
            value=st.session_state.gmail_config['email'] if st.session_state.gmail_config else "tokuda@picocela.com",
            help="PicoCELA社で使用するGmailアドレスを入力"
        )
        
        sender_name = st.text_input(
            "送信者名を入力してください",
            value=st.session_state.gmail_config['sender_name'] if st.session_state.gmail_config else "PicoCELA Inc.",
            help="メール送信時に表示される名前"
        )
        
        if st.button("✅ Step 1 完了"):
            st.session_state.email_input = email
            st.session_state.sender_name_input = sender_name
            st.session_state.setup_step = 2
            st.rerun()
    
    # Step 2: アプリパスワード取得ガイド
    if st.session_state.setup_step >= 2:
        st.subheader("🔑 Step 2: Googleアプリパスワードの取得")
        
        st.warning("""
        **重要**: Gmailの通常パスワードではなく、「アプリパスワード」が必要です。
        """)
        
        with st.expander("📋 アプリパスワード取得手順（クリックして展開）"):
            st.markdown("""
            **手順:**
            
            1. **Googleアカウント管理画面**にアクセス
               - https://myaccount.google.com にアクセス
            
            2. **セキュリティ**タブをクリック
            
            3. **2段階認証プロセス**を有効化
               - まだ有効でない場合は設定してください
            
            4. **アプリパスワード**を検索
               - 検索ボックスで「アプリパスワード」と検索
            
            5. **新しいアプリパスワードを生成**
               - アプリ: 「メール」を選択
               - デバイス: 「その他（カスタム名）」→ 「FusionCRM」と入力
               - **生成**をクリック
            
            6. **16文字のパスワードをコピー**
               - 例: `abcd efgh ijkl mnop`
               - スペースも含めてそのままコピー
            """)
            
            st.info("💡 **ヒント**: アプリパスワードは1回だけ表示されるので、必ずコピーしてください！")
        
        # アプリパスワード入力
        app_password = st.text_input(
            "Googleアプリパスワードを入力してください",
            type="password",
            help="16文字のアプリパスワード（スペースあり）を入力",
            placeholder="abcd efgh ijkl mnop"
        )
        
        if app_password:
            if st.button("🧪 接続テスト"):
                test_config = {
                    "email": st.session_state.get('email_input', ''),
                    "password": app_password,
                    "sender_name": st.session_state.get('sender_name_input', ''),
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587
                }
                
                with st.spinner("接続テスト中..."):
                    success, message = email_dist.test_gmail_connection(test_config)
                
                if success:
                    st.success(f"✅ {message}")
                    
                    # 設定保存
                    if email_dist.save_gmail_config(test_config):
                        st.success("✅ 設定を保存しました")
                        st.session_state.setup_step = 3
                        st.rerun()
                else:
                    st.error(f"❌ {message}")
                    
                    with st.expander("❓ よくある問題と解決方法"):
                        st.markdown("""
                        **よくあるエラー:**
                        
                        1. **認証エラー**
                           - アプリパスワードが正しいか確認
                           - 2段階認証が有効か確認
                        
                        2. **接続エラー**
                           - インターネット接続を確認
                           - ファイアウォール設定を確認
                        
                        3. **パスワード形式エラー**
                           - スペースを含めて正確に入力
                           - コピー＆ペーストを推奨
                        """)
    
    # Step 3: 設定完了
    if st.session_state.setup_step >= 3:
        st.subheader("✅ Step 3: 設定完了！")
        
        st.success("🎉 Gmail設定が完了しました！")
        
        config = st.session_state.gmail_config
        st.balloons()
        
        # 設定サマリー
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**メールアドレス**: {config['email']}")
            st.info(f"**送信者名**: {config['sender_name']}")
        with col2:
            st.info(f"**SMTPサーバー**: {config['smtp_server']}")
            st.info(f"**ポート**: {config['smtp_port']}")
        
        # 次のステップ案内
        st.markdown("### 🚀 次のステップ")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 メール配信を開始", type="primary"):
                st.switch_page("配信")
        
        with col2:
            if st.button("🧪 テスト送信"):
                st.switch_page("テスト")
        
        # 設定リセット
        if st.button("🔄 設定をやり直す"):
            st.session_state.setup_step = 1
            st.session_state.gmail_config = None
            st.rerun()

def render_email_campaign():
    """メール配信画面"""
    st.title("📧 メール配信")
    
    # Gmail設定確認
    if not st.session_state.gmail_config:
        st.error("❌ Gmail設定が必要です")
        if st.button("⚙️ Gmail設定を行う"):
            st.switch_page("Gmail設定")
        return
    
    st.success(f"✅ Gmail設定済み: {st.session_state.gmail_config['email']}")
    
    email_dist = WebEmailDistribution()
    
    # 企業データ取得
    df = get_companies_data()
    if df.empty:
        st.warning("配信対象企業が見つかりません")
        return
    
    # 配信対象選択
    st.subheader("🎯 配信対象選択")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "ステータス",
            ["全て"] + list(df['status'].unique())
        )
    
    with col2:
        min_score = st.number_input(
            "最小スコア",
            min_value=0,
            max_value=int(df['picocela_relevance_score'].max()) if not df.empty else 200,
            value=0
        )
    
    with col3:
        max_count = st.number_input(
            "最大送信数",
            min_value=1,
            max_value=100,
            value=10
        )
    
    # フィルター適用
    filtered_df = df.copy()
    
    if status_filter != "全て":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= min_score]
    filtered_df = filtered_df.head(max_count)
    
    st.info(f"📊 配信対象: {len(filtered_df)}社")
    
    if len(filtered_df) > 0:
        # 対象企業表示
        with st.expander("📋 配信対象企業一覧"):
            st.dataframe(filtered_df[['company_name', 'email_address', 'status', 'picocela_relevance_score']])
        
        # メール内容
        st.subheader("✉️ メール内容")
        
        # テンプレート
        template_type = st.selectbox(
            "テンプレート",
            ["初回提案", "フォローアップ", "デモ依頼", "カスタム"]
        )
        
        # テンプレート内容
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
        
        elif template_type == "デモ依頼":
            default_subject = "PicoCELA 製品デモンストレーションのご案内"
            default_body = """Dear {company_name} 様

お世話になっております。
株式会社PicoCELAです。

弊社のメッシュネットワークソリューションの実際の動作を
ご覧いただけるデモンストレーションをご用意いたします。

所要時間：約30分
場所：貴社またはオンライン

ご都合の良い日時をお聞かせください。

株式会社PicoCELA
営業部"""
        else:
            default_subject = ""
            default_body = ""
        
        # メール内容入力
        subject = st.text_input("件名", value=default_subject)
        body = st.text_area("本文", value=default_body, height=250)
        
        # 送信設定
        st.subheader("⚙️ 送信設定")
        send_interval = st.slider("送信間隔（秒）", 1, 30, 5)
        
        # 送信実行
        if st.button("🚀 配信開始", type="primary"):
            if subject and body:
                if st.checkbox("✅ 配信を実行することを確認しました"):
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    failed_count = 0
                    
                    for i, (idx, company) in enumerate(filtered_df.iterrows()):
                        company_name = company['company_name']
                        email_address = company['email_address']
                        
                        status_text.text(f"送信中: {company_name} ({i+1}/{len(filtered_df)})")
                        
                        # メール送信
                        success, message = email_dist.send_email(
                            email_address, company_name, subject, body
                        )
                        
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                            st.error(f"{company_name}: {message}")
                        
                        progress_bar.progress((i + 1) / len(filtered_df))
                        
                        if i < len(filtered_df) - 1:
                            time.sleep(send_interval)
                    
                    status_text.success("🎉 配信完了！")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("送信成功", success_count)
                    col2.metric("送信失敗", failed_count)
                    col3.metric("成功率", f"{success_count/(success_count+failed_count)*100:.1f}%" if (success_count+failed_count) > 0 else "0%")
                
                else:
                    st.warning("確認チェックボックスにチェックを入れてください")
            else:
                st.error("件名と本文を入力してください")

def main():
    """メイン関数"""
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("📧 FusionCRM")
        st.markdown("**メール配信システム**")
        
        # 設定状況表示
        if st.session_state.gmail_config:
            st.success("✅ Gmail設定完了")
            st.info(f"📧 {st.session_state.gmail_config['email']}")
        else:
            st.error("❌ Gmail設定が必要")
        
        # ページ選択
        page = st.radio(
            "メニュー",
            ["⚙️ Gmail設定", "📧 メール配信"]
        )
    
    # ページ表示
    if page == "⚙️ Gmail設定":
        render_gmail_setup()
    elif page == "📧 メール配信":
        render_email_campaign()

if __name__ == "__main__":
    main()