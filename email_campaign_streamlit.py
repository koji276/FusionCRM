#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Streamlit メール配信インターフェース
既存の email_distribution.py と連携したWebインターフェース
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 既存のEmailDistributionクラスをインポート
try:
    from email_distribution import EmailDistribution
except ImportError:
    st.error("email_distribution.py が見つかりません。同じディレクトリに配置してください。")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="📧 FusionCRM メール配信",
    page_icon="📧",
    layout="wide"
)

# セッション状態の初期化
if 'email_dist' not in st.session_state:
    st.session_state.email_dist = EmailDistribution()
if 'selected_companies' not in st.session_state:
    st.session_state.selected_companies = []

def get_dashboard_stats():
    """ダッシュボード統計の取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        cursor = conn.cursor()
        
        # 基本統計
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies WHERE email_address IS NOT NULL AND email_address != ''")
        email_available = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies WHERE status = 'New'")
        new_companies = cursor.fetchone()[0]
        
        # 今日の送信数
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) FROM email_history WHERE DATE(sent_at) = ?", (today,))
        today_sent = cursor.fetchone()[0]
        
        # 成功率（過去30日）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
            FROM email_history 
            WHERE sent_at >= ?
        """, (thirty_days_ago,))
        
        result = cursor.fetchone()
        total_sent = result[0] if result[0] else 0
        success_sent = result[1] if result[1] else 0
        success_rate = (success_sent / total_sent * 100) if total_sent > 0 else 0
        
        conn.close()
        
        return {
            'total_companies': total_companies,
            'email_available': email_available,
            'new_companies': new_companies,
            'today_sent': today_sent,
            'success_rate': success_rate,
            'total_sent_30d': total_sent
        }
    except Exception as e:
        st.error(f"統計取得エラー: {e}")
        return {}

