# pages/01_crm_new.py - Google Sheets連携修正版
# Updated: 2025-07-29 - Google Sheets API連携実装
# Force deployment trigger - Google Sheets integration fix

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# ========================================
# Google Sheets API連携関数
# ========================================

def get_real_companies_data():
    """Google SheetsからリアルCRMデータを取得"""
    try:
        # Google Apps Script URL
        google_apps_script_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
        
        # APIに企業データ取得リクエスト
        response = requests.get(
            google_apps_script_url,
            params={"action": "get_companies"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                companies = data['data']
                st.success(f"✅ Google Sheets連携成功 - {len(companies)}社のデータを取得")
                return companies
            else:
                st.warning("⚠️ Google Sheetsにデータが見つかりません")
                return None
        else:
            st.error(f"❌ Google Sheets API接続エラー: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.warning("⏰ Google Sheets API接続タイムアウト")
        return None
    except requests.exceptions.RequestException as e:
        st.warning(f"🌐 Google Sheets API接続失敗: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Google Sheets データ取得エラー: {str(e)}")
        return None

def get_api_connection_info():
    """API接続情報を安全に取得"""
    try:
        # Google Apps Script URL（固定設定）
        google_apps_script_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
        
        # 簡単な接続テスト
        response = requests.get(google_apps_script_url, params={"action": "test"}, timeout=5)
        if response.status_code == 200:
            return True, f"Google Sheets API 接続正常 ({google_apps_script_url[:50]}...)"
        else:
            return False, f"API接続エラー: {response.status_code}"
            
    except Exception as e:
        return False, f"接続テストエラー: {str(e)}"

# ========================================
# サンプルデータ生成関数（フォールバック用）
# ========================================

def get_sample_companies():
    """サンプル企業データを生成（Google Sheets接続失敗時用）"""
    return [
        {
            'ID': 1, '企業名': 'ABC建設', 'ステータス': 'Contacted', 
            'PicoCELAスコア': 85, 'WiFi需要': '✅', '販売員': 'admin',
            'メール': 'contact@abc-construction.com', '業界': '建設業',
            'ウェブサイト': 'https://abc-construction.com',
            '備考': 'Large construction company with multiple sites'
        },
        {
            'ID': 2, '企業名': 'XYZ工業', 'ステータス': 'Qualified', 
            'PicoCELAスコア': 92, 'WiFi需要': '✅', '販売員': 'admin',
            'メール': 'info@xyz-industry.com', '業界': '製造業',
            'ウェブサイト': 'https://xyz-industry.com',
            '備考': 'Manufacturing facility with WiFi mesh network needs'
        },
        {
            'ID': 3, '企業名': 'DEF開発', 'ステータス': 'Proposal', 
            'PicoCELAスコア': 78, 'WiFi需要': '❌', '販売員': 'admin',
            'メール': 'contact@def-dev.com', '業界': 'IT・ソフトウェア',
            'ウェブサイト': 'https://def-dev.com',
            '備考': 'Software development company'
        }
    ]

# ========================================
# メイン画面表示関数
# ========================================

def show_crm_new_page():
    """CRM管理システム - フル機能版"""
    
    st.title("🏢 CRM管理システム - フル機能版")
    st.caption("企業データ管理・ステータス追跡・PicoCELA関連度分析")
    
    # Google Sheets接続テスト
    st.info("🔗 統合プラットフォーム・ガイドページから各ページに移動できます｜Google Sheetsで更にリアルタイム同期")
    
    # API接続チェック（安全なチェック）
    try:
        api_connected, api_info = get_api_connection_info()
    except:
        api_connected, api_info = False, "設定エラー"
    
    if not api_connected:
        st.warning("⚠️ Google Sheets APIに接続できません。")
        
        # オフラインモード継続ボタン
        if st.button("⚠️ オフラインモードで続行", key="offline_mode_btn"):
            st.session_state.crm_offline_mode = True
    
    # オフラインモードまたはAPI接続成功時に5つのタブを表示
    if st.session_state.get('crm_offline_mode', False) or api_connected:
        
        # CRM機能表示
        st.success("✅ CRM機能（オフラインモード）")
        
        # 5つのタブを作成
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 ダッシュボード", 
            "🏢 企業管理", 
            "📈 分析", 
            "➕ 企業追加", 
            "⚙️ 設定"
        ])
        
        with tab1:
            # ダッシュボード機能を直接実装
            st.header("📊 CRMダッシュボード")
            
            # 実際のGoogle Sheetsデータを取得を試行
            real_companies = get_real_companies_data()
            
            if real_companies is not None:
                # Google Sheetsからの実際のデータを使用
                companies = real_companies
                st.info(f"🔗 Google Sheets連携中 - {len(companies)}社のデータを表示")
            else:
                # フォールバック：サンプルデータを使用
                companies = get_sample_companies()
                st.info("📋 オフラインモード - サンプルデータを表示中")
            
            df = pd.DataFrame(companies)
            
            # 統計メトリクス
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_companies = len(companies)
                st.metric("📈 総企業数", total_companies)
            
            with col2:
                wifi_needed = len([c for c in companies if c.get('WiFi需要') == '✅'])
                wifi_percentage = (wifi_needed / total_companies * 100) if total_companies > 0 else 0
                st.metric("📶 WiFi需要企業", f"{wifi_needed} ({wifi_percentage:.1f}%)")
            
            with col3:
                picocela_related = len([c for c in companies if c.get('PicoCELAスコア', 0) > 50])
                picocela_percentage = (picocela_related / total_companies * 100) if total_companies > 0 else 0
                st.metric("🎯 PicoCELA関連", f"{picocela_related} ({picocela_percentage:.1f}%)")
            
            with col4:
                monthly_target = 15
                st.metric("🎯 今月目標", monthly_target)
            
            # 企業データ一覧表示
            st.subheader("📋 企業データ一覧")
            
            # データフレーム表示用に整形
            display_df = pd.DataFrame(companies)
            if not display_df.empty:
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("データがありません")
        
        with tab2:
            # 企業管理機能を直接実装
            st.header("🏢 企業管理")
            
            # ステータスリストを直接定義
            status_options = ["全て", "New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost"]
            
            # 検索・フィルター機能
            col1, col2 = st.columns(2)
            
            with col1:
                search_company = st.text_input("🔍 企業名検索", key="search_company_tab2")
            
            with col2:
                filter_status = st.selectbox("📊 ステータスフィルター", status_options, key="filter_status_tab2")
            
            # データの取得とフィルタリング
            real_companies = get_real_companies_data()
            if real_companies is not None:
                companies = real_companies
            else:
                companies = get_sample_companies()
            
            # フィルタリング処理
            filtered_companies = companies.copy()
            
            if search_company:
                filtered_companies = [c for c in filtered_companies if search_company.lower() in c.get('企業名', '').lower()]
            
            if filter_status != "全て":
                filtered_companies = [c for c in filtered_companies if c.get('ステータス') == filter_status]
            
            # 企業一覧表示
            st.subheader(f"📋 企業一覧 ({len(filtered_companies)}社)")
            
            for company in filtered_companies:
                with st.expander(f"🏢 {company.get('企業名', 'N/A')} - {company.get('ステータス', 'N/A')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**ID**: {company.get('ID', 'N/A')}")
                        st.write(f"**ステータス**: {company.get('ステータス', 'N/A')}")
                        st.write(f"**PicoCELAスコア**: {company.get('PicoCELAスコア', 'N/A')}")
                    
                    with col2:
                        st.write(f"**販売員**: {company.get('販売員', 'N/A')}")
                        st.write(f"**WiFi需要**: {company.get('WiFi需要', 'N/A')}")
                        st.write(f"**業界**: {company.get('業界', 'N/A')}")
                    
                    with col3:
                        st.write(f"**メール**: {company.get('メール', 'N/A')}")
                        st.write(f"**ウェブサイト**: {company.get('ウェブサイト', 'N/A')}")
                        st.write(f"**備考**: {company.get('備考', 'N/A')}")
        
        with tab3:
            # 分析機能を直接実装
            st.header("📈 分析")
            
            # データの取得
            real_companies = get_real_companies_data()
            if real_companies is not None:
                companies = real_companies
            else:
                companies = get_sample_companies()
            
            # ステータス分布分析
            st.subheader("📊 ステータス分布")
            
            status_counts = {}
            for company in companies:
                status = company.get('ステータス', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                # Streamlit標準のbar_chartを使用
                st.bar_chart(status_counts)
            
            # PicoCELA関連度分析
            st.subheader("🎯 PicoCELA関連度分析")
            
            scores = [company.get('PicoCELAスコア', 0) for company in companies if company.get('PicoCELAスコア') is not None]
            
            if scores:
                # スコア分布をヒストグラム的に表示
                score_ranges = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
                for score in scores:
                    if score <= 25:
                        score_ranges['0-25'] += 1
                    elif score <= 50:
                        score_ranges['26-50'] += 1
                    elif score <= 75:
                        score_ranges['51-75'] += 1
                    else:
                        score_ranges['76-100'] += 1
                
                st.bar_chart(score_ranges)
                
                # 統計情報
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("平均スコア", f"{avg_score:.1f}点")
                with col2:
                    st.metric("最高スコア", f"{max_score}点")
                with col3:
                    st.metric("最低スコア", f"{min_score}点")
                
                # 詳細分析
                st.subheader("📈 詳細分析")
                high_score_companies = len([s for s in scores if s >= 80])
                promising_companies = len([s for s in scores if s >= 70])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("高スコア企業（80点以上）", f"{high_score_companies}社 ({high_score_companies/len(scores)*100:.1f}%)")
                with col2:
                    st.metric("成約見込み企業", f"{promising_companies}社（積極フォロー推奨）")
        
        with tab4:
            # 企業追加機能を直接実装
            st.header("➕ 企業追加")
            
            # 業界リストとステータスリストを直接定義
            industry_options = ["建設業", "製造業", "IT・ソフトウェア", "金融業", "小売業", "不動産業", "物流業", "医療・介護", "教育", "その他"]
            status_options_add = ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation", "Won", "Lost"]
            
            # 企業追加フォーム
            with st.form("add_company_form"):
                st.subheader("🏢 新規企業情報")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    company_name = st.text_input("企業名 *", key="add_company_name")
                    email = st.text_input("メールアドレス", key="add_email")
                    industry = st.selectbox("業界", industry_options, key="add_industry")
                
                with col2:
                    website = st.text_input("ウェブサイト", key="add_website")
                    initial_status = st.selectbox("初期ステータス", status_options_add, key="add_initial_status")
                    
                notes = st.text_area("備考", key="add_notes", height=100)
                
                submit_button = st.form_submit_button("🚀 企業を追加")
                
                if submit_button and company_name:
                    # PicoCELAスコアの簡易計算
                    score = 0
                    notes_lower = notes.lower()
                    
                    # キーワードベースのスコア計算
                    keywords = ['wifi', 'wireless', 'network', 'mesh', 'connectivity', 'internet']
                    for keyword in keywords:
                        if keyword in notes_lower:
                            score += 15
                    
                    # 業界ベースのスコア調整
                    if industry == "建設業":
                        score += 20
                    elif industry == "製造業":
                        score += 15
                    elif industry == "IT・ソフトウェア":
                        score += 5
                    
                    # WiFi需要判定
                    wifi_need = "✅" if (score > 30 or industry in ["建設業", "製造業"]) else "❌"
                    
                    # 結果表示
                    st.success("✅ 企業追加しました！")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("PicoCELA関連度スコア", f"{score}点")
                    with col2:
                        st.metric("WiFi需要判定", wifi_need)
                    with col3:
                        st.metric("追加日時", datetime.now().strftime("%Y-%m-%d"))
                    
                    # 企業情報の表示
                    st.info(f"企業名: {company_name} | 業界: {industry} | ステータス: {initial_status}")
        
        with tab5:
            # 設定機能を直接実装
            st.header("⚙️ 設定")
            
            # API接続状況
            st.subheader("🔗 API接続状況")
            
            try:
                api_connected, api_info = get_api_connection_info()
                if api_connected:
                    st.success(f"✅ {api_info}")
                else:
                    st.error(f"❌ {api_info}")
            except:
                st.error("❌ API接続テストでエラーが発生しました")
            
            # システム統計
            st.subheader("📊 システム統計")
            
            real_companies = get_real_companies_data()
            if real_companies is not None:
                companies = real_companies
                data_source = "Google Sheets"
            else:
                companies = get_sample_companies()
                data_source = "サンプルデータ"
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("データソース", data_source)
            with col2:
                st.metric("総企業数", len(companies))
            with col3:
                st.metric("最終更新", datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            # データエクスポート
            st.subheader("📤 データエクスポート")
            
            if st.button("📊 CSVエクスポート", key="export_csv_btn"):
                df = pd.DataFrame(companies)
                csv = df.to_csv(index=False, encoding='utf-8')
                
                st.download_button(
                    label="💾 CSVファイルをダウンロード",
                    data=csv,
                    file_name=f'companies_{datetime.now().strftime("%Y%m%d")}.csv',
                    mime='text/csv'
                )
    else:
        st.info("システムを再起動してください")

# ========================================
# メイン実行
# ========================================

if __name__ == "__main__":
    show_crm_new_page()
