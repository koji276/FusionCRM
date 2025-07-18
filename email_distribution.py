#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Professional Email Distribution Module (Complete Fixed Version)
PicoCELA社専用メール配信システム（完全修正版）
"""

import json
import smtplib
import sqlite3
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import sys

class EmailDistribution:
    def __init__(self, config_path="config"):
        """メール配信システムの初期化"""
        self.config_path = config_path
        self.ensure_config_dir()
        self.gmail_config = self.load_gmail_config()
        self.system_config = self.load_system_config()
        self.email_templates = self.load_email_templates()
        
    def ensure_config_dir(self):
        """設定ディレクトリの確保"""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
    
    def load_gmail_config(self):
        """Gmail設定の読み込み（送信者名の自動修正付き）"""
        try:
            config_file = os.path.join(self.config_path, "gmail_config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 送信者名がアプリパスワードになっている場合の自動修正
            if config.get('sender_name') == config.get('password'):
                print("⚠️ 送信者名を自動修正しています...")
                config['sender_name'] = "PicoCELA Inc."
                self.save_gmail_config(config)
                print("✅ 送信者名を 'PicoCELA Inc.' に修正しました")
            
            return config
        except FileNotFoundError:
            print("❌ Gmail設定ファイルが見つかりません。設定を行ってください。")
            return self.setup_gmail_config()
        except Exception as e:
            print(f"❌ Gmail設定読み込みエラー: {e}")
            return None
    
    def save_gmail_config(self, config):
        """Gmail設定の保存"""
        config_file = os.path.join(self.config_path, "gmail_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def setup_gmail_config(self):
        """Gmail設定のセットアップ"""
        print("\n🔧 Gmail設定セットアップ")
        print("=" * 50)
        
        email = input("Gmail アドレス [tokuda@picocela.com]: ").strip() or "tokuda@picocela.com"
        password = input("アプリパスワード [bmzr lbrs cbbn jtmr]: ").strip() or "bmzr lbrs cbbn jtmr"
        sender_name = input("送信者名 [PicoCELA Inc.]: ").strip() or "PicoCELA Inc."
        
        config = {
            "email": email,
            "password": password,
            "sender_name": sender_name,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587
        }
        
        self.save_gmail_config(config)
        print("✅ Gmail設定を保存しました")
        
        # 接続テスト
        if self.test_gmail_connection(config):
            return config
        else:
            return None
    
    def test_gmail_connection(self, config):
        """Gmail接続テスト"""
        try:
            print("📧 Gmail接続テスト中...")
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email'], config['password'])
            server.quit()
            print("✅ Gmail接続テスト成功")
            return True
        except Exception as e:
            print(f"❌ Gmail接続テストエラー: {e}")
            return False
    
    def load_system_config(self):
        """システム設定の読み込み"""
        try:
            config_file = os.path.join(self.config_path, "system_config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = {
                "email_distribution": {
                    "batch_size": 20,
                    "daily_limit": 500,
                    "delay_range": [3, 8],
                    "max_retries": 3
                }
            }
            # デフォルト設定を保存
            config_file = os.path.join(self.config_path, "system_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
    
    def load_email_templates(self):
        """メールテンプレートの読み込み"""
        try:
            config_file = os.path.join(self.config_path, "email_templates.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_templates = {
                "initial_contact": {
                    "subject": "PicoCELA メッシュネットワークソリューションのご案内",
                    "body": """Dear {company_name} 様

お世話になっております。
株式会社PicoCELAの営業担当です。

建設現場でのワイヤレス通信にお困りではありませんか？

弊社のメッシュネットワーク技術により、以下のメリットを提供いたします：

• 建設現場での安定したワイヤレス通信
• 既存インフラに依存しない独立ネットワーク
• IoTセンサー・モニタリング機器との連携
• 現場安全性向上・デジタル化推進

詳細な資料をお送りいたしますので、お時間をいただけますでしょうか。

株式会社PicoCELA
営業部"""
                },
                "follow_up": {
                    "subject": "PicoCELA メッシュネットワーク - フォローアップ",
                    "body": """Dear {company_name} 様

先日はお時間をいただき、ありがとうございました。

弊社のメッシュネットワークソリューションについて、
追加でご質問やご相談がございましたら、お気軽にお声がけください。

