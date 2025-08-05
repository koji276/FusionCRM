import streamlit as st
import requests
import json

st.title("🔧 GAS接続テスト - シンプル版")

# 新しいGAS v16 URL
api_url = "https://script.google.com/macros/s/AKfycbx3e5TpdzcsBueF68sOonUJwd9j2-zR5OEZoqGZ0-0E57vYutCq5ivl3QJIUfKQ6vCUkw/exec"

st.write("### テスト1: GAS接続確認")
if st.button("🧪 テスト接続"):
    try:
        response = requests.get(
            api_url,
            params={"action": "test"},
            timeout=30
        )
        
        st.write(f"**Status Code**: {response.status_code}")
        st.write(f"**Raw Response**: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ テスト接続成功!")
            st.json(data)
        else:
            st.error(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ エラー: {str(e)}")

st.write("### テスト2: 企業データ取得")
if st.button("📊 企業データ取得"):
    try:
        response = requests.get(
            api_url,
            params={"action": "get_companies"},
            timeout=30
        )
        
        st.write(f"**Status Code**: {response.status_code}")
        st.write(f"**Raw Response**: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ データ取得成功!")
            st.json(data)
            
            if data.get('companies'):
                st.write(f"**取得企業数**: {len(data['companies'])}社")
                for i, company in enumerate(data['companies'][:3]):
                    st.write(f"**企業{i+1}**: {company.get('company_name', 'N/A')}")
            else:
                st.warning("⚠️ companiesキーが見つかりません")
        else:
            st.error(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ エラー: {str(e)}")

st.write("### デバッグ情報")
st.write(f"**使用URL**: {api_url}")
st.write("**期待されるレスポンス形式**:")
st.code("""
{
  "success": true,
  "companies": [...],
  "count": 1,
  "timestamp": "..."
}
""")
