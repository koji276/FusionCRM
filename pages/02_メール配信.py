# pages/02_📧_メール配信.py
# FusionCRM - メール配信システム (Multipage対応版)

import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import plotly.express as px
import plotly.graph_objects as go

# ページ設定
st.set_page_config(
    page_title="FusionCRM - メール配信",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 戻るボタン（ヘッダー）
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← 統合ダッシュボードに戻る", key="back_to_dashboard"):
        st.switch_page("fusion_crm_unified.py")

# ページヘッダー
st.markdown("# 📧 メール配信システム")
st.markdown("### Gmail統合・AI業界特化・一括配信・追跡システム")

# ナビゲーション情報
st.info("💡 **統合プラットフォーム**: CRM企業データと連携 | GPT-3.5による業界特化カスタマイズ")

# サイドバー情報
with st.sidebar:
    st.markdown("### 🔗 クイックナビゲーション")
    st.markdown("- 📊 [統合ダッシュボード](../)")
    st.markdown("- 🏢 [企業管理](01_🏢_CRM管理.py)")
    st.markdown("- 📧 **メール配信** (現在)")
    
    st.markdown("---")
    st.markdown("### 📧 メール機能")
    st.markdown("""
    ✅ **Gmail統合送信**
    - SMTP認証対応
    - 送信制限管理
    - エラーハンドリング
    
    ✅ **AI業界特化**
    - GPT-3.5カスタマイズ
    - 企業別個別化
    - 建設業界専門
    
    ✅ **一括配信管理**
    - ステータス別配信
    - WiFi需要企業優先
    - 送信結果追跡
    """)
    
    st.markdown("---")
    
    # システム状況
    st.markdown("### 📊 配信状況")
    
    # Gmail接続状況
    gmail_connected = st.session_state.get('gmail_connected', False)
    if gmail_connected:
        st.success("🟢 Gmail: 接続済み")
    else:
        st.warning("🟡 Gmail: 未接続")
    
    # 今日の送信数
    today_sent = st.session_state.get('today_sent', 0)
    st.metric("今日の送信数", f"{today_sent}/500", "件")
    
    # 成功率
    success_rate = st.session_state.get('success_rate', 95.5)
    st.metric("送信成功率", f"{success_rate}%", "+2.1%")

# セッション状態の初期化
if 'email_templates' not in st.session_state:
    st.session_state.email_templates = {
        'wifi_proposal': {
            'name': 'WiFi需要企業向け提案',
            'subject': '建設現場のワイヤレス通信課題解決のご提案 - PicoCELA',
            'body': '''拝啓　時下ますますご清栄のこととお慶び申し上げます。

PicoCELA株式会社の{sender_name}と申します。
{company_name}様の建設現場における通信インフラにつきまして、革新的なソリューションをご提案させていただきたく、ご連絡いたします。

■ 建設現場特有の通信課題
・複雑な現場レイアウトでの電波伝達
・重機による電波干渉
・工期に応じた迅速な設置・撤去

■ PicoCELAメッシュネットワークの特長
・障害物を迂回する自律的ネットワーク
・設置工事不要の簡単展開
・現場規模に応じた柔軟な拡張

建設業界における実績も豊富で、{company_name}様の現場環境に最適化したソリューションをご提案可能です。

ご興味をお持ちいただけましたら、現場での実証デモンストレーションも承ります。
まずは15分程度のオンライン説明の機会をいただけませんでしょうか。

何卒ご検討のほど、よろしくお願い申し上げます。

敬具

{sender_name}
PicoCELA株式会社'''
        },
        'general_proposal': {
            'name': '一般企業向け提案',
            'subject': 'PicoCELA メッシュネットワークソリューションのご案内',
            'body': '''拝啓　{company_name}様

平素より大変お世話になっております。
PicoCELA株式会社の{sender_name}と申します。

この度、{company_name}様の事業展開において、私どものメッシュネットワーク技術がお役に立てるのではないかと考え、ご連絡させていただきました。

■ PicoCELAの特長
・自律的に最適経路を選択するメッシュネットワーク
・IoT機器の安定した接続環境を提供
・産業用途に特化した堅牢な設計

{company_name}様の業界における課題解決実績もございます。
まずは情報交換の機会をいただければ幸いです。

ご都合の良い日時をお聞かせください。

よろしくお願いいたします。

{sender_name}
PicoCELA株式会社'''
        },
        'followup': {
            'name': 'フォローアップ',
            'subject': 'PicoCELAソリューション - フォローアップのご連絡',
            'body': '''拝啓　{company_name}様

先日はお忙しい中、貴重なお時間をいただき誠にありがとうございました。

ご質問いただいた点について、技術チームと検討した結果をお送りいたします：

・導入コストについて：現場規模に応じた段階的導入も可能
・技術サポート：専任エンジニアによる24時間サポート体制
・実証期間：1ヶ月間の無料トライアル実施

ご不明な点やご質問がございましたら、お気軽にお声かけください。
引き続きどうぞよろしくお願いいたします。

敬具

{sender_name}
PicoCELA株式会社'''
        }
    }

# メインコンテンツエリア
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 配信ダッシュボード", "📧 メール作成", "📤 一括配信", "📈 配信分析", "⚙️ 設定"])

with tab1:
    st.markdown("## 📊 メール配信ダッシュボード")
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("今月送信数", "1,247", "+47 (今週)")
    with col2:
        st.metric("開封率", "23.5%", "+1.2%")
    with col3:
        st.metric("返信率", "8.7%", "+0.8%")
    with col4:
        st.metric("成約率", "2.1%", "+0.3%")
    
    # 配信パフォーマンス
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 配信パフォーマンス推移")
        
        # 日別データ
        dates = pd.date_range('2025-07-20', '2025-07-27')
        sent_data = [45, 52, 38, 67, 71, 48, 35]
        opened_data = [12, 15, 9, 18, 19, 11, 8]
        replied_data = [3, 4, 2, 6, 7, 3, 2]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=sent_data, mode='lines+markers',
                               name='送信数', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=dates, y=opened_data, mode='lines+markers',
                               name='開封数', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=dates, y=replied_data, mode='lines+markers',
                               name='返信数', line=dict(color='red')))
        fig.update_layout(title="日別配信パフォーマンス", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 テンプレート別効果")
        
        template_data = {
            'テンプレート': ['WiFi需要企業向け', '一般企業向け', 'フォローアップ'],
            '送信数': [456, 512, 279],
            '開封率': [28.5, 19.2, 35.8],
            '返信率': [12.3, 6.1, 15.7]
        }
        
        df_template = pd.DataFrame(template_data)
        
        fig = px.bar(df_template, x='テンプレート', y=['開封率', '返信率'],
                    title="テンプレート別効果比較",
                    barmode='group')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # リアルタイム配信状況
    st.markdown("### ⚡ リアルタイム配信状況")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📤 送信キュー")
        queue_data = {
            '優先度': ['高', '中', '低'],
            '件数': [15, 23, 8]
        }
        df_queue = pd.DataFrame(queue_data)
        st.dataframe(df_queue, hide_index=True)
    
    with col2:
        st.markdown("#### 📊 今日の配信")
        st.progress(today_sent / 500, text=f"{today_sent}/500 件")
        st.caption("Gmail送信制限: 500件/日")
    
    with col3:
        st.markdown("#### 🕐 次回配信予定")
        st.info("⏰ 15:30 - WiFi需要企業 (12件)")
        st.info("⏰ 17:00 - フォローアップ (8件)")

with tab2:
    st.markdown("## 📧 メール作成・カスタマイズ")
    
    # CRM連携企業選択
    st.markdown("### 🏢 送信対象企業選択（CRM連携）")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # サンプル企業データ
        companies = [
            "ABC建設株式会社 (Qualified, スコア: 92)",
            "XYZ工業 (Contacted, スコア: 85)", 
            "DEF開発 (Proposal, スコア: 78)",
            "株式会社GHI建設 (Replied, スコア: 67)"
        ]
        
        selected_companies = st.multiselect(
            "送信対象企業を選択:",
            companies,
            help="CRMシステムから企業データを取得"
        )
        
        # フィルター
        min_score = st.slider("最小PicoCELAスコア", 0, 100, 70)
        status_filter = st.multiselect(
            "対象ステータス",
            ['New', 'Contacted', 'Replied', 'Qualified'],
            default=['Contacted', 'Qualified']
        )
    
    with col2:
        # 選択企業の詳細
        if selected_companies:
            st.markdown("#### 📋 選択企業詳細")
            for company in selected_companies:
                with st.expander(company.split(" (")[0]):
                    st.write("**ステータス**: Qualified")
                    st.write("**PicoCELAスコア**: 92点")
                    st.write("**WiFi需要**: ✅")
                    st.write("**メール**: info@company.com")
                    st.write("**最終連絡**: 2025-07-25")
    
    # テンプレート選択
    st.markdown("### 📝 メールテンプレート選択")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        template_choice = st.selectbox(
            "テンプレートを選択:",
            list(st.session_state.email_templates.keys()),
            format_func=lambda x: st.session_state.email_templates[x]['name']
        )
        
        # AI個別化設定
        st.markdown("#### 🤖 AI個別化設定")
        use_ai_customization = st.checkbox("GPT-3.5による個別化", value=True)
        
        if use_ai_customization:
            customization_level = st.selectbox(
                "個別化レベル",
                ["軽微", "標準", "高度"],
                index=1
            )
            
            focus_areas = st.multiselect(
                "重点訴求ポイント",
                ["通信課題", "コスト削減", "工期短縮", "安全性向上", "効率化"],
                default=["通信課題", "効率化"]
            )
    
    with col2:
        # メール内容編集
        selected_template = st.session_state.email_templates[template_choice]
        
        subject = st.text_input(
            "件名:",
            value=selected_template['subject']
        )
        
        body = st.text_area(
            "本文:",
            value=selected_template['body'],
            height=400
        )
        
        # プレビュー
        if st.button("👀 プレビュー表示"):
            st.markdown("#### 📧 プレビュー")
            with st.container():
                st.markdown(f"**件名**: {subject}")
                st.markdown("**本文**:")
                preview_body = body.format(
                    company_name="株式会社サンプル",
                    sender_name="徳田"
                )
                st.text(preview_body)
    
    # AI個別化実行
    if use_ai_customization and selected_companies:
        st.markdown("### 🤖 AI個別化実行")
        
        if st.button("✨ AI個別化を実行", use_container_width=True):
            with st.spinner("GPT-3.5で企業別カスタマイズ中..."):
                time.sleep(3)  # API呼び出しのシミュレーション
            
            st.success("✅ AI個別化完了！企業別にカスタマイズされました")
            
            # カスタマイズ結果表示
            st.markdown("#### 📝 カスタマイズ結果")
            
            for i, company in enumerate(selected_companies[:2]):  # 最初の2社のみ表示
                with st.expander(f"📧 {company.split(' (')[0]} 向けカスタマイズ"):
                    st.markdown("**カスタマイズされた件名**:")
                    st.info(f"建設現場DXソリューション - {company.split(' (')[0]}様の効率化をサポート")
                    
                    st.markdown("**個別化ポイント**:")
                    st.write("• 企業規模に応じた導入プランの提案")
                    st.write("• 業界特有の課題（建設現場の通信環境）に特化")
                    st.write("• 過去の建設業界実績を具体的に記載")

with tab3:
    st.markdown("## 📤 一括配信実行")
    
    # 配信設定
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚙️ 配信設定")
        
        # 送信者情報
        sender_name = st.text_input("送信者名", value="徳田")
        sender_email = st.text_input("送信者メール", value="tokuda@picocela.com")
        
        # 配信タイミング
        send_timing = st.radio(
            "配信タイミング",
            ["即座に送信", "指定時刻に送信", "配信キューに追加"]
        )
        
        if send_timing == "指定時刻に送信":
            send_date = st.date_input("送信日")
            send_time = st.time_input("送信時刻")
        
        # 配信制限
        st.markdown("#### 📊 配信制限管理")
        daily_limit = st.number_input("1日の送信上限", value=500, max_value=500)
        batch_size = st.number_input("バッチサイズ", value=10, max_value=50)
        delay_seconds = st.number_input("送信間隔（秒）", value=2, max_value=60)
    
    with col2:
        st.markdown("### 📋 配信対象サマリー")
        
        if selected_companies:
            st.success(f"✅ 選択企業: {len(selected_companies)}社")
            
            # 配信対象詳細
            summary_data = {
                '項目': ['選択企業数', 'WiFi需要企業', '高スコア企業', '予想開封数', '予想返信数'],
                '値': [len(selected_companies), 
                      len(selected_companies) - 1,  # サンプル
                      len(selected_companies),
                      int(len(selected_companies) * 0.235),  # 23.5%開封率
                      int(len(selected_companies) * 0.087)]   # 8.7%返信率
            }
            
            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, hide_index=True)
            
            # 予想配信時間
            total_time = len(selected_companies) * delay_seconds / 60
            st.info(f"⏱️ 予想配信時間: {total_time:.1f}分")
        else:
            st.warning("⚠️ 配信対象企業を選択してください")
    
    # Gmail認証確認
    st.markdown("### 🔐 Gmail認証確認")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gmail_username = st.text_input("Gmailアドレス", value="your-email@gmail.com")
        gmail_password = st.text_input("Gmailアプリパスワード", type="password")
        
        if st.button("🔍 Gmail接続テスト"):
            if gmail_username and gmail_password:
                with st.spinner("Gmail接続をテスト中..."):
                    time.sleep(2)
                st.success("✅ Gmail接続成功")
                st.session_state.gmail_connected = True
            else:
                st.error("❌ Gmail認証情報を入力してください")
    
    with col2:
        if st.session_state.get('gmail_connected', False):
            st.success("🟢 Gmail認証: 完了")
            st.info("📊 本日の送信可能数: 453/500")
        else:
            st.warning("🟡 Gmail認証が必要です")
    
    # 配信実行
    st.markdown("### 🚀 配信実行")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 配信実行", use_container_width=True, type="primary"):
            if not selected_companies:
                st.error("❌ 配信対象企業を選択してください")
            elif not st.session_state.get('gmail_connected', False):
                st.error("❌ Gmail認証を完了してください")
            else:
                # 配信実行シミュレーション
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, company in enumerate(selected_companies):
                    progress = (i + 1) / len(selected_companies)
                    progress_bar.progress(progress)
                    status_text.text(f"送信中: {company.split(' (')[0]} ({i+1}/{len(selected_companies)})")
                    time.sleep(1)  # 送信シミュレーション
                
                st.success(f"✅ {len(selected_companies)}社への配信完了！")
                st.balloons()
                
                # 送信結果更新
                st.session_state.today_sent = st.session_state.get('today_sent', 0) + len(selected_companies)
    
    with col2:
        if st.button("📋 配信キューに追加", use_container_width=True):
            if selected_companies:
                st.success(f"✅ {len(selected_companies)}社を配信キューに追加")
            else:
                st.error("❌ 配信対象企業を選択してください")
    
    with col3:
        if st.button("⏸️ 配信一時停止", use_container_width=True):
            st.warning("⏸️ 進行中の配信を一時停止しました")

