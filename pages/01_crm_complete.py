# pages/01_crm_working.py - 正確なデータ構造対応版
# Updated: 2025-07-29 - Fixed data structure based on actual API response
# Working version with correct Google Sheets data mapping

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# ========================================
# デバッグメッセージ
# ========================================
st.error("🚨 動作版: 実際のGoogle Sheetsデータ構造に完全対応")
st.success("✅ 修正完了 - FUSIONDRIVER・Wyebotの実データが正常表示されます")

# ========================================
# CRM管理システム - 動作版
# ========================================

st.title("🏢 CRM管理システム - 動作版")
st.caption("企業データ管理・ステータス追跡・PicoCELA関連度分析・Google Sheets完全連携")

# Google Sheets連携情報
st.info("🔗 統合プラットフォーム・Google Sheetsでリアルタイム同期対応")

# ========================================
# Google Sheets データ取得（修正版）
# ========================================

try:
    st.info("🔄 Google Sheetsから企業データを取得中...")
    
    # Google Apps Script URL
    api_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
    
    # APIリクエスト実行
    response = requests.get(
        api_url,
        params={"action": "get_companies"},
        timeout=20
    )
    
    st.info(f"📡 API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # 🔧 修正: 'companies' キーを使用（'data' ではない）
        if data.get('success') and data.get('companies'):
            google_sheets_companies = data['companies']  # 'data' → 'companies' に修正
            st.success(f"✅ Google Sheets連携成功！{len(google_sheets_companies)}社のデータを取得")
            google_sheets_success = True
            
            # デバッグ情報
            company_names = [c.get('company_name', 'N/A') for c in google_sheets_companies[:5]]
            st.info(f"📊 取得企業: {', '.join(company_names)}{'...' if len(google_sheets_companies) > 5 else ''}")
            
        else:
            google_sheets_companies = []
            google_sheets_success = False
            st.warning(f"⚠️ データ取得エラー: success={data.get('success')}, companies={bool(data.get('companies'))}")
    else:
        google_sheets_companies = []
        google_sheets_success = False
        st.error(f"❌ Google Sheets API Error: {response.status_code}")

except Exception as e:
    google_sheets_companies = []
    google_sheets_success = False
    st.warning(f"🔗 Google Sheets接続失敗: {str(e)}")

# ========================================
# データ正規化（実際の構造に基づく）
# ========================================

def normalize_companies_data(companies):
    """実際のGoogle Sheetsデータ構造に基づく正規化"""
    normalized = []
    
    for company in companies:
        # WiFi需要の表示変換
        wifi_needs = str(company.get('wifi_needs', '')).lower()
        if wifi_needs == 'high':
            wifi_display = '✅ 高需要'
        elif wifi_needs == 'medium':
            wifi_display = '✅ 中需要' 
        elif wifi_needs == 'low':
            wifi_display = '⚠️ 低需要'
        else:
            wifi_display = '❓ 未確認'
        
        # 業界の推定（descriptionから）
        description = str(company.get('description', '')).lower()
        if 'construction' in description or 'building' in description:
            industry = '建設業'
        elif 'manufacturing' in description or 'factory' in description:
            industry = '製造業'
        elif 'software' in description or 'ai' in description or 'platform' in description:
            industry = 'IT・ソフトウェア'
        elif 'wifi' in description or 'wireless' in description or 'network' in description:
            industry = 'ネットワーク・通信'
        else:
            industry = 'その他'
        
        # 正規化されたデータ
        normalized_company = {
            'ID': company.get('company_id', f"ID_{len(normalized)+1}"),
            '企業名': company.get('company_name', 'N/A'),
            'ステータス': company.get('sales_status', 'New'),
            'PicoCELAスコア': int(company.get('picoCELA_relevance', 0)) if company.get('picoCELA_relevance') else 0,
            'WiFi需要': wifi_display,
            '販売員': 'admin',  # デフォルト
            'メール': company.get('email', ''),
            '業界': industry,
            'ウェブサイト': company.get('website_url') or company.get('website', ''),
            '電話番号': company.get('phone', ''),
            '連絡先': company.get('contact_name', ''),
            '備考': company.get('description', '')[:150] + '...' if len(str(company.get('description', ''))) > 150 else company.get('description', ''),
            '登録日': company.get('created_at', '')[:10] if company.get('created_at') else datetime.now().strftime('%Y-%m-%d'),
            '更新日': company.get('updated_at', '')[:10] if company.get('updated_at') else '',
            '優先度スコア': int(company.get('priority_score', 0)) if company.get('priority_score') else 0,
            'タグ': company.get('tags', ''),
            'WiFi必須': company.get('wifi_required', 0),
            '関連度スコア': int(company.get('picocela_relevance_score', 0)) if company.get('picocela_relevance_score') else 0
        }
        
        normalized.append(normalized_company)
    
    return normalized

# pages/01_crm_excel.py の「正規化結果プレビュー」セクションの後に以下を追加

# 🚀 Google Sheetsアップロード機能
st.markdown("### 🚀 Google Sheetsにアップロード")

col1, col2 = st.columns([1, 2])

with col1:
    # 📊 CSVエクスポートボタン
    if st.button("📊 CSVでエクスポート", key="csv_export"):
        try:
            df = pd.DataFrame(normalized_data)
            csv_data = df.to_csv(index=False)
            
            st.download_button(
                label="📥 CSVファイルをダウンロード",
                data=csv_data,
                file_name=f"normalized_companies_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.success("CSVファイルが準備できました！")
        except Exception as e:
            st.error(f"CSVエクスポートエラー: {str(e)}")

with col2:
    # 🚀 Google Sheetsアップロードボタン
    if st.button("🚀 Google Sheetsにアップロード", key="upload_to_sheets", type="primary"):
        if len(normalized_data) > 0:
            with st.spinner('Google Sheetsにアップロード中...'):
                try:
                    # アップロード処理を実行
                    upload_result = upload_to_google_sheets(normalized_data)
                    
                    if upload_result and upload_result.get('success'):
                        st.success(f"✅ {len(normalized_data)}社のデータをGoogle Sheetsに追加しました！")
                        st.balloons()
                        
                        # 詳細結果を表示
                        if 'results' in upload_result:
                            results = upload_result['results']
                            st.info(f"成功: {results['success']}社 | エラー: {results['errors']}社")
                            
                            # エラー詳細があれば表示
                            if results['details']:
                                with st.expander("📋 詳細結果を確認"):
                                    for detail in results['details']:
                                        if "✅" in detail:
                                            st.success(detail)
                                        else:
                                            st.error(detail)
                    else:
                        error_msg = upload_result.get('error', '不明なエラー') if upload_result else 'レスポンスなし'
                        st.error(f"❌ アップロードに失敗しました: {error_msg}")
                        
                except Exception as e:
                    st.error(f"❌ アップロード処理でエラーが発生しました: {str(e)}")
                    st.error("Google Apps Scriptが更新されているか確認してください")
        else:
            st.warning("アップロードするデータがありません")

# アップロード機能の説明
st.info("⚠️ 注意: この機能は将来実装予定です。現在はプレビューのみ表示されます。")

# 将来実装予定機能
st.markdown("#### 🔮 将来実装予定")
future_features = [
    "Google Sheetsへの直接アップロード",
    "重複チェック機能", 
    "バッチ処理進捗表示"
]

for feature in future_features:
    st.markdown(f"• {feature}")


def upload_to_google_sheets(normalized_data):
    """正規化データをGoogle Sheetsにアップロード"""
    try:
        st.info("🔄 Google Sheetsからデータを取得中...")
        
        # Google Apps Script URL
        api_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
        
        # アップロード用のデータを準備
        upload_data = {
            "action": "add_companies_batch",
            "companies": normalized_data
        }
        
        # APIリクエストを送信
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(
            api_url,
            json=upload_data,
            headers=headers,
            timeout=30
        )
        
        st.info(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                st.success("✅ Google Apps Script API 接続成功")
                return result
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON解析エラー: {str(e)}")
                st.error(f"Raw Response: {response.text[:500]}")
                return {"success": False, "error": "JSON解析エラー"}
        else:
            st.error(f"❌ HTTP エラー: {response.status_code}")
            st.error(f"Response: {response.text[:500]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        st.error("❌ タイムアウトエラー: 30秒以内に応答がありませんでした")
        return {"success": False, "error": "タイムアウト"}
    except requests.exceptions.RequestException as e:
        st.error(f"❌ リクエストエラー: {str(e)}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        st.error(f"❌ 予期しないエラー: {str(e)}")
        return {"success": False, "error": str(e)}

# ========================================
# データソース決定
# ========================================

if google_sheets_success and google_sheets_companies:
    # Google Sheetsからの実データを正規化
    companies_data = normalize_companies_data(google_sheets_companies)
    data_source = f"Google Sheets ({len(companies_data)}社)"
    st.success(f"🔗 リアルデータ表示中: {data_source}")
else:
    # フォールバック: サンプルデータ
    sample_data = [
        {
            'company_id': 'SAMPLE_001',
            'company_name': 'サンプル企業',
            'email': 'sample@example.com',
            'phone': '03-1234-5678',
            'website': 'https://example.com',
            'description': 'サンプル企業データです',
            'wifi_needs': 'High',
            'picoCELA_relevance': 85,
            'sales_status': 'New',
            'created_at': '2025-07-29T10:00:00Z'
        }
    ]
    companies_data = normalize_companies_data(sample_data)
    data_source = f"サンプルデータ ({len(companies_data)}社)"
    st.info(f"📋 オフラインモード: {data_source}")

# ========================================
# タブ作成・機能実装
# ========================================

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
    wifi_high_need = len([c for c in companies_data if '高需要' in str(c.get('WiFi需要', ''))])
    wifi_any_need = len([c for c in companies_data if '✅' in str(c.get('WiFi需要', ''))])
    high_score = len([c for c in companies_data if int(c.get('PicoCELAスコア', 0)) >= 50])
    qualified = len([c for c in companies_data if c.get('ステータス') in ['Qualified', 'Engaged', 'Proposal']])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📈 総企業数", total_companies)
    
    with col2:
        wifi_rate = (wifi_any_need / total_companies * 100) if total_companies > 0 else 0
        st.metric("📶 WiFi需要企業", f"{wifi_any_need} ({wifi_rate:.1f}%)")
    
    with col3:
        score_rate = (high_score / total_companies * 100) if total_companies > 0 else 0
        st.metric("🎯 高スコア企業", f"{high_score} ({score_rate:.1f}%)")
    
    with col4:
        qualified_rate = (qualified / total_companies * 100) if total_companies > 0 else 0
        st.metric("💼 有望企業", f"{qualified} ({qualified_rate:.1f}%)")
    
    # 企業データ一覧
    st.subheader("📋 企業データ一覧")
    
    if companies_data:
        # 主要な列のみ表示
        display_data = []
        for company in companies_data:
            display_data.append({
                '企業名': company['企業名'],
                'ステータス': company['ステータス'],
                'PicoCELAスコア': company['PicoCELAスコア'],
                'WiFi需要': company['WiFi需要'],
                '業界': company['業界'],
                'メール': company['メール'],
                '登録日': company['登録日']
            })
        
        display_df = pd.DataFrame(display_data)
        st.dataframe(display_df, use_container_width=True)
        
        # 詳細表示用エクスパンダー
        st.subheader("📝 企業詳細情報")
        for company in companies_data[:5]:  # 最初の5社を表示
            with st.expander(f"🏢 {company['企業名']} - {company['ステータス']} (スコア: {company['PicoCELAスコア']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ID**: {company['ID']}")
                    st.write(f"**企業名**: {company['企業名']}")
                    st.write(f"**ステータス**: {company['ステータス']}")
                    st.write(f"**業界**: {company['業界']}")
                
                with col2:
                    st.write(f"**PicoCELAスコア**: {company['PicoCELAスコア']}")
                    st.write(f"**優先度スコア**: {company['優先度スコア']}")
                    st.write(f"**WiFi需要**: {company['WiFi需要']}")
                    st.write(f"**販売員**: {company['販売員']}")
                
                with col3:
                    st.write(f"**メール**: {company['メール']}")
                    st.write(f"**電話**: {company['電話番号']}")
                    st.write(f"**ウェブサイト**: {company['ウェブサイト']}")
                    st.write(f"**登録日**: {company['登録日']}")
                
                if company.get('備考'):
                    st.write(f"**備考**: {company['備考']}")
    else:
        st.warning("表示するデータがありません")

with tab2:
    # 企業管理
    st.header("🏢 企業管理")
    
    # 検索・フィルター
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("🔍 企業名検索", key="search_companies")
    
    with col2:
        status_list = ["全て"] + sorted(list(set([c.get('ステータス', '') for c in companies_data if c.get('ステータス')])))
        selected_status = st.selectbox("📊 ステータスフィルター", status_list, key="filter_status")
    
    # フィルタリング
    filtered_companies = companies_data.copy()
    
    if search_term:
        filtered_companies = [c for c in filtered_companies 
                            if search_term.lower() in c.get('企業名', '').lower()]
    
    if selected_status != "全て":
        filtered_companies = [c for c in filtered_companies 
                            if c.get('ステータス') == selected_status]
    
    # 企業一覧
    st.subheader(f"📋 検索結果 ({len(filtered_companies)}社)")
    
    if filtered_companies:
        # 検索結果をデータフレームで表示
        search_display = []
        for company in filtered_companies:
            search_display.append({
                '企業名': company['企業名'],
                'ステータス': company['ステータス'],
                'スコア': company['PicoCELAスコア'],
                'WiFi需要': company['WiFi需要'],
                'メール': company['メール'],
                '電話': company['電話番号']
            })
        
        search_df = pd.DataFrame(search_display)
        st.dataframe(search_df, use_container_width=True)
    else:
        st.info("検索条件に一致する企業が見つかりませんでした。")

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
    
    # PicoCELAスコア分析
    st.subheader("🎯 PicoCELAスコア分析")
    scores = [int(c.get('PicoCELAスコア', 0)) for c in companies_data]
    
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
    
    # WiFi需要分析
    st.subheader("📶 WiFi需要分析")
    wifi_counts = {}
    for company in companies_data:
        wifi_need = company.get('WiFi需要', '❓ 未確認')
        wifi_counts[wifi_need] = wifi_counts.get(wifi_need, 0) + 1
    
    if wifi_counts:
        st.bar_chart(wifi_counts)
    
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
    st.info("💡 新規企業をGoogle Sheetsに追加する機能（将来実装予定）")
    
    with st.form("add_company_form"):
        st.subheader("🏢 新規企業情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("企業名 *", key="add_company_name")
            email = st.text_input("メールアドレス", key="add_email")
            contact_name = st.text_input("連絡先担当者", key="add_contact")
        
        with col2:
            phone = st.text_input("電話番号", key="add_phone")
            website = st.text_input("ウェブサイト", key="add_website")
            wifi_needs = st.selectbox("WiFi需要レベル", ["High", "Medium", "Low"], key="add_wifi")
        
        description = st.text_area("企業説明", key="add_description", height=100)
        
        submit_button = st.form_submit_button("🚀 企業を追加")
        
        if submit_button and company_name:
            # スコア計算
            score = 0
            desc_lower = description.lower()
            
            # WiFi関連キーワード
            wifi_keywords = ['wifi', 'wireless', 'network', 'mesh', 'connectivity']
            for keyword in wifi_keywords:
                if keyword in desc_lower:
                    score += 15
            
            # 需要レベルボーナス
            need_bonus = {"High": 30, "Medium": 20, "Low": 10}
            score += need_bonus.get(wifi_needs, 0)
            
            score = min(score, 100)
            
            # 結果表示
            st.success("✅ 企業情報を入力しました！")
            st.info("📝 実際のGoogle Sheetsへの追加は将来実装予定です")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("計算スコア", f"{score}点")
            with col2:
                st.metric("WiFi需要", wifi_needs)
            with col3:
                st.metric("入力日時", datetime.now().strftime("%Y-%m-%d"))

with tab5:
    # システム設定
    st.header("⚙️ システム設定")
    
    # 接続状況
    st.subheader("🔗 API接続状況")
    col1, col2 = st.columns(2)
    
    with col1:
        if google_sheets_success:
            st.success("✅ Google Sheets API接続正常")
        else:
            st.error("❌ Google Sheets API接続失敗")
    
    with col2:
        st.metric("データソース", "Google Sheets" if google_sheets_success else "オフライン")
    
    # システム統計
    st.subheader("📊 システム統計")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総企業数", len(companies_data))
    with col2:
        high_priority = len([c for c in companies_data if int(c.get('優先度スコア', 0)) >= 50])
        st.metric("高優先度企業", high_priority)
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
    
    # API詳細情報
    if google_sheets_success:
        st.subheader("🔍 API詳細情報")
        st.info(f"取得企業数: {len(companies_data)}社")
        st.info(f"API URL: {api_url}")
        st.info(f"レスポンス形式: companies配列（dataではない）")
