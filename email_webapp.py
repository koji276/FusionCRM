#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Streamlit Cloud対応 メール配信システム（完全修正版・エラー修正）
実際のデータベース接続 + 確実なSMTP送信
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
    """Streamlit Cloud対応メール配信Webアプリケーション（完全修正版）"""
    
    def __init__(self):
        pass
    
    def is_gmail_configured(self):
        """Gmail設定状況確認"""
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
        """メール送信（前回成功したSMTP方式）"""
        if not self.is_gmail_configured():
            return False, "Gmail設定が無効です"
        
        try:
            config = st.session_state.gmail_config
            
            msg = MIMEMultipart()
            msg['From'] = f"{config['sender_name']} <{config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
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
    
    def update_company_status(self, company_name, new_status="Contacted"):
        """企業ステータス更新"""
        try:
            conn = sqlite3.connect('fusion_crm.db')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE companies 
                SET sales_status = ?, updated_at = datetime('now')
                WHERE company_name = ?
            """, (new_status, company_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.warning(f"ステータス更新エラー: {e}")
            return False

def get_companies_data():
    """
    fusion_crm.dbの詳細調査（デバッグ強化版）
    """
    try:
        db_path = 'fusion_crm.db'
        
        if not os.path.exists(db_path):
            st.error(f"❌ データベースファイルが見つかりません: {db_path}")
            return pd.DataFrame()
        
        st.info(f"🔍 データベース調査開始: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. すべてのテーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        st.success(f"📋 発見されたテーブル: {tables}")
        
        if not tables:
            st.error("❌ テーブルが見つかりません")
            conn.close()
            return pd.DataFrame()
        
        # 2. 各テーブルの詳細調査
        for table_name in tables:
            try:
                st.write(f"\n🔍 **テーブル '{table_name}' の調査:**")
                
                # テーブル構造
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                col_names = [col[1] for col in columns]
                st.write(f"   📋 列: {col_names}")
                
                # レコード数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                st.write(f"   📊 レコード数: {count}")
                
                # サンプルデータ（最初の3行）
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    st.write(f"   📄 サンプルデータ:")
                    for i, row in enumerate(sample_data, 1):
                        st.write(f"      行{i}: {dict(zip(col_names, row))}")
                
                # メールアドレスっぽい列があるかチェック
                email_cols = [col for col in col_names if any(keyword in col.lower() for keyword in ['email', 'mail', 'メール'])]
                if email_cols:
                    st.success(f"   ✅ メール列発見: {email_cols}")
                    
                    # メールアドレスがあるレコード数
                    email_col = email_cols[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {email_col} IS NOT NULL AND {email_col} != ''")
                    email_count = cursor.fetchone()[0]
                    st.write(f"   📧 メールアドレス有りレコード: {email_count}")
                    
                    if email_count > 0:
                        # 実際のメールアドレスサンプル
                        cursor.execute(f"SELECT {email_col} FROM {table_name} WHERE {email_col} IS NOT NULL AND {email_col} != '' LIMIT 5")
                        email_samples = [row[0] for row in cursor.fetchall()]
                        st.write(f"   📧 メールサンプル: {email_samples}")
                        
                        # このテーブルからデータを取得してみる
                        company_col = next((col for col in col_names if any(keyword in col.lower() for keyword in ['name', '名前', 'company'])), col_names[0])
                        
                        query = f"""
                            SELECT 
                                {company_col} as company_name,
                                {email_col} as email_address,
                                'New' as status,
                                50 as picocela_relevance_score
                            FROM {table_name}
                            WHERE {email_col} IS NOT NULL 
                            AND {email_col} != ''
                            LIMIT 10
                        """
                        
                        st.write(f"   🔍 テストクエリ: {query}")
                        
                        try:
                            df = pd.read_sql_query(query, conn)
                            st.success(f"   ✅ データ取得成功: {len(df)}件")
                            
                            # 取得したデータを表示
                            st.write("   📊 取得データ:")
                            st.dataframe(df)
                            
                            conn.close()
                            return df
                            
                        except Exception as query_error:
                            st.error(f"   ❌ クエリエラー: {query_error}")
                
            except Exception as table_error:
                st.error(f"❌ テーブル '{table_name}' 調査エラー: {table_error}")
                continue
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ データベース調査エラー: {e}")
    
    # フォールバック
    st.warning("⚠️ フォールバックデータを使用します")
    sample_data = {
        'company_name': ['FUSIONDRIVER', 'テストコンストラクション株式会社', 'スマートビルディング合同会社'],
        'email_address': ['koji@fusiondriver.biz', 'contact@test-construction.com', 'info@smart-building.co.jp'],
        'status': ['New', 'New', 'New'],
        'picocela_relevance_score': [70, 115, 120]
    }
    
    return pd.DataFrame(sample_data)

def render_header():
    """ヘッダー"""
    st.title("📧 FusionCRM メール配信システム")
    st.markdown("**独立メール配信アプリケーション（エラー修正版）**")
    
    st.info("🔗 [メインシステムに戻る](https://automl-3ynrytum8tugw8ytcue7ay.streamlit.app/) （別タブで開く）")

def render_gmail_setup():
    """Gmail設定"""
    st.header("⚙️ Gmail設定")
    
    app = StreamlitEmailWebApp()
    
    if app.is_gmail_configured():
        st.success("✅ Gmail設定済み")
        config = st.session_state.gmail_config
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**メール**: {config['email']}")
        with col2:
            st.info(f"**送信者名**: {config['sender_name']}")
        
        if st.button("🔄 設定をクリア"):
            st.session_state.gmail_config = None
            st.session_state.setup_completed = False
            st.rerun()
    else:
        st.error("❌ Gmail設定が必要です")
    
    with st.expander("🔧 Gmail設定・変更"):
        st.markdown("### 📋 前回成功した設定を使用")
        st.info("前回の成功設定: tokuda@picocela.com + アプリパスワード")
        
        with st.form("gmail_setup"):
            email = st.text_input("Gmailアドレス", value="tokuda@picocela.com")
            password = st.text_input("アプリパスワード", type="password", placeholder="bmzr lbrs cbbn jtmr")
            sender_name = st.text_input("送信者名", value="PicoCELA Inc.")
            
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
    """メール配信（完全修正版）"""
    st.header("📧 メール配信")
    
    app = StreamlitEmailWebApp()
    
    if not app.is_gmail_configured():
        st.error("❌ Gmail設定が必要です。上記で設定してください。")
        return
    
    df = get_companies_data()
    
    if len(df) == 0:
        st.error("❌ 配信対象企業が見つかりません")
        return
    
    st.subheader("🎯 配信対象")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_options = ["全て"] + list(df['status'].unique()) if 'status' in df.columns else ["全て", "New"]
        status_filter = st.selectbox("ステータス", status_options)
    with col2:
        min_score = st.number_input("最小スコア", min_value=0, value=0)
    with col3:
        max_count = st.number_input("最大送信数", min_value=1, max_value=50, value=1)
    
    filtered_df = df.copy()
    
    if status_filter != "全て":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if 'picocela_relevance_score' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= min_score]
        filtered_df = filtered_df.sort_values('picocela_relevance_score', ascending=False)
    
    filtered_df = filtered_df.head(max_count)
    
    st.info(f"📊 配信対象: {len(filtered_df)}社")
    
    if len(filtered_df) > 0:
        with st.expander("📋 配信対象企業"):
            display_columns = ['company_name', 'email_address', 'status']
            if 'picocela_relevance_score' in filtered_df.columns:
                display_columns.append('picocela_relevance_score')
            st.dataframe(filtered_df[display_columns])
        
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
        
        send_interval = st.slider("送信間隔（秒）", 1, 30, 5)
        
        # 修正された送信処理
        confirm_checked = st.checkbox("✅ 配信実行を確認")
        send_button = st.button("🚀 メール配信開始", type="primary")
        
        if send_button:
            st.write("🔍 ボタンが押されました")
            
            if not subject:
                st.error("❌ 件名が入力されていません")
            elif not body:
                st.error("❌ 本文が入力されていません")
            elif not confirm_checked:
                st.error("❌ 確認チェックボックスをチェックしてください")
            else:
                st.write("🚀 送信処理を開始します...")
                
                gmail_config = st.session_state.gmail_config
                st.write(f"📧 送信元: {gmail_config.get('email', 'なし')}")
                st.write(f"👤 送信者名: {gmail_config.get('sender_name', 'なし')}")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                success_count = 0
                failed_count = 0
                results = []
                
                for i, (idx, company) in enumerate(filtered_df.iterrows()):
                    company_name = company['company_name']
                    email_address = company['email_address']
                    
                    progress = (i + 1) / len(filtered_df)
                    progress_bar.progress(progress)
                    status_text.text(f"📧 {i+1}/{len(filtered_df)}. {company_name} ({email_address}) 送信中...")
                    
                    success, message = app.send_email(email_address, company_name, subject, body)
                    
                    if success:
                        success_count += 1
                        status_icon = "✅"
                        app.update_company_status(company_name, "Contacted")
                    else:
                        failed_count += 1
                        status_icon = "❌"
                    
                    results.append({
                        'company': company_name,
                        'email': email_address,
                        'status': '成功' if success else '失敗',
                        'message': message,
                        'icon': status_icon
                    })
                    
                    with results_container:
                        st.write("📊 **送信結果:**")
                        for result in results[-3:]:
                            st.write(f"{result['icon']} {result['company']} - {result['status']}")
                    
                    if i < len(filtered_df) - 1:
                        delay_variation = random.randint(-1, 2)
                        actual_delay = max(1, send_interval + delay_variation)
                        status_text.text(f"⏱️ {actual_delay}秒待機中...")
                        time.sleep(actual_delay)
                
                progress_bar.progress(1.0)
                status_text.success("🎉 配信完了！")
                
                st.success("📧 メール配信が完了しました！")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("✅ 送信成功", success_count)
                col2.metric("❌ 送信失敗", failed_count)
                total = success_count + failed_count
                success_rate = (success_count / total * 100) if total > 0 else 0
                col3.metric("📈 成功率", f"{success_rate:.1f}%")
                
                if st.checkbox("📋 詳細結果を表示"):
                    st.write("**全送信結果:**")
                    for result in results:
                        st.write(f"{result['icon']} **{result['company']}** ({result['email']}) - {result['status']}")
                        if result['status'] == '失敗':
                            st.write(f"   💬 エラー: {result['message']}")
    else:
        st.warning("📭 フィルター条件に一致する企業がありません")

def main():
    """メイン関数"""
    render_header()
    render_gmail_setup()
    render_email_campaign()
    
    st.markdown("---")
    st.markdown("**💡 注意**: この設定はセッション中のみ有効です。ブラウザを閉じると設定がリセットされます。")
    st.markdown("**🔧 修正点**: インデントエラー修正 + 確実なSMTP送信方式")

if __name__ == "__main__":
    main()
