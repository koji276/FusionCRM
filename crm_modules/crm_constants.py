"""
CRM定数定義モジュール
fusion_crm_main.pyから抽出
"""

# 拡張ステータス定義
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

# PicoCELA関連キーワード
PICOCELA_KEYWORDS = [
    'network', 'mesh', 'wireless', 'wifi', 'connectivity',
    'iot', 'smart', 'digital', 'automation', 'sensor', 'ai',
    'construction', 'building', 'site', 'industrial', 'management',
    'platform', 'solution', 'integration', 'control', 'monitoring'
]

# メール設定
EMAIL_AVAILABLE = True
EMAIL_ERROR_MESSAGE = ""

# メールテンプレート
EMAIL_TEMPLATES = {
    "wifi_needed": {
        "subject": "建設現場のワイヤレス通信課題解決のご提案 - PicoCELA",
        "body": """{company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

建設現場でのワイヤレス通信にお困りではありませんか？

弊社のメッシュネットワーク技術により、以下のメリットを提供いたします：

• 既存インフラに依存しない独立ネットワーク構築
• IoTセンサー・モニタリング機器との安定した連携
• 現場安全性向上・リアルタイム状況把握
• 通信エリアの柔軟な拡張・移設対応

建設業界での豊富な導入実績がございます。
詳細な資料をお送りいたしますので、15分程度お時間をいただけますでしょうか。

何かご質問がございましたら、お気軽にお声かけください。

株式会社PicoCELA
営業部"""
    },
    "general": {
        "subject": "PicoCELA メッシュネットワークソリューションのご案内",
        "body": """{company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

弊社は建設・産業分野向けのワイヤレス通信ソリューションを提供しております。

貴社の事業にお役立ていただけるソリューションがあるかもしれません。
ぜひ一度お話をお聞かせください。

株式会社PicoCELA
営業部"""
    }
}

# データインポート設定
IMPORT_SETTINGS = {
    'fusion_columns': {
        'company_name': '企業名（必須）',
        'email': 'メールアドレス',
        'phone': '電話番号',
        'website_url': 'ウェブサイト',
        'industry': '業界',
        'notes': '備考・説明',
        'source': '情報源'
    },
    
    'mapping_rules': {
        'company_name': ['company name', 'company_name', 'name', 'organization', 'business name'],
        'email': ['email', 'email address', 'e-mail', 'mail', 'contact email'],
        'phone': ['phone', 'telephone', 'tel', 'contact phone', 'phone number'],
        'website_url': ['website', 'url', 'web', 'homepage', 'site'],
        'industry': ['industry', 'sector', 'business type', 'category'],
        'notes': ['description', 'notes', 'comment', 'remarks', 'details'],
        'source': ['source', 'origin', 'lead source', 'channel']
    },
    
    'wifi_indicators': [
        'wifi', 'wireless', 'network', 'connectivity', 'mesh',
        'iot', 'smart', 'digital', 'automation', 'sensor',
        'monitoring', 'tracking', 'communication'
    ],
    
    'scoring_keywords': {
        'network': 15, 'mesh': 20, 'wireless': 15, 'wifi': 15,
        'connectivity': 10, 'iot': 10, 'smart': 8, 'automation': 8,
        'construction': 12, 'building': 10, 'industrial': 8
    }
}