with tab4:
    st.markdown("## 📈 配信分析・効果測定")
    
    # 期間選択
    col1, col2, col3 = st.columns(3)
    with col1:
        date_range = st.selectbox("分析期間", ["今週", "今月", "過去3ヶ月", "カスタム"])
    with col2:
        if date_range == "カスタム":
            start_date = st.date_input("開始日")
    with col3:
        if date_range == "カスタム":
            end_date = st.date_input("終了日")
    
    # 詳細分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 企業ステータス別効果")
        
        status_analysis = {
            'ステータス': ['New', 'Contacted', 'Replied', 'Qualified'],
            '送信数': [245, 387, 156, 89],
            '開封率': [18.2, 23.5, 31.4, 28.1],
            '返信率': [4.1, 8.7, 15.4, 12.4],
            '成約率': [0.8, 2.1, 5.8, 7.9]
        }
        
        df_status_analysis = pd.DataFrame(status_analysis)
        
        fig = px.line(df_status_analysis, x='ステータス', y=['開封率', '返信率', '成約率'],
                     title="ステータス別パフォーマンス")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 PicoCELAスコア別効果")
        
        score_analysis = {
            'スコア範囲': ['0-40', '41-60', '61-80', '81-100'],
            '送信数': [123, 234, 345, 175],
            '返信率': [3.2, 6.8, 12.5, 18.9],
            '成約率': [0.5, 1.8, 4.2, 8.1]
        }
        
        df_score_analysis = pd.DataFrame(score_analysis)
        
        fig = px.scatter(df_score_analysis, x='送信数', y='返信率', 
                        size='成約率', hover_name='スコア範囲',
                        title="スコア別効果分析")
        st.plotly_chart(fig, use_container_width=True)
    
    # ROI分析
    st.markdown("### 💰 ROI分析")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("配信コスト", "¥125,000", "月額")
    with col2:
        st.metric("獲得案件", "15件", "+3件")
    with col3:
        st.metric("案件単価", "¥2,500,000", "平均")
    with col4:
        roi = (15 * 2500000 - 125000) / 125000 * 100
        st.metric("ROI", f"{roi:.0f}%", "+45%")
    
    # 改善提案
    st.markdown("### 💡 改善提案（AI分析）")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📈 効果向上のポイント**
        
        1. **高スコア企業への集中**
           - PicoCELAスコア80点以上の企業は返信率18.9%
           - 配信リソースの最適配分を推奨
        
        2. **フォローアップの強化**
           - Repliedステータス企業の成約率5.8%
           - 2週間後の自動フォロー設定を推奨
        """)
    
    with col2:
        st.warning("""
        **⚠️ 改善が必要な領域**
        
        1. **Newステータス企業**
           - 開封率18.2%と低水準
           - 件名の改善が必要
        
        2. **送信タイミング**
           - 火曜日午前の開封率が高い傾向
           - 配信スケジュールの最適化を推奨
        """)

with tab5:
    st.markdown("## ⚙️ メール設定")
    
    # Gmail SMTP設定
    st.markdown("### 📧 Gmail SMTP設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔐 認証情報")
        
        smtp_server = st.text_input("SMTPサーバー", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTPポート", value=587)
        
        gmail_user = st.text_input("Gmailアドレス")
        gmail_app_password = st.text_input("アプリパスワード", type="password", 
                                         help="Gmailのアプリパスワードを入力")
        
        # 送信制限設定
        st.markdown("#### 📊 送信制限")
        daily_limit_setting = st.number_input("1日の送信上限", value=500, max_value=500)
        hourly_limit = st.number_input("1時間の送信上限", value=50, max_value=100)
        batch_delay = st.slider("送信間隔（秒）", 1, 60, 2)
    
    with col2:
        st.markdown("#### 📊 現在の設定状況")
        
        if gmail_user and gmail_app_password:
            st.success("🟢 Gmail認証: 設定済み")
            st.info(f"📧 送信者: {gmail_user}")
            st.info(f"📊 日次制限: {daily_limit_setting}/500")
        else:
            st.warning("🟡 Gmail認証情報を入力してください")
        
        # 設定テスト
        if st.button("🔍 SMTP接続テスト", use_container_width=True):
            if gmail_user and gmail_app_password:
                with st.spinner("SMTP接続をテスト中..."):
                    time.sleep(2)
                st.success("✅ SMTP接続成功")
            else:
                st.error("❌ 認証情報を入力してください")
    
    # メールテンプレート管理
    st.markdown("### 📝 メールテンプレート管理")
    
    # 既存テンプレート一覧
    st.markdown("#### 📋 既存テンプレート")
    
    template_list = []
    for key, template in st.session_state.email_templates.items():
        template_list.append({
            'ID': key,
            'テンプレート名': template['name'],
            '件名': template['subject'][:50] + "..." if len(template['subject']) > 50 else template['subject'],
            '使用回数': f"{hash(key) % 100}回"  # サンプル使用回数
        })
    
    df_templates = pd.DataFrame(template_list)
    st.dataframe(df_templates, hide_index=True, use_container_width=True)
    
    # 新規テンプレート追加
    st.markdown("#### ➕ 新規テンプレート追加")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_template_name = st.text_input("テンプレート名")
        new_template_subject = st.text_input("件名")
    
    with col2:
        new_template_category = st.selectbox(
            "カテゴリ",
            ["初回提案", "フォローアップ", "お礼", "その他"]
        )
        use_ai_generation = st.checkbox("AI生成アシスト", value=True)
    
    new_template_body = st.text_area("本文", height=200)
    
    if st.button("💾 テンプレートを保存"):
        if new_template_name and new_template_subject and new_template_body:
            # 新しいテンプレートをセッション状態に保存
            new_key = f"custom_{len(st.session_state.email_templates)}"
            st.session_state.email_templates[new_key] = {
                'name': new_template_name,
                'subject': new_template_subject,
                'body': new_template_body
            }
            st.success("✅ 新しいテンプレートを保存しました")
        else:
            st.error("❌ すべての項目を入力してください")
    
    # 設定保存
    st.markdown("---")
    if st.button("💾 すべての設定を保存", use_container_width=True):
        st.success("✅ 設定を保存しました")
        st.info("設定は即座に反映されます")

# フッター
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📧 FusionCRM v12.0**")
    st.caption("メール配信システム")

with col2:
    st.markdown("**📊 配信統計**")
    st.caption(f"最終配信: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

with col3:
    st.markdown("**🔗 開発**")
    st.caption("PicoCELA Team")

# 開発ノート
st.info("""
💡 **開発ノート**: このページは既存の `email_webapp.py` の機能を統合プラットフォーム用に再構築したものです。
実際の運用では、Gmail SMTP認証、GPT-3.5 API連携、CRMデータ同期等の実装が必要です。
""")

# 成功時のバルーン表示制御
if 'show_balloons' in st.session_state and st.session_state.show_balloons:
    st.balloons()
    st.session_state.show_balloons = False
