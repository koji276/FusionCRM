"""
FusionCRM - 企業管理モジュール（Google Sheets専用版）
PicoCELA社向け建設業界特化CRMシステム
"""

import pandas as pd
from datetime import datetime
import requests

# 拡張ステータス定義（既存のまま）
SALES_STATUS = {
    'New': '新規企業',
    'Contacted': '初回連絡済み', 
    'Replied': '返信あり',
    'Engaged': '継続対話中',
    'Qualified': '有望企業確定',
    'Proposal': '提案書提出済み',
    'Negotiation': '契約交渉中',
    'Won': '受注成功',
    'Lost': '失注',
    'Dormant': '休眠中'
}

# ステータス優先度
STATUS_PRIORITY = {
    'Won': 10, 'Negotiation': 9, 'Proposal': 8, 'Qualified': 7,
    'Engaged': 6, 'Replied': 5, 'Contacted': 4, 'New': 3,
    'Dormant': 2, 'Lost': 1
}

# PicoCELA関連キーワード
PICOCELA_KEYWORDS = [
    'network', 'mesh', 'wireless', 'wifi', 'connectivity',
    'iot', 'smart', 'digital', 'automation', 'sensor', 'ai',
    'construction', 'building', 'site', 'industrial', 'management',
    'platform', 'solution', 'integration', 'control', 'monitoring',
    'infrastructure', 'communication', 'technology', 'system',
    'device', 'data', 'cloud', 'edge', 'real-time', 'remote'
]

