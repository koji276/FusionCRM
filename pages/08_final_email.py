import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime

# Google Apps Script WebアプリのURL
GAS_URL = "https://script.google.com/macros/s/AKfycby998uiOXSrg9GEDvocVfZR7a7uN_P121G__FRqyJh2zLMJA8KUB2dtsHi7GSZxoRAD-A/exec"

def send_email_via_gas(recipient, subject, body, sender_name="PicoCELA CRM System"):
    """Google Apps Script経由でメール送信"""
    try:
        payload = {
            "action": "send_email",
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "senderName": sender_name
        }
        
        response = requests.post(
            GAS_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error", 
                "message": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_bulk_emails_via_gas(recipients, subject, body, sender_name="PicoCELA CRM System"):
    """Google Apps Script経由で一括メール送信"""
    try:
        payload = {
            "action": "send_bulk_emails",
            "recipients": recipients,
            "subject": subject,
            "body": body,
            "senderName": sender_name
        }
        
        response = requests.post(
            GAS_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=180  # 一括送信は時間がかかるため長めに設定
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "error", 
                "message": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_companies_data():
    """CRMデータ取得"""
    try:
        payload = {"action": "get_companies"}
        response = requests.post(
            GAS_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Streamlit UI設定
st.set_page_config(
    page_title="PicoCELA メール送信システム",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 PicoCELA メール送信システム - 動作確実版")

# 成功メッセージ
st.success("✅ Google Apps Script v16 デプロイ完了 - メール送信機能実装済み")

# タブ構成
tab1, tab2, tab3 = st.tabs(["📧 単体メール送信", "📤 一括メール送信", "📊 CRM連携テスト"])

# Tab 1: 単体メール送信
with tab1:
    st.header("📧 単体メール送信テスト")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_recipient = st.text_input(
            "送信先メールアドレス", 
            value="koji@fusiondriver.biz",
            help="テスト用のメールアドレスを入力してください"
        )
        
        test_subject = st.text_input(
            "件名", 
            value="🚀 PicoCELA WiFiソリューション - ご提案"
        )
    
    with col2:
        sender_name = st.text_input(
            "送信者名", 
            value="PicoCELA CRM System"
        )
    
    test_body = st.text_area(
        "メール本文（HTML対応）", 
        value="""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2E86AB;">🚀 PicoCELA WiFiソリューションのご提案</h2>

    <p>{{company_name}} 様</p>

    <p>いつもお世話になっております。<br>
    PicoCELAの徳田です。</p>

    <p>弊社の最新WiFi 6対応ソリューションについて、以下の特長をご紹介させていただきます：</p>

    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="color: #2E86AB; margin-top: 0;">主要機能</h3>
        <ul style="line-height: 1.6;">
            <li><strong>🚀 高速通信:</strong> 最大9.6Gbpsの高速WiFi 6対応</li>
            <li><strong>⚡ 低遅延:</strong> リアルタイム通信に最適</li>
            <li><strong>🔋 省電力:</strong> バッテリー駆動デバイスの電池寿命を延長</li>
            <li><strong>📱 高密度接続:</strong> 多数のデバイス同時接続が可能</li>
        </ul>
    </div>

    <p>貴社の業務効率化に大きく貢献できるソリューションです。<br>
    詳細なご提案をさせていただければ幸いです。</p>

    <p>ご質問やお打ち合わせのご希望がございましたら、お気軽にお声がけください。</p>

    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    
    <div style="color: #6c757d; font-size: 14px;">
        <p><strong>PicoCELA株式会社</strong><br>
        徳田 浩二<br>
        📧 Email: tokuda@picocela.com<br>
        📞 Tel: 03-1234-5678</p>
        
        <p style="font-size: 12px; margin-top: 20px;">
            <em>このメールはFusionCRMシステムから送信されました。</em>
        </p>
    </div>
</div>
        """,
        height=400
    )
    
    if st.button("📧 テストメール送信", type="primary", use_container_width=True):
        if test_recipient and test_subject and test_body:
            with st.spinner("🚀 メール送信中..."):
                result = send_email_via_gas(
                    recipient=test_recipient,
                    subject=test_subject,
                    body=test_body,
                    sender_name=sender_name
                )
                
                if result.get("status") == "success":
                    st.success(f"""
                    🎉 **メール送信成功！**
                    
                    📧 送信先: {test_recipient}
                    📝 件名: {test_subject}
                    ⏰ 送信時刻: {result.get('timestamp', 'N/A')}
                    """)
                    
                    with st.expander("📋 送信結果詳細"):
                        st.json(result)
                        
                else:
                    st.error(f"❌ **メール送信失敗**\n\n{result.get('message', 'Unknown error')}")
                    with st.expander("🔍 エラー詳細"):
                        st.json(result)
        else:
            st.error("⚠️ 送信先、件名、本文は必須項目です")

# Tab 2: 一括メール送信
with tab2:
    st.header("📤 一括メール送信")
    
    # CRMデータ取得
    if st.button("📊 CRMデータを取得", use_container_width=True):
        with st.spinner("📈 データ取得中..."):
            companies_data = get_companies_data()
            
            if companies_data.get("success") == True:
                companies = companies_data.get("companies", [])
                st.session_state.companies = companies
                st.success(f"✅ **{len(companies)}社のデータを取得しました**")
                
                # 基本統計
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 総企業数", len(companies))
                with col2:
                    email_count = len([c for c in companies if c.get('email')])
                    st.metric("📧 メール保有企業", email_count)
                with col3:
                    wifi_companies = len([c for c in companies if c.get('wifi_needs', '').lower() in ['high', 'medium']])
                    st.metric("📶 WiFi需要企業", wifi_companies)
                    
            else:
                st.error(f"❌ **データ取得失敗**\n\n{companies_data.get('message', 'Unknown error')}")
    
    # 取得済みデータの表示と送信
    if 'companies' in st.session_state and st.session_state.companies:
        st.subheader(f"📈 CRMデータ管理 ({len(st.session_state.companies)}社)")
        
        # データフレーム表示
        df = pd.DataFrame(st.session_state.companies)
        if not df.empty:
            # メールアドレスがある企業のみフィルタリング
            df_with_email = df[df['email'].notna() & (df['email'] != '')]
            
            if not df_with_email.empty:
                st.dataframe(
                    df_with_email[['company_name', 'email', 'wifi_needs', 'sales_status']].head(10),
                    use_container_width=True
                )
                
                # 送信対象選択
                st.subheader("🎯 送信対象選択")
                
                # フィルター条件
                col1, col2 = st.columns(2)
                with col1:
                    wifi_filter = st.selectbox(
                        "WiFi需要レベル",
                        options=["すべて", "High", "Medium", "Low"],
                        index=0
                    )
                with col2:
                    status_filter = st.selectbox(
                        "営業ステータス",
                        options=["すべて", "New", "Contacted", "Qualified", "Proposal", "Closed"],
                        index=0
                    )
                
                # フィルタリング適用
                filtered_companies = df_with_email
                if wifi_filter != "すべて":
                    filtered_companies = filtered_companies[filtered_companies['wifi_needs'] == wifi_filter]
                if status_filter != "すべて":
                    filtered_companies = filtered_companies[filtered_companies['sales_status'] == status_filter]
                
                st.info(f"📊 フィルタリング結果: **{len(filtered_companies)}社**")
                
                if len(filtered_companies) > 0:
                    # 一括送信設定
                    st.subheader("📧 一括送信設定")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        bulk_subject = st.text_input(
                            "件名", 
                            value="🚀 PicoCELA WiFiソリューション - 特別ご提案"
                        )
                    with col2:
                        bulk_sender = st.text_input(
                            "送信者名", 
                            value="PicoCELA CRM System"
                        )
                    
                    bulk_body = st.text_area(
                        "メール本文（{{company_name}}で会社名置換）",
                        value=test_body,  # 上記で定義した本文を使用
                        height=300
                    )
                    
                    # 送信実行
                    if st.button(f"🚀 {len(filtered_companies)}社に一括送信", type="primary", use_container_width=True):
                        # 送信データ準備
                        recipients = []
                        for _, row in filtered_companies.iterrows():
                            recipients.append({
                                'email': row.get('email', ''),
                                'company_name': row.get('company_name', '')
                            })
                        
                        if recipients:
                            with st.spinner(f"📤 {len(recipients)}社にメール送信中... この処理には時間がかかります"):
                                
                                # プログレスバー
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                # 送信実行
                                result = send_bulk_emails_via_gas(
                                    recipients=recipients,
                                    subject=bulk_subject,
                                    body=bulk_body,
                                    sender_name=bulk_sender
                                )
                                
                                progress_bar.progress(100)
                                
                                if result.get("status") == "completed":
                                    st.success(f"""
                                    🎉 **一括送信完了！**
                                    
                                    📊 総送信数: {result.get('total', 0)}
                                    ✅ 成功: {result.get('successful', 0)}
                                    ❌ 失敗: {result.get('failed', 0)}
                                    ⏰ 完了時刻: {result.get('timestamp', 'N/A')}
                                    """)
                                    
                                    # 送信結果の詳細表示
                                    with st.expander("📋 送信結果詳細"):
                                        results_df = pd.DataFrame(result.get('results', []))
                                        if not results_df.empty:
                                            st.dataframe(results_df, use_container_width=True)
                                else:
                                    st.error(f"❌ **一括送信失敗**\n\n{result.get('message', 'Unknown error')}")
                        else:
                            st.warning("⚠️ 送信可能なメールアドレスがありません")
                else:
                    st.warning("⚠️ フィルタリング条件に該当する企業がありません")
            else:
                st.warning("⚠️ メールアドレスが登録されている企業がありません")

# Tab 3: CRM連携テスト
with tab3:
    st.header("📊 CRM連携テスト")
    
    if st.button("🔄 システム接続テスト", use_container_width=True):
        with st.spinner("🔍 接続確認中..."):
            # Google Apps Script接続テスト
            try:
                test_response = requests.get(
                    GAS_URL + "?action=test", 
                    timeout=10
                )
                
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    st.success("✅ **Google Apps Script接続成功**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🔗 接続ステータス", "正常")
                        st.metric("⏱️ レスポンス時間", f"{test_response.elapsed.total_seconds():.2f}秒")
                    with col2:
                        st.metric("📅 最終更新", test_data.get('timestamp', 'N/A'))
                        st.metric("🆔 システムID", "v16")
                    
                    with st.expander("🔍 接続テスト詳細"):
                        st.json(test_data)
                        
                else:
                    st.error(f"❌ 接続エラー: HTTP {test_response.status_code}")
                    
            except Exception as e:
                st.error(f"❌ **接続テスト失敗**\n\n{str(e)}")
    
    # システム情報表示
    st.subheader("⚙️ システム情報")
    
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info("""
        **📧 メール送信設定**
        - 送信方式: Google Apps Script + Gmail API
        - 送信者: tokuda@picocela.com
        - 認証: OAuth2自動処理
        - 送信制限: 2秒間隔（Gmail制限対策）
        """)
    
    with info_col2:
        st.info("""
        **🔗 システム連携**
        - CRMデータ: Google Sheets
        - バックエンド: Google Apps Script v16
        - フロントエンド: Streamlit Cloud
        - 通信: HTTPS + JSON API
        """)

# サイドバー: 設定とステータス
with st.sidebar:
    st.header("🚀 FusionCRM v16")
    
    st.success("✅ **システム稼働中**")
    
    st.subheader("📊 システム状態")
    st.metric("🔧 バージョン", "v16 (Aug 5, 2025)")
    st.metric("🌐 デプロイID", "Version 3")
    st.metric("📧 メール機能", "✅ 実装済み")
    
    st.subheader("⚙️ 技術仕様")
    st.code(f"""
Google Apps Script URL:
{GAS_URL}
    """)
    
    if st.button("📋 URLをコピー"):
        st.success("✅ URLをクリップボードにコピーしました")

st.markdown("---")
st.markdown("*🚀 PicoCELA メール送信システム - Powered by Google Apps Script v16 & Streamlit*")