def get_companies_for_display():
    """表示用企業データの取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        
        # 既存のget_companies_for_campaignメソッドを活用
        companies = st.session_state.email_dist.get_companies_for_campaign()
        
        if companies:
            # DataFrameに変換
            df = pd.DataFrame(companies, columns=[
                'id', 'company_name', 'email_address', 'website', 
                'phone', 'status', 'picocela_relevance_score'
            ])
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"企業データ取得エラー: {e}")
        return pd.DataFrame()

def get_email_history():
    """送信履歴の取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        query = """
            SELECT 
                eh.sent_at,
                c.company_name,
                eh.email_type,
                eh.subject,
                eh.status,
                eh.error_message
            FROM email_history eh
            LEFT JOIN companies c ON eh.company_id = c.id
            ORDER BY eh.sent_at DESC
            LIMIT 100
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"履歴取得エラー: {e}")
        return pd.DataFrame()

def render_dashboard():
    """ダッシュボード表示"""
    st.title("📧 FusionCRM メール配信システム")
    st.markdown("**既存システム連携型 Web インターフェース**")
    
    # 統計表示
    stats = get_dashboard_stats()
    
    if stats:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("総企業数", f"{stats['total_companies']:,}")
        
        with col2:
            st.metric("メール配信可能", f"{stats['email_available']:,}")
        
        with col3:
            st.metric("新規企業", f"{stats['new_companies']:,}")
        
        with col4:
            st.metric("今日の送信数", f"{stats['today_sent']:,}")
        
        with col5:
            st.metric("成功率(30日)", f"{stats['success_rate']:.1f}%")
    
    # 設定状況確認
    gmail_config = st.session_state.email_dist.gmail_config
    
    if gmail_config:
        st.success(f"✅ Gmail設定済み: {gmail_config['email']} ({gmail_config['sender_name']})")
    else:
        st.error("❌ Gmail設定が必要です。設定タブで設定を行ってください。")
    
    # 配信対象企業サマリー
    st.subheader("📊 配信対象企業サマリー")
    
    df = get_companies_for_display()
    if not df.empty:
        # ステータス分布
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title="企業ステータス分布")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # スコア分布
            fig = px.histogram(df, x='picocela_relevance_score', 
                             title="PicoCELA関連性スコア分布", nbins=20)
            st.plotly_chart(fig, use_container_width=True)
        
        # 高優先度企業リスト
        st.subheader("🎯 高優先度企業（上位10社）")
        top_companies = df.nlargest(10, 'picocela_relevance_score')[
            ['company_name', 'email_address', 'status', 'picocela_relevance_score']
        ]
        st.dataframe(top_companies, use_container_width=True)
    else:
        st.warning("配信対象企業が見つかりません。")

def render_campaign_creator():
    """キャンペーン作成"""
    st.title("🚀 メールキャンペーン作成")
    
    # Gmail設定確認
    if not st.session_state.email_dist.gmail_config:
        st.error("Gmail設定が必要です。設定タブで設定を行ってください。")
        return
    
    # 企業データ取得
    df = get_companies_for_display()
    if df.empty:
        st.warning("配信対象企業が見つかりません。")
        return
    
    # フィルター設定
    st.subheader("🎯 配信対象選択")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "ステータスフィルター",
            ["全て"] + list(df['status'].unique())
        )
    
    with col2:
        min_score = st.number_input(
            "最小関連性スコア", 
            min_value=0, 
            max_value=int(df['picocela_relevance_score'].max()),
            value=0
        )
    
    with col3:
        max_companies = st.number_input(
            "最大送信数", 
            min_value=1, 
            max_value=100,
            value=20
        )
    
    # フィルター適用
    filtered_df = df.copy()
    
    if status_filter != "全て":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    filtered_df = filtered_df[filtered_df['picocela_relevance_score'] >= min_score]
    filtered_df = filtered_df.head(max_companies)
    
    st.info(f"📊 配信対象: {len(filtered_df)}社")
    
    # 対象企業表示
    if len(filtered_df) > 0:
        with st.expander("📋 配信対象企業一覧"):
            st.dataframe(filtered_df[['company_name', 'email_address', 'status', 'picocela_relevance_score']])
        
        # テンプレート選択
        st.subheader("📝 メールテンプレート")
        
        templates = st.session_state.email_dist.email_templates
        template_names = list(templates.keys())
        
        selected_template = st.selectbox(
            "テンプレート選択",
            template_names,
            format_func=lambda x: {
                'initial_contact': '初回提案メール',
                'follow_up': 'フォローアップメール'
            }.get(x, x)
        )
        
        # テンプレート内容表示
        if selected_template:
            template = templates[selected_template]
            
            st.text_input("件名", value=template['subject'], disabled=True)
            st.text_area("本文", value=template['body'], height=200, disabled=True)
        
        # 送信設定
        st.subheader("⚙️ 送信設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            send_interval = st.slider(
                "送信間隔（秒）", 
                min_value=1, 
                max_value=30,
                value=5,
                help="メール送信の間隔を設定します。長めに設定することでGmailの制限を回避できます。"
            )
        
        with col2:
            update_status = st.checkbox(
                "送信後にステータス更新", 
                value=True,
                help="送信成功後に企業ステータスを'Contacted'に更新します。"
            )
        
        # 送信実行
        st.subheader("🚀 キャンペーン実行")
        
        if st.button("📤 キャンペーン送信開始", type="primary"):
            
            # 確認ダイアログ
            if st.checkbox(f"✅ {len(filtered_df)}社への送信を確認しました"):
                
                # プログレスバー
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_placeholder = st.empty()
                
                success_count = 0
                failed_count = 0
                results = []
                
                # 送信実行
                for i, (idx, company) in enumerate(filtered_df.iterrows()):
                    company_name = company['company_name']
                    email_address = company['email_address']
                    
                    status_text.text(f"送信中: {company_name} ({i+1}/{len(filtered_df)})")
                    
                    # メール送信
                    success, message = st.session_state.email_dist.send_email(
                        email_address, company_name, selected_template
                    )
                    
                    # 結果記録
                    results.append({
                        'company_name': company_name,
                        'email_address': email_address,
                        'status': '成功' if success else '失敗',
                        'message': message
                    })
                    
                    if success:
                        success_count += 1
                        # ステータス更新
                        if update_status:
                            st.session_state.email_dist.update_company_status(company_name, "Contacted")
                    else:
                        failed_count += 1
                    
                    # プログレス更新
                    progress_bar.progress((i + 1) / len(filtered_df))
                    
                    # 結果表示更新
                    with results_placeholder.container():
                        col1, col2, col3 = st.columns(3)
                        col1.metric("送信成功", success_count)
                        col2.metric("送信失敗", failed_count)
                        col3.metric("成功率", f"{success_count/(success_count+failed_count)*100:.1f}%" if (success_count+failed_count) > 0 else "0%")
                    
                    # 送信間隔
                    if i < len(filtered_df) - 1:
                        time.sleep(send_interval)
                
                # 最終結果
                status_text.success("🎉 キャンペーン送信完了！")
                
                # 詳細結果表示
                st.subheader("📊 送信結果詳細")
                results_df = pd.DataFrame(results)
                st.dataframe(results_df, use_container_width=True)
                
                # サマリー
                total = success_count + failed_count
                success_rate = (success_count / total * 100) if total > 0 else 0
                
                st.success(f"""
                **キャンペーン完了サマリー**
                - 送信成功: {success_count}件
                - 送信失敗: {failed_count}件  
                - 成功率: {success_rate:.1f}%
                - 使用テンプレート: {selected_template}
                """)
            else:
                st.warning("送信を実行するには確認チェックボックスにチェックを入れてください。")

def render_settings():
    """設定管理"""
    st.title("⚙️ Gmail設定管理")
    
    # 現在の設定表示
    current_config = st.session_state.email_dist.gmail_config
    
    if current_config:
        st.success("✅ 現在の設定")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**メールアドレス:** {current_config['email']}")
            st.info(f"**送信者名:** {current_config['sender_name']}")
        with col2:
            st.info(f"**SMTPサーバー:** {current_config['smtp_server']}")
            st.info(f"**ポート:** {current_config['smtp_port']}")
    else:
        st.error("❌ Gmail設定が見つかりません")
    
    # 設定変更フォーム
    st.subheader("🔧 設定変更")
    
    with st.form("gmail_config_form"):
        email = st.text_input(
            "Gmail アドレス", 
            value=current_config['email'] if current_config else "tokuda@picocela.com"
        )
        
        password = st.text_input(
            "アプリパスワード", 
            type="password",
            value=current_config['password'] if current_config else "",
            help="Gmailの2段階認証を有効にし、アプリパスワードを生成してください"
        )
        
        sender_name = st.text_input(
            "送信者名", 
            value=current_config['sender_name'] if current_config else "PicoCELA Inc."
        )
        
        submitted = st.form_submit_button("💾 設定保存")
        
        if submitted:
            new_config = {
                "email": email,
                "password": password,
                "sender_name": sender_name,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            }
            
            # 接続テスト
            with st.spinner("接続テスト中..."):
                success, message = st.session_state.email_dist.test_gmail_connection(new_config)
            
            if success:
                st.session_state.email_dist.save_gmail_config(new_config)
                st.session_state.email_dist.gmail_config = new_config
                st.success("✅ Gmail設定を保存しました")
                st.rerun()
            else:
                st.error(f"❌ 接続テスト失敗: {message}")

def render_history():
    """送信履歴"""
    st.title("📊 送信履歴・分析")
    
    # 履歴データ取得
    df = get_email_history()
    
    if df.empty:
        st.info("送信履歴がありません。")
        return
    
    # 統計表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総送信数", len(df))
    
    with col2:
        success_count = len(df[df['status'] == 'success'])
        st.metric("送信成功", success_count)
    
    with col3:
        failed_count = len(df[df['status'] == 'failed'])
        st.metric("送信失敗", failed_count)
    
    with col4:
        success_rate = (success_count / len(df) * 100) if len(df) > 0 else 0
        st.metric("成功率", f"{success_rate:.1f}%")
    
    # 時系列チャート
    if 'sent_at' in df.columns:
        df['sent_at'] = pd.to_datetime(df['sent_at'])
        df['date'] = df['sent_at'].dt.date
        
        daily_stats = df.groupby(['date', 'status']).size().unstack(fill_value=0)
        
        if not daily_stats.empty:
            st.subheader("📈 日別送信数推移")
            fig = px.bar(daily_stats.reset_index(), x='date', y=['success', 'failed'], 
                        title="日別送信成功・失敗数", barmode='stack')
            st.plotly_chart(fig, use_container_width=True)
    
    # 履歴テーブル
    st.subheader("📋 送信履歴詳細")
    
    # フィルター
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("ステータスフィルター", ["全て", "success", "failed"])
    with col2:
        days_filter = st.selectbox("期間フィルター", [7, 30, 90, 365], index=1)
    
    # フィルター適用
    filtered_df = df.copy()
    
    if status_filter != "全て":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if 'sent_at' in filtered_df.columns:
        cutoff_date = datetime.now() - timedelta(days=days_filter)
        filtered_df = filtered_df[filtered_df['sent_at'] >= cutoff_date]
    
    # 表示
    st.dataframe(filtered_df, use_container_width=True)

def main():
    """メイン関数"""
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("📧 FusionCRM")
        st.markdown("**メール配信システム**")
        
        # システム状態表示
        if st.session_state.email_dist.gmail_config:
            st.success("✅ システム準備完了")
        else:
            st.error("❌ Gmail設定が必要")
        
        # ナビゲーション
        page = st.radio(
            "ナビゲーション",
            ["📊 ダッシュボード", "🚀 キャンペーン作成", "📋 送信履歴", "⚙️ 設定"]
        )
        
        st.markdown("---")
        st.markdown("**クイックアクション**")
        
        if st.button("🔄 メインシステムに戻る"):
            st.info("メインのfusion_crm_main.pyを起動してください")
        
        if st.button("💻 コマンドライン版起動"):
            st.info("ターミナルで 'python email_distribution.py' を実行してください")
    
    # ページ表示
    if page == "📊 ダッシュボード":
        render_dashboard()
    elif page == "🚀 キャンペーン作成":
        render_campaign_creator()
    elif page == "📋 送信履歴":
        render_history()
    elif page == "⚙️ 設定":
        render_settings()

if __name__ == "__main__":
    main()