class ENRDataProcessor:
    """ENRデータ処理・分析クラス（変更なし）"""
    
    @staticmethod
    def calculate_picocela_relevance(company_data):
        """PicoCELA関連度スコア計算（ENR企業向け最適化）"""
        score = 0
        text_fields = [
            str(company_data.get('company_name', '')),
            str(company_data.get('website_url', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', '')),
            str(company_data.get('description', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        # キーワードマッチング
        matched_keywords = []
        for keyword in PICOCELA_KEYWORDS:
            if keyword.lower() in full_text:
                score += 10
                matched_keywords.append(keyword)
        
        # 建設業界ボーナス
        construction_terms = ['construction', 'building', 'contractor', 'engineering']
        for term in construction_terms:
            if term in full_text:
                score += 5
        
        return min(score, 100), matched_keywords
    
    @staticmethod
    def detect_wifi_requirement(company_data):
        """WiFi・ワイヤレス需要判定（建設業界特化）"""
        wifi_indicators = [
            'wifi', 'wireless', 'network', 'connectivity', 'mesh',
            'iot', 'smart building', 'construction tech', 'digital construction',
            'site management', 'remote monitoring', 'sensor network',
            'communication system', 'field connectivity'
        ]
        
        text_fields = [
            str(company_data.get('company_name', '')),
            str(company_data.get('notes', '')),
            str(company_data.get('industry', '')),
            str(company_data.get('description', ''))
        ]
        
        full_text = ' '.join(text_fields).lower()
        
        for indicator in wifi_indicators:
            if indicator in full_text:
                return True
        
        return False
    
    @staticmethod
    def calculate_priority_score(company_data):
        """戦略的優先度スコア計算"""
        relevance, _ = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        
        priority = relevance
        
        # WiFi必要企業に大幅ボーナス
        if wifi_required:
            priority += 50
        
        # ENR企業ボーナス
        if company_data.get('source', '').lower().find('enr') >= 0:
            priority += 20
        
        # 企業規模による調整
        employees = str(company_data.get('employees_count', '')).lower()
        if any(size in employees for size in ['large', '1000+', 'enterprise']):
            priority += 15
        elif any(size in employees for size in ['medium', '100-1000', 'mid']):
            priority += 10
        
        return min(priority, 150)
    
    @staticmethod
    def enr_strategic_analysis(companies_df):
        """ENRデータ戦略的分析"""
        if companies_df.empty:
            return {}
        
        analysis = {
            'total_companies': len(companies_df),
            'wifi_required_count': len(companies_df[companies_df['wifi_required'] == 1]),
            'high_priority_count': len(companies_df[companies_df['priority_score'] >= 100]),
            'avg_relevance_score': companies_df['picocela_relevance_score'].mean(),
            'top_targets': companies_df.nlargest(10, 'priority_score')[
                ['company_name', 'priority_score', 'wifi_required', 'picocela_relevance_score']
            ].to_dict('records')
        }
        
        # ステータス別分析
        status_analysis = companies_df.groupby('sales_status').agg({
            'company_id': 'count',
            'picocela_relevance_score': 'mean',
            'priority_score': 'mean',
            'wifi_required': 'sum'
        }).round(2)
        
        analysis['status_breakdown'] = status_analysis.to_dict('index')
        
        return analysis

class CompanyManager:
    """企業管理クラス（Google Sheets専用版）"""
    
    def __init__(self, gas_url):
        self.gas_url = gas_url
        self.ensure_database_schema()
    
    def _call_api(self, action, method='GET', data=None):
        """Google Apps Script API呼び出し"""
        try:
            if method == 'GET':
                response = requests.get(f"{self.gas_url}?action={action}")
            else:
                response = requests.post(
                    self.gas_url,
                    json={"action": action, **data} if data else {"action": action},
                    headers={'Content-Type': 'application/json'}
                )
            
            result = response.json()
            if not result.get('success'):
                raise Exception(result.get('error', 'Unknown error'))
            
            return result
        except Exception as e:
            print(f"API呼び出しエラー（{action}）: {str(e)}")
            return None
    
    def ensure_database_schema(self):
        """データベーススキーマ確保"""
        result = self._call_api('init_database', method='POST')
        if result and result.get('spreadsheet_url'):
            print(f"Google Sheets準備完了: {result['spreadsheet_url']}")
    
    def add_company(self, company_data, user_id="system"):
        """企業追加（ENR最適化・自動分析付き）"""
        # PicoCELA関連度とWiFi需要を自動計算
        relevance_score, matched_keywords = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        priority_score = ENRDataProcessor.calculate_priority_score(company_data)
        
        # データ準備
        company_data['picocela_relevance_score'] = relevance_score
        company_data['keywords_matched'] = ','.join(matched_keywords)
        company_data['wifi_required'] = 1 if wifi_required else 0
        company_data['priority_score'] = priority_score
        company_data['status'] = company_data.get('status', 'New')
        company_data['source'] = company_data.get('source', 'Manual')
        
        # API呼び出し
        result = self._call_api('add_company', method='POST', data={'company': company_data})
        
        if result:
            return result.get('company_id')
        return None
    
    def update_status(self, company_id, new_status, user_id, reason="", notes="", next_steps=""):
        """ステータス更新（履歴記録・次のアクション管理）"""
        # 次のアクション推奨設定
        next_action = self._suggest_next_action(new_status)
        
        # API呼び出し
        result = self._call_api('update_status', method='POST', data={
            'company_id': company_id,
            'new_status': new_status,
            'note': f"{reason} - {notes} - 次のアクション: {next_action}"
        })
        
        if result:
            return {
                'success': True,
                'message': f"ステータスを{SALES_STATUS.get(new_status, new_status)}に更新しました",
                'next_action': next_action
            }
        
        return {'success': False, 'message': 'ステータス更新に失敗しました'}
    
    def _suggest_next_action(self, status):
        """ステータス別次アクション推奨"""
        action_map = {
            'New': '初回メール送信',
            'Contacted': 'フォローアップメール（1週間後）',
            'Replied': 'オンラインミーティング設定',
            'Engaged': '現場訪問・詳細ニーズ確認',
            'Qualified': '提案書作成・カスタマイズ',
            'Proposal': '社内検討状況確認',
            'Negotiation': '条件調整・最終提案',
            'Won': '契約履行・導入支援',
            'Lost': '関係維持・将来機会確認',
            'Dormant': '再活性化キャンペーン'
        }
        return action_map.get(status, '')
    
    def get_companies_by_criteria(self, status=None, wifi_required=None, 
                                min_priority=0, min_relevance=0, limit=None):
        """条件別企業取得（戦略的フィルタリング）"""
        result = self._call_api('get_companies')
        
        if result and result.get('companies'):
            df = pd.DataFrame(result['companies'])
            
            # 数値型に変換
            for col in ['priority_score', 'picocela_relevance_score', 'wifi_required']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # フィルタリング
            df = df[df['priority_score'] >= min_priority]
            df = df[df['picocela_relevance_score'] >= min_relevance]
            
            if status:
                if isinstance(status, list):
                    df = df[df['sales_status'].isin(status)]
                else:
                    df = df[df['sales_status'] == status]
            
            if wifi_required is not None:
                df = df[df['wifi_required'] == wifi_required]
            
            # ソート
            df = df.sort_values(['priority_score', 'updated_at'], ascending=[False, False])
            
            if limit:
                df = df.head(limit)
            
            return df
        
        return pd.DataFrame()
    
    def get_strategic_pipeline(self):
        """戦略的パイプライン分析"""
        result = self._call_api('get_analytics')
        
        if result and result.get('analytics'):
            analytics = result['analytics']
            
            # パイプラインデータ作成
            pipeline_data = []
            for status, count in analytics.get('status_breakdown', {}).items():
                pipeline_data.append({
                    'status': status,
                    'company_count': count,
                    'avg_relevance': 0,  # TODO: APIで平均値も返すように
                    'avg_priority': 0,
                    'wifi_companies': 0,
                    'high_priority_count': 0
                })
            
            pipeline_df = pd.DataFrame(pipeline_data)
            
            # WiFi戦略企業取得
            wifi_companies = self.get_companies_by_criteria(wifi_required=True, limit=20)
            
            return {
                'pipeline': pipeline_df,
                'wifi_strategy_targets': wifi_companies,
                'total_companies': analytics.get('total_companies', 0),
                'wifi_required_total': sum(1 for k, v in analytics.get('wifi_needs_breakdown', {}).items() 
                                         if k in ['High', 'Critical'])
            }
        
        return {
            'pipeline': pd.DataFrame(),
            'wifi_strategy_targets': pd.DataFrame(),
            'total_companies': 0,
            'wifi_required_total': 0
        }
    
    def get_company_details(self, company_id):
        """企業詳細情報取得（履歴付き）"""
        # 企業基本情報
        companies_result = self._call_api('get_companies')
        
        if companies_result and companies_result.get('companies'):
            companies = companies_result['companies']
            company = next((c for c in companies if c.get('company_id') == company_id), None)
            
            if company:
                # ステータス履歴取得
                history_result = self._call_api(f'get_history&company_id={company_id}')
                history = history_result.get('history', []) if history_result else []
                
                return {
                    'company': company,
                    'status_history': history
                }
        
        return None

# 使用例とテスト関数
def test_company_management():
    """テスト関数"""
    # Google Apps Script URLを設定
    gas_url = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
    
    cm = CompanyManager(gas_url)
    
    # テスト企業データ
    test_company = {
        'company_name': 'Test Construction Tech',
        'email': 'contact@testconstruction.com',
        'industry': 'Construction Technology',
        'description': 'IoT and wireless solutions for construction sites',
        'source': 'ENR Import'
    }
    
    # 企業追加テスト
    company_id = cm.add_company(test_company, 'test_user')
    print(f"Added company ID: {company_id}")
    
    # ステータス更新テスト
    if company_id:
        result = cm.update_status(
            company_id, 'Contacted', 'test_user', 
            '初回メール送信完了', 'WiFi需要企業として確認'
        )
        print(f"Status update result: {result}")
    
    # 戦略的分析テスト
    pipeline = cm.get_strategic_pipeline()
    print(f"Pipeline analysis: {pipeline}")

if __name__ == "__main__":
    test_company_management()
