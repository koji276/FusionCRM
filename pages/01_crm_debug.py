# pages/01_crm_debug.py - データ構造デバッグ版
# Updated: 2025-07-29 - Debug actual Google Sheets data structure
# Complete data structure analysis

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# ========================================
# デバッグメッセージ
# ========================================
st.error("🚨 デバッグ版: Google Sheetsの実際のデータ構造を詳細分析")
st.success("✅ データ構造完全解析版")

# ========================================
# CRM管理システム - デバッグ版
# ========================================

st.title("🏢 CRM管理システム - デバッグ版")
st.caption("Google Sheetsデータ構造の完全解析")

# ========================================
# Google Sheets データ取得・詳細分析
# ========================================

st.header("🔍 Google Sheetsデータ構造解析")

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
        # 生のレスポンステキストを表示
        st.subheader("📄 生のAPIレスポンス（最初の1000文字）")
        raw_text = response.text
        st.text(raw_text[:1000] + "..." if len(raw_text) > 1000 else raw_text)
        
        try:
            data = response.json()
            
            # JSONの基本構造を表示
            st.subheader("📊 JSON基本構造")
            st.write(f"success: {data.get('success')}")
            st.write(f"data exists: {bool(data.get('data'))}")
            st.write(f"data type: {type(data.get('data'))}")
            st.write(f"data length: {len(data.get('data', []))}")
            
            if data.get('success') and data.get('data'):
                companies = data['data']
                
                # 最初の企業データの完全構造を表示
                st.subheader("🏢 最初の企業データの完全構造")
                if companies:
                    first_company = companies[0]
                    st.write("**全フィールド一覧:**")
                    
                    for key, value in first_company.items():
                        st.write(f"• **{key}**: `{type(value).__name__}` = {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                    
                    # JSONとして整形表示
                    st.subheader("📋 最初の企業データ（JSON形式）")
                    st.json(first_company)
                    
                    # 2番目の企業データも表示（比較用）
                    if len(companies) > 1:
                        st.subheader("🏢 2番目の企業データ（比較用）")
                        second_company = companies[1]
                        st.json(second_company)
                
                # 全企業のキー一覧を収集
                st.subheader("🔑 全企業で使用されているキー一覧")
                all_keys = set()
                for company in companies:
                    all_keys.update(company.keys())
                
                sorted_keys = sorted(list(all_keys))
                st.write(f"**総キー数**: {len(sorted_keys)}")
                
                for i, key in enumerate(sorted_keys):
                    # 各キーがどれだけの企業で使用されているかカウント
                    usage_count = sum(1 for company in companies if key in company and company[key] is not None and str(company[key]).strip() != '')
                    st.write(f"{i+1:2d}. **{key}** - 使用企業数: {usage_count}/{len(companies)}")
                
                # データ型分析
                st.subheader("📈 データ型分析")
                key_types = {}
                for company in companies:
                    for key, value in company.items():
                        if key not in key_types:
                            key_types[key] = set()
                        key_types[key].add(type(value).__name__)
                
                for key, types in sorted(key_types.items()):
                    st.write(f"• **{key}**: {', '.join(types)}")
                
                # サンプル値表示
                st.subheader("💼 各フィールドのサンプル値")
                for key in sorted_keys[:10]:  # 最初の10個のキー
                    sample_values = []
                    for company in companies[:3]:  # 最初の3社
                        if key in company and company[key] is not None:
                            value = str(company[key])[:50] + ('...' if len(str(company[key])) > 50 else '')
                            sample_values.append(value)
                    
                    if sample_values:
                        st.write(f"**{key}**: {' | '.join(sample_values)}")
                
                # ========================================
                # 簡易ダッシュボード（現在のロジック）
                # ========================================
                
                st.header("📊 現在のロジックでの簡易ダッシュボード")
                
                # 現在の正規化ロジックを適用
                normalized_companies = []
                for company in companies:
                    normalized = {
                        'ID': company.get('company_id') or company.get('ID') or f"ID_{len(normalized_companies)+1}",
                        '企業名': company.get('company_name') or company.get('企業名') or 'N/A',
                        'ステータス': company.get('sales_status') or company.get('ステータス') or 'New',
                        'PicoCELAスコア': company.get('picoCELA_relevance') or company.get('PicoCELAスコア') or 0,
                        'WiFi需要': company.get('wifi_needs') or company.get('WiFi需要') or 'Unknown',
                        'メール': company.get('email') or company.get('メール') or '',
                        '備考': company.get('description') or company.get('備考') or ''
                    }
                    normalized_companies.append(normalized)
                
                # 正規化結果表示
                st.subheader("🔄 正規化後のデータ")
                for i, company in enumerate(normalized_companies[:3]):
                    st.write(f"**企業 {i+1}:**")
                    for key, value in company.items():
                        st.write(f"  • {key}: {value}")
                    st.write("---")
                
                # データフレーム表示
                if normalized_companies:
                    st.subheader("📋 データフレーム表示")
                    df = pd.DataFrame(normalized_companies)
                    st.dataframe(df, use_container_width=True)
                
                google_sheets_success = True
                
            else:
                st.error("❌ データの 'success' フラグが False または 'data' が空です")
                st.json(data)
                google_sheets_success = False
                
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON解析エラー: {str(e)}")
            st.text("Raw response:")
            st.text(response.text[:500])
            google_sheets_success = False
            
    else:
        st.error(f"❌ HTTP Error: {response.status_code}")
        st.text(f"Response: {response.text}")
        google_sheets_success = False

except Exception as e:
    st.error(f"❌ 接続エラー: {str(e)}")
    google_sheets_success = False

# ========================================
# 推奨される修正案
# ========================================

st.header("💡 推奨される修正案")

if google_sheets_success:
    st.success("✅ Google Sheets接続成功！上記のデータ構造分析を基に正確な正規化ロジックを作成できます。")
    
    st.info("""
    **次のステップ:**
    1. 上記の「全フィールド一覧」を確認
    2. 実際に使用されているキー名を特定
    3. データ型を確認
    4. 正規化ロジックを修正
    """)
    
else:
    st.error("❌ Google Sheets接続失敗。API設定を確認してください。")

# ========================================
# キー名マッピング推測
# ========================================

st.header("🔍 推測されるキー名マッピング")

expected_mappings = {
    "企業名": ["company_name", "name", "企業名", "会社名"],
    "メール": ["email", "mail", "メール", "メールアドレス"],
    "ステータス": ["sales_status", "status", "ステータス", "状態"],
    "PicoCELAスコア": ["picoCELA_relevance", "picocela_relevance", "relevance", "score", "スコア"],
    "WiFi需要": ["wifi_needs", "wifi_requirement", "WiFi需要", "需要"],
    "業界": ["industry", "sector", "業界", "分野"],
    "ウェブサイト": ["website", "website_url", "url", "ウェブサイト"],
    "備考": ["description", "notes", "memo", "備考", "説明"]
}

for japanese_key, possible_keys in expected_mappings.items():
    st.write(f"**{japanese_key}**: {' または '.join(possible_keys)}")

st.info("上記のデータ構造分析結果と照らし合わせて、正確なキー名を特定してください。")
