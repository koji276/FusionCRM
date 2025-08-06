# pages/02_email_oauth2.py - Gmail OAuth2メール送信システム
# Updated: 2025-08-05 - 完全新規OAuth2実装

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# OAuth2とGmail API用のインポート
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    import google.auth
except ImportError:
    st.error("必要なライブラリがインストールされていません。requirements.txtに以下を追加してください：")
    st.code("""
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
    """)
    st.stop()

# ページ設定
st.set_page_config(
    page_title="Gmail OAuth2メール配信",
    page_icon="📧",
    layout="wide"
)

# Streamlit Secretsから認証情報を取得
@st.cache_data
def get_client_config():
    """Streamlit Secretsから OAuth2 設定を取得"""
    try:
        return {
            "web": {
                "client_id": st.secrets["gmail_oauth"]["client_id"],
                "client_secret": st.secrets["gmail_oauth"]["client_secret"],
                "project_id": st.secrets["gmail_oauth"]["project_id"],
                "auth_uri": st.secrets["gmail_oauth"]["auth_uri"],
                "token_uri": st.secrets["gmail_oauth"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gmail_oauth"]["auth_provider_x509_cert_url"],
                "redirect_uris": [st.secrets["gmail_oauth"]["redirect_uri"]],
                "javascript_origins": [st.secrets["gmail_oauth"]["javascript_origin"]]
            }
        }
    except KeyError as e:
        st.error(f"Streamlit Secretsの設定が不完全です: {e}")
        st.info("secrets.tomlファイルを確認してください。")
        return None

# OAuth2設定
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def get_oauth2_flow():
    """OAuth2フローを初期化"""
    client_config = get_client_config()
    if not client_config:
        return None
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["gmail_oauth"]["redirect_uri"]
    )
    return flow

def authenticate_user():
    """ユーザー認証を実行"""
    flow = get_oauth2_flow()
    if not flow:
        return None
    
    # 認証URL生成
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    st.write("### 🔐 Gmail OAuth2認証")
    st.write("tokuda@picocela.com からメールを送信するために、Gmail APIへのアクセス許可が必要です。")
    
    st.markdown(f"**[📧 Gmailアクセスを許可する]({auth_url})**")
    
    # 認証コード入力
    auth_code = st.text_input(
        "認証コードを入力してください:",
        help="上記リンクをクリックして取得した認証コードを入力"
    )
    
    if auth_code:
        try:
            # 認証コードからトークンを取得
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            # セッション状態に保存
            st.session_state.gmail_credentials = credentials
            st.success("✅ Gmail認証成功！tokuda@picocela.com からメール送信が可能になりました。")
            st.rerun()
            
        except Exception as e:
            st.error(f"認証エラー: {e}")
    
    return None

