#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FusionCRM - Streamlit Cloud対応 メール配信システム（完全修正版・エラー修正）
実際のデータベース接続 + 確実なSMTP送信
"""

import streamlit as st
import sqlite3
import pandas as pd
import json
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ページ設定
st.set_page_config(
    page_title="📧 FusionCRM メール配信システム",
    page_icon="📧",
    layout="wide"
)

# セッション状態の初期化
if 'gmail_config' not in st.session_state:
    st.session_state.gmail_config = None
if 'setup_completed' not in st.session_state:
    st.session_state.setup_completed = False

class StreamlitEmailWebApp:
    """Streamlit Cloud対応メール配信Webアプリケーション（完全修正版）"""
    
    def __init__(self):
        pass
    
    def is_gmail_configured(self):
        """Gmail設定状況確認"""
        return st.session_state.gmail_config is not None and st.session_state.setup_completed
    
    def save_gmail_config_to_session(self, config):
        """Gmail設定をセッション状態に保存"""
        try:
            st.session_state.gmail_config = config
            st.session_state.setup_completed = True
            return True
        except Exception as e:
            st.error(f"設定保存エラー: {e}")
            return False
    
    def test_gmail_connection(self, config):
        """Gmail接続テスト"""
        try:
            server = smtplib.SMTP(config['smtp_server'], config['
