"""
ENRデータ処理・スコアリングモジュール
fusion_crm_main.pyから抽出
"""

import pandas as pd
from .constants import PICOCELA_KEYWORDS, IMPORT_SETTINGS

class ENRDataProcessor:
    """ENRデータ処理クラス"""
    
    @staticmethod
    def calculate_picocela_relevance(company_data):
        """PicoCELA関連度スコア計算"""
        score = 0
        text_fields = [
            str(company_data.get('company_name', '')),
            str(company_data.get('website_url', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for keyword in PICOCELA_KEYWORDS:
            if keyword.lower() in full_text:
                score += 10
        
        return min(score, 100)
    
    @staticmethod
    def detect_wifi_requirement(company_data):
        """WiFi需要判定"""
        wifi_indicators = [
            'wifi', 'wireless', 'network', 'connectivity', 
            'iot', 'smart building', 'construction tech'
        ]
        
        text_fields = [
            str(company_data.get('company_name', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for indicator in wifi_indicators:
            if indicator in full_text:
                return True
        return False
    
    @staticmethod
    def calculate_priority_score(company_data):
        """優先度スコア計算"""
        relevance = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        
        priority = relevance
        if wifi_required:
            priority += 50
        
        return min(priority, 150)


class DataImportProcessor:
    """データインポート処理クラス"""
    
    @staticmethod
    def suggest_column_mapping(file_columns):
        """カラムマッピングの自動提案"""
        mapping_rules = IMPORT_SETTINGS['mapping_rules']
        suggestions = {}
        
        for fusion_col, patterns in mapping_rules.items():
            for file_col in file_columns:
                if any(pattern.lower() in file_col.lower() for pattern in patterns):
                    suggestions[fusion_col] = file_col
                    break
        
        return suggestions
    
    @staticmethod
    def detect_wifi_need_from_data(company_data):
        """データからWiFi需要を判定"""
        wifi_indicators = IMPORT_SETTINGS['wifi_indicators']
        
        text_fields = [
            company_data.get('company_name', ''),
            company_data.get('notes', ''),
            company_data.get('industry', '')
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for indicator in wifi_indicators:
            if indicator in full_text:
                return 1
        
        return 0
    
    @staticmethod
    def calculate_picocela_relevance_from_data(company_data):
        """データからPicoCELA関連度を計算"""
        score = 0
        keywords = IMPORT_SETTINGS['scoring_keywords']
        
        text_fields = [
            company_data.get('company_name', ''),
            company_data.get('notes', ''),
            company_data.get('industry', '')
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for keyword, points in keywords.items():
            if keyword in full_text:
                score += points
        
        return min(score, 100)
    
    @staticmethod
    def calculate_priority_from_data(company_data):
        """優先度スコアを計算"""
        base_score = company_data.get('picocela_relevance_score', 0)
        
        if company_data.get('wifi_required', 0) == 1:
            base_score += 50
        
        # メールアドレスがある場合のボーナス
        if company_data.get('email'):
            base_score += 10
        
        # ウェブサイトがある場合のボーナス
        if company_data.get('website_url'):
            base_score += 5
        
        return min(base_score, 150)
    
    @staticmethod
    def create_import_preview(df, mapping, auto_wifi_detection, auto_picocela_scoring):
        """インポートプレビューデータの作成"""
        preview_data = []
        
        for _, row in df.iterrows():
            company_data = {}
            
            # マッピングに基づいてデータを変換
            for fusion_col, file_col in mapping.items():
                if file_col in df.columns:
                    value = row[file_col]
                    if pd.isna(value):
                        value = ''
                    company_data[fusion_col] = str(value)
            
            # 必須フィールドの確認
            if not company_data.get('company_name'):
                continue
            
            # WiFi需要の自動判定
            if auto_wifi_detection:
                company_data['wifi_required'] = DataImportProcessor.detect_wifi_need_from_data(company_data)
            else:
                company_data['wifi_required'] = 0
            
            # PicoCELA関連度の自動計算
            if auto_picocela_scoring:
                company_data['picocela_relevance_score'] = DataImportProcessor.calculate_picocela_relevance_from_data(company_data)
            else:
                company_data['picocela_relevance_score'] = 0
            
            # 優先度スコア計算
            company_data['priority_score'] = DataImportProcessor.calculate_priority_from_data(company_data)
            
            # デフォルト値設定
            company_data['sales_status'] = 'New'
            company_data['source'] = company_data.get('source', 'Data Import')
            
            preview_data.append(company_data)
        
        return pd.DataFrame(preview_data)
    
    @staticmethod
    def show_data_quality_analysis(df):
        """データ品質分析の表示"""
        import streamlit as st
        
        st.subheader("🔍 データ品質分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 基本統計**")
            st.metric("総行数", len(df))
            st.metric("列数", len(df.columns))
            
            # 欠損値チェック
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                st.markdown("**⚠️ 欠損値**")
                for col, count in missing_data[missing_data > 0].items():
                    st.text(f"• {col}: {count}行 ({count/len(df)*100:.1f}%)")
            else:
                st.success("✅ 欠損値なし")
        
        with col2:
            st.markdown("**📈 データ分析**")
            
            # メールアドレスの有効性
            if 'Email Address' in df.columns or any('email' in col.lower() for col in df.columns):
                email_col = next((col for col in df.columns if 'email' in col.lower()), None)
                if email_col:
                    valid_emails = df[email_col].notna().sum()
                    st.metric("有効メールアドレス", f"{valid_emails}/{len(df)}")
            
            # WiFi関連企業の予測
            text_columns = df.select_dtypes(include=['object']).columns
            wifi_count = 0
            for col in text_columns:
                wifi_count += df[col].astype(str).str.contains('wifi|wireless|network', case=False, na=False).sum()
            
            if wifi_count > 0:
                st.metric("WiFi関連キーワード検出", f"{wifi_count}件")
