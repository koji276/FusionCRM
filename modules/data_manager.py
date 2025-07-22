"""
データ管理システム
企業データの取得、管理、インポート機能
"""

import time
import pandas as pd
from typing import Dict, List
import streamlit as st

# from email_database import IntegratedEmailDatabase


def get_companies_from_sheets() -> List[Dict]:
    """Google Sheetsから企業データを取得"""
    try:
        # 既存のGoogle Sheets URL使用
        sheet_url = "https://docs.google.com/spreadsheets/d/1ySS3zLbEwq3U54pzIRAbKLyhOWR2YdBUSdK_xr_7WNY"
        csv_url = f"{sheet_url}/export?format=csv&gid=580124806"
        
        # データ読み込み
        df = pd.read_csv(csv_url)
        
        # 必要な列のみ抽出・整形
        companies = []
        for index, row in df.iterrows():
            company_data = {
                'company_id': f"COMP_{index:03d}",
                'company_name': str(row.get('company_name', '')).strip(),
                'email': str(row.get('email', '')).strip(),
                'description': str(row.get('description', '')).strip(),
                'website': str(row.get('website', '')).strip(),
                'phone': str(row.get('phone', '')).strip(),
                'industry': str(row.get('industry', '')).strip(),
                'country': str(row.get('country', '')).strip()
            }
            
            # 有効なデータのみ追加
            if company_data['company_name'] and company_data['email']:
                companies.append(company_data)
        
        st.success(f"✅ Google Sheetsから{len(companies)}社のデータを取得")
        return companies
        
    except Exception as e:
        st.error(f"Google Sheets接続エラー: {str(e)}")
        
        # フォールバックデータ
        return [
            {
                'company_id': 'FUSION_001',
                'company_name': 'FUSIONDRIVER',
                'email': 'koji@fusiondriver.biz',
                'description': 'WiFi solution for construction sites with wireless communication integration',
                'website': 'https://www.fusiondriver.biz',
                'phone': '',
                'industry': 'Technology',
                'country': 'Japan'
            }
        ]


def render_company_data_management():
    """企業データ手動管理機能"""
    st.subheader("📝 企業データ管理")
    
    db = IntegratedEmailDatabase()
    
    # データ追加フォーム
    with st.expander("➕ 企業データ手動追加"):
        with st.form("add_company_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_company_name = st.text_input("企業名*")
                new_email = st.text_input("メールアドレス*")
                new_website = st.text_input("ウェブサイト")
                new_phone = st.text_input("電話番号")
            
            with col2:
                new_description = st.text_area("事業説明", height=100)
                new_industry = st.text_input("業界")
                new_country = st.selectbox("国", ["Japan", "USA", "UK", "Germany", "Other"])
            
            submitted = st.form_submit_button("企業を追加")
            
            if submitted and new_company_name and new_email:
                new_company = {
                    'company_id': f"MANUAL_{int(time.time())}",
                    'company_name': new_company_name,
                    'email': new_email,
                    'description': new_description,
                    'website': new_website,
                    'phone': new_phone,
                    'industry': new_industry,
                    'country': new_country
                }
                
                db.save_company(new_company)
                st.success(f"✅ {new_company_name} を追加しました")
                st.rerun()
    
    # 既存企業データ表示
    st.subheader("💼 登録済み企業データ")
    
    companies = db.get_companies(50)
    if companies:
        # フィルター
        col1, col2 = st.columns(2)
        with col1:
            country_filter = st.selectbox("国フィルター", 
                                        ["All"] + list(set(c.get('country', 'Unknown') for c in companies)))
        with col2:
            industry_filter = st.selectbox("業界フィルター", 
                                         ["All"] + list(set(c.get('industry', 'Unknown') for c in companies)))
        
        # フィルター適用
        filtered_companies = companies
        if country_filter != "All":
            filtered_companies = [c for c in filtered_companies if c.get('country') == country_filter]
        if industry_filter != "All":
            filtered_companies = [c for c in filtered_companies if c.get('industry') == industry_filter]
        
        # データ表示
        df = pd.DataFrame(filtered_companies)
        if not df.empty:
            df = df[['company_name', 'email', 'industry', 'country', 'updated_at']]
            st.dataframe(df, use_container_width=True)
        
        st.info(f"表示中: {len(filtered_companies)}社 / 総数: {len(companies)}社")
    else:
        st.warning("⚠️ 登録済み企業データがありません")


def render_csv_import():
    """CSV一括インポート機能"""
    st.subheader("📥 CSV一括インポート")
    
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=['csv'])
    if uploaded_file is not None:
        try:
            import_df = pd.read_csv(uploaded_file)
            st.write("**アップロードデータプレビュー:**")
            st.dataframe(import_df.head())
            
            # カラムマッピング
            st.write("**カラムマッピング:**")
            col1, col2 = st.columns(2)
            
            required_fields = ['company_name', 'email', 'description']
            optional_fields = ['website', 'phone', 'industry', 'country']
            
            mapping = {}
            
            with col1:
                st.write("**必須フィールド:**")
                for field in required_fields:
                    mapping[field] = st.selectbox(
                        f"{field} ← CSV列", 
                        [""] + list(import_df.columns),
                        key=f"map_{field}"
                    )
            
            with col2:
                st.write("**オプションフィールド:**")
                for field in optional_fields:
                    mapping[field] = st.selectbox(
                        f"{field} ← CSV列",
                        [""] + list(import_df.columns),
                        key=f"map_{field}"
                    )
            
            # インポート実行
            if all(mapping[field] for field in required_fields):
                if st.button("📥 データをインポート"):
                    db = IntegratedEmailDatabase()
                    import_count = 0
                    
                    for _, row in import_df.iterrows():
                        company_data = {
                            'company_id': f"IMPORT_{int(time.time())}_{import_count}",
                        }
                        
                        for field, csv_col in mapping.items():
                            if csv_col:
                                company_data[field] = str(row[csv_col]).strip()
                        
                        if company_data.get('company_name') and company_data.get('email'):
                            db.save_company(company_data)
                            import_count += 1
                    
                    st.success(f"✅ {import_count}社のデータをインポートしました")
                    st.rerun()
            else:
                st.warning("⚠️ 必須フィールド（company_name, email, description）のマッピングを完了してください")
                
        except Exception as e:
            st.error(f"❌ CSVインポートエラー: {str(e)}")
