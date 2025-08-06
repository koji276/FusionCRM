# pages/05_working_email.py - 動作確実版
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="PicoCELA メール送信システム - 動作確実版",
    page_icon="📧",
    layout="wide"
)

st.title("📧 PicoCELA メール送信システム - 動作確実版")
st.markdown("---")

# CRMデータ取得関数（以前動いていたURL使用）
@st.cache_data(ttl=300)
def get_crm_data():
    """Google Apps ScriptからCRMデータを取得"""
    try:
        # 前回動いていたGoogle Apps ScriptのURL
        api_url = "https://script.google.com/macros/s/AKfycby998uiOXSrg9GEDvocVfZR7a7uN_P121GFRqyJh2zLMJA8KUB2dtsHi7GSZxoRAD-A/exec"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(
            api_url,
            params={"action": "get_companies"},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame(data)
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"CRMデータ取得エラー: {e}")
        return pd.DataFrame()

def send_single_email(from_email, from_password, to_email, subject, body, company_name):
    """単体メール送信関数（Outlook SMTP使用）"""
    try:
        # Gmail SMTP設定（PicoCELAメール対応）
        msg = MIMEMultipart()
        msg['From'] = f"Koji Tokuda (PicoCELA) <{from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = 'tokuda@picocela.com'
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        
        return True, "送信成功"
        
    except smtplib.SMTPAuthenticationError:
        return False, "認証エラー - アプリパスワードを確認してください"
    except smtplib.SMTPRecipientsRefused:
        return False, f"無効なメールアドレス: {to_email}"
    except Exception as e:
        return False, f"送信エラー: {str(e)}"

def send_batch_emails(from_email, from_password, companies_data, max_emails, send_interval):
    """一括メール送信関数"""
    st.write(f"📤 {min(max_emails, len(companies_data))}社への送信開始")
    
    sent_count = 0
    failed_count = 0
    
    # 進捗表示
    progress_bar = st.progress(0)
    status_area = st.empty()
    
    for i, company in enumerate(companies_data[:max_emails]):
        company_name = company.get('company_name', company.get('Company_Name', 'Unknown'))
        company_email = company.get('email', company.get('Contact_Email', ''))
        industry = company.get('industry', company.get('Industry', 'Unknown'))
        
        # 進捗更新
        progress = (i + 1) / min(max_emails, len(companies_data))
        progress_bar.progress(progress)
        status_area.write(f"送信中: {company_name} ({i+1}/{min(max_emails, len(companies_data))})")
        
        # 送信間隔（最初以外）
        if i > 0:
            time.sleep(send_interval)
        
        # メールアドレス確認
        if not company_email:
            st.error(f"❌ {company_name} - メールアドレスが見つかりません")
            failed_count += 1
            continue
        
        # メール内容生成
        subject = f"Partnership Opportunity - PicoCELA Advanced Wi-Fi Solutions"
        
        body = f"""Dear {company_name} Team,

I hope this message finds you well.

My name is Koji Tokuda from PicoCELA Inc. (NASDAQ: PCLA), a leading provider of advanced industrial multi-hop mesh Wi-Fi access point solutions.

We specialize in creating robust, scalable wireless networks that can extend up to 10 hops with ultra-low latency (2-3ms per hop), reducing traditional cabling infrastructure by up to 90%.

Given your operations in the {industry} sector, I believe there could be significant synergies between our technologies and your business objectives.

Our picoCELA technology offers:
• Reliable connectivity in challenging industrial environments
• Easy deployment and maintenance with minimal infrastructure
• Scalable solutions that grow with your business
• Proven ROI through reduced cabling and installation costs

Would you be open to a brief conversation to explore potential partnership opportunities? I'd be happy to share more details about how our solutions have helped companies in similar industries optimize their connectivity infrastructure.

Thank you for your time and consideration.

Best regards,

Koji Tokuda
CEO
PicoCELA Inc.
tokuda@picocela.com
+1 (408) 692-5500

---
This email was sent from our integrated CRM system. If you would prefer not to receive future communications, please reply with "UNSUBSCRIBE".
"""
        
        # メール送信実行
        success, message = send_single_email(
            from_email, from_password, company_email, subject, body, company_name
        )
        
        if success:
            sent_count += 1
            st.success(f"✅ {company_name} - {message}")
        else:
            failed_count += 1
            st.error(f"❌ {company_name} - {message}")
            
            # 認証エラーの場合は中止
            if "認証エラー" in message:
                st.error("認証エラーのため送信を中止します")
                break
    
    # 完了サマリー
    total_attempted = min(max_emails, len(companies_data))
    success_rate = (sent_count / total_attempted * 100) if total_attempted > 0 else 0
    
    st.write("---")
    st.write("📊 **送信完了サマリー**")
    st.write(f"✅ 成功: {sent_count}社")
    st.write(f"❌ 失敗: {failed_count}社")
    st.write(f"📈 成功率: {success_rate:.1f}%")
    
    if sent_count > 0:
        st.balloons()
    
    return {
        'sent_count': sent_count,
        'failed_count': failed_count,
        'success_rate': success_rate
    }

