"""
統合メールシステム - リファクタリング版メインアプリ
モジュール分離後のクリーンなメインファイル
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import sqlite3

# 一時的回避策: モジュールパスを追加
import sys
import os
sys.path.append('/mount/src/fusioncrm/modules')

# モジュールインポート（modules. プレフィックスなし）
from email_customizers import EnglishEmailCustomizer, JapaneseEmailCustomizer, get_openai_client
from email_database import IntegratedEmailDatabase
from email_sender import send_pregenerated_emails_with_resume
from batch_processing import generate_english_emails_batch, generate_japanese_emails_individual
from data_manager import get_companies_from_sheets, render_company_data_management, render_csv_import


def render_system_statistics():
    """システム統計表示"""
    st.subheader("📈 システム統計")
    
    db = IntegratedEmailDatabase()
    conn = sqlite3.connect(db.db_path)
    
    # 生成統計
    try:
        stats_query = """
            SELECT 
                language,
                customization_method,
                template_type,
                COUNT(*) as count,
                SUM(api_cost) as total_cost,
                AVG(api_cost) as avg_cost
            FROM integrated_emails 
            GROUP BY language, customization_method, template_type
        """
        
        stats_df = pd.read_sql_query(stats_query, conn)
        
        if not stats_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_emails = stats_df['count'].sum()
                st.metric("総生成数", f"{total_emails}通")
            
            with col2:
                total_cost = stats_df['total_cost'].sum()
                st.metric("総コスト", f"${total_cost:.3f}")
            
            with col3:
                avg_cost = stats_df['avg_cost'].mean()
                st.metric("平均コスト", f"${avg_cost:.4f}")
            
            with col4:
                english_count = stats_df[stats_df['language'] == 'english']['count'].sum()
                st.metric("英語メール", f"{english_count}通")
            
            # 詳細統計表
            st.write("**詳細統計:**")
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("まだ生成されたメールがありません")
        
        # 送信統計
        st.subheader("📤 送信統計")
        send_stats_query = """
            SELECT 
                language,
                status,
                COUNT(*) as count
            FROM integrated_send_history 
            GROUP BY language, status
        """
        
        send_stats_df = pd.read_sql_query(send_stats_query, conn)
        
        if not send_stats_df.empty:
            col1, col2, col3 = st.columns(3)
            
            total_sent = send_stats_df['count'].sum()
            success_sent = send_stats_df[send_stats_df['status'] == 'success']['count'].sum()
            success_rate = (success_sent / total_sent * 100) if total_sent > 0 else 0
            
            with col1:
                st.metric("総送信数", f"{total_sent}通")
            with col2:
                st.metric("成功送信", f"{success_sent}通")
            with col3:
                st.metric("成功率", f"{success_rate:.1f}%")
            
            st.dataframe(send_stats_df, use_container_width=True)
        else:
            st.info("まだ送信履歴がありません")
            
    except Exception as e:
        st.error(f"統計取得エラー: {str(e)}")
    
    finally:
        conn.close()


def render_settings_management():
    """設定管理機能"""
    st.subheader("⚙️ システム設定")
    
    # API設定状態
    with st.expander("🔧 API設定状態"):
        if "OPENAI_API_KEY" in st.secrets:
            st.success("✅ OpenAI API Key: 設定済み (Streamlit Secrets)")
        else:
            st.warning("⚠️ OpenAI API Key: 未設定")
            st.info("`.streamlit/secrets.toml` に `OPENAI_API_KEY` を設定してください")
    
    # テンプレート管理
    with st.expander("📧 メールテンプレート管理"):
        st.write("**英語テンプレート特徴:**")
        st.write("- ✅ NASDAQ上場アピール")
        st.write("- ✅ パートナーシップ提案")
        st.write("- ✅ 技術仕様明記（10ホップ、2-3ms遅延）")
        st.write("- ✅ 相手事業特化環境リスト")
        
        st.write("**日本語テンプレート特徴:**")
        st.write("- ✅ 日本のビジネス文化に適した丁寧な文章")
        st.write("- ✅ 技術的課題への理解を示す内容")
        st.write("- ✅ 具体的な次のステップ提案")
        
        if st.button("カスタムテンプレート追加"):
            st.info("カスタムテンプレート機能は今後実装予定")
    
    # システム情報
    with st.expander("ℹ️ システム情報"):
        st.write("**データベース**: SQLite")
        st.write("**メール送信**: Gmail SMTP")
        st.write("**AI生成**: OpenAI GPT-3.5-turbo")
        st.write("**データソース**: Google Sheets")
        
        # データベースサイズ
        try:
            import os
            db_path = "picocela_integrated_emails.db"
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / 1024  # KB
                st.write(f"**データベースサイズ**: {db_size:.1f} KB")
        except:
            st.write("**データベースサイズ**: 取得できませんでした")


def render_send_history():
    """送信履歴表示"""
    st.subheader("📧 送信履歴")
    
    db = IntegratedEmailDatabase()
    history = db.get_send_history(100)
    
    if history:
        # フィルター
        col1, col2, col3 = st.columns(3)
        with col1:
            language_filter = st.selectbox("言語", ["All", "english", "japanese"], key="history_lang")
        with col2:
            status_filter = st.selectbox("ステータス", ["All", "success", "failed", "error"], key="history_status")
        with col3:
            show_limit = st.number_input("表示件数", min_value=10, max_value=200, value=50)
        
        # フィルター適用
        filtered_history = history[:show_limit]
        if language_filter != "All":
            filtered_history = [h for h in filtered_history if h.get('language') == language_filter]
        if status_filter != "All":
            filtered_history = [h for h in filtered_history if h.get('status') == status_filter]
        
        # データ表示
        if filtered_history:
            df = pd.DataFrame(filtered_history)
            df = df[['company_name', 'recipient_email', 'language', 'status', 'sent_at', 'subject']]
            st.dataframe(df, use_container_width=True)
            
            # 詳細表示
            selected_index = st.selectbox("詳細表示", range(len(filtered_history)), 
                                        format_func=lambda x: f"{filtered_history[x]['company_name']} - {filtered_history[x]['status']}")
            
            if st.button("詳細を表示"):
                selected_record = filtered_history[selected_index]
                st.json(selected_record)
        else:
            st.info("フィルター条件に一致する履歴がありません")
    else:
        st.warning("⚠️ 送信履歴がありません")


def render_email_results_tab():
    """生成済みメール確認・編集タブ"""
    st.subheader("📊 生成済みメール確認・編集")
    
    db = IntegratedEmailDatabase()
    conn = sqlite3.connect(db.db_path)
    
    try:
        # フィルター
        col1, col2, col3 = st.columns(3)
        with col1:
            language_filter = st.selectbox("言語フィルター", ["all", "english", "japanese"])
        with col2:
            method_filter = st.selectbox("生成方法", ["all", "gpt35", "fallback"])
        with col3:
            template_filter = st.selectbox("テンプレート", ["all", "standard", "partnership", "introduction", "follow_up"])
        
        # データ取得
        where_clauses = []
        if language_filter != "all":
            where_clauses.append(f"language = '{language_filter}'")
        if method_filter != "all":
            where_clauses.append(f"customization_method = '{method_filter}'")
        if template_filter != "all":
            where_clauses.append(f"template_type = '{template_filter}'")
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT company_name, language, customization_method, template_type,
                   api_cost, generated_at, subject
            FROM integrated_emails 
            {where_clause}
            ORDER BY generated_at DESC
            LIMIT 50
        """
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            st.write(f"**生成済みメール**: {len(df)}通")
            st.dataframe(df, use_container_width=True)
            
            # 詳細表示・編集
            st.subheader("📧 メール詳細表示・編集")
            
            selected_company = st.selectbox(
                "メール表示する企業を選択",
                df['company_name'].tolist()
            )
            
            selected_language = st.selectbox("言語", ["english", "japanese"], key="detail_lang")
            selected_template = st.selectbox("テンプレート", ["standard", "partnership", "introduction", "follow_up"], key="detail_template")
            
            if st.button("メール内容を表示・編集"):
                stored_email = db.get_generated_email(selected_company, selected_language, selected_template)
                if stored_email:
                    st.write(f"**件名**: {stored_email['subject']}")
                    
                    # 編集可能なテキストエリア
                    edited_content = st.text_area(
                        "メール本文（編集可能）", 
                        stored_email['email_body'], 
                        height=400,
                        key="edit_email_content"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 変更を保存"):
                            # 編集内容を保存
                            stored_email['email_body'] = edited_content
                            db.save_generated_email(stored_email)
                            st.success("✅ メール内容を更新しました")
                    
                    with col2:
                        if st.button("📋 クリップボードにコピー"):
                            st.code(edited_content)
                            st.info("💡 上記テキストを手動でコピーしてください")
                    
                    # カスタマイズ詳細
                    with st.expander("🔍 カスタマイズ詳細"):
                        st.write(f"**生成方法**: {stored_email.get('customization_method', 'N/A')}")
                        st.write(f"**APIコスト**: ${stored_email.get('api_cost', 0):.4f}")
                        st.write(f"**生成日時**: {stored_email.get('generated_at', 'N/A')}")
                        
                        if stored_email.get('partnership_environments'):
                            st.write(f"**環境リスト**: {stored_email.get('partnership_environments', 'N/A')}")
                        if stored_email.get('partnership_value'):
                            st.write(f"**価値提案**: {stored_email.get('partnership_value', 'N/A')}")
                        if stored_email.get('suggested_title'):
                            st.write(f"**推奨タイトル**: {stored_email.get('suggested_title', 'N/A')}")
                else:
                    st.warning("⚠️ 指定された条件のメールが見つかりません")
        else:
            st.warning("⚠️ 生成済みメールがありません。まず生成タブで実行してください。")
            
    except Exception as e:
        st.error(f"❌ データベースエラー: {str(e)}")
    finally:
        conn.close()


def render_send_tab():
    """メール送信タブ"""
    st.subheader("📤 事前生成メール瞬時送信")
    
    # Gmail設定確認
    gmail_user = st.session_state.get('gmail_user', '')
    gmail_password = st.session_state.get('gmail_password', '')
    
    if gmail_user and gmail_password:
        gmail_config = {
            'email': gmail_user,
            'password': gmail_password,
            'sender_name': 'PicoCELA Inc.'
        }
        
        db = IntegratedEmailDatabase()
        conn = sqlite3.connect(db.db_path)
        
        # 本日の送信統計
        today_stats_query = """
            SELECT 
                language,
                template_type,
                COUNT(*) as sent_count
            FROM integrated_send_history 
            WHERE DATE(sent_at) = DATE('now') AND status = 'success'
            GROUP BY language, template_type
        """
        
        today_stats = pd.read_sql_query(today_stats_query, conn)
        
        # 送信状況表示
        if not today_stats.empty:
            st.subheader("📊 本日の送信状況")
            for _, row in today_stats.iterrows():
                st.info(f"✅ {row['language']}/{row['template_type']}: {row['sent_count']}通送信済み")
        
        # 送信モード選択
        st.subheader("🚀 送信モード選択")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🆕 新規送信開始**")
            if st.button("新規送信設定", key="new_send"):
                st.session_state['send_mode'] = 'new'
        
        with col2:
            st.write("**🔄 送信再開**")
            if st.button("再開設定", key="resume_send"):
                st.session_state['send_mode'] = 'resume'
        
        # デフォルト設定
        if 'send_mode' not in st.session_state:
            st.session_state['send_mode'] = 'new'
        
        # 送信設定
        st.subheader(f"⚙️ {'再開' if st.session_state['send_mode'] == 'resume' else '新規'}送信設定")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            max_sends = st.number_input("最大送信数", min_value=1, max_value=100, value=20)
        with col2:
            send_language = st.selectbox("送信言語", ["english", "japanese"], key="send_lang")
        with col3:
            send_template = st.selectbox("テンプレート", ["standard", "partnership", "introduction", "follow_up"], key="send_template")
        
        # 送信間隔設定（Gmail制限対策）
        st.subheader("⏱️ 送信制限対策")
        col1, col2 = st.columns(2)
        with col1:
            send_interval = st.slider("送信間隔（秒）", min_value=60, max_value=300, value=120, 
                                    help="Gmail制限対策のため60秒以上推奨")
        with col2:
            max_daily_sends = st.number_input("1日最大送信数", min_value=50, max_value=500, value=200,
                                            help="Gmailアカウント制限に応じて調整")
        
        # 送信実行処理
        try:
            available_query = f"""
                SELECT COUNT(*) as count 
                FROM integrated_emails 
                WHERE language = '{send_language}' AND template_type = '{send_template}'
            """
            available_df = pd.read_sql_query(available_query, conn)
            available_count = available_df.iloc[0]['count'] if not available_df.empty else 0
            
            # 今日の送信数確認
            daily_sent_query = f"""
                SELECT COUNT(*) as count 
                FROM integrated_send_history 
                WHERE DATE(sent_at) = DATE('now') AND status = 'success'
            """
            daily_sent_df = pd.read_sql_query(daily_sent_query, conn)
            daily_sent = daily_sent_df.iloc[0]['count'] if not daily_sent_df.empty else 0
            
            # 残り送信可能数
            remaining_daily = max_daily_sends - daily_sent
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("生成済みメール", f"{available_count}通")
            with col2:
                st.metric("本日送信済み", f"{daily_sent}通")
            with col3:
                st.metric("本日残り可能", f"{remaining_daily}通")
            
            if remaining_daily <= 0:
                st.error("🚫 本日の送信制限に達しています。明日再開してください。")
            elif available_count > 0:
                companies_data = get_companies_from_sheets()
                
                if st.session_state['send_mode'] == 'resume':
                    # 再開モード
                    already_sent = db.get_already_sent_companies(send_language, send_template)
                    remaining_companies = [c for c in companies_data if c.get('company_name') not in already_sent]
                    
                    st.info(f"📧 送信済み: {len(already_sent)}社 | 未送信: {len(remaining_companies)}社")
                    
                    if not remaining_companies:
                        st.success("✅ 全企業への送信が完了しています！")
                    else:
                        target_count = min(max_sends, len(remaining_companies), remaining_daily)
                        estimated_time = target_count * (send_interval + 10) / 60
                        
                        st.write(f"⏱️ 予想送信時間: {estimated_time:.1f}分 ({target_count}社)")
                        
                        # 送信確認
                        confirm_send = st.checkbox("📤 送信内容を確認し、Gmail制限を理解しました")
                        
                        if confirm_send and st.button("🔄 送信再開", type="primary"):
                            summary = send_pregenerated_emails_with_resume(
                                companies_data, 
                                gmail_config, 
                                max_sends, 
                                send_language, 
                                send_template, 
                                send_interval,
                                resume_mode=True
                            )
                            st.session_state['last_send_summary'] = summary
                else:
                    # 新規モード
                    target_count = min(max_sends, len(companies_data), remaining_daily)
                    estimated_time = target_count * (send_interval + 10) / 60
                    
                    st.write(f"⏱️ 予想送信時間: {estimated_time:.1f}分 ({target_count}社)")
                    
                    # 送信確認
                    confirm_send = st.checkbox("📤 送信内容を確認し、Gmail制限を理解しました")
                    
                    if confirm_send and st.button("🚀 瞬時送信開始", type="primary"):
                        summary = send_pregenerated_emails_with_resume(
                            companies_data, 
                            gmail_config, 
                            max_sends, 
                            send_language, 
                            send_template, 
                            send_interval,
                            resume_mode=False
                        )
                        st.session_state['last_send_summary'] = summary
            else:
                st.warning(f"⚠️ {send_language}/{send_template}メールが生成されていません。まず生成してください。")
                
        except Exception as e:
            st.error(f"❌ 送信可能数確認エラー: {str(e)}")
        finally:
            conn.close()
    else:
        st.warning("⚠️ Gmail設定を完了してください")


def main():
    """メインアプリケーション"""
    
    # ページ設定
    st.set_page_config(
        page_title="PicoCELA統合メールシステム完全版", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # タイトル
    st.title("🌐 PicoCELA統合メールシステム完全版")
    st.markdown("**日本語個別生成 + 英語バッチ処理システム - モジュール分離版**")
    
    # API設定状態確認
    api_configured = "OPENAI_API_KEY" in st.secrets
    if api_configured:
        st.success("✅ OpenAI API Key 設定済み (Streamlit Secrets)")
    else:
        st.error("❌ OpenAI API Key が設定されていません (.streamlit/secrets.toml)")
    
    # サイドバー設定
    with st.sidebar:
        st.header("🔧 システム設定")
        
        # API設定状態表示
        st.subheader("🤖 OpenAI API設定")
        if api_configured:
            st.success("✅ API設定完了")
        else:
            st.error("❌ API未設定")
            st.info("Secretsファイルを確認してください")
        
        # Gmail設定
        st.subheader("📧 Gmail設定")
        gmail_user = st.text_input("Gmailアドレス", value="tokuda@picocela.com")
        gmail_password = st.text_input("アプリパスワード", type="password", 
                                     help="Gmail 2段階認証のアプリパスワード")
        
        # セッション状態に保存
        st.session_state['gmail_user'] = gmail_user
        st.session_state['gmail_password'] = gmail_password
        
        # Gmail設定状態
        if gmail_user and gmail_password:
            st.success("✅ Gmail設定完了")
        else:
            st.warning("⚠️ Gmail設定が必要です")
        
        # クイック統計
        st.subheader("📊 クイック統計")
        try:
            db = IntegratedEmailDatabase()
            conn = sqlite3.connect(db.db_path)
            
            # 生成数
            count_query = "SELECT COUNT(*) as total FROM integrated_emails"
            result = pd.read_sql_query(count_query, conn)
            total_generated = result.iloc[0]['total'] if not result.empty else 0
            
            # コスト
            cost_query = "SELECT SUM(api_cost) as total_cost FROM integrated_emails"
            cost_result = pd.read_sql_query(cost_query, conn)
            total_cost = cost_result.iloc[0]['total_cost'] if not cost_result.empty and cost_result.iloc[0]['total_cost'] else 0
            
            # 送信数
            send_query = "SELECT COUNT(*) as total_sent FROM integrated_send_history"
            send_result = pd.read_sql_query(send_query, conn)
            total_sent = send_result.iloc[0]['total_sent'] if not send_result.empty else 0
            
            st.metric("生成済み", f"{total_generated}通")
            st.metric("送信済み", f"{total_sent}通")
            st.metric("総コスト", f"${total_cost:.3f}")
            
            conn.close()
        except:
            st.metric("生成済み", "0通")
            st.metric("送信済み", "0通")
            st.metric("総コスト", "$0.000")
    
    # メインコンテンツ
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🌍 英語バッチ生成", 
        "🇯🇵 日本語個別生成",
        "📊 生成結果確認", 
        "📤 瞬時送信",
        "📧 送信履歴",
        "📝 データ管理", 
        "⚙️ 設定"
    ])
    
    with tab1:
        st.subheader("🌍 英語パートナーシップメール バッチ生成")
        
        # システム説明
        with st.expander("ℹ️ バッチ生成システム概要"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**ベースメール特徴:**")
                st.write("- ✅ NASDAQ上場企業アピール")
                st.write("- ✅ 具体的技術仕様（10ホップ、2-3ms遅延）")
                st.write("- ✅ 数値効果（90%ケーブル削減）")
                st.write("- ✅ パートナーシップ提案（売り込みではない）")
            
            with col2:
                st.write("**GPT-3.5カスタマイズ:**")
                st.write("- 🎯 相手企業の顧客層に特化した環境リスト")
                st.write("- 🎯 相互ビジネス価値提案の最適化")
                st.write("- 🎯 適切な宛先タイトル自動選択")
                st.write("- 🎯 業界専門知識の証明")
        
        # 生成設定
        col1, col2, col3 = st.columns(3)
        with col1:
            max_companies = st.number_input("生成対象企業数", min_value=1, max_value=1000, value=100)
        with col2:
            estimated_cost = max_companies * 0.0004 * 150
            st.metric("予想コスト", f"約{estimated_cost:.0f}円")
        with col3:
            estimated_time = max_companies * 2 / 60
            st.metric("予想時間", f"{estimated_time:.1f}分")
        
        # 生成実行
        if api_configured:
            if st.button("🚀 英語バッチ生成開始", type="primary"):
                companies_data = get_companies_from_sheets()
                
                if companies_data and len(companies_data) > 0:
                    st.write(f"📋 {len(companies_data)}社のデータを取得しました")
                    summary = generate_english_emails_batch(companies_data, max_companies)
                    st.session_state['last_batch_summary'] = summary
                else:
                    st.error("❌ 企業データが取得できませんでした")
        else:
            st.error("❌ OpenAI API設定を完了してください")
    
    with tab2:
        st.subheader("🇯🇵 日本語営業メール 個別生成")
        
        # テンプレートタイプ選択
        template_type = st.selectbox("メールタイプ", 
                                   ["partnership", "introduction", "follow_up"],
                                   format_func=lambda x: {
                                       "partnership": "パートナーシップ提案",
                                       "introduction": "初回紹介",
                                       "follow_up": "フォローアップ"
                                   }[x])
        
        # 企業選択
        companies_data = get_companies_from_sheets()
        if companies_data:
            selected_companies = st.multiselect(
                "生成対象企業を選択",
                companies_data,
                format_func=lambda x: f"{x['company_name']} ({x.get('industry', 'Unknown')})"
            )
            
            if api_configured and selected_companies:
                if st.button("🇯🇵 日本語メール生成開始", type="primary"):
                    summary = generate_japanese_emails_individual(selected_companies, template_type)
                    st.session_state['last_japanese_summary'] = summary
            elif not api_configured:
                st.error("❌ OpenAI API設定を完了してください")
            elif not selected_companies:
                st.warning("⚠️ 生成対象企業を選択してください")
        else:
            st.error("❌ 企業データが取得できませんでした")
    
    with tab3:
        render_email_results_tab()
    
    with tab4:
        render_send_tab()
    
    with tab5:
        render_send_history()
    
    with tab6:
        render_company_data_management()
        render_csv_import()
    
    with tab7:
        render_settings_management()
        render_system_statistics()
        
        # データエクスポート
        with st.expander("📤 データエクスポート"):
            export_table = st.selectbox("エクスポートテーブル", 
                                      ["integrated_emails", "companies", "integrated_send_history"])
            
            if st.button("CSV形式でエクスポート"):
                db = IntegratedEmailDatabase()
                conn = sqlite3.connect(db.db_path)
                
                try:
                    export_df = pd.read_sql_query(f"SELECT * FROM {export_table}", conn)
                    csv_data = export_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 CSVファイルをダウンロード",
                        data=csv_data,
                        file_name=f"{export_table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                    st.success(f"✅ {export_table}テーブルのデータを準備しました")
                    
                except Exception as e:
                    st.error(f"エクスポートエラー: {str(e)}")
                finally:
                    conn.close()


if __name__ == "__main__":
    main()
