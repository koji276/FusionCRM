"""
CRMダッシュボード表示モジュール
fusion_crm_main.pyから抽出
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def show_dashboard(company_manager):
    """ダッシュボード"""
    st.header("📊 ダッシュボード")
    
    # 基本統計
    all_companies = company_manager.get_all_companies()
    total_companies = len(all_companies)
    
    if total_companies == 0:
        st.info("📋 企業データがありません。サンプルデータを追加してテストしてください。")
        
        if st.button("🚀 サンプルデータを追加", type="primary"):
            sample_companies = [
                {
                    'company_name': 'テストコンストラクション株式会社',
                    'email': 'contact@test-construction.com',
                    'industry': 'Construction',
                    'notes': 'WiFi, IoT, wireless network solutions needed for construction sites',
                    'source': 'Sample Data'
                },
                {
                    'company_name': 'スマートビルディング合同会社',
                    'email': 'info@smart-building.co.jp',
                    'industry': 'Smart Building',
                    'notes': 'mesh network, construction tech, digital solutions',
                    'source': 'Sample Data'
                }
            ]
            
            success_count = 0
            for company in sample_companies:
                result = company_manager.add_company(company, 'system')
                if result:
                    success_count += 1
            
            if success_count > 0:
                st.success(f"✅ {success_count}社のサンプルデータを追加しました！")
                st.rerun()
        
        return
    
    # 統計計算（安全にカラム確認）
    try:
        wifi_companies = len(all_companies[all_companies['wifi_required'] == 1]) if 'wifi_required' in all_companies.columns else 0
        high_priority = len(all_companies[all_companies['priority_score'] >= 100]) if 'priority_score' in all_companies.columns else 0
        engaged_plus = len(all_companies[all_companies['sales_status'].isin(['Engaged', 'Qualified', 'Proposal', 'Negotiation'])]) if 'sales_status' in all_companies.columns else 0
    except:
        wifi_companies = 0
        high_priority = 0
        engaged_plus = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", total_companies)
    
    with col2:
        wifi_pct = f"{wifi_companies/total_companies*100:.1f}%" if total_companies > 0 else "0%"
        st.metric("📶 WiFi必要企業", wifi_companies, wifi_pct)
    
    with col3:
        high_pct = f"{high_priority/total_companies*100:.1f}%" if total_companies > 0 else "0%"
        st.metric("🎯 高優先度企業", high_priority, high_pct)
    
    with col4:
        st.metric("🔥 商談中企業", engaged_plus)
    
    # 企業一覧表示
    if not all_companies.empty:
        st.subheader("📋 企業一覧（最新10社）")
        
        # 表示用データ準備
        display_columns = ['company_name', 'sales_status']
        if 'industry' in all_companies.columns:
            display_columns.append('industry')
        if 'wifi_required' in all_companies.columns:
            display_columns.append('wifi_required')
        if 'priority_score' in all_companies.columns:
            display_columns.append('priority_score')
        
        display_df = all_companies[display_columns].tail(10) if all(col in all_companies.columns for col in display_columns) else all_companies.tail(10)
        
        st.dataframe(display_df, use_container_width=True)


def show_analytics(company_manager):
    """分析・レポート"""
    st.header("📈 分析・レポート")
    
    companies_df = company_manager.get_all_companies()
    
    if companies_df.empty:
        st.info("分析するデータがありません。企業データを追加してください。")
        return
    
    # 基本統計
    st.subheader("📊 基本統計")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ステータス分布
        if 'sales_status' in companies_df.columns:
            status_counts = companies_df['sales_status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title="ステータス分布")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # WiFi需要分布
        if 'wifi_required' in companies_df.columns:
            wifi_counts = companies_df['wifi_required'].map({1: 'WiFi必要', 0: 'WiFi不要'}).value_counts()
            fig = px.bar(x=wifi_counts.index, y=wifi_counts.values, 
                        title="WiFi需要分布")
            st.plotly_chart(fig, use_container_width=True)
    
    # 詳細分析
    if len(companies_df) > 5:
        st.subheader("📈 詳細分析")
        
        # 業界別分析
        if 'industry' in companies_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                industry_counts = companies_df['industry'].value_counts()
                if len(industry_counts) > 0:
                    fig = px.bar(x=industry_counts.values, y=industry_counts.index, 
                                orientation='h', title="業界別企業数")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 優先度分析
                if 'priority_score' in companies_df.columns:
                    priority_bins = pd.cut(companies_df['priority_score'], 
                                         bins=[0, 50, 100, 150], 
                                         labels=['低', '中', '高'])
                    priority_counts = priority_bins.value_counts()
                    
                    fig = px.pie(values=priority_counts.values, names=priority_counts.index,
                                title="優先度分布")
                    st.plotly_chart(fig, use_container_width=True)
    
    # データサマリー
    st.subheader("📋 データサマリー")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 最近追加された企業
        if 'created_at' in companies_df.columns:
            recent_companies = companies_df.tail(5)
            st.write("**最近追加された企業:**")
            for _, company in recent_companies.iterrows():
                st.write(f"• {company.get('company_name', 'Unknown')}")
    
    with col2:
        # 高優先度企業
        if 'priority_score' in companies_df.columns:
            high_priority = companies_df[companies_df['priority_score'] >= 100].head(5)
            st.write("**高優先度企業:**")
            for _, company in high_priority.iterrows():
                score = company.get('priority_score', 0)
                st.write(f"• {company.get('company_name', 'Unknown')} ({score}点)")
    
    with col3:
        # WiFi需要企業
        if 'wifi_required' in companies_df.columns:
            wifi_companies = companies_df[companies_df['wifi_required'] == 1].head(5)
            st.write("**WiFi需要企業:**")
            for _, company in wifi_companies.iterrows():
                st.write(f"• {company.get('company_name', 'Unknown')}")


def show_email_campaigns(email_manager, company_manager):
    """メールキャンペーン"""
    st.header("📧 メールキャンペーン")
    st.info("Google Sheets版では基本的なメール機能のみ提供します")
    
    templates = email_manager.get_email_templates()
    
    st.subheader("📝 メールテンプレート")
    
    template_choice = st.selectbox(
        "テンプレート選択",
        list(templates.keys()),
        format_func=lambda x: "WiFi需要企業向け" if x == "wifi_needed" else "一般企業向け"
    )
    
    selected_template = templates[template_choice]
    
    st.text_area("件名", value=selected_template["subject"], disabled=True, height=50)
    st.text_area("本文", value=selected_template["body"], height=300, disabled=True)
    
    # メール配信システムへのリンク
    st.markdown("---")
    email_manager.add_email_distribution_link()