株式会社PicoCELA
営業部"""
                }
            }
            # デフォルトテンプレートを保存
            config_file = os.path.join(self.config_path, "email_templates.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_templates, f, ensure_ascii=False, indent=2)
            return default_templates
    
    def get_companies_for_campaign(self, status_filter=None, limit=None):
        """キャンペーン対象企業の取得（正しい列名で修正済み）"""
        try:
            conn = sqlite3.connect('fusion_crm.db')
            cursor = conn.cursor()
            
            if status_filter:
                query = """
                    SELECT id, company_name, email_address, website, phone, status, picocela_relevance_score 
                    FROM companies 
                    WHERE status = ? AND email_address IS NOT NULL AND email_address != '' 
                    ORDER BY picocela_relevance_score DESC
                """
                cursor.execute(query, (status_filter,))
            else:
                query = """
                    SELECT id, company_name, email_address, website, phone, status, picocela_relevance_score 
                    FROM companies 
                    WHERE status = 'New' AND email_address IS NOT NULL AND email_address != '' 
                    ORDER BY picocela_relevance_score DESC
                """
                cursor.execute(query)
            
            companies = cursor.fetchall()
            if limit:
                companies = companies[:limit]
            
            conn.close()
            return companies
            
        except Exception as e:
            print(f"❌ 企業データ取得エラー: {e}")
            return []
    
    def send_email(self, to_email, company_name, template_name="initial_contact"):
        """単一メール送信（送信者名修正済み）"""
        if not self.gmail_config:
            return False, "Gmail設定が無効です"
        
        try:
            template = self.email_templates.get(template_name, self.email_templates["initial_contact"])
            
            msg = MIMEMultipart()
            msg['From'] = f"{self.gmail_config['sender_name']} <{self.gmail_config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = template['subject']
            
            body = template['body'].format(company_name=company_name)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.gmail_config['smtp_server'], self.gmail_config['smtp_port'])
            server.starttls()
            server.login(self.gmail_config['email'], self.gmail_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.gmail_config['email'], to_email, text)
            server.quit()
            
            self.log_email_history(company_name, to_email, template_name, "success")
            return True, "送信成功"
            
        except Exception as e:
            error_msg = f"送信エラー: {str(e)}"
            self.log_email_history(company_name, to_email, template_name, "failed", error_msg)
            return False, error_msg
    
    def log_email_history(self, company_name, email, template_name, status, error_msg=None):
        """送信履歴の記録（実際のテーブル構造に対応）"""
        try:
            conn = sqlite3.connect('fusion_crm.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM companies WHERE company_name = ?", (company_name,))
            result = cursor.fetchone()
            company_id = result[0] if result else None
            
            # 実際のemail_historyテーブル構造に合わせて履歴記録
            cursor.execute("""
                INSERT INTO email_history (company_id, email_type, subject, content, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (company_id, template_name, f"Campaign to {company_name}", f"Email sent to {email}", status, error_msg))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # 履歴記録エラーは警告のみ（メール送信は継続）
            pass
    
    def update_company_status(self, company_name, new_status):
        """企業ステータスの更新"""
        try:
            conn = sqlite3.connect('fusion_crm.db')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE companies 
                SET status = ?, last_contact_date = ?, updated_at = ?
                WHERE company_name = ?
            """, (new_status, datetime.now(), datetime.now(), company_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ ステータス更新エラー: {e}")
    
    def run_campaign(self, max_emails=20, status_filter="New"):
        """メールキャンペーン実行（完全修正版）"""
        print("🚀 FusionCRM プロフェッショナル配信ツール（完全修正版）")
        print("=" * 60)
        
        if not self.gmail_config:
            print("❌ Gmail設定が無効です。設定を行ってください。")
            return
        
        # 対象企業取得
        companies = self.get_companies_for_campaign(status_filter, max_emails)
        
        if not companies:
            print("📭 配信対象企業が見つかりません。")
            return
        
        print(f"📊 配信対象: {len(companies)}社")
        print(f"📧 Gmail設定: {self.gmail_config['email']}")
        print(f"👤 送信者名: {self.gmail_config['sender_name']}")
        print(f"📝 テンプレート: initial_contact")
        
        # 対象企業リスト表示
        print("\n📋 配信対象企業:")
        for i, company in enumerate(companies, 1):
            print(f"  {i:2d}. {company[1]} ({company[2]})")
        
        # 送信確認
        response = input(f"\n{len(companies)}社に配信を開始しますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ 配信をキャンセルしました。")
            return
        
        # バッチ送信実行
        success_count = 0
        failed_count = 0
        
        print("\n🚀 配信開始...")
        print("=" * 60)
        
        for i, company in enumerate(companies, 1):
            company_id = company[0]
            company_name = company[1]
            email_address = company[2]  # email_address列（修正済み）
            
            print(f"📧 {i:2d}/{len(companies)}. {company_name} ({email_address}) 送信中...")
            
            success, message = self.send_email(email_address, company_name)
            
            if success:
                print(f"✅ {company_name} - 送信成功")
                success_count += 1
                # ステータス更新
                self.update_company_status(company_name, "Contacted")
            else:
                print(f"❌ {company_name} - {message}")
                failed_count += 1
            
            # 送信間隔（最後の企業以外）
            if i < len(companies):
                delay = random.randint(*self.system_config["email_distribution"]["delay_range"])
                print(f"⏱️ {delay}秒待機中...")
                time.sleep(delay)
        
        # 結果サマリー
        total = success_count + failed_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 配信結果サマリー")
        print(f"✅ 送信成功: {success_count}件")
        print(f"❌ 送信失敗: {failed_count}件")
        print(f"📈 成功率: {success_rate:.1f}%")
        print(f"📧 送信者名: {self.gmail_config['sender_name']}")
        print("=" * 60)

def main():
    """メイン実行関数"""
    print("🚀 FusionCRM Professional Email Distribution (Complete Fixed Version)")
    print("PicoCELA メッシュネットワーク営業支援システム（完全修正版）")
    print("=" * 70)
    
    # 配信システム初期化
    email_dist = EmailDistribution()
    
    if not email_dist.gmail_config:
        print("❌ Gmail設定が完了していません。終了します。")
        return
    
    # 設定確認表示
    print(f"\n✅ Gmail設定確認:")
    print(f"   📧 メールアドレス: {email_dist.gmail_config['email']}")
    print(f"   👤 送信者名: {email_dist.gmail_config['sender_name']}")
    print(f"   🔧 SMTP: {email_dist.gmail_config['smtp_server']}")
    
    # 対話式メニュー
    while True:
        print("\n📋 メニュー:")
        print("1. 新規企業への一括配信（推奨）")
        print("2. 特定ステータス企業への配信")
        print("3. テスト送信（1社のみ）")
        print("4. 配信履歴確認")
        print("5. Gmail設定確認・変更")
        print("6. 企業データ確認")
        print("7. 終了")
        
        choice = input("\n選択してください (1-7): ")
        
        if choice == "1":
            # 新規企業への配信
            max_emails = input("配信数を入力 (デフォルト20): ")
            max_emails = int(max_emails) if max_emails.isdigit() else 20
            email_dist.run_campaign(max_emails=max_emails, status_filter="New")
            
        elif choice == "2":
            # 特定ステータス配信
            print("利用可能ステータス: New, Contacted, Replied, Qualified")
            status = input("ステータスを入力: ") or "New"
            max_emails = input("配信数を入力 (デフォルト10): ")
            max_emails = int(max_emails) if max_emails.isdigit() else 10
            email_dist.run_campaign(max_emails=max_emails, status_filter=status)
            
        elif choice == "3":
            # テスト送信
            companies = email_dist.get_companies_for_campaign("New", 1)
            if companies:
                company = companies[0]
                company_name = company[1]
                email_address = company[2]
                print(f"\n🧪 テスト送信: {company_name} ({email_address})")
                success, message = email_dist.send_email(email_address, company_name)
                if success:
                    print(f"✅ テスト送信成功: {company_name}")
                else:
                    print(f"❌ テスト送信失敗: {message}")
            else:
                print("❌ テスト対象企業が見つかりません")
                
        elif choice == "4":
            # 履歴確認
            try:
                conn = sqlite3.connect('fusion_crm.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT eh.sent_at, c.company_name, eh.status, eh.error_message
                    FROM email_history eh
                    LEFT JOIN companies c ON eh.company_id = c.id
                    ORDER BY eh.sent_at DESC
                    LIMIT 15
                """)
                history = cursor.fetchall()
                
                if history:
                    print("\n📊 最新の配信履歴 (15件):")
                    for record in history:
                        status_icon = "✅" if record[2] == "success" else "❌"
                        error_info = f" ({record[3]})" if record[3] else ""
                        print(f"{status_icon} {record[0]} - {record[1]} - {record[2]}{error_info}")
                else:
                    print("📭 配信履歴がありません")
                    
                conn.close()
                
            except Exception as e:
                print(f"❌ 履歴取得エラー: {e}")
        
        elif choice == "5":
            # Gmail設定確認・変更
            print(f"\n📧 現在のGmail設定:")
            print(f"   メールアドレス: {email_dist.gmail_config['email']}")
            print(f"   送信者名: {email_dist.gmail_config['sender_name']}")
            
            if input("設定を変更しますか？ (y/N): ").lower() == 'y':
                email_dist.gmail_config = email_dist.setup_gmail_config()
        
        elif choice == "6":
            # 企業データ確認
            try:
                conn = sqlite3.connect('fusion_crm.db')
                cursor = conn.cursor()
                
                # ステータス別企業数
                cursor.execute("SELECT status, COUNT(*) FROM companies GROUP BY status")
                status_counts = cursor.fetchall()
                
                print("\n📊 企業データ統計:")
                for status, count in status_counts:
                    print(f"   {status}: {count}社")
                
                # メール配信可能企業
                cursor.execute("SELECT COUNT(*) FROM companies WHERE email_address IS NOT NULL AND email_address != ''")
                email_available = cursor.fetchone()[0]
                print(f"   メール配信可能: {email_available}社")
                
                # 配信対象サンプル
                cursor.execute("""
                    SELECT company_name, email_address, status 
                    FROM companies 
                    WHERE email_address IS NOT NULL AND email_address != '' 
                    ORDER BY picocela_relevance_score DESC 
                    LIMIT 5
                """)
                samples = cursor.fetchall()
                
                if samples:
                    print("\n📋 配信対象サンプル (上位5社):")
                    for company, email, status in samples:
                        print(f"   • {company} ({email}) - {status}")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ データ確認エラー: {e}")
        
        elif choice == "7":
            print("👋 FusionCRM Professional Email Distribution を終了します。")
            print("🎯 今後も PicoCELA の営業活動を支援いたします！")
            break
            
        else:
            print("❌ 無効な選択です。1-7を入力してください。")

if __name__ == "__main__":
    main()