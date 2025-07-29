# Google Sheets API接続修正版 - CORS対応
def get_google_sheets_data():
    """Google SheetsからCRMデータを取得する修正版"""
    try:
        st.info("🔄 Google Sheetsからデータを取得中...")
        
        # Google Apps Script URL
        api_url = "https://script.google.com/macros/s/AKfycbykUlinwW4oVA08Uo1pqbhHsBWtVM1SMFoo34OMT9kRJ0tRVccsaydlmV5lxjzTrGCu/exec"
        
        # ヘッダーを追加してCORS問題を回避
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # APIリクエスト実行（タイムアウト短縮）
        response = requests.get(
            api_url,
            params={"action": "get_companies"},
            headers=headers,
            timeout=30,  # タイムアウトを30秒に延長
            verify=True  # SSL証明書の検証を有効化
        )
        
        st.info(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                st.info(f"📊 Raw API Response: {str(data)[:200]}...")  # デバッグ用
                
                if data.get('success') and data.get('data'):
                    companies = data['data']
                    st.success(f"✅ Google Sheets連携成功！{len(companies)}社のデータを取得しました")
                    return companies, True
                else:
                    st.warning(f"⚠️ API Response Structure Issue: {data}")
                    return [], False
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON Parse Error: {str(e)}")
                st.error(f"Raw Response: {response.text[:500]}...")
                return [], False
        else:
            st.error(f"❌ HTTP Error: {response.status_code}")
            st.error(f"Response Headers: {dict(response.headers)}")
            return [], False
            
    except requests.exceptions.Timeout:
        st.warning("⏰ Google Sheets API接続がタイムアウトしました（30秒）")
        return [], False
    except requests.exc
