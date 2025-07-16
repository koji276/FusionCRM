"""
FusionCRM - 企業管理モジュール（拡張ステータス対応）
PicoCELA社向け建設業界特化CRMシステム
"""

import sqlite3
import pandas as pd
from datetime import datetime

# 拡張ステータス定義
SALES_STATUS = {
    'New': '新規企業',
    'Contacted': '初回連絡済み', 
    'Replied': '返信あり',
    'Engaged': '継続対話中',      # 🆕 オンラインミーティング段階
    'Qualified': '有望企業確定',
    'Proposal': '提案書提出済み',  # 🆕 提案段階
    'Negotiation': '契約交渉中',  # 🆕 条件調整段階
    'Won': '受注成功',            # 🆕 成約
    'Lost': '失注',
    'Dormant': '休眠中'           # 🆕 再活性化対象
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
    """ENRデータ処理・分析クラス"""
    
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
        status_analysis = companies_df.groupby('status').agg({
            'id': 'count',
            'picocela_relevance_score': 'mean',
            'priority_score': 'mean',
            'wifi_required': 'sum'
        }).round(2)
        
        analysis['status_breakdown'] = status_analysis.to_dict('index')
        
        return analysis

class CompanyManager:
    """企業管理クラス（拡張ステータス・ENR最適化対応）"""
    
    def __init__(self, db_name="fusion_crm.db"):
        self.db_name = db_name
        self.ensure_database_schema()
    
    def ensure_database_schema(self):
        """データベーススキーマ確保"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # 企業テーブル（拡張フィールド）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                website_url TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                industry TEXT,
                employees_count TEXT,
                revenue_range TEXT,
                status TEXT DEFAULT 'New',
                picocela_relevance_score INTEGER DEFAULT 0,
                keywords_matched TEXT,
                wifi_required BOOLEAN DEFAULT 0,
                priority_score INTEGER DEFAULT 0,
                source TEXT DEFAULT 'Manual',
                description TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact_date TIMESTAMP,
                next_action TEXT,
                next_action_date TIMESTAMP,
                contact_person TEXT,
                position TEXT,
                decision_maker BOOLEAN DEFAULT 0
            )
        ''')
        
        # ステータス履歴テーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY,
                company_id INTEGER,
                old_status TEXT,
                new_status TEXT,
                changed_by TEXT,
                change_reason TEXT,
                notes TEXT,
                action_taken TEXT,
                next_steps TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # 既存カラム追加（安全処理）
        self._add_missing_columns(cursor)
        
        conn.commit()
        conn.close()
    
    def _add_missing_columns(self, cursor):
        """既存データベースに新カラム追加"""
        new_columns = [
            ('companies', 'wifi_required', 'BOOLEAN DEFAULT 0'),
            ('companies', 'priority_score', 'INTEGER DEFAULT 0'),
            ('companies', 'source', 'TEXT DEFAULT "Manual"'),
            ('companies', 'description', 'TEXT'),
            ('companies', 'notes', 'TEXT'),
            ('companies', 'last_contact_date', 'TIMESTAMP'),
            ('companies', 'next_action', 'TEXT'),
            ('companies', 'next_action_date', 'TIMESTAMP'),
            ('companies', 'contact_person', 'TEXT'),
            ('companies', 'position', 'TEXT'),
            ('companies', 'decision_maker', 'BOOLEAN DEFAULT 0')
        ]
        
        for table, column, definition in new_columns:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
            except sqlite3.OperationalError:
                # カラムが既に存在する場合は無視
                pass
    
    def add_company(self, company_data, user_id="system"):
        """企業追加（ENR最適化・自動分析付き）"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # PicoCELA関連度とWiFi需要を自動計算
        relevance_score, matched_keywords = ENRDataProcessor.calculate_picocela_relevance(company_data)
        wifi_required = ENRDataProcessor.detect_wifi_requirement(company_data)
        priority_score = ENRDataProcessor.calculate_priority_score(company_data)
        
        cursor.execute('''
            INSERT INTO companies (
                company_name, website_url, email, phone, address, 
                industry, employees_count, revenue_range, status,
                picocela_relevance_score, keywords_matched, wifi_required, 
                priority_score, source, description, notes,
                contact_person, position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            company_data.get('company_name'),
            company_data.get('website_url'),
            company_data.get('email'),
            company_data.get('phone'),
            company_data.get('address'),
            company_data.get('industry'),
            company_data.get('employees_count'),
            company_data.get('revenue_range'),
            company_data.get('status', 'New'),
            relevance_score,
            ','.join(matched_keywords),
            wifi_required,
            priority_score,
            company_data.get('source', 'Manual'),
            company_data.get('description', ''),
            company_data.get('notes', ''),
            company_data.get('contact_person', ''),
            company_data.get('position', '')
        ))
        
        company_id = cursor.lastrowid
        
        # ステータス履歴記録
        self._log_status_change(
            cursor, company_id, None, 'New', user_id, 
            "企業登録", f"自動分析完了 - 関連度:{relevance_score}, WiFi需要:{wifi_required}"
        )
        
        conn.commit()
        conn.close()
        return company_id
    
    def update_status(self, company_id, new_status, user_id, reason="", notes="", next_steps=""):
        """ステータス更新（履歴記録・次のアクション管理）"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # 現在のステータス取得
        cursor.execute('SELECT status, company_name FROM companies WHERE id = ?', (company_id,))
        result = cursor.fetchone()
        old_status = result[0] if result else None
        company_name = result[1] if result else "Unknown"
        
        # ステータス更新
        cursor.execute('''
            UPDATE companies 
            SET status = ?, updated_at = CURRENT_TIMESTAMP, last_contact_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, company_id))
        
        # 次のアクション推奨設定
        next_action = self._suggest_next_action(new_status)
        if next_action:
            cursor.execute('''
                UPDATE companies 
                SET next_action = ?
                WHERE id = ?
            ''', (next_action, company_id))
        
        # 履歴記録
        self._log_status_change(
            cursor, company_id, old_status, new_status, user_id, 
            reason, notes, next_action, next_steps
        )
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f"{company_name}のステータスを{SALES_STATUS.get(new_status, new_status)}に更新しました",
            'next_action': next_action
        }
    
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
    
    def _log_status_change(self, cursor, company_id, old_status, new_status, user_id, 
                          reason="", notes="", action_taken="", next_steps=""):
        """ステータス変更履歴記録"""
        cursor.execute('''
            INSERT INTO status_history (
                company_id, old_status, new_status, changed_by, 
                change_reason, notes, action_taken, next_steps
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (company_id, old_status, new_status, user_id, reason, notes, action_taken, next_steps))
    
    def get_companies_by_criteria(self, status=None, wifi_required=None, 
                                min_priority=0, min_relevance=0, limit=None):
        """条件別企業取得（戦略的フィルタリング）"""
        conn = sqlite3.connect(self.db_name)
        
        query = '''
            SELECT *, 
                   CASE 
                       WHEN wifi_required = 1 THEN '🟢 WiFi必要'
                       ELSE '⚪ WiFi不要'
                   END as wifi_status
            FROM companies 
            WHERE priority_score >= ? AND picocela_relevance_score >= ?
        '''
        params = [min_priority, min_relevance]
        
        if status:
            if isinstance(status, list):
                placeholders = ','.join(['?' for _ in status])
                query += f' AND status IN ({placeholders})'
                params.extend(status)
            else:
                query += ' AND status = ?'
                params.append(status)
        
        if wifi_required is not None:
            query += ' AND wifi_required = ?'
            params.append(wifi_required)
        
        query += ' ORDER BY priority_score DESC, updated_at DESC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def get_strategic_pipeline(self):
        """戦略的パイプライン分析"""
        conn = sqlite3.connect(self.db_name)
        
        # 各ステータスでの企業数と品質
        pipeline_query = '''
            SELECT 
                status,
                COUNT(*) as company_count,
                AVG(picocela_relevance_score) as avg_relevance,
                AVG(priority_score) as avg_priority,
                SUM(wifi_required) as wifi_companies,
                COUNT(CASE WHEN priority_score >= 100 THEN 1 END) as high_priority_count
            FROM companies 
            GROUP BY status
            ORDER BY 
                CASE status
                    WHEN 'Won' THEN 10
                    WHEN 'Negotiation' THEN 9
                    WHEN 'Proposal' THEN 8
                    WHEN 'Qualified' THEN 7
                    WHEN 'Engaged' THEN 6
                    WHEN 'Replied' THEN 5
                    WHEN 'Contacted' THEN 4
                    WHEN 'New' THEN 3
                    WHEN 'Dormant' THEN 2
                    WHEN 'Lost' THEN 1
                    ELSE 0
                END DESC
        '''
        
        pipeline_df = pd.read_sql_query(pipeline_query, conn)
        
        # WiFi戦略企業（最優先ターゲット）
        wifi_strategy_query = '''
            SELECT company_name, status, priority_score, picocela_relevance_score, 
                   email, last_contact_date, next_action
            FROM companies 
            WHERE wifi_required = 1
            ORDER BY priority_score DESC
            LIMIT 20
        '''
        
        wifi_strategy_df = pd.read_sql_query(wifi_strategy_query, conn)
        
        conn.close()
        
        return {
            'pipeline': pipeline_df,
            'wifi_strategy_targets': wifi_strategy_df,
            'total_companies': len(self.get_companies_by_criteria()),
            'wifi_required_total': len(self.get_companies_by_criteria(wifi_required=True))
        }
    
    def get_company_details(self, company_id):
        """企業詳細情報取得（履歴付き）"""
        conn = sqlite3.connect(self.db_name)
        
        # 企業基本情報
        company_query = 'SELECT * FROM companies WHERE id = ?'
        company_df = pd.read_sql_query(company_query, conn, params=[company_id])
        
        # ステータス履歴
        history_query = '''
            SELECT old_status, new_status, changed_by, change_reason, 
                   notes, action_taken, next_steps, created_at
            FROM status_history 
            WHERE company_id = ?
            ORDER BY created_at DESC
        '''
        history_df = pd.read_sql_query(history_query, conn, params=[company_id])
        
        conn.close()
        
        if company_df.empty:
            return None
        
        return {
            'company': company_df.iloc[0].to_dict(),
            'status_history': history_df.to_dict('records') if not history_df.empty else []
        }

# 使用例とテスト関数
def test_company_management():
    """テスト関数"""
    cm = CompanyManager()
    
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