#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Streamlit統合版 with メール配信機能
PicoCELA社専用営業管理システム（完全統合版）
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
import plotly.express as px
import plotly.graph_objects as go
import os

# セッション状態の初期化
if 'email_config' not in st.session_state:
    st.session_state.email_config = None
if 'selected_companies' not in st.session_state:
    st.session_state.selected_companies = []

class EmailDistribution:
    """メール配信クラス（Streamlit統合版）"""
    
    def __init__(self):
        self.config_path = "config"
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """設定ディレクトリの確保"""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
    
    def load_gmail_config(self):
        """Gmail設定の読み込み"""
        try:
            config_file = os.path.join(self.config_path, "gmail_config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def save_gmail_config(self, config):
        """Gmail設定の保存"""
        config_file = os.path.join(self.config_path, "gmail_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
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
    
    def send_email(self, to_email, company_name, subject, body, config):
        """単一メール送信"""
        try:
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
    
    def log_email_history(self, company_id, company_name, email, subject, status, error_msg=None):
        """送信履歴の記録"""
        try:
            conn = sqlite3.connect('fusion_crm.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO email_history (company_id, email_type, subject, content, status, error_message, sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (company_id, 'campaign', subject, f"Email sent to {email}", status, error_msg, datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"履歴記録エラー: {e}")

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
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def update_company_status(company_ids, new_status):
    """企業ステータスの一括更新"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in company_ids])
        cursor.execute(f"""
            UPDATE companies 
            SET status = ?, last_contact_date = ?, updated_at = ?
            WHERE id IN ({placeholders})
        """, [new_status, datetime.now(), datetime.now()] + company_ids)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"ステータス更新エラー: {e}")
        return False

def render_dashboard():
    """メインダッシュボード"""
    st.title("🚀 FusionCRM - PicoCELA営業管理システム")
    st.markdown("**Google Sheets版（クラウド対応）- Version 6.0**")
    
    # 企業データ取得
    df = get_companies_data()
    
    if df.empty:
        st.warning("企業データが見つかりません。")
        return
    
    # ダッシュボード統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", len(df), delta=None)
    
    with col2:
        wifi_companies = len(df[df['status'] == 'New'])
        st.metric("WiFi必要企業", wifi_companies, delta=f"+{wifi_companies}")
    
    with col3:
        high_priority = len(df[df['picocela_relevance_score'] >= 100])
        st.metric("高優先度企業", high_priority, delta=f"+{high_priority}")
    
    with col4:
        contacted = len(df[df['status'] == 'Contacted'])
        st.metric("商談中企業", contacted, delta=None)
    
    # ステータス分布チャート
    st.subheader("📊 企業ステータス分布")
    status_counts = df['status'].value_counts()
    fig = px.pie(values=status_counts.values, names=status_counts.index, 
                 title="企業ステータス分布")
    st.plotly_chart(fig, use_container_width=True)
    
    # 企業一覧（最新10社）
    st.subheader("📋 企業一覧（最新10社）")
    display_df = df.head(10)[['company_name', 'email_address', 'status', 'picocela_relevance_score']]
    st.dataframe(display_df, use_container_width=True)

def render_email_campaign():
    """メールキャンペーン機能"""
    st.title("📧 メールキャンペーン")
    
    email_dist = EmailDistribution()
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["📝 キャンペーン作成", "⚙️ 設定", "📊 送信履歴", "📈 分析"])
    
    with tab1:
        st.subheader("📝 メールキャンペーン作成")
        
        # Gmail設定確認
        gmail_config = email_dist.load_gmail_config()
        if not gmail_config:
            st.error("Gmail設定が見つかりません。設定タブで設定を行ってください。")
            return
        
        st.success(f"Gmail設定: {gmail_config['email']} ({gmail_config['sender_name']})")
        
        # 企業選択
        df = get_companies_data()
        if df.empty:
            st.warning("配信対象企業が見つかりません。")
            return
        
        # フィルター
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox(
                "ステータスフィルター",
                ["全て", "New", "Contacted", "Replied", "Qualified"]
            )
        
        with col2:
            priority_filter = st.selectbox(
                "優先度フィルター", 
                ["全て", "高優先度（100+）", "中優先度（50-99）", "低優先度（-49）"]
            )
        
        # フィルター適用
        filtered_df = df.copy()
        
        if status_filter != "全て":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        if priority_filter == "高優先度（100+）":
            filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= 100]
        elif priority_filter == "中優先度（50-99）":
            filtered_df = filtered_df[(filtered_df['picocela_relevance_score'] >= 50) & 
                                    (filtered_df['picocela_relevance_score'] < 100)]
        elif priority_filter == "低優先度（-49）":
            filtered_df = filtered_df[filtered_df['picocela_relevance_score'] < 50]
        
        st.write(f"📊 配信対象: {len(filtered_df)}社")
        
        # 企業選択
        if len(filtered_df) > 0:
            selected_companies = st.multiselect(
                "配信対象企業を選択",
                options=filtered_df.index.tolist(),
                format_func=lambda x: f"{filtered_df.loc[x, 'company_name']} ({filtered_df.loc[x, 'email_address']})",
                default=filtered_df.head(5).index.tolist()
            )
            
            # メール内容
            st.subheader("✉️ メール内容")
            
            # テンプレート選択
            template_type = st.selectbox(
                "テンプレート選択",
                ["カスタム", "初回提案", "フォローアップ", "デモ依頼"]
            )
            
            # テンプレート内容設定
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
            
            # メール入力
            email_subject = st.text_input("件名", value=default_subject)
            email_body = st.text_area("本文", value=default_body, height=300)
            
            # 送信オプション
            col1, col2 = st.columns(2)
            with col1:
                send_interval = st.slider("送信間隔（秒）", 1, 10, 3)
            with col2:
                update_status = st.checkbox("送信後にステータス更新", value=True)
            
            # プレビュー
            if st.button("👀 プレビュー"):
                if selected_companies and email_subject and email_body:
                    sample_company = filtered_df.loc[selected_companies[0], 'company_name']
                    preview_body = email_body.replace('{company_name}', sample_company)
                    
                    st.info("**プレビュー**")
                    st.write(f"**件名:** {email_subject}")
                    st.write(f"**本文:**")
                    st.text(preview_body)
            
            # 送信実行
            if st.button("🚀 キャンペーン送信", type="primary"):
                if selected_companies and email_subject and email_body:
                    
                    # 確認
                    st.warning(f"{len(selected_companies)}社に送信します。よろしいですか？")
                    
                    if st.button("✅ 送信実行"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        failed_count = 0
                        
                        for i, idx in enumerate(selected_companies):
                            company = filtered_df.loc[idx]
                            company_name = company['company_name']
                            email_address = company['email_address']
                            company_id = company['id']
                            
                            status_text.text(f"送信中: {company_name}")
                            
                            # メール送信
                            success, message = email_dist.send_email(
                                email_address, company_name, email_subject, email_body, gmail_config
                            )
                            
                            # 履歴記録
                            email_dist.log_email_history(
                                company_id, company_name, email_address, 
                                email_subject, "success" if success else "failed",
                                None if success else message
                            )
                            
                            if success:
                                success_count += 1
                                if update_status:
                                    update_company_status([company_id], "Contacted")
                            else:
                                failed_count += 1
                                st.error(f"{company_name}: {message}")
                            
                            # プログレス更新
                            progress_bar.progress((i + 1) / len(selected_companies))
                            
                            # 間隔制御
                            if i < len(selected_companies) - 1:
                                time.sleep(send_interval)
                        
                        # 結果表示
                        status_text.text("送信完了")
                        st.success(f"送信完了: 成功 {success_count}件, 失敗 {failed_count}件")
                        
                        # キャッシュクリア（データ更新反映）
                        st.rerun()
                
                else:
                    st.error("企業選択、件名、本文をすべて入力してください。")
    
    with tab2:
        st.subheader("⚙️ Gmail設定")
        
        # 現在の設定表示
        current_config = email_dist.load_gmail_config()
        if current_config:
            st.success("現在の設定:")
            st.write(f"📧 メールアドレス: {current_config['email']}")
            st.write(f"👤 送信者名: {current_config['sender_name']}")
        
        # 新規設定
        with st.form("gmail_config"):
            st.write("**新しい設定**")
            
            email = st.text_input("Gmail アドレス", 
                                value=current_config['email'] if current_config else "tokuda@picocela.com")
            password = st.text_input("アプリパスワード", type="password",
                                   value=current_config['password'] if current_config else "")
            sender_name = st.text_input("送信者名", 
                                      value=current_config['sender_name'] if current_config else "PicoCELA Inc.")
            
            if st.form_submit_button("💾 設定保存"):
                new_config = {
                    "email": email,
                    "password": password,
                    "sender_name": sender_name,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587
                }
                
                # 接続テスト
                success, message = email_dist.test_gmail_connection(new_config)
                
                if success:
                    email_dist.save_gmail_config(new_config)
                    st.success("✅ Gmail設定を保存しました")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with tab3:
        st.subheader("📊 送信履歴")
        
        try:
            conn = sqlite3.connect('fusion_crm.db')
            query = """
                SELECT eh.sent_at, c.company_name, eh.subject, eh.status, eh.error_message
                FROM email_history eh
                LEFT JOIN companies c ON eh.company_id = c.id
                ORDER BY eh.sent_at DESC
                LIMIT 50
            """
            history_df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True)
                
                # 統計
                success_rate = len(history_df[history_df['status'] == 'success']) / len(history_df) * 100
                st.metric("成功率", f"{success_rate:.1f}%")
            else:
                st.info("送信履歴がありません。")
                
        except Exception as e:
            st.error(f"履歴取得エラー: {e}")
    
    with tab4:
        st.subheader("📈 キャンペーン分析")
        st.info("分析機能は今後のアップデートで追加予定です。")

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="FusionCRM - PicoCELA営業管理",
        page_icon="🚀",
        layout="wide"
    )
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("🚀 FusionCRM")
        st.markdown("**PicoCELA営業管理システム**")
        
        page = st.radio(
            "ナビゲーション",
            ["📊 ダッシュボード", "📧 メールキャンペーン", "🏢 企業管理", "📈 分析・レポート"]
        )
    
    # ページ表示
    if page == "📊 ダッシュボード":
        render_dashboard()
    elif page == "📧 メールキャンペーン":
        render_email_campaign()
    elif page == "🏢 企業管理":
        st.title("🏢 企業管理")
        st.info("企業管理機能は今後のアップデートで追加予定です。")
    elif page == "📈 分析・レポート":
        st.title("📈 分析・レポート")
        st.info("分析・レポート機能は今後のアップデートで追加予定です。")

if __name__ == "__main__":
    main()
