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
import requests

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
    Google Sheets からデータ取得（FusionCRM本体と同期）
    """
    st.info("🔍 データソース確認中...")
    
    # 1. Google Sheets から直接データを取得
    try:
        # FusionCRM Database のGoogle Sheets URL
        sheets_url = "https://docs.google.com/spreadsheets/d/1ySS3zLbEwq3U54pzIRAbKLyhOWR2YdBUSdk_xr_7WNY"
        
        # CSVエクスポート用のURL（公開されている場合）
        csv_export_url = f"{sheets_url}/export?format=csv&gid=0"
        
        st.info(f"🔗 Google Sheets 接続試行: {sheets_url}")
        
        try:
            # CSV形式でデータを取得
            response = requests.get(csv_export_url, timeout=10)
            
            if response.status_code == 200:
                # CSVデータをPandasで読み込み
                from io import StringIO
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data)
                
                st.success(f"✅ Google Sheets から {len(df)}件のデータを取得成功")
                st.info(f"📋 取得した列: {list(df.columns)}")
                
                # データの最初の3行を表示
                if len(df) > 0:
                    st.write("📊 データサンプル:")
                    st.dataframe(df.head(3))
                
                # 列名を標準化
                column_mapping = {}
                for col in df.columns:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['company_name', 'name']):
                        column_mapping[col] = 'company_name'
                    elif any(keyword in col_lower for keyword in ['email']):
                        column_mapping[col] = 'email_address'
                    elif any(keyword in col_lower for keyword in ['picocela_rele', 'priority']):
                        column_mapping[col] = 'picocela_relevance_score'
                    elif any(keyword in col_lower for keyword in ['status']):
                        column_mapping[col] = 'status'
                
                # 列名変更
                df_renamed = df.rename(columns=column_mapping)
                
                # 必須列が存在するかチェック
                if 'company_name' in df_renamed.columns and 'email_address' in df_renamed.columns:
                    # データをクリーニング
                    df_clean = df_renamed[['company_name', 'email_address']].copy()
                    
                    # ステータスとスコアを追加（存在しない場合）
                    if 'status' not in df_renamed.columns:
                        df_clean['status'] = 'New'
                    else:
                        df_clean['status'] = df_renamed['status'].fillna('New')
                    
                    if 'picocela_relevance_score' not in df_renamed.columns:
                        df_clean['picocela_relevance_score'] = 50
                    else:
                        df_clean['picocela_relevance_score'] = pd.to_numeric(df_renamed['picocela_relevance_score'], errors='coerce').fillna(50)
                    
                    # 有効なメールアドレスのみフィルタ
                    df_clean = df_clean[df_clean['email_address'].notna()]
                    df_clean = df_clean[df_clean['email_address'].str.contains('@', na=False)]
                    df_clean = df_clean[df_clean['company_name'].notna()]
                    
                    st.success(f"📧 有効なメールアドレス: {len(df_clean)}件")
                    
                    if len(df_clean) > 0:
                        return df_clean
                    else:
                        st.warning("⚠️ 有効なデータが見つかりません")
                else:
                    st.error("❌ 必要な列（company_name, email）が見つかりません")
                    
            else:
                st.warning(f"⚠️ Google Sheets アクセス失敗 (ステータス: {response.status_code})")
                
        except Exception as sheets_error:
            st.warning(f"⚠️ Google Sheets 接続エラー: {sheets_error}")
            
    except Exception as e:
        st.error(f"❌ Google Sheets 処理エラー: {e}")
    
    # 2. Google Apps Script API 経由でデータ取得を試行
    try:
        st.info("🔄 Google Apps Script API 経由での取得を試行...")
        
        # FusionCRM本体で使用されているGoogle Apps Script URL
        gas_url = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"  # 実際のURLに置き換えが必要
        
        # ここでGoogle Apps Script経由のデータ取得を実装
        # （現在は仮の実装）
        
    except Exception as gas_error:
        st.warning(f"⚠️ Google Apps Script API エラー: {gas_error}")
    
    # 3. 手動データ入力オプション
    st.write("---")
    st.subheader("📝 手動企業データ入力")
    st.info("💡 Google Sheets のデータが取得できない場合は、手動でデータを入力してください")
    
    with st.expander("➕ 企業データを手動で追加"):
        with st.form("manual_company_input"):
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("会社名", value="FUSIONDRIVER")
                email = st.text_input("メールアドレス", value="koji@fusiondriver.biz")
            with col2:
                status = st.selectbox("ステータス", ["New", "Contacted", "Replied"])
                score = st.number_input("優先スコア", min_value=0, max_value=100, value=70)
            
            if st.form_submit_button("➕ 企業を追加"):
                if company_name and email and '@' in email:
                    # セッション状態に保存
                    if 'manual_companies' not in st.session_state:
                        st.session_state.manual_companies = []
                    
                    st.session_state.manual_companies.append({
                        'company_name': company_name,
                        'email_address': email,
                        'status': status,
                        'picocela_relevance_score': score
                    })
                    
                    st.success(f"✅ {company_name} を追加しました")
                    st.rerun()  # 画面を更新
                else:
                    st.error("❌ 会社名と有効なメールアドレスを入力してください")
    
    # 4. 手動入力データを返す
    if 'manual_companies' in st.session_state and st.session_state.manual_companies:
        df = pd.DataFrame(st.session_state.manual_companies)
        st.success(f"✅ 手動入力データを使用: {len(df)}社")
        st.dataframe(df)
        return df
    
    # 5. Google Sheets URL の設定オプション
    st.write("---")
    st.subheader("🔗 Google Sheets URL 設定")
    
    with st.expander("⚙️ Google Sheets 接続設定"):
        st.markdown("""
        **FusionCRM本体のGoogle Sheetsに直接接続するには：**
        
        1. **Google Sheets を公開設定にする**
        2. **シートのURLをコピー**
        3. **以下に入力**
        """)
        
        sheets_url_input = st.text_input(
            "Google Sheets URL", 
            value="https://docs.google.com/spreadsheets/d/1ySS3zLbEwq3U54pzIRAbKLyhOWR2YdBUSdk_xr_7WNY",
            help="FusionCRMで使用されているGoogle SheetsのURL"
        )
        
        if st.button("🔄 指定したシートからデータを取得"):
            if sheets_url_input:
                try:
                    csv_url = f"{sheets_url_input}/export?format=csv&gid=0"
                    response = requests.get(csv_url, timeout=10)
                    
                    if response.status_code == 200:
                        df = pd.read_csv(StringIO(response.text))
                        st.success(f"✅ 指定シートから {len(df)}件取得")
                        st.dataframe(df.head())
                        # この結果をセッション状態に保存することも可能
                    else:
                        st.error(f"❌ シートアクセス失敗: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"❌ 取得エラー: {e}")
    
    # 6. フォールバック（FUSIONDRIVERを含む）
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