# メイン機能
def main():
    # サイドバー設定
    with st.sidebar:
        st.header("🔧 メール設定")
        
        # Gmail/Outlook設定
        email_service = st.selectbox("メールサービス", ["Outlook", "Gmail"], help="OutlookがPicoCELAメール推奨")
        
        if email_service == "Outlook":
            st.info("💡 PicoCELAメール（tokuda@picocela.com）推奨")
            default_email = "tokuda@picocela.com"
            smtp_info = "Outlook SMTP使用"
        else:
            st.info("💡 Gmail SMTP使用")
            default_email = "your-email@gmail.com"
            smtp_info = "Gmail SMTP使用"
        
        from_email = st.text_input("送信元メール", value=default_email)
        from_password = st.text_input("アプリパスワード", type="password", 
                                    help="2段階認証のアプリパスワードを使用")
        
        st.write(f"**設定**: {smtp_info}")
        
        # 送信設定
        st.header("📊 送信設定")
        max_emails = st.number_input("最大送信数", min_value=1, max_value=100, value=10, 
                                   help="テスト送信は10件程度推奨")
        send_interval = st.slider("送信間隔（秒）", min_value=30, max_value=300, value=120, 
                                help="メール制限対策のため120秒推奨")
        
        # 設定確認
        if from_email and from_password:
            st.success("✅ メール設定完了")
        else:
            st.warning("⚠️ メール設定が必要")

    # メインコンテンツ
    tab1, tab2, tab3 = st.tabs(["📧 単体送信", "🚀 一括送信", "📋 CRMデータ"])
    
    with tab1:
        st.subheader("📧 単体メール送信テスト")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_email = st.text_input("テスト送信先", placeholder="test@example.com")
            test_subject = st.text_input("件名", value="PicoCELA Partnership Test")
        
        with col2:
            test_company = st.text_input("会社名", value="Test Company")
        
        if st.button("📧 テスト送信実行", type="primary"):
            if from_email and from_password and test_email:
                test_body = f"""Dear {test_company} Team,

This is a test message from PicoCELA's integrated email system.

If you received this message, our email configuration is working correctly.

Best regards,
Koji Tokuda
PicoCELA Inc.
tokuda@picocela.com"""
                
                success, message = send_single_email(
                    from_email, from_password, test_email, test_subject, test_body, test_company
                )
                
                if success:
                    st.success(f"✅ テスト送信成功: {message}")
                else:
                    st.error(f"❌ テスト送信失敗: {message}")
            else:
                st.warning("すべての項目を入力してください")
    
    with tab2:
        st.subheader("🚀 CRM連携一括メール送信")
        
        # CRMデータ取得
        crm_data = get_crm_data()
        
        if not crm_data.empty:
            st.success(f"✅ CRMデータ: {len(crm_data)}社")
            
            # データプレビュー
            with st.expander("📋 送信対象企業プレビュー"):
                st.dataframe(crm_data.head(10), use_container_width=True)
            
            # 送信実行
            col1, col2 = st.columns(2)
            
            with col1:
                if from_email and from_password:
                    st.success("✅ メール設定確認済み")
                else:
                    st.error("❌ サイドバーでメール設定を完了してください")
            
            with col2:
                estimated_time = max_emails * (send_interval + 10) / 60
                st.info(f"⏱️ 予想時間: {estimated_time:.1f}分")
            
            # 送信確認と実行
            if from_email and from_password:
                confirm_send = st.checkbox("📤 送信内容を確認し、メール制限を理解しました")
                
                if confirm_send:
                    if st.button("🚀 一括送信開始", type="primary"):
                        result = send_batch_emails(
                            from_email, from_password, crm_data.to_dict('records'), 
                            max_emails, send_interval
                        )
                        
                        # 結果をセッションに保存
                        st.session_state['last_send_result'] = result
                        st.session_state['last_send_time'] = datetime.now().isoformat()
        else:
            st.error("❌ CRMデータを取得できませんでした")
            st.info("Google Apps Scriptの接続を確認してください")
    
    with tab3:
        st.subheader("📋 CRMデータ確認")
        
        # データ取得と表示
        if st.button("🔄 データ再取得"):
            st.cache_data.clear()
        
        crm_data = get_crm_data()
        
        if not crm_data.empty:
            st.success(f"✅ 取得成功: {len(crm_data)}社")
            
            # 統計情報
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総企業数", len(crm_data))
            with col2:
                valid_emails = crm_data['email'].notna().sum() if 'email' in crm_data.columns else 0
                st.metric("有効メール", valid_emails)
            with col3:
                email_rate = (valid_emails / len(crm_data) * 100) if len(crm_data) > 0 else 0
                st.metric("メール有効率", f"{email_rate:.1f}%")
            
            # データテーブル
            st.dataframe(crm_data, use_container_width=True)
        else:
            st.error("❌ データ取得失敗")
            st.info("Google Apps Scriptの設定を確認してください")

    # 最後の送信結果表示
    if 'last_send_result' in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 最終送信結果")
        result = st.session_state['last_send_result']
        st.sidebar.write(f"✅ 成功: {result['sent_count']}社")
        st.sidebar.write(f"❌ 失敗: {result['failed_count']}社")
        st.sidebar.write(f"📈 成功率: {result['success_rate']:.1f}%")
        st.sidebar.write(f"⏰ 送信時刻: {st.session_state.get('last_send_time', 'Unknown')}")

if __name__ == "__main__":
    main()
