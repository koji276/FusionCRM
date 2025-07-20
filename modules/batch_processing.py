"""
バッチ処理システム
英語・日本語メールの一括生成処理
"""

import time
from typing import Dict, List
import streamlit as st

from email_customizers import EnglishEmailCustomizer, JapaneseEmailCustomizer
from email_database import IntegratedEmailDatabase


def generate_english_emails_batch(companies_data: List[Dict], max_companies: int = None) -> Dict:
    """英語メールバッチ生成"""
    customizer = EnglishEmailCustomizer()
    db = IntegratedEmailDatabase()
    
    companies_to_process = companies_data[:max_companies] if max_companies else companies_data
    total_companies = len(companies_to_process)
    
    st.write(f"🌍 {total_companies}社の英語パートナーシップメール生成中...")
    
    # 処理予測
    estimated_time_minutes = (total_companies * 2) / 60
    estimated_cost = total_companies * 0.0004
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("処理対象", f"{total_companies}社")
    with col2:
        st.metric("予想時間", f"{estimated_time_minutes:.1f}分")
    with col3:
        st.metric("予想コスト", f"${estimated_cost:.3f}")
    
    # バッチ処理実行
    results = []
    total_cost = 0.0
    success_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_tracker = st.empty()
    
    start_time = time.time()
    
    for i, company in enumerate(companies_to_process):
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        # 進捗更新
        progress = (i + 1) / total_companies
        progress_bar.progress(progress)
        status_text.text(f"生成中: {company.get('company_name', 'Unknown')} ({i+1}/{total_companies})")
        
        # 時間予測
        if i > 0:
            avg_time = elapsed_time / i
            remaining_time = (total_companies - i) * avg_time / 60
            time_tracker.text(f"経過: {elapsed_time/60:.1f}分 | 残り: {remaining_time:.1f}分")
        
        # 企業データ保存
        db.save_company(company)
        
        # メール生成
        result = customizer.customize_email_gpt35(company)
        results.append(result)
        
        # データベース保存
        db.save_generated_email(result)
        
        if result.get('customization_method') == 'gpt35':
            success_count += 1
            total_cost += result.get('api_cost', 0.0)
        
        # 5社ごとに進捗表示
        if (i + 1) % 5 == 0:
            success_rate = (success_count / (i + 1)) * 100
            st.success(f"✅ {i+1}社完了 (GPT成功率: {success_rate:.1f}%)")
        
        # API制限対応
        time.sleep(1)
    
    # 完了サマリー
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    summary = {
        'total_processed': total_companies,
        'gpt35_success': success_count,
        'fallback_used': total_companies - success_count,
        'success_rate': (success_count / total_companies) * 100,
        'total_cost_usd': total_cost,
        'total_cost_jpy': total_cost * 150,
        'total_time_minutes': total_elapsed / 60,
        'avg_cost_per_email': total_cost / total_companies if total_companies > 0 else 0
    }
    
    st.balloons()
    st.success(f"🎉 英語メールバッチ生成完了！")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("GPT成功", f"{success_count}社", f"{summary['success_rate']:.1f}%")
    with col2:
        st.metric("総コスト", f"¥{summary['total_cost_jpy']:.0f}")
    with col3:
        st.metric("処理時間", f"{summary['total_time_minutes']:.1f}分")
    with col4:
        st.metric("平均コスト", f"${summary['avg_cost_per_email']:.4f}")
    
    return summary


def generate_japanese_emails_individual(companies_data: List[Dict], template_type: str = "partnership") -> Dict:
    """日本語メール個別生成"""
    customizer = JapaneseEmailCustomizer()
    db = IntegratedEmailDatabase()
    
    st.write(f"🇯🇵 日本語メール個別生成開始...")
    
    results = []
    total_cost = 0.0
    
    for i, company in enumerate(companies_data):
        st.write(f"処理中: {company.get('company_name')} ({i+1}/{len(companies_data)})")
        
        # 企業データ保存
        db.save_company(company)
        
        # メール生成
        result = customizer.customize_japanese_email(company, template_type)
        results.append(result)
        
        # データベース保存
        result['template_type'] = template_type
        db.save_generated_email(result)
        
        total_cost += result.get('api_cost', 0.0)
        
        # 結果表示
        with st.expander(f"📧 {company.get('company_name')} - 生成結果"):
            st.write(f"**件名**: {result.get('subject')}")
            st.text_area("内容", result.get('email_content'), height=300, key=f"email_{i}")
    
    summary = {
        'total_processed': len(companies_data),
        'total_cost_usd': total_cost,
        'total_cost_jpy': total_cost * 150
    }
    
    st.success(f"✅ 日本語メール {len(companies_data)}件生成完了")
    
    return summary
