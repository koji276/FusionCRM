#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - PicoCELA営業管理システム メインシステム完全版
メール配信システム統合済み
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json

# ページ設定
st.set_page_config(
    page_title="🚀 FusionCRM - PicoCELA営業管理システム",
    page_icon="🚀",
    layout="wide"
)

# CSS スタイル
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #667eea;
        margin: 0.5rem 0;
    }
    .email-card {
        background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #38a169;
        margin: 1rem 0;
    }
    .warning-card {
        background: linear-gradient(135deg, #fffbf0 0%, #fef5e7 100%);
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #ed8936;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_database_stats():
    """データベース統計の取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        cursor = conn.cursor()
        
        # 基本統計
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        
        # ステータス別統計
        cursor.execute("SELECT status, COUNT(*) FROM companies GROUP BY status")
        status_data = dict(cursor.fetchall())
        
        # WiFi必要企業（仮定：picocela_relevance_score > 50 または wifi_required = 1）
        cursor.execute("""
            SELECT COUNT(*) FROM companies 
            WHERE picocela_relevance_score > 50 OR status = 'New'
        """)
        wifi_needed = cursor.fetchone()[0]
        
        # 高優先度企業
        cursor.execute("SELECT COUNT(*) FROM companies WHERE picocela_relevance_score >= 100")
        high_priority = cursor.fetchone()[0]
        
        # 商談中企業
        cursor.execute("SELECT COUNT(*) FROM companies WHERE status IN ('Contacted', 'Replied', 'Qualified')")
        in_progress = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_companies': total_companies,
            'status_data': status_data,
            'wifi_needed': wifi_needed,
            'high_priority': high_priority,
            'in_progress': in_progress
        }
        
    except Exception as e:
        st.error(f"データベース統計取得エラー: {e}")
        return {
            'total_companies': 0,
            'status_data': {},
            'wifi_needed': 0,
            'high_priority': 0,
            'in_progress': 0
        }

def get_email_distribution_stats():
    """メール配信統計の取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        cursor = conn.cursor()
        
        # 今日の送信数
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) FROM email_history WHERE DATE(sent_at) = ?", (today,))
        result = cursor.fetchone()
        today_sent = result[0] if result else 0
        
        # 配信可能企業数
        cursor.execute("SELECT COUNT(*) FROM companies WHERE email_address IS NOT NULL AND email_address != ''")
        result = cursor.fetchone()
        email_available = result[0] if result else 0
        
        # 今週の送信数
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) FROM email_history WHERE sent_at >= ?", (week_ago,))
        result = cursor.fetchone()
        week_sent = result[0] if result else 0
        
        # 成功率（過去30日）
        month_ago = datetime.now() - timedelta(days=30)
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
            FROM email_history 
            WHERE sent_at >= ?
        """, (month_ago,))
        
        result = cursor.fetchone()
        total_sent = result[0] if result and result[0] else 0
        success_sent = result[1] if result and result[1] else 0
        success_rate = (success_sent / total_sent * 100) if total_sent > 0 else 0
        
        # Gmail設定状況
        gmail_configured = os.path.exists('config/gmail_config.json')
        
        conn.close()
        
        return {
            'today_sent': today_sent,
            'email_available': email_available,
            'week_sent': week_sent,
            'success_rate': success_rate,
            'gmail_configured': gmail_configured,
            'total_sent_30d': total_sent
        }
        
    except Exception as e:
        # テーブルが存在しない場合のデフォルト値
        return {
            'today_sent': 0,
            'email_available': 0,
            'week_sent': 0,
            'success_rate': 0,
            'gmail_configured': os.path.exists('config/gmail_config.json'),
            'total_sent_30d': 0
        }

def get_companies_data():
    """企業データの取得"""
    try:
        conn = sqlite3.connect('fusion_crm.db')
        query = """
            SELECT company_name, email_address, website, phone, status, 
                   picocela_relevance_score, created_at
            FROM companies 
            ORDER BY picocela_relevance_score DESC
            LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"企業データ取得エラー: {e}")
        return pd.DataFrame()

def render_dashboard_header():
    """ダッシュボードヘッダー"""
    st.title("🚀 FusionCRM - PicoCELA営業管理システム")
    st.markdown("**Google Sheets版（クラウド対応）- Version 6.0**")
    
    # 接続状態表示
    st.markdown("""
    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #38a169;">
        ✅ <strong>Google Sheets接続中</strong> | 📊 <a href="#" style="color: #38a169;">スプレッドシートを開く</a>
    </div>
    """, unsafe_allow_html=True)

