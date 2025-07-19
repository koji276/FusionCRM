#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Streamlit Cloud対応 メール配信システム（完全修正版）
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
        """
        メール送信（前回成功したSMTP方式）
        """
        if not self.is_gmail_configured():
            return False, "Gmail設定が無効です"
        
        try:
            config = st.session_state.gmail_config
            
            # メッセージ作成（前回成功した方式）
            msg = MIMEMultipart()
            msg['From'] = f"{config['sender_name']} <{config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 会社名の置換
            formatted_body = body.replace('{company_name}', company_name)
            msg.attach(MIMEText(formatted_body, 'plain', 'utf-8'))
            
            # SMTP送信（前回成功した設定）
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
    実際のFusionCRMデータベースから企業データ取得（データベース探索版）
    """
    try:
        # 複数のデータベースファイルを試行
        db_files = ['fusion_crm.db', 'companies.db', 'crm.db', 'data.db']
        
        for db_file in db_files:
            try:
                if os.path.exists(db_file):
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # 利用可能なテーブル一覧を取得
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    st.info(f"📋 {db_file} のテーブル: {tables}")
                    
                    # 企業データっぽいテーブルを探す
                    company_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['company', 'companies', '企業', 'corp', 'business'])]
                    
                    if company_tables:
                        table_name = company_tables[0]
                        st.success(f"✅ テーブル発見: {table_name}")
                        
                        # テーブル構造確認
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        st.info(f"📋 {table_name} の列: {columns}")
                        
                        # 動的クエリ構築
                        name_col = next((col for col in columns if any(keyword in col.lower() for keyword in ['name', '名前', 'company'])), columns[0])
                        email_col = next((col for col in columns if any(keyword in col.lower() for keyword in ['email', 'mail', 'メール'])), None)
                        
                        if email_col:
                            query = f"""
                                SELECT 
                                    {name_col} as company_name,
                                    {email_col} as email_address,
                                    'New' as status,
                                    50 as picocela_relevance_score
                                FROM {table_name}
                                WHERE {email_col} IS NOT NULL 
                                AND {email_col} != ''
                                LIMIT 10
                            """
                            
                            df = pd.read_sql_query(query, conn)
                            conn.close()
                            
                            if len(df) > 0:
                                st.success(f"✅ {db_file}の{table_name}から {len(df)}社のデータを取得")
                                return df
                    
                    conn.close()
            except Exception as e:
                st.warning(f"⚠️ {db_file}: {e}")
                continue
        
        # データベースが見つからない場合
        st.error("❌ 有効なデータベースが見つかりません")
        
    except Exception as e:
        st.error(f"❌ データベース探索エラー: {e}")
    
    # フォールバック：FUSIONDRIVERを含む確実なテストデータ
    st.warning("⚠️ フォールバックデータを使用します")
    sample_data = {
        'company_name': [
            'FUSIONDRIVER',
            'テストコンストラクション株式会社',
            'スマートビルディング合同会社'
        ],
        'email_address': [
            'koji@fusiondriver.biz',
            'contact@test-construction.com',
            'info@smart-building.co.jp'
        ],
        'status': ['New', 'New', 'New'],
        'picocela_relevance_score': [70, 115, 120]
    }
    
    return pd.DataFrame(sample_data)

def render_header():
    """ヘッダー"""
    st.title("📧 FusionCRM メール配信システム")
    st.markdown("**独立メール配信アプリケーション（完全修正版）**")
    
    # メインシステムへのリンク
    st.info("🔗 [メインシステムに戻る](https://automl-3ynrytum8tugw8ytcue7ay.streamlit.app/) （別タブで開く）")

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
        st.markdown("### 📋 前回成功した設定を使用")
        st.info("前回の成功設定: tokuda@picocela.com + アプリパスワード")
        
        with st.form("gmail_setup"):
            email = st.text_input(
                "Gmailアドレス", 
                value="tokuda@picocela.com"
            )
            password = st.text_input(
                "アプリパスワード", 
                type="password",
                placeholder="bmzr lbrs cbbn jtmr"
            )
            sender_name = st.text_input(
                "送信者名", 
                value="PicoCELA Inc."
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
    """メール配信（完全修正版）"""
    st.header("📧 メール配信")
    
    app = StreamlitEmailWebApp()
    
    if not app.is_gmail_configured():
        st.error("❌ Gmail設定が必要です。上記で設定してください。")
        return
    
    # 企業データ取得（実際のDB接続）
    df = get_companies_data()
    
    if len(df) == 0:
        st.error("❌ 配信対象企業が見つかりません")
        return
    
    # 配信設定
    st.subheader("🎯 配信対象")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_options = ["全て"] + list(df['status'].unique()) if 'status' in df.columns else ["全て", "New"]
        status_filter = st.selectbox("ステータス", status_options)
    with col2:
        min_score = st.number_input("最小スコア", min_value=0, value=0)
    with col3:
        max_count = st.number_input("最大送信数", min_value=1, max_value=50, value=5)
    
    # フィルター適用
    filtered_df = df.copy()
    
    if status_filter != "全て":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if 'picocela_relevance_score' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= min_score]
        filtered_df = filtered_df.sort_values('picocela_relevance_score', ascending=False)
    
    filtered_df = filtered_df.head(max_count)
    
    st.info(f"📊 配信対象: {len(filtered_df)}社")
    
    if len(filtered_df) > 0:
        # 対象企業表示
        with st.expander("📋 配信対象企業"):
            display_columns = ['company_name', 'email_address', 'status']
            if 'picocela_relevance_score' in filtered_df.columns:
                display_columns.append('picocela_relevance_score')
            st.dataframe(filtered_df[display_columns])
        
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
        
        # 送信実行（修正版）
        col1, col2 = st.columns([3, 1])
        with col1:
            confirm_checked = st.checkbox("✅ 配信実行を確認")
        with col2:
            send_button = st.button("🚀 メール配信開始", type="primary")
        
        # 送信実行（修正版）
        col1, col2 = st.columns([3, 1])
        with col1:
            confirm_checked = st.checkbox("✅ 配信実行を確認")
        with col2:
            send_button = st.button("🚀 メール配信開始", type="primary")
        
        # デバッグ情報表示
        if send_button:
            st.write("🔍 ボタンが押されました")
            if not subject:
                st.error("❌ 件名が入力されていません")
            if not body:
                st.error("❌ 本文が入力されていません")
            if not confirm_checked:
                st.error("❌ 確認チェックボックスがチェックされていません")
            
            # Gmail設定確認
            if not app.is_gmail_configured():
                st.error("❌ Gmail設定が無効です")
            else:
                st.write("✅ Gmail設定OK")
        
        if send_button and subject and body and confirm_checked:
            st.write("🚀 送信処理を開始します...")
            
            # Gmail設定を再確認
            gmail_config = st.session_state.gmail_config
            st.write(f"📧 送信元: {gmail_config.get('email', 'なし')}")
            st.write(f"👤 送信者名: {gmail_config.get('sender_name', 'なし')}")
            
            if not gmail_config or not gmail_config.get('email'):
                st.error("❌ Gmail設定が不完全です")
                return
                    st.info(f"🚀 {len(filtered_df)}社への配信を開始します...")
                    
                    # 進捗表示
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.container()
                    
                    success_count = 0
                    failed_count = 0
                    results = []
                    
                    for i, (idx, company) in enumerate(filtered_df.iterrows()):
                        company_name = company['company_name']
                        email_address = company['email_address']
                        
                        # 進捗更新
                        progress = (i + 1) / len(filtered_df)
                        progress_bar.progress(progress)
                        status_text.text(f"📧 {i+1}/{len(filtered_df)}. {company_name} ({email_address}) 送信中...")
                        
                        # メール送信（前回成功したSMTP方式）
                        success, message = app.send_email(email_address, company_name, subject, body)
                        
                        if success:
                            success_count += 1
                            status_icon = "✅"
                            # ステータス更新
                            app.update_company_status(company_name, "Contacted")
                        else:
                            failed_count += 1
                            status_icon = "❌"
                        
                        # 結果記録
                        results.append({
                            'company': company_name,
                            'email': email_address,
                            'status': '成功' if success else '失敗',
                            'message': message,
                            'icon': status_icon
                        })
                        
                        # リアルタイム結果表示
                        with results_container:
                            st.write("📊 **送信結果:**")
                            for result in results[-3:]:  # 最新3件表示
                                st.write(f"{result['icon']} {result['company']} - {result['status']}")
                        
                        # 送信間隔（最後以外）
                        if i < len(filtered_df) - 1:
                            delay_variation = random.randint(-1, 2)  # ランダム性追加
                            actual_delay = max(1, send_interval + delay_variation)
                            status_text.text(f"⏱️ {actual_delay}秒待機中...")
                            time.sleep(actual_delay)
                    
                    # 完了表示
                    progress_bar.progress(1.0)
                    status_text.success("🎉 配信完了！")
                    
                    # 最終結果
                    st.success("📧 メール配信が完了しました！")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("✅ 送信成功", success_count)
                    col2.metric("❌ 送信失敗", failed_count)
                    total = success_count + failed_count
                    success_rate = (success_count / total * 100) if total > 0 else 0
                    col3.metric("📈 成功率", f"{success_rate:.1f}%")
                    
                    # 詳細結果表示
                    if st.checkbox("📋 詳細結果を表示"):
                        st.write("**全送信結果:**")
                        for result in results:
                            st.write(f"{result['icon']} **{result['company']}** ({result['email']}) - {result['status']}")
                            if result['status'] == '失敗':
                                st.write(f"   💬 エラー: {result['message']}")
                
                else:
                    st.warning("⚠️ 確認チェックボックスにチェックしてください")
            else:
                st.error("❌ 件名と本文を入力してください")
    else:
        st.warning("📭 フィルター条件に一致する企業がありません")

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
    st.markdown("**🔧 修正点**: 実際のデータベース接続 + 前回成功したSMTP送信方式 + ステータス自動更新")

if __name__ == "__main__":
    main()