def send_gmail(to_email, subject, body, credentials):
    """Gmail APIでメール送信"""
    try:
        # Gmail API サービス構築
        service = build('gmail', 'v1', credentials=credentials)
        
        # メッセージ作成
        message = MIMEMultipart()
        message['to'] = to_email
        message['from'] = 'tokuda@picocela.com'
        message['subject'] = subject
        
        # HTML形式のメール本文
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px;">
                <h2 style="color: #1f4e79;">PicoCELA Business Solutions</h2>
                {body.replace(chr(10), '<br>')}
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    Best regards,<br>
                    Koji Tokuda<br>
                    PicoCELA, Inc.<br>
                    Email: tokuda@picocela.com
                </p>
            </div>
        </body>
        </html>
        """
        
        message.attach(MIMEText(html_body, 'html'))
        
        # Base64エンコード
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # メール送信
        send_result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True, send_result['id']
        
    except Exception as e:
        return False, str(e)

def get_crm_data():
    """CRMデータを取得（既存のGoogle Sheets連携を使用）"""
    try:
        # 既存のCRMシステムから企業データを取得
        api_url = "https://script.google.com/macros/s/AKfycby998uiOXSrg9GEDvocVfZR7a7uN_P121GFRqyJh2zLMJA8KUB2dtsHi7GSZxoRAD-A/exec"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(
            api_url,
            params={"action": "get_companies"},
            headers=headers,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'companies' in data:
                return pd.DataFrame(data['companies'])
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"CRMデータ取得エラー: {e}")
        return pd.DataFrame()

# メインアプリケーション
def main():
    st.title("📧 Gmail OAuth2メール配信システム")
    st.markdown("---")
    
    # 認証状態の確認
    if 'gmail_credentials' not in st.session_state:
        st.write("### 🚀 Gmail OAuth2認証が必要です")
        authenticate_user()
        return
    
    # 認証済みの場合の機能
    credentials = st.session_state.gmail_credentials
    
    # 成功メッセージ
    st.success("✅ Gmail OAuth2認証済み - tokuda@picocela.com から送信可能")
    
    # タブ構成
    tab1, tab2, tab3 = st.tabs(["📧 メール作成", "📊 CRM連携", "📈 送信履歴"])
    
    with tab1:
        st.header("メール作成・送信")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # メール作成フォーム
            to_email = st.text_input("宛先メールアドレス:", placeholder="example@company.com")
            subject = st.text_input("件名:", placeholder="PicoCELA Wi-Fi Solution for Your Business")
            
            # プリセットメールテンプレート
            template_option = st.selectbox(
                "メールテンプレート:",
                ["カスタム", "初回営業", "製品紹介", "フォローアップ", "セミナー案内"]
            )
            
            if template_option == "初回営業":
                default_body = """Dear [Company Name],

I hope this email finds you well. My name is Koji Tokuda from PicoCELA, Inc.

We specialize in advanced Wi-Fi solutions for industrial and construction environments. Based on your company profile, I believe our picoCELA technology could significantly improve your wireless connectivity and operational efficiency.

Key benefits of our solution:
• Reliable Wi-Fi in harsh environments
• Easy installation and maintenance
• Scalable for projects of any size
• Cost-effective implementation

Would you be interested in a brief 15-minute discussion about how picoCELA can enhance your operations?

Looking forward to your response."""
            else:
                default_body = ""
            
            body = st.text_area(
                "メール本文:",
                value=default_body,
                height=300,
                placeholder="メール本文を入力してください..."
            )
        
        with col2:
            st.write("### 🎯 送信設定")
            st.info("**送信者**: tokuda@picocela.com")
            st.info("**認証**: OAuth2 (Gmail API)")
            
            # 送信ボタン
            if st.button("📧 メール送信", type="primary"):
                if to_email and subject and body:
                    with st.spinner("メール送信中..."):
                        success, result = send_gmail(to_email, subject, body, credentials)
                        
                        if success:
                            st.success(f"✅ メール送信成功！メッセージID: {result}")
                            st.balloons()
                        else:
                            st.error(f"❌ メール送信失敗: {result}")
                else:
                    st.warning("すべての項目を入力してください。")
    
    with tab2:
        st.header("CRM連携メール配信")
        
        # CRMデータ取得
        crm_data = get_crm_data()
        
        if not crm_data.empty:
            st.success(f"✅ CRMデータ取得成功: {len(crm_data)}社")
            
            # 送信対象企業の選択
            st.write("### 📋 送信対象企業選択")
            
            # フィルタリング
            wifi_filter = st.selectbox(
                "WiFi需要レベル:",
                ["全て", "High", "Medium", "Low"]
            )
            
            filtered_data = crm_data.copy()
            if wifi_filter != "全て":
                filtered_data = filtered_data[filtered_data['wifi_needs'] == wifi_filter]
            
            # 企業リスト表示
            st.write(f"**対象企業数**: {len(filtered_data)}社")
            
            if len(filtered_data) > 0:
                # 選択可能な企業リスト
                selected_companies = st.multiselect(
                    "送信先企業を選択:",
                    options=filtered_data['company_name'].tolist(),
                    default=filtered_data['company_name'].tolist()[:5]  # 最初の5社をデフォルト選択
                )
                
                if selected_companies:
                    # バッチ送信設定
                    batch_subject = st.text_input(
                        "一括送信件名:",
                        value="PicoCELA Wi-Fi Solutions - Perfect for Your Industry"
                    )
                    
                    batch_body = st.text_area(
                        "一括送信メール本文:",
                        value="""Dear [Company Name] Team,