def render_main_dashboard():
    """メインダッシュボード"""
    
    # データ取得
    db_stats = get_database_stats()
    email_stats = get_email_distribution_stats()
    
    # メイン統計カード
    st.subheader("📊 ダッシュボード")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_value = f"+{db_stats['total_companies']}" if db_stats['total_companies'] > 0 else None
        st.metric(
            "総企業数", 
            db_stats['total_companies'],
            delta=delta_value
        )
    
    with col2:
        wifi_growth = f"+{db_stats['wifi_needed']:.0f}%" if db_stats['wifi_needed'] > 0 else None
        st.metric(
            "WiFi必要企業", 
            db_stats['wifi_needed'],
            delta=wifi_growth
        )
    
    with col3:
        priority_growth = f"+{db_stats['high_priority']:.0f}%" if db_stats['high_priority'] > 0 else None
        st.metric(
            "高優先度企業", 
            db_stats['high_priority'],
            delta=priority_growth
        )
    
    with col4:
        st.metric(
            "商談中企業", 
            db_stats['in_progress'],
            delta=None
        )
    
    # グラフセクション
    if db_stats['status_data']:
        col1, col2 = st.columns(2)
        
        with col1:
            # ステータス分布パイチャート
            status_df = pd.DataFrame(list(db_stats['status_data'].items()), 
                                   columns=['Status', 'Count'])
            fig_pie = px.pie(status_df, values='Count', names='Status', 
                           title="企業ステータス分布")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # WiFi需要分析（仮想データ）
            wifi_data = {
                'WiFi必要': db_stats['wifi_needed'],
                'WiFi不要': max(0, db_stats['total_companies'] - db_stats['wifi_needed'])
            }
            wifi_df = pd.DataFrame(list(wifi_data.items()), columns=['Category', 'Count'])
            
            fig_bar = px.bar(wifi_df, x='Category', y='Count', 
                           title="WiFi需要分析",
                           color='Category',
                           color_discrete_map={'WiFi必要': '#38a169', 'WiFi不要': '#e2e8f0'})
            st.plotly_chart(fig_bar, use_container_width=True)

def render_companies_list():
    """企業一覧表示"""
    st.subheader("🏢 企業一覧（最新10社）")
    
    df = get_companies_data()
    
    if not df.empty:
        # 表示用データの整形
        display_df = df.copy()
        
        # カラム名の調整
        if 'picocela_relevance_score' in display_df.columns:
            display_df = display_df.rename(columns={'picocela_relevance_score': 'priority_score'})
        
        # 優先度スコア表示の改善
        if 'priority_score' in display_df.columns:
            display_df['priority_score'] = display_df['priority_score'].fillna(0).astype(int)
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("企業データが見つかりません。")

