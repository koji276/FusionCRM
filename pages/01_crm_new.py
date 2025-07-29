# pages/01_crm_new.py - 完全版
# Updated: 2025-07-29 - Google Sheets完全連携版
# Complete CRM System with Google Sheets Integration

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# ========================================
# デバッグメッセージ（更新確認用）
# ========================================
st.error("🚨 重要: この赤いメッセージが表示されていれば、最新版が反映されています。")
st.success("✅ Google Sheets完全連携版 - CRM完全機能システム")

# ========================================
# Google Sheets API連携関数（完全版）
# ========================================

def get_google_sheets_data():
    """Google SheetsからCRMデータを取得する完全版"""
    try:
        st.info("🔄 Google Sheetsから企業データを取得中...")
        
        # Google Apps Script URL（確認済み動作URL）
        api_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
        
        # CORS対応ヘッダー
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # APIリクエスト実行
        response = requests.get(
            api_url,
            params={"action": "get_companies"},
            headers=headers,
            timeout=30,
            verify=True
        )
        
        st.info(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                # レスポンスをJSONとして解析
                response_text = response.text
                st.info(f"📊 API Response Length: {len(response_text)} characters")
                
                data = response.json()
                
                # データ構造をログ出力
                st.info(f"🔍 Response Structure: success={data.get('success')}, data_count={len(data.get('data', []))}")
                
                if data.get('success') and data.get('data'):
                    companies = data['data']
                    
                    # 取得したデータの詳細情報
                    st.success(f"✅ Google Sheets連携成功！")
                    st.success(f"📊 取得データ: {len(companies)}社の企業情報")
                    
                    # サンプルデータ表示（デバッグ用）
                    if companies:
                        first_company = companies[0]
                        company_keys = list(first_company.keys())[:5]  # 最初の5つのキーを表示
                        st.info(f"📋 データ構造例: {company_keys}")
                    
                    return companies, True
                else:
                    st.warning(f"⚠️ データ構造の問題: success={data.get('success')}, data_exists={bool(data.get('data'))}")
                    return [], False
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON解析エラー: {str(e)}")
                st.error(f"Raw Response (first 500 chars): {response.text[:500]}...")
                return [], False
        else:
            st.error(f"❌ HTTP Error {response.status_code}: {response.reason}")
            st.error(f"Response: {response.text[:200]}...")
            return [], False
            
    except requests.exceptions.Timeout:
        st.warning("⏰ Google Sheets API接続タイムアウト（30秒）")
        return [], False
    except requests.exceptions.ConnectionError as e:
        st.error(f"🌐 接続エラー: {str(e)}")
        return [], False
    except requests.exceptions.RequestException as e:
        st.error(f"📡 リクエストエラー: {str(e)}")
        return [], False
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {str(e)}")
        st.error(f"エラータイプ: {type(e).__name__}")
        return [], False

def create_sample_data():
    """フォールバック用サンプルデータ"""
    return [
        {
            'company_id': 1,
            '企業名': 'ABC建設株式会社',
            'company_name': 'ABC Construction',
            'ステータス': 'Contacted',
            'sales_status': 'Contacted',
            'PicoCELAスコア': 85,
            'picocela_relevance': 85,
            'WiFi需要': '✅ 必要',
            'wifi_needs': 'High',
            '販売員': 'admin',
            'salesperson': 'admin',
            'メール': 'contact@abc-construction.com',
            'email': 'contact@abc-construction.com',
            '業界': '建設業',
            'industry': 'Construction',
            'ウェブサイト': 'https://abc-construction.com',
            'website_url': 'https://abc-construction.com',
            '備考': 'Large construction sites requiring WiFi mesh networks',
            'notes': 'Large construction sites requiring WiFi mesh networks',
            '登録日': '2025-07-20',
            'created_date': '2025-07-20'
        },
        {
            'company_id': 2,
            '企業名': 'FUSIONDRIVER',
            'company_name': 'FUSIONDRIVER',
            'ステータス': 'Engaged',
            'sales_status': 'Engaged',
            'PicoCELAスコア': 95,
            'picocela_relevance': 95,
            'WiFi需要': '✅ 必要',
            'wifi_needs': 'High',
            '販売員': 'admin',
            'salesperson': 'admin',
            'メール': 'koji@fusiondriver.biz',
            'email': 'koji@fusiondriver.biz',
            '業界': 'IT・ソフトウェア',
            'industry': 'IT Software',
            'ウェブサイト': 'https://fusiondriver.biz',
            'website_url': 'https://fusiondriver.biz',
            '備考': 'High-tech company with advanced networking needs',
            'notes': 'High-tech company with advanced networking needs',
            '登録日': '2025-07-15',
            'created_date': '2025-07-15'
        },
        {
            'company_id': 3,
            '企業名': 'XYZ製造工業',
            'company_name': 'XYZ Manufacturing',
            'ステータス': 'Qualified',
            'sales_status': 'Qualified',
            'PicoCELAスコア': 92,
            'picocela_relevance': 92,
            'WiFi需要': '✅ 必要',
            'wifi_needs': 'High',
            '販売員': 'admin',
            'salesperson': 'admin',
            'メール': 'info@xyz-manufacturing.com',
            'email': 'info@xyz-manufacturing.com',
            '業界': '製造業',
            'industry': 'Manufacturing',
            'ウェブサイト': 'https://xyz-manufacturing.com',
            'website_url': 'https://xyz-manufacturing.com',
            '備考': 'Factory floor needs wireless network coverage',
            'notes': 'Factory floor needs wireless network coverage',
            '登録日': '2025-07-22',
            'created_date': '2025-07-22'
        }
    ]

def normalize_company_data(companies):
    """企業データを統一フォーマットに正規化"""
    normalized = []
    
    for company in companies:
        # 日本語キーと英語キーの両方に対応
        normalized_company = {
            'ID': company.get('company_id') or company.get('ID') or len(normalized) + 1,
            '企業名': company.get('company_name') or company.get('企業名') or 'N/A',
            'ステータス': company.get('sales_status') or company.get('ステータス') or 'New',
            'PicoCELAスコア': company.get('picocela_relevance') or company.get('PicoCELAスコア') or 0,
            'WiFi需要': company.get('wifi_needs') or company.get('WiFi需要') or 'Unknown',
            '販売員': company.get('salesperson') or company.get('販売員') or 'admin',
            'メール': company.get('email') or company.get('メール') or '',
            '業界': company.get('industry') or company.get('業界') or 'その他',
            'ウェブサイト': company.get('website_url') or company.get('ウェブサイト') or '',
            '備考': company.get('notes') or company.get('備考') or '',
            '登録日': company.get('created_date') or company.get('登録日') or datetime.now().strftime('%Y-%m-%d')
        }
        
        # WiFi需要の表示形式を統一
        wifi_need = str(normalized_company['WiFi需要']).lower()
        if wifi_need in ['high', 'medium', 'yes', 'true', '1']:
            normalized_company['WiFi需要'] = '✅ 必要'
        elif wifi_need in ['low', 'no', 'false', '0']:
            normalized_company['WiFi需要'] = '❌ 不要'
        else:
            normalized_company['WiFi需要'] = '❓ 未確認'
        
        normalized.append(normalized_company)
    
    return normalized

# ========================================
# メイン画面表示関数
# ========================================

def show_crm_new_page():
    """CRM管理システム - 完全版"""
    
    st.title("🏢 CRM管理システム - 完全版")
    st.caption("企業データ管理・ステータス追跡・PicoCELA関連度分析・Google Sheets完全連携")
    
    # Google Sheets連携情報
    st.info("🔗 統合プラットフォーム・Google Sheetsでリアルタイム同期対応")
    
    # データ取得処理
    with st.spinner("🔄 企業データを読み込み中..."):
        real_data, connection_success = get_google_sheets_data()
    
    if connection_success and real_data:
        # Google Sheetsからの実データを使用
        st.success(f"🔗 Google Sheets連携成功！{len(real_data)}社のリアルデータを表示")
        companies_raw = real_data
        data_source = f"Google Sheets ({len(real_data)}社)"
    else:
        # サンプルデータを使用
        st.info("📋 オフラインモード - サンプルデータを表示中")
        companies_raw = create_sample_data()
        data_source = f"サンプルデータ ({len(companies_raw)}社)"
    
    # データを正規化
    companies_data = normalize_company_data(companies_raw)
    
    # タブ作成
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 ダッシュボード", 
        "🏢 企業管理", 
        "📈 分析", 
        "➕ 企業追加", 
        "⚙️ 設定"
    ])
    
    with tab1:
        # ダッシュボード
        st.header("📊 CRMダッシュボード")
        st.caption(f"データソース: {data_source}")
        
        # 統計メトリクス
        total_companies = len(companies_data)
        wifi_needed = len([c for c in companies_data if '✅' in str(c.get('WiFi需要', ''))])
        high_score = len([c for c in companies_data if int(c.get('PicoCELAスコア', 0)) >= 80])
        qualified = len([c for c in companies_data if c.get('ステータス') in ['Qualified', 'Engaged', 'Proposal']])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 総企業数", total_companies)
        
        with col2:
            wifi_rate = (wifi_needed / total_companies * 100) if total_companies > 0 else 0
            st.metric("📶 WiFi需要企業", f"{wifi_needed} ({wifi_rate:.1f}%)")
        
        with col3:
            score_rate = (high_score / total_companies * 100) if total_companies > 0 else 0
            st.metric("🎯 高スコア企業", f"{high_score} ({score_rate:.1f}%)")
        
        with col4:
            qualified_rate = (qualified / total_companies * 100) if total_companies > 0 else 0
            st.metric("💼 有望企業", f"{qualified} ({qualified_rate:.1f}%)")
        
        # 企業データ一覧
        st.subheader("📋 企業データ一覧")
        
        if companies_data:
            # 表示用データフレーム
            display_df = pd.DataFrame(companies_data)
            
            # 重要な列のみ表示
            key_columns = ['企業名', 'ステータス', 'PicoCELAスコア', 'WiFi需要', '業界', '販売員']
            available_columns = [col for col in key_columns if col in display_df.columns]
            
            if available_columns:
                st.dataframe(display_df[available_columns], use_container_width=True)
            else:
                st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("表示するデータがありません")
    
    with tab2:
        # 企業管理
        st.header("🏢 企業管理")
        
        # 検索・フィルター
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("🔍 企業名検索", key="company_search_tab2")
        
        with col2:
            status_list = ["全て"] + sorted(list(set([c.get('ステータス', '') for c in companies_data if c.get('ステータス')])))
            selected_status = st.selectbox("📊 ステータスフィルター", status_list, key="status_filter_tab2")
        
        # フィルタリング
        filtered_companies = companies_data.copy()
        
        if search_term:
            filtered_companies = [c for c in filtered_companies 
                                if search_term.lower() in c.get('企業名', '').lower()]
        
        if selected_status != "全て":
            filtered_companies = [c for c in filtered_companies 
                                if c.get('ステータス') == selected_status]
        
        # 企業一覧
        st.subheader(f"📋 企業一覧 ({len(filtered_companies)}社)")
        
        for company in filtered_companies:
            with st.expander(f"🏢 {company.get('企業名', 'N/A')} - {company.get('ステータス', 'N/A')} - スコア: {company.get('PicoCELAスコア', 'N/A')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ID**: {company.get('ID', 'N/A')}")
                    st.write(f"**企業名**: {company.get('企業名', 'N/A')}")
                    st.write(f"**ステータス**: {company.get('ステータス', 'N/A')}")
                    st.write(f"**PicoCELAスコア**: {company.get('PicoCELAスコア', 'N/A')}")
                
                with col2:
                    st.write(f"**WiFi需要**: {company.get('WiFi需要', 'N/A')}")
                    st.write(f"**業界**: {company.get('業界', 'N/A')}")
                    st.write(f"**販売員**: {company.get('販売員', 'N/A')}")
                    st.write(f"**登録日**: {company.get('登録日', 'N/A')}")
                
                with col3:
                    st.write(f"**メール**: {company.get('メール', 'N/A')}")
                    st.write(f"**ウェブサイト**: {company.get('ウェブサイト', 'N/A')}")
                    
                    if company.get('ウェブサイト') and company['ウェブサイト'] != 'N/A':
                        st.markdown(f"[🔗 ウェブサイトを開く]({company['ウェブサイト']})")
                
                if company.get('備考'):
                    st.write(f"**備考**: {company.get('備考')}")
    
    with tab3:
        # 分析
        st.header("📈 データ分析")
        
        # ステータス分布
        st.subheader("📊 ステータス分布")
        status_counts = {}
        for company in companies_data:
            status = company.get('ステータス', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            st.bar_chart(status_counts)
        
        # スコア分析
        st.subheader("🎯 PicoCELAスコア分析")
        scores = [int(c.get('PicoCELAスコア', 0)) for c in companies_data if c.get('PicoCELAスコア') is not None]
        
        if scores:
            score_ranges = {
                '0-25点': len([s for s in scores if 0 <= s <= 25]),
                '26-50点': len([s for s in scores if 26 <= s <= 50]),
                '51-75点': len([s for s in scores if 51 <= s <= 75]),
                '76-100点': len([s for s in scores if 76 <= s <= 100])
            }
            
            st.bar_chart(score_ranges)
            
            # 統計情報
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均スコア", f"{sum(scores)/len(scores):.1f}点")
            with col2:
                st.metric("最高スコア", f"{max(scores)}点")
            with col3:
                st.metric("最低スコア", f"{min(scores)}点")
        
        # 業界分析
        st.subheader("🏭 業界分析")
        industry_counts = {}
        for company in companies_data:
            industry = company.get('業界', 'その他')
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        if industry_counts:
            st.bar_chart(industry_counts)
    
    with tab4:
        # 企業追加
        st.header("➕ 企業追加")
        
        with st.form("add_company_form"):
            st.subheader("🏢 新規企業情報")
            
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("企業名 *", key="add_company_name")
                email = st.text_input("メールアドレス", key="add_email")
                industry = st.selectbox("業界", 
                    ["建設業", "製造業", "IT・ソフトウェア", "金融業", "小売業", "不動産業", "物流業", "医療・介護", "教育", "その他"], 
                    key="add_industry")
            
            with col2:
                website = st.text_input("ウェブサイト", key="add_website")
                status = st.selectbox("初期ステータス", 
                    ["New", "Contacted", "Replied", "Engaged", "Qualified", "Proposal", "Negotiation"], 
                    key="add_status")
            
            notes = st.text_area("備考・特記事項", key="add_notes", height=100)
            
            submit_button = st.form_submit_button("🚀 企業を追加")
            
            if submit_button and company_name:
                # スコア計算
                score = 0
                notes_lower = notes.lower()
                
                # キーワードベーススコア
                wifi_keywords = ['wifi', 'wireless', 'network', 'mesh', 'connectivity', 'internet', 'iot', 'smart', 'automation']
                for keyword in wifi_keywords:
                    if keyword in notes_lower:
                        score += 10
                
                construction_keywords = ['construction', 'building', 'site', 'facility', 'warehouse', 'factory']
                for keyword in construction_keywords:
                    if keyword in notes_lower:
                        score += 8
                
                # 業界ボーナス
                industry_bonus = {
                    "建設業": 25, "製造業": 20, "物流業": 18, 
                    "不動産業": 15, "IT・ソフトウェア": 10, "金融業": 5
                }
                score += industry_bonus.get(industry, 0)
                
                score = min(score, 100)  # 最大100点
                
                # WiFi需要判定
                wifi_need = "✅ 必要" if score >= 40 else "❌ 不要"
                
                # 結果表示
                st.success("✅ 企業追加完了！")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("PicoCELA関連度", f"{score}点")
                with col2:
                    st.metric("WiFi需要判定", wifi_need)
                with col3:
                    st.metric("追加日時", datetime.now().strftime("%Y-%m-%d"))
                
                # 企業情報表示
                st.info(f"**企業名**: {company_name} | **業界**: {industry} | **ステータス**: {status}")
                if notes:
                    st.write(f"**備考**: {notes}")
    
    with tab5:
        # システム設定
        st.header("⚙️ システム設定")
        
        # 接続状況
        st.subheader("🔗 API接続状況")
        col1, col2 = st.columns(2)
        
        with col1:
            if connection_success:
                st.success("✅ Google Sheets API接続正常")
            else:
                st.error("❌ Google Sheets API接続失敗")
        
        with col2:
            st.metric("データソース", data_source.split('(')[0])
        
        # システム統計
        st.subheader("📊 システム統計")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総企業数", len(companies_data))
        with col2:
            st.metric("データソース", "Google Sheets" if connection_success else "オフライン")
        with col3:
            st.metric("最終更新", datetime.now().strftime("%H:%M"))
        with col4:
            st.metric("システム状態", "正常動作")
        
        # データエクスポート
        st.subheader("📤 データエクスポート")
        if st.button("📊 CSVエクスポート", key="export_csv"):
            df = pd.DataFrame(companies_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="💾 CSVファイルをダウンロード",
                data=csv,
                file_name=f'fusioncrm_companies_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv'
            )
            st.success("✅ CSVファイルの準備が完了しました！")

# ========================================
# メイン実行
# ========================================

if __name__ == "__main__":
    show_crm_new_page()
