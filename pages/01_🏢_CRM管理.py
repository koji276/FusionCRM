# pages/01_🏢_CRM管理.py
# FusionCRM - 企業管理システム (Multipage対応版)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ページ設定
st.set_page_config(
    page_title="FusionCRM - 企業管理",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 戻るボタン（ヘッダー）
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← 統合ダッシュボードに戻る", key="back_to_dashboard"):
        st.switch_page("fusion_crm_unified.py")

# ページヘッダー
st.markdown("# 🏢 CRM管理システム")
st.markdown("### 企業データ管理・ステータス追跡・PicoCELA関連度分析")

# ナビゲーション情報
st.info("💡 **統合プラットフォーム**: サイドバーから他のページに移動 | Google Sheets連携でリアルタイム同期")

# サイドバー情報
with st.sidebar:
    st.markdown("### 🔗 クイックナビゲーション")
    st.markdown("- 📊 [統合ダッシュボード](../)")
    st.markdown("- 🏢 **企業管理** (現在)")
    st.markdown("- 📧 [メール配信](02_📧_メール配信.py)")
    
    st.markdown("---")
    st.markdown("### 🎯 CRM機能")
    st.markdown("""
    ✅ **10段階ステータス管理**
    - New → Contacted → Replied
    - Engaged → Qualified → Proposal
    - Negotiation → Won/Lost/Dormant
    
    ✅ **PicoCELA関連度スコア**
    - 自動キーワード分析
    - 優先度計算（0-150点）
    
    ✅ **Google Sheets同期**
    - リアルタイム更新
    - チーム共有対応
    """)
    
    st.markdown("---")
    
    # システム状況
    st.markdown("### 📊 システム状況")
    st.success("🟢 Google Sheets接続: 正常")
    st.success("🟢 データ同期: リアルタイム")
    st.info("📈 総企業数: 1,247社")

# メインコンテンツエリア
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 ダッシュボード", "🏢 企業管理", "📈 分析", "📤 データ管理", "⚙️ 設定"])

with tab1:
    st.markdown("## 📊 CRMダッシュボード")
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", "1,247", "+47 (今月)")
    with col2:
        st.metric("アクティブ企業", "892", "+12 (今週)")
    with col3:
        st.metric("PicoCELA関連", "156", "+8 (高スコア)")
    with col4:
        st.metric("今月成約", "15", "+3 (先月比)")
    
    # ステータス分布とスコア分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 企業ステータス分布（10段階）")
        
        status_data = {
            'ステータス': ['New', 'Contacted', 'Replied', 'Engaged', 'Qualified', 
                        'Proposal', 'Negotiation', 'Won', 'Lost', 'Dormant'],
            '企業数': [120, 180, 95, 78, 45, 32, 18, 25, 85, 42],
            '成約可能性': [5, 15, 25, 40, 60, 75, 85, 100, 0, 10]
        }
        
        df_status = pd.DataFrame(status_data)
        
        # カラーマップ
        colors = ['#ff6b6b', '#ffa500', '#ffeb3b', '#4caf50', '#2196f3', 
                 '#9c27b0', '#e91e63', '#4caf50', '#9e9e9e', '#607d8b']
        
        fig = px.bar(df_status, x='ステータス', y='企業数', 
                    title="ステータス別企業数",
                    color='成約可能性',
                    color_continuous_scale='RdYlGn')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 PicoCELA関連度スコア分布")
        
        # スコア分布（サンプルデータ）
        import numpy as np
        np.random.seed(42)
        scores = np.random.beta(2, 5, 1000) * 100
        
        fig = px.histogram(x=scores, nbins=20, 
                          title="PicoCELA関連度スコア分布",
                          labels={'x': 'スコア', 'y': '企業数'})
        fig.add_vline(x=70, line_dash="dash", line_color="red", 
                     annotation_text="高優先度ライン (70点)")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # パフォーマンス推移
    st.markdown("### 📈 月次パフォーマンス推移")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 月次データ
        months = ['4月', '5月', '6月', '7月']
        new_companies = [35, 42, 38, 47]
        conversions = [8, 12, 9, 15]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=new_companies, mode='lines+markers',
                               name='新規企業', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=months, y=conversions, mode='lines+markers',
                               name='成約数', line=dict(color='green')))
        fig.update_layout(title="新規企業・成約数推移", height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 成約率
        conversion_rates = [22.9, 28.6, 23.7, 31.9]  # 成約率%
        
        fig = px.bar(x=months, y=conversion_rates,
                    title="月次成約率",
                    labels={'x': '月', 'y': '成約率 (%)'})
        fig.update_traces(marker_color='lightgreen')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("## 🏢 企業管理")
    
    # 検索・フィルター
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_term = st.text_input("🔍 企業名検索", placeholder="企業名を入力...")
    with col2:
        status_filter = st.selectbox("📋 ステータス", 
            ['全て', 'New', 'Contacted', 'Replied', 'Engaged', 'Qualified', 
             'Proposal', 'Negotiation', 'Won', 'Lost', 'Dormant'])
    with col3:
        score_filter = st.slider("🎯 最小PicoCELAスコア", 0, 100, 0)
    with col4:
        wifi_filter = st.selectbox("📶 WiFi需要", ['全て', 'あり', 'なし'])
    
    # 企業リスト（サンプルデータ）
    st.markdown("### 📋 企業リスト")
    
    company_data = {
        '企業ID': ['CRM001', 'CRM002', 'CRM003', 'CRM004', 'CRM005', 'CRM006'],
        '企業名': ['ABC建設株式会社', 'XYZ工業', 'DEF開発', '株式会社GHI建設', 'JKL建設', 'MNO工業'],
        'ステータス': ['Contacted', 'Qualified', 'Proposal', 'Replied', 'New', 'Engaged'],
        'PicoCELAスコア': [85, 92, 78, 67, 73, 88],
        '優先度': [135, 142, 128, 117, 123, 138],
        'WiFi需要': ['✅', '✅', '❌', '✅', '✅', '✅'],
        'メール': ['info@abc-const.jp', 'contact@xyz-ind.com', 'sales@def-dev.co.jp', 
                  'info@ghi-const.com', 'contact@jkl-const.jp', 'info@mno-ind.com'],
        '最終更新': ['2025-07-25', '2025-07-26', '2025-07-27', '2025-07-24', '2025-07-27', '2025-07-26']
    }
    
    df_companies = pd.DataFrame(company_data)
    
    # フィルター適用
    if search_term:
        df_companies = df_companies[df_companies['企業名'].str.contains(search_term, case=False, na=False)]
    if status_filter != '全て':
        df_companies = df_companies[df_companies['ステータス'] == status_filter]
    if score_filter > 0:
        df_companies = df_companies[df_companies['PicoCELAスコア'] >= score_filter]
    if wifi_filter == 'あり':
        df_companies = df_companies[df_companies['WiFi需要'] == '✅']
    elif wifi_filter == 'なし':
        df_companies = df_companies[df_companies['WiFi需要'] == '❌']
    
    # データ表示
    st.dataframe(
        df_companies,
        use_container_width=True,
        hide_index=True,
        column_config={
            "PicoCELAスコア": st.column_config.ProgressColumn(
                "PicoCELAスコア",
                help="PicoCELA関連度スコア (0-100)",
                min_value=0,
                max_value=100,
            ),
            "優先度": st.column_config.NumberColumn(
                "優先度",
                help="総合優先度スコア",
                min_value=0,
                max_value=200,
                format="%d"
            ),
            "メール": st.column_config.TextColumn(
                "メール",
                width="medium"
            )
        }
    )
    
    # 選択企業のアクション
    st.markdown("### ⚡ アクション")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ 新規企業追加", use_container_width=True):
            st.success("新規企業追加画面を開きました（実装予定）")
    
    with col2:
        if st.button("📧 選択企業にメール", use_container_width=True):
            st.success("メール配信ページに移動（実装予定）")
    
    with col3:
        if st.button("📤 データエクスポート", use_container_width=True):
            csv = df_companies.to_csv(index=False)
            st.download_button(
                label="📥 CSVダウンロード",
                data=csv,
                file_name=f"企業リスト_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col4:
        if st.button("🔄 Google Sheets同期", use_container_width=True):
            with st.spinner("Google Sheetsと同期中..."):
                # 実際の同期処理をここに実装
                import time
                time.sleep(2)
            st.success("✅ Google Sheets同期完了")

with tab3:
    st.markdown("## 📈 分析・レポート")
    
    # 高度分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 業界別パフォーマンス")
        
        industry_data = {
            '業界': ['建設', '製造', 'IT', '小売', 'その他'],
            '企業数': [450, 280, 150, 120, 247],
            '成約率': [12.5, 8.9, 15.2, 6.3, 7.8]
        }
        
        df_industry = pd.DataFrame(industry_data)
        
        fig = px.scatter(df_industry, x='企業数', y='成約率', size='企業数',
                        hover_name='業界', title="業界別 企業数 vs 成約率")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 スコア vs 成約率")
        
        # スコア範囲別成約率
        score_ranges = ['0-20', '21-40', '41-60', '61-80', '81-100']
        conversion_by_score = [2.1, 4.8, 8.3, 15.7, 28.4]
        
        fig = px.bar(x=score_ranges, y=conversion_by_score,
                    title="PicoCELAスコア別成約率",
                    labels={'x': 'スコア範囲', 'y': '成約率 (%)'})
        fig.update_traces(marker_color='lightblue')
        st.plotly_chart(fig, use_container_width=True)
    
    # パイプライン分析
    st.markdown("### 🔄 パイプライン分析")
    
    pipeline_data = {
        'ステージ': ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Closing'],
        '企業数': [500, 200, 80, 35, 15],
        '予想収益': [0, 50000, 200000, 450000, 750000]
    }
    
    df_pipeline = pd.DataFrame(pipeline_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.funnel(df_pipeline, x='企業数', y='ステージ',
                       title="営業パイプライン")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(df_pipeline, x='ステージ', y='予想収益',
                    title="ステージ別予想収益")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown("## 📤 データ管理")
    
    # データインポート
    st.markdown("### 📥 データインポート")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📄 CSVファイルアップロード")
        uploaded_file = st.file_uploader(
            "企業データ CSV ファイルを選択",
            type=['csv'],
            help="CSV形式の企業データをアップロードできます"
        )
        
        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                st.success(f"✅ {len(df_upload)} 件のデータを読み込みました")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                if st.button("📤 Google Sheetsにインポート"):
                    with st.spinner("データをインポート中..."):
                        # 実際のインポート処理をここに実装
                        import time
                        time.sleep(3)
                    st.success("✅ データインポート完了")
                    
            except Exception as e:
                st.error(f"❌ ファイル読み込みエラー: {e}")
    
    with col2:
        st.markdown("#### 🔍 ENRデータ自動収集")
        
        st.info("""
        **FusionReach連携**
        - ENR企業データの自動収集
        - PicoCELA関連度自動判定
        - 優先度スコア自動計算
        """)
        
        if st.button("🚀 ENRデータ収集開始", use_container_width=True):
            with st.spinner("ENRデータを収集中..."):
                # 実際の収集処理をここに実装
                import time
                time.sleep(4)
            st.success("✅ 47社の新規企業データを収集しました")
    
    # データエクスポート
    st.markdown("### 📤 データエクスポート")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 全企業データ", use_container_width=True):
            # サンプルデータでエクスポート
            csv_data = df_companies.to_csv(index=False)
            st.download_button(
                "📥 CSVダウンロード",
                csv_data,
                f"全企業データ_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("🎯 高スコア企業のみ", use_container_width=True):
            high_score = df_companies[df_companies['PicoCELAスコア'] >= 80]
            csv_data = high_score.to_csv(index=False)
            st.download_button(
                "📥 CSVダウンロード",
                csv_data,
                f"高スコア企業_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    with col3:
        if st.button("📧 メール配信リスト", use_container_width=True):
            email_list = df_companies[['企業名', 'メール', 'ステータス']]
            csv_data = email_list.to_csv(index=False)
            st.download_button(
                "📥 CSVダウンロード",
                csv_data,
                f"メール配信リスト_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )

with tab5:
    st.markdown("## ⚙️ 設定")
    
    # Google Sheets設定
    st.markdown("### 🔗 Google Sheets連携設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sheets_url = st.text_input(
            "📊 Google Sheets URL",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="CRMデータが保存されているGoogle SheetsのURL"
        )
        
        api_key = st.text_input(
            "🔑 Google Apps Script API URL",
            type="password",
            placeholder="Google Apps ScriptのAPI URL",
            help="データ同期用のGoogle Apps Script URL"
        )
        
        # 同期設定
        st.markdown("#### 🔄 同期設定")
        auto_sync = st.checkbox("自動同期を有効にする", value=True)
        sync_interval = st.selectbox("同期間隔", ["5分", "15分", "30分", "1時間"], index=1)
    
    with col2:
        st.markdown("#### 📊 接続状況")
        
        # 接続状況表示
        if sheets_url and api_key:
            st.success("🟢 Google Sheets: 接続済み")
            st.info(f"📈 最終同期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            st.metric("同期データ数", "1,247", "企業")
        else:
            st.warning("🟡 Google Sheets: 未接続")
            st.info("URL・API Keyを入力してください")
        
        # 接続テスト
        if st.button("🔍 接続テスト", use_container_width=True):
            if sheets_url and api_key:
                with st.spinner("接続をテスト中..."):
                    import time
                    time.sleep(2)
                st.success("✅ 接続テスト成功")
                st.balloons()
            else:
                st.error("❌ URL・API Keyを入力してください")
        
        # 手動同期
        if st.button("🔄 今すぐ同期", use_container_width=True):
            with st.spinner("Google Sheetsと同期中..."):
                import time
                time.sleep(3)
            st.success("✅ 同期完了")
    
    # PicoCELAスコアリング設定
    st.markdown("### 🎯 PicoCELAスコアリング設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 関連キーワード")
        keywords = st.text_area(
            "PicoCELA関連キーワード（カンマ区切り）",
            value="network,mesh,wireless,wifi,connectivity,iot,smart,digital,automation,sensor",
            help="企業のPicoCELA関連度を判定するキーワード"
        )
        
        wifi_bonus = st.slider("WiFi需要ボーナス", 0, 100, 50, 
                              help="WiFi需要がある企業への追加スコア")
    
    with col2:
        st.markdown("#### ⚙️ スコア計算設定")
        
        base_weight = st.slider("基本関連度重み", 0.0, 1.0, 0.7)
        industry_weight = st.slider("業界適合度重み", 0.0, 1.0, 0.3)
        
        st.markdown("**計算式**:")
        st.code("""
priority_score = (
    relevance_score * base_weight + 
    industry_score * industry_weight
) + (wifi_bonus if wifi_required else 0)
        """)
    
    # 設定保存
    if st.button("💾 設定を保存", use_container_width=True):
        st.success("✅ 設定を保存しました")
        st.info("新しい設定は次回の同期から適用されます")

# フッター
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🏢 FusionCRM v12.0**")
    st.caption("企業管理システム")

with col2:
    st.markdown("**📊 データ統計**")
    st.caption(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

with col3:
    st.markdown("**🔗 開発**")
    st.caption("PicoCELA Team")

# 注意事項
st.info("""
💡 **開発ノート**: このページは既存の `fusion_crm_main.py` の機能を統合プラットフォーム用に再構築したものです。
実際の運用では、Google Sheets API、認証システム、データベース処理等の実装が必要です。
""")