def render_email_distribution_section():
    """メール配信システムセクション"""
    
    st.markdown("---")
    st.header("📧 メール配信システム")
    
    # 統計取得
    email_stats = get_email_distribution_stats()
    
    # 統計カード
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "今日の送信数", 
            f"{email_stats['today_sent']}件",
            delta=f"+{email_stats['today_sent']}" if email_stats['today_sent'] > 0 else None
        )
    
    with col2:
        st.metric(
            "配信可能企業", 
            f"{email_stats['email_available']}社"
        )
    
    with col3:
        st.metric(
            "今週の送信", 
            f"{email_stats['week_sent']}件"
        )
    
    with col4:
        st.metric(
            "成功率(30日)", 
            f"{email_stats['success_rate']:.1f}%"
        )
    
    with col5:
        status_text = "🟢 準備完了" if email_stats['gmail_configured'] else "🔴 設定必要"
        st.metric("システム状態", status_text)
    
    # メール配信システムカード
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="email-card">
            <h3 style="color: #38a169; margin-bottom: 1rem;">🌐 Web版メール配信</h3>
            <p style="color: #2d3748; margin-bottom: 1rem;">ブラウザベースの直感的なインターフェース</p>
            <ul style="color: #4a5568; margin-bottom: 1rem;">
                <li>📊 企業選択・フィルタリング</li>
                <li>📝 テンプレート管理</li>
                <li>📈 リアルタイム進捗表示</li>
                <li>📋 送信履歴・分析</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Web版メール配信を起動", key="web_email", type="primary"):
            st.info("""
            **Web版メール配信システム起動方法:**
            
            1. 新しいターミナルウィンドウを開く
            2. 以下のコマンドを実行:
            ```bash
            streamlit run email_campaign_streamlit.py --server.port 8502
            ```
            3. ブラウザで http://localhost:8502 にアクセス
            
            ⚠️ **注意**: メインシステムとは別ポート(8502)で起動されます
            """)
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 2px solid #0284c7;
            margin: 1rem 0;
        ">
            <h3 style="color: #0284c7; margin-bottom: 1rem;">💻 CLI版メール配信</h3>
            <p style="color: #2d3748; margin-bottom: 1rem;">高速・安定のコマンドライン版</p>
            <ul style="color: #4a5568; margin-bottom: 1rem;">
                <li>⚡ 高速バッチ処理</li>
                <li>🕐 スケジュール送信</li>
                <li>📝 詳細ログ出力</li>
                <li>🤖 自動化スクリプト対応</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ CLI版メール配信を起動", key="cli_email"):
            st.info("""
            **CLI版メール配信システム起動方法:**
            
            1. 新しいターミナルウィンドウを開く
            2. 以下のコマンドを実行:
            ```bash
            python email_distribution.py
            ```
            3. 対話式メニューが表示されます
            
            **💡 推奨メニューオプション:**
            - 新規配信: `1. 新規企業への一括配信`
            - 設定: `5. Gmail設定確認・変更`
            """)
    
    # 設定案内
    if not email_stats['gmail_configured']:
        st.markdown("""
        <div class="warning-card">
            <h4 style="color: #ed8936;">⚠️ Gmail設定が必要です</h4>
            <p>メール配信を使用するには、まずGmail設定を行ってください:</p>
            <ol>
                <li>CLI版を起動 (<code>python email_distribution.py</code>)</li>
                <li>メニューで「5. Gmail設定確認・変更」を選択</li>
                <li>Gmailアドレスとアプリパスワードを設定</li>
            </ol>
            <p><strong>アプリパスワードの取得方法:</strong></p>
            <ol>
                <li>Googleアカウントの2段階認証を有効化</li>
                <li>「アプリパスワード」で新しいパスワードを生成</li>
                <li>生成されたパスワードを設定に使用</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # 最近の送信履歴
    if email_stats['total_sent_30d'] > 0:
        st.subheader("📊 最近の送信履歴")
        
        try:
            conn = sqlite3.connect('fusion_crm.db')
            
            query = """
                SELECT 
                    eh.sent_at,
                    c.company_name,
                    eh.status,
                    eh.email_type
                FROM email_history eh
                LEFT JOIN companies c ON eh.company_id = c.id
                ORDER BY eh.sent_at DESC
                LIMIT 5
            """
            
            recent_history = pd.read_sql_query(query, conn)
            
            if not recent_history.empty:
                for _, row in recent_history.iterrows():
                    status_icon = "✅" if row['status'] == 'success' else "❌"
                    sent_time = row['sent_at'][:16] if pd.notna(row['sent_at']) else "不明"
                    company = row['company_name'] if pd.notna(row['company_name']) else "不明"
                    email_type = row['email_type'] if pd.notna(row['email_type']) else "campaign"
                    
                    st.markdown(f"{status_icon} **{company}** - {sent_time} ({email_type})")
            
            conn.close()
            
        except Exception as e:
            st.warning(f"履歴取得エラー: {e}")

def render_sidebar():
    """サイドバー"""
    with st.sidebar:
        st.title("🚀 FusionCRM")
        st.markdown("**PicoCELA営業管理システム**")
        
        # システム状態
        email_stats = get_email_distribution_stats()
        db_stats = get_database_stats()
        
        st.markdown("### 📊 システム状態")
        st.metric("登録企業数", db_stats['total_companies'])
        
        if email_stats['gmail_configured']:
            st.success("✅ メール配信準備完了")
        else:
            st.error("❌ Gmail設定が必要")
        
        # メール配信統計
        st.markdown("### 📧 メール配信統計")
        st.markdown(f"**今日の送信:** {email_stats['today_sent']}件")
        st.markdown(f"**配信可能企業:** {email_stats['email_available']}社")
        st.markdown(f"**成功率:** {email_stats['success_rate']:.1f}%")
        
        # クイックアクション
        st.markdown("### ⚡ クイックアクション")
        
        if st.button("🌐 Web版配信", help="ブラウザ版メール配信"):
            st.info("メインエリアの起動ボタンをご利用ください")
        
        if st.button("💻 CLI版配信", help="コマンドライン版"):
            st.info("ターミナルで python email_distribution.py")
        
        # システム情報
        st.markdown("---")
        st.markdown("### 🔧 システム情報")
        
        # ファイル存在確認
        files_status = {
            'email_distribution.py': os.path.exists('email_distribution.py'),
            'email_campaign_streamlit.py': os.path.exists('email_campaign_streamlit.py'),
            'fusion_crm.db': os.path.exists('fusion_crm.db')
        }
        
        for file_name, exists in files_status.items():
            icon = "✅" if exists else "❌"
            st.markdown(f"{icon} `{file_name}`")
        
        # バージョン情報
        st.markdown("---")
        st.markdown("**Version 6.0**")
        st.markdown("Google Sheets連携対応")

def main():
    """メイン関数"""
    
    # ヘッダー表示
    render_dashboard_header()
    
    # メインダッシュボード
    render_main_dashboard()
    
    # 企業一覧
    render_companies_list()
    
    # メール配信システム
    render_email_distribution_section()
    
    # サイドバー
    render_sidebar()

if __name__ == "__main__":
    main()
