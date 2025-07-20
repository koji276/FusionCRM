"""
メールカスタマイズエンジン
英語・日本語メールの生成とカスタマイズ機能
"""

import json
import time
from typing import Dict, Optional
from datetime import datetime
import streamlit as st


def get_openai_client():
    """OpenAI クライアントを安全に取得"""
    try:
        from openai import OpenAI
        
        # Streamlit Secrets からAPIキー取得を優先
        if "OPENAI_API_KEY" in st.secrets:
            return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        else:
            st.error("❌ OPENAI_API_KEY が .streamlit/secrets.toml に設定されていません")
            return None
    except ImportError:
        st.error("❌ OpenAI ライブラリがインストールされていません")
        return None
    except Exception as e:
        st.error(f"❌ OpenAI クライアント初期化エラー: {e}")
        return None


class EnglishEmailCustomizer:
    """英語パートナーシップメールのカスタマイゼーション"""
    
    def __init__(self, api_key: str = None):
        self.openai_client = get_openai_client()
        
        # 高品質ベースメール
        self.base_email_template = """Subject: Exploring Strategic Partnership for Industrial Mesh Wi-Fi Solutions

Dear {title},

I hope this message finds you well.

My name is Koji Tokuda from PicoCELA Inc. (NASDAQ: PCLA), a NASDAQ-listed company specializing in advanced Industrial multi-hop mesh Wi-Fi access point solutions.

PicoCELA's unique technology enables:
• Ultra-stable, multi-hop wireless connectivity over wide areas (10 hops available)
• Video, Voice, Robotics control traffic available even if mesh (2-3m sec/hop latency)  
• Reduced installation costs and deployment time (Maximum 90% LAN cable reduction)
• Reliable coverage in challenging environments such as:
{industry_specific_environments}

{custom_value_proposition}

As we continue to expand globally, we are eager to establish partnerships that deliver mutual value. Beyond offering our technology, we support partners in expanding their business into the Japanese and broader Asian markets. By combining your solutions with our technology, we believe we can create differentiated offerings and new business opportunities in both regions.

For more information about PicoCELA and our solutions, please visit our website: https://picocela.com/en/

Would you be open to a brief call to discuss potential collaboration?

If you prefer not to receive further communication regarding potential business collaboration, please let me know, and I will remove you from our contact list.

Thank you very much for your time.

Best regards,
Koji Tokuda
Business Development Manager
PicoCELA Inc. (NASDAQ: PCLA)
tokuda@picocela.com
1-408-850-5058
4F SANOS Nihombashi Building,
2−34−5 Nihombashi-Ningyocho,
Chuo-ku, Tokyo 103-0013, Japan
https://picocela.com/en/"""

        # パートナーシップ特化カスタマイズプロンプト
        self.customization_prompt = """
Customize PicoCELA partnership proposal for specific company.

Company: {company_name}
Business: {description}

This is a PARTNERSHIP proposal (not sales). Focus on mutual business opportunities.

Current generic environments:
• Industrial facilities
• Construction sites  
• Mines
• Disaster recovery and temporary networks
• Warehouses

Task: Replace with 4-5 challenging environments specific to this company's target markets/customers.

Requirements:
- Match their industry expertise and customer base
- Emphasize technical RF/networking challenges PicoCELA solves
- Show you understand their business domain
- Use professional technical language

Output JSON:
{{
  "partnership_environments": "• [Environment 1 specific to their customers]\\n• [Environment 2]\\n• [Environment 3]\\n• [Environment 4]\\n• [Environment 5 if relevant]",
  "partnership_value": "2-3 sentences about mutual partnership benefits for their business and customer base",
  "suggested_title": "Business Development Manager/Partnership Manager/CEO etc"
}}

Focus on THEIR CUSTOMERS' challenges that PicoCELA can help solve.
"""
    
    def customize_email_gpt35(self, company_data: Dict) -> Dict:
        """GPT-3.5による英語メールカスタマイズ"""
        if not self.openai_client:
            return self._create_fallback_email(company_data.get('company_name', ''), error="OpenAI API未設定")
            
        company_name = company_data.get('company_name', '')
        description = company_data.get('description', '')
        
        if not description or description.strip() == "":
            return self._create_fallback_email(company_name)
        
        try:
            # GPT-3.5でカスタマイズ部分のみ生成
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": self.customization_prompt.format(
                        company_name=company_name,
                        description=description
                    )}
                ],
                max_tokens=300,
                temperature=0.3,
                timeout=30
            )
            
            # コスト計算
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.0015 + output_tokens * 0.002) / 1000
            
            # レスポンス解析
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '')
            
            customization = json.loads(result_text)
            
            # ベースメールにカスタマイズを適用
            customized_email = self.base_email_template.format(
                title=customization.get('suggested_title', 'Business Development Manager'),
                industry_specific_environments=customization.get('partnership_environments', ''),
                custom_value_proposition=customization.get('partnership_value', '')
            )
            
            return {
                'company_id': company_data.get('company_id'),
                'company_name': company_name,
                'customized_email': customized_email,
                'subject': 'Exploring Strategic Partnership for Industrial Mesh Wi-Fi Solutions',
                'partnership_environments': customization.get('partnership_environments'),
                'partnership_value': customization.get('partnership_value'),
                'suggested_title': customization.get('suggested_title'),
                'api_cost': cost,
                'tokens_used': input_tokens + output_tokens,
                'customization_method': 'gpt35',
                'language': 'english',
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._create_fallback_email(company_name, error=str(e))
    
    def _create_fallback_email(self, company_name: str, error: str = None) -> Dict:
        """フォールバックメール（元の汎用版）"""
        customized_email = self.base_email_template.format(
            title='Business Development Manager',
            industry_specific_environments='• Industrial facilities\n• Construction sites\n• Mines\n• Disaster recovery and temporary networks\n• Warehouses',
            custom_value_proposition='Our technology can significantly enhance your wireless infrastructure capabilities while reducing deployment costs and complexity.'
        )
        
        return {
            'company_name': company_name,
            'customized_email': customized_email,
            'subject': 'Exploring Strategic Partnership for Industrial Mesh Wi-Fi Solutions',
            'partnership_environments': '• Industrial facilities\n• Construction sites\n• Mines\n• Disaster recovery and temporary networks\n• Warehouses',
            'partnership_value': 'Our technology can significantly enhance your wireless infrastructure capabilities while reducing deployment costs and complexity.',
            'suggested_title': 'Business Development Manager',
            'api_cost': 0.0,
            'customization_method': 'fallback',
            'language': 'english',
            'error': error,
            'generated_at': datetime.now().isoformat()
        }


class JapaneseEmailCustomizer:
    """日本語営業メールのカスタマイゼーション"""
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # 日本語ベーステンプレート
        self.base_template = """件名: {subject}

{company_name} 御中

いつもお世話になっております。
PicoCELA株式会社の{sender_name}と申します。

この度、貴社の{business_description}に関連して、弊社のワイヤレスソリューションがお役に立てる可能性があると考え、ご連絡させていただきました。

{custom_content}

PicoCELA独自の技術特徴：
• 最大10ホップの安定したメッシュ通信
• 低遅延（ホップあたり2-3ms）でリアルタイム制御対応
• 配線工事を最大90%削減可能
• {industry_specific_benefits}

{call_to_action}

ご多忙中恐れ入りますが、ご検討のほど、よろしくお願い申し上げます。

{signature}
"""
    
    def customize_japanese_email(self, company_data: Dict, template_type: str = "partnership") -> Dict:
        """日本語メールのカスタマイズ"""
        if not self.openai_client:
            return self._create_fallback_japanese_email(company_data)
        
        try:
            prompt = f"""
以下の企業向けに、PicoCELAの無線技術を紹介する営業メールをカスタマイズしてください。

企業名: {company_data.get('company_name', '')}
事業内容: {company_data.get('description', '')}
業界: {company_data.get('industry', '')}

要求:
1. 相手企業の事業に特化した技術的課題を理解していることを示す
2. PicoCELAの技術がどのように解決できるかを具体的に説明
3. 日本のビジネス文化に適した丁寧な文章
4. パートナーシップの可能性を示唆

JSON形式で回答:
{{
  "subject": "件名",
  "custom_content": "カスタマイズされた本文（2-3段落）",
  "industry_specific_benefits": "業界特化の技術メリット",
  "call_to_action": "具体的な提案・次のステップ"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.4
            )
            
            customization = json.loads(response.choices[0].message.content)
            
            # テンプレートに適用
            email_content = self.base_template.format(
                subject=customization.get('subject', 'PicoCELAワイヤレスソリューションのご提案'),
                company_name=company_data.get('company_name', ''),
                sender_name='徳田',
                business_description=company_data.get('description', '事業'),
                custom_content=customization.get('custom_content', ''),
                industry_specific_benefits=customization.get('industry_specific_benefits', ''),
                call_to_action=customization.get('call_to_action', ''),
                signature=self._get_japanese_signature()
            )
            
            return {
                'company_id': company_data.get('company_id'),
                'company_name': company_data.get('company_name'),
                'email_content': email_content,
                'subject': customization.get('subject'),
                'language': 'japanese',
                'customization_method': 'gpt35',
                'api_cost': (response.usage.total_tokens * 0.00175) / 1000,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._create_fallback_japanese_email(company_data, error=str(e))
    
    def _create_fallback_japanese_email(self, company_data: Dict, error: str = None) -> Dict:
        """日本語フォールバックメール"""
        email_content = self.base_template.format(
            subject='PicoCELAワイヤレスソリューションのご提案',
            company_name=company_data.get('company_name', ''),
            sender_name='徳田',
            business_description=company_data.get('description', '事業'),
            custom_content='貴社の事業展開において、安定したワイヤレス通信環境の構築が重要な要素となっているのではないでしょうか。',
            industry_specific_benefits='厳しい環境での安定通信',
            call_to_action='もしご興味をお持ちいただけましたら、15分程度のお電話でご説明させていただければと思います。',
            signature=self._get_japanese_signature()
        )
        
        return {
            'company_id': company_data.get('company_id'),
            'company_name': company_data.get('company_name'),
            'email_content': email_content,
            'subject': 'PicoCELAワイヤレスソリューションのご提案',
            'language': 'japanese',
            'customization_method': 'fallback',
            'api_cost': 0.0,
            'error': error,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_japanese_signature(self) -> str:
        """日本語署名"""
        return """――――――――――――――――――――
PicoCELA株式会社
ビジネス開発部
徳田 幸次
〒103-0013 
東京都中央区日本橋人形町2-34-5
SANOS日本橋ビル4F
TEL: 1-408-850-5058
Email: tokuda@picocela.com
URL: https://picocela.com/
――――――――――――――――――――"""
