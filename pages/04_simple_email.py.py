# pages/04_simple_email.py - 認証不要のメール送信システム
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import requests

st.set_page_config(
    page_title="シンプルメール送信",
    page_icon="📧",
    layout="wide"
)

st.title("📧 シンプルメール送信システム")
st.markdown("---")

# CRMデータ取得関数
@st.cache_data(ttl=300)
def get_crm_data():
    try:
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

# メール送信方法の選択
st.header("🚀 実用的なメール送信オプション")

tab1, tab2, tab3 = st.tabs(["📧 Gmail SMTP", "📊 CRM連携", "📋 送信履歴"])

with tab1:
    st.subheader("Gmail SMTP設定")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("💡 Gmail SMTPを使用した確実なメール送信")
        
        # Gmail SMTP設定
        gmail_user = st.text_input("送信者Gmail:", placeholder="your-email@gmail.com")
        gmail_password = st.text_input("Gmailパスワード:", type="password", placeholder="アプリパスワードまたは通常パスワード")
        
        # メール作成
        to_email = st.text_input("宛先:", placeholder="recipient@example.com")
        subject = st.text_input("件名:", placeholder="PicoCELA Wi-Fi Solutions")
        
        # メールテンプレート
        template_option = st.selectbox(
            "メールテンプレート:",
            ["カスタム", "営業メール", "フォローアップ", "製品紹介"]
        )
        
        if template_option == "営業メール":
            default_body = """Dear [Company Name],

I hope this email finds you well. I'm reaching out from PicoCELA regarding our advanced Wi-Fi solutions.

Our picoCELA technology offers:
• Reliable connectivity in industrial environments
• Easy deployment and maintenance
• Scalable solutions for any project size

Would you be interested in a brief discussion about how we can enhance your operations?

Best regards,
Koji Tokuda
PicoCELA, Inc."""
        else:
            default_body = ""
        
        body = st.text_area("メール本文:", value=default_body, height=200)
        
        # 送信ボタン
        if st.button("📧 メール送信", type="primary"):
            if gmail_user and gmail_password and to_email and subject and body:
                try:
                    # Gmail SMTP設定
                    msg = MIMEMultipart()
                    msg['From'] = gmail_user
                    msg['To'] = to_email
                    msg['Subject'] = subject
                    
                    msg.attach(MIMEText(body, 'plain'))
                    
                    # SMTP送信
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(gmail_user, gmail_password)
                    
                    text = msg.as_string()
                    server.sendmail(gmail_user, to_email, text)
                    server.quit()
                    
                    st.success("✅ メール送信成功！")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ 送信エラー: {e}")
                    st.info("💡 Gmailのアプリパスワードを使用してください")
            else:
                st.warning("すべての項目を入力してください")
    
    with col2:
        st.write("### 📋 送信設定")
        st.info("**方法**: Gmail SMTP")
        st.info("**認証**: 標準ログイン")
        st.info("**制限**: 500通/日")
        
        st.write("### ⚙️ 設定ヘルプ")
        with st.expander("Gmailアプリパスワード設定"):
            st.write("""
            1. Googleアカウント設定
            2. セキュリティ → 2段階認証有効化
            3. アプリパスワード生成
            4. 生成されたパスワードを使用
            """)

with tab2:
    st.subheader("CRM連携メール配信")
    
    # CRMデータ取得
    crm_data = get_crm_data()
    
    if not crm_data.empty:
        st.success(f"✅ CRMデータ: {len(crm_data)}社")
        
        # フィルタリング
        wifi_filter = st.selectbox("WiFi需要レベル:", ["全て", "High", "Medium", "Low"])
        
        filtered_data = crm_data.copy()
        if wifi_filter != "全て":
            filtered_data = filtered_data[filtered_data['wifi_needs'] == wifi_filter]
        
        st.write(f"**対象企業**: {len(filtered_data)}社")
        
        if len(filtered_data) > 0:
            # 企業選択
            selected_companies = st.multiselect(
                "送信先企業:",
                options=filtered_data['company_name'].tolist(),
                default=filtered_data['company_name'].tolist()[:3]
            )
            
            if selected_companies:
                # 送信設定
                batch_gmail = st.text_input("送信Gmail:", key="batch_gmail")
                batch_password = st.text_input("パスワード:", type="password", key="batch_password")
                batch_subject = st.text_input("件名:", value="PicoCELA Wi-Fi Solutions for Your Business")
                
                batch_body = st.text_area(
                    "メール本文:",
                    value="""Dear [Company Name] Team,

I hope this message finds you well. I'm writing from PicoCELA about our Wi-Fi solutions.

Our technology is perfect for companies like yours in the [Industry] sector.

Key benefits:
• Reliable industrial-grade Wi-Fi
• Easy installation and maintenance
• Proven ROI for similar companies

Would you be interested in a brief call to discuss how picoCELA can benefit your operations?

Best regards,
Koji Tokuda
PicoCELA, Inc.""",
                    height=200
                )
                
                # 一括送信
                if st.button("🚀 一括送信", type="primary"):
                    if batch_gmail and batch_password:
                        progress_bar = st.progress(0)
                        success_count = 0
                        
                        for i, company in enumerate(selected_companies):
                            try:
                                company_data = filtered_data[filtered_data['company_name'] == company].iloc[0]
                                
                                if pd.notna(company_data['email']) and company_data['email']:
                                    # メール個別化
                                    personalized_body = batch_body.replace('[Company Name]', company)
                                    
                                    # SMTP送信
                                    msg = MIMEMultipart()
                                    msg['From'] = batch_gmail
                                    msg['To'] = company_data['email']
                                    msg['Subject'] = batch_subject
                                    msg.attach(MIMEText(personalized_body, 'plain'))
                                    
                                    server = smtplib.SMTP('smtp.gmail.com', 587)
                                    server.starttls()
                                    server.login(batch_gmail, batch_password)
                                    server.sendmail(batch_gmail, company_data['email'], msg.as_string())
                                    server.quit()
                                    
                                    success_count += 1
                                    st.write(f"✅ {company}: 送信成功")
                                else:
                                    st.write(f"⚠️ {company}: メールアドレスなし")
                                
                                progress_bar.progress((i + 1) / len(selected_companies))
                                
                            except Exception as e:
                                st.write(f"❌ {company}: 送信失敗 - {str(e)}")
                        
                        st.success(f"🎉 一括送信完了！成功: {success_count}/{len(selected_companies)}件")
                        if success_count > 0:
                            st.balloons()
                    else:
                        st.warning("Gmail認証情報を入力してください")
    else:
        st.warning("CRMデータを取得できませんでした")

with tab3:
    st.subheader("送信履歴・統計")
    
    # 模擬統計
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今日の送信", "0", "📧")
    with col2:
        st.metric("今月の送信", "0", "📊") 
    with col3:
        st.metric("成功率", "0%", "✅")
    
    st.info("💡 実際の送信履歴はメール送信後に表示されます")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>📧 Gmail SMTP | 🏢 PicoCELA メール配信システム</p>
        <p>💡 OAuth2が困難な場合の実用的な代替ソリューション</p>
    </div>
    """, 
    unsafe_allow_html=True
)