I hope this message finds you well. I'm reaching out from PicoCELA, Inc., a leading provider of advanced Wi-Fi solutions.

Given your expertise in [Industry], I believe our picoCELA technology could be a valuable addition to your operations. Our solutions are specifically designed for:

• Industrial environments requiring reliable connectivity
• Construction sites with challenging wireless conditions  
• Manufacturing facilities needing robust network infrastructure

We've successfully helped companies similar to yours achieve:
✓ 99%+ network uptime
✓ 50% reduction in connectivity issues
✓ Seamless integration with existing systems

Would you be interested in a brief conversation about how picoCELA can enhance your operations?

Best regards,
Koji Tokuda""",
                        height=300
                    )
                    
                    # バッチ送信ボタン
                    if st.button("🚀 一括メール送信", type="primary"):
                        progress_bar = st.progress(0)
                        success_count = 0
                        
                        for i, company in enumerate(selected_companies):
                            company_data = filtered_data[filtered_data['company_name'] == company].iloc[0]
                            
                            if pd.notna(company_data['email']) and company_data['email']:
                                # 会社名を本文に挿入
                                personalized_body = batch_body.replace('[Company Name]', company)
                                
                                # メール送信
                                success, result = send_gmail(
                                    company_data['email'],
                                    batch_subject,
                                    personalized_body,
                                    credentials
                                )
                                
                                if success:
                                    success_count += 1
                                    st.write(f"✅ {company}: 送信成功")
                                else:
                                    st.write(f"❌ {company}: 送信失敗 - {result}")
                            else:
                                st.write(f"⚠️ {company}: メールアドレスなし")
                            
                            # プログレスバー更新
                            progress_bar.progress((i + 1) / len(selected_companies))
                        
                        st.success(f"🎉 一括送信完了！成功: {success_count}/{len(selected_companies)}件")
                        st.balloons()
        else:
            st.warning("CRMデータが取得できませんでした。")
    
    with tab3:
        st.header("送信履歴・統計")
        
        # ダミーデータ（実装時にはデータベースから取得）
        st.write("### 📊 今日の送信統計")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("送信数", "15", "↗️ +8")
        with col2:
            st.metric("成功率", "93.3%", "↗️ +2.1%")
        with col3:
            st.metric("開封率", "24.5%", "↗️ +1.2%")
        with col4:
            st.metric("応答率", "8.7%", "↗️ +0.5%")
        
        st.write("### 📈 送信履歴")
        
        # 模擬送信履歴
        history_data = pd.DataFrame({
            '送信時刻': ['2025-08-05 15:30', '2025-08-05 15:25', '2025-08-05 15:20'],
            '宛先': ['abc@construction.com', 'info@meshautomation.com', 'contact@interroll.com'],
            '件名': ['PicoCELA Wi-Fi Solutions', 'Industrial Connectivity Solutions', 'Wi-Fi for Manufacturing'],
            'ステータス': ['送信成功', '送信成功', '送信成功'],
            '送信者': ['tokuda@picocela.com', 'tokuda@picocela.com', 'tokuda@picocela.com']
        })
        
        st.dataframe(history_data, use_container_width=True)
    
    # フッター
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🔐 Gmail OAuth2 | 📧 tokuda@picocela.com | 🏢 PicoCELA, Inc.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
