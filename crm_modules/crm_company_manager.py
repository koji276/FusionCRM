"""
企業管理モジュール
fusion_crm_main.pyから抽出
"""

import streamlit as st
import pandas as pd
from .data_processor import ENRDataProcessor

class CompanyManager:
    """企業管理クラス（Google Sheets専用版）"""
    
    def __init__(self, api):
        self.api = api
        self._ensure_database()
    
    def _ensure_database(self):
        """データベース初期化確認"""
        result = self.api.call_api('init_database', method='POST')
        if result and result.get('success') and result.get('spreadsheet_url'):
            st.session_state.spreadsheet_url = result['spreadsheet_url']
    
    def add_company(self, company_data, user_id="system"):
        """企業追加"""
        try:
            # PicoCELA関連度とWiFi需要を自動計算
            relevance_score = ENRDataProcessor.calculate_picocela_relevance(company_data)
            wifi_required = 1 if ENRDataProcessor.detect_wifi_requirement(company_data) else 0
            priority_score = ENRDataProcessor.calculate_priority_score(company_data)
            
            company_data['picocela_relevance_score'] = relevance_score
            company_data['wifi_required'] = wifi_required
            company_data['priority_score'] = priority_score
            company_data['sales_status'] = company_data.get('sales_status', 'New')
            
            result = self.api.call_api('add_company', method='POST', data={'company': company_data})
            
            if result and result.get('success'):
                return result.get('company_id')
            return None
            
        except Exception as e:
            st.error(f"企業追加エラー: {str(e)}")
            return None
    
    def update_status(self, company_id, new_status, user_id, reason="", notes=""):
        """ステータス更新"""
        try:
            result = self.api.call_api('update_status', method='POST', data={
                'company_id': company_id,
                'new_status': new_status,
                'note': f"{reason} - {notes}" if reason else notes
            })
            
            return result and result.get('success')
            
        except Exception as e:
            st.error(f"ステータス更新エラー: {str(e)}")
            return False
    
    def get_companies_by_status(self, status=None, wifi_required=None):
        """ステータス別企業取得"""
        try:
            result = self.api.call_api('get_companies')
            
            if result and result.get('success') and result.get('companies'):
                df = pd.DataFrame(result['companies'])
                
                # 安全なフィルタリング（カラムの存在確認）
                if status and not df.empty and 'sales_status' in df.columns:
                    df = df[df['sales_status'] == status]
                
                if wifi_required is not None and not df.empty and 'wifi_required' in df.columns:
                    df = df[df['wifi_required'] == wifi_required]
                
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"企業データ取得エラー: {str(e)}")
            return pd.DataFrame()
    
    def get_all_companies(self):
        """全企業取得"""
        return self.get_companies_by_status()


class EmailCampaignManager:
    """メールキャンペーン管理（Google Sheets版）"""
    
    def __init__(self, api):
        self.api = api
        self.email_available = True
        self.smtp_settings = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True
        }
    
    def send_single_email(self, to_email, subject, body, from_email, from_password, from_name="PicoCELA Inc."):
        """単一メール送信"""
        try:
            import smtplib
            import ssl
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_settings['smtp_server'], self.smtp_settings['smtp_port']) as server:
                if self.smtp_settings['use_tls']:
                    server.starttls(context=context)
                server.login(from_email, from_password)
                server.send_message(msg)
            
            return True, "メール送信成功"
            
        except Exception as e:
            return False, f"メール送信エラー: {str(e)}"
    
    def get_email_templates(self):
        """メールテンプレート"""
        from .constants import EMAIL_TEMPLATES
        return EMAIL_TEMPLATES
    
    def add_email_distribution_link(self):
        """メール配信システムへのリンクボタンを追加"""
        import os
        
        st.markdown("---")
        st.subheader("📧 メール配信システム")
        
        # Gmail設定確認
        gmail_configured = os.path.exists('config/gmail_config.json')
        
        if gmail_configured:
            st.success("✅ Gmail設定済み - メール配信システム利用可能")
        else:
            st.warning("⚠️ Gmail設定が必要です（メール配信システムで設定できます）")
        
        # 実際のStreamlit CloudのURLにリンク
        email_system_url = "https://aiplusagents-4j4kitm3mapdvaxkhi3npk.streamlit.app/"
        
        # リンクボタン
        st.markdown(f"""
        <a href="{email_system_url}" target="_blank">
            <button style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8