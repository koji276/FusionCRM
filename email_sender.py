"""
メール送信システム
Gmail SMTP経由での送信、リトライ機能、制限対策
"""

import time
import smtplib
from typing import Dict, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

from email_database import IntegratedEmailDatabase


def send_email_smtp(to_email: str, subject: str, body: str, gmail_config: Dict) -> bool:
    """Gmail SMTP経由でメール送信"""
    try:
        # SMTP設定
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # MIMEメッセージ作成
        msg = MIMEMultipart()
        msg['From'] = f"{gmail_config['sender_name']} <{gmail_config['email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # 本文添付
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP接続・送信
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_config['email'], gmail_config['password'])
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        st.error(f"メール送信エラー: {str(e)}")
        return False


def send_email_smtp_with_retry(to_email: str, subject: str, body: str, gmail_config: Dict, max_retries: int = 3) -> bool:
    """リトライ機能付きメール送信"""
    for attempt in range(max_retries):
        try:
            # SMTP設定
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            
            # MIMEメッセージ作成
            msg = MIMEMultipart()
            msg['From'] = f"{gmail_config['sender_name']} <{gmail_config['email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 本文添付
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP接続・送信
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(gmail_config['email'], gmail_config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(30)  # 30秒待機してリトライ
                continue
            else:
                raise e
    
    return False


def send_pregenerated_emails_with_resume(company_list: List[Dict], gmail_config: Dict, 
                                        max_emails: int = 50, language: str = 'english',
                                        template_type: str = 'standard', send_interval: int = 60,
                                        resume_mode: bool = False) -> Dict:
    """重複なし再開機能付き瞬時送信"""
    db = IntegratedEmailDatabase()
    
    # 送信済み企業を除外
    if resume_mode:
        already_sent = db.get_already_sent_companies(language, template_type)
        remaining_companies = [c for c in company_list if c.get('company_name') not in already_sent]
        st.info(f"📧 送信済み: {len(already_sent)}社 | 残り: {len(remaining_companies)}社")
    else:
        remaining_companies = company_list
        already_sent = []
    
    target_companies = remaining_companies[:max_emails]
    
    if not target_companies:
        st.success("✅ 全企業への送信が完了しています！")
        return {'all_completed': True}
    
    st.write(f"📤 {'再開' if resume_mode else '開始'}: {len(target_companies)}社への送信")
    
    sent_count = 0
    failed_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_remaining_text = st.empty()
    
    start_time = time.time()
    
    for i, company in enumerate(target_companies):
        # 進捗更新
        progress = (i + 1) / len(target_companies)
        progress_bar.progress(progress)
        status_text.text(f"送信中: {company.get('company_name', 'Unknown')} ({i+1}/{len(target_companies)})")
        
        # 残り時間表示
        if i > 0:
            elapsed = time.time() - start_time
            estimated_total = elapsed / i * len(target_companies)
            remaining = estimated_total - elapsed
            time_remaining_text.text(f"⏱️ 残り時間: {remaining/60:.1f}分")
        
        # 送信前に再度確認（他のプロセスで送信済みの場合）
        company_name = company.get('company_name')
        if company_name in db.get_already_sent_companies(language, template_type):
            st.info(f"⚠️ {company_name} - 既に送信済みのためスキップ")
            continue
        
        # データベースからメール取得
        stored_email = db.get_generated_email(company_name, language, template_type)
        
        if stored_email:
            try:
                # Gmail制限対策: より長い間隔
                if i > 0:
                    time.sleep(send_interval)
                
                # 送信実行（リトライ機能付き）
                success = send_email_smtp_with_retry(
                    to_email=company.get('email'),
                    subject=stored_email['subject'],
                    body=stored_email['email_body'],
                    gmail_config=gmail_config,
                    max_retries=3
                )
                
                # 送信履歴保存
                send_record = {
                    'company_id': company.get('company_id', ''),
                    'company_name': company_name,
                    'recipient_email': company.get('email'),
                    'language': language,
                    'subject': stored_email['subject'],
                    'status': 'success' if success else 'failed',
                    'smtp_response': 'OK' if success else 'SMTP Error',
                    'template_type': template_type
                }
                db.save_send_history(send_record)
                
                if success:
                    sent_count += 1
                    st.success(f"✅ {company.get('company_name')} - 送信成功")
                else:
                    failed_count += 1
                    st.error(f"❌ {company.get('company_name')} - 送信失敗")
                    
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                st.error(f"❌ {company.get('company_name')} - エラー: {error_msg[:50]}")
                
                # Gmail制限検知
                if "quota" in error_msg.lower() or "limit" in error_msg.lower() or "authentication" in error_msg.lower():
                    st.error("🚫 Gmail送信制限に達しました。24時間後に再開してください。")
                    break
                
                # エラー履歴保存
                send_record = {
                    'company_id': company.get('company_id', ''),
                    'company_name': company_name,
                    'recipient_email': company.get('email'),
                    'language': language,
                    'subject': stored_email.get('subject', 'Unknown'),
                    'status': 'error',
                    'smtp_response': error_msg[:100],
                    'template_type': template_type
                }
                db.save_send_history(send_record)
        else:
            failed_count += 1
            st.warning(f"⚠️ {company.get('company_name')} - 事前生成メールなし")
    
    # 完了処理
    total_time = time.time() - start_time
    total_sent_today = len(already_sent) + sent_count
    
    summary = {
        'total_attempted': len(target_companies),
        'successful_sends': sent_count,
        'failed_sends': failed_count,
        'total_sent_today': total_sent_today,
        'success_rate': (sent_count / len(target_companies)) * 100 if target_companies else 0,
        'total_time_minutes': total_time / 60,
        'remaining_companies': len(remaining_companies) - len(target_companies)
    }
    
    st.success(f"🎉 送信{'再開' if resume_mode else ''}完了！")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今回送信", f"{sent_count}通")
    with col2:
        st.metric("本日総送信", f"{total_sent_today}通")
    with col3:
        st.metric("成功率", f"{summary['success_rate']:.1f}%")
    with col4:
        st.metric("残り企業", f"{summary['remaining_companies']}社")
    
    return summary


# 互換性のための旧関数
def send_pregenerated_emails(company_list: List[Dict], gmail_config: Dict, 
                            max_emails: int = 50, language: str = 'english',
                            template_type: str = 'standard') -> Dict:
    """旧バージョン互換性のための関数"""
    return send_pregenerated_emails_with_resume(
        company_list, gmail_config, max_emails, language, template_type, 60, False
    )


def send_pregenerated_emails_with_interval(company_list: List[Dict], gmail_config: Dict, 
                                          max_emails: int = 50, language: str = 'english',
                                          template_type: str = 'standard', send_interval: int = 60) -> Dict:
    """旧バージョン互換性のための関数 - 新しい再開機能にリダイレクト"""
    return send_pregenerated_emails_with_resume(
        company_list, gmail_config, max_emails, language, template_type, send_interval, False
    )
