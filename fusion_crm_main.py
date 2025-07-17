"""
FusionCRM – PicoCELA 営業管理システム  
Google Sheets 専用版（2025‑07‑17 リファクタリング）
--------------------------------------------------
* 旧 SQLite 依存を完全撤廃し、Apps Script + Sheets API のみで動作
* `show_data_import()` を実装（CSV / Excel 一括取り込み）
* Google Apps Script 側の `get_analytics` 追加を前提に呼び出し方式を GET→POST に統一
* コード全体をモジュール分割しやすい構造へ整理
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    import smtplib
    import ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
except ImportError:
    # メール送信機能を無効化
    smtplib = None  # type: ignore

# ---------------------------------------------------------------------------
# 定数・設定
# ---------------------------------------------------------------------------

PAGE_TITLE = "FusionCRM – PicoCELA 営業管理システム"
SALES_STATUS = [
    "New", "Contacted", "Replied", "Engaged", "Qualified",
    "Proposal", "Negotiation", "Won", "Lost", "Dormant",
]
PICOCELA_KEYWORDS = [
    "network", "mesh", "wireless", "wifi", "connectivity", "iot",
    "smart", "digital", "automation", "sensor", "ai", "construction",
    "building", "site", "industrial", "management", "platform",
]

# ---------------------------------------------------------------------------
# Google Sheets / Apps Script クライアント
# ---------------------------------------------------------------------------

class GoogleSheetsAPI:
    """Apps Script 側と REST で通信する軽量ラッパー"""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint.rstrip("/")
        self._ping()

    # ------------------------------
    # プライベートユーティリティ
    # ------------------------------

    def _ping(self) -> None:
        res = st.session_state.get("_ping_result")
        if res:
            return  # すでに疎通確認済み
        r = self._request("test", method="GET")
        if not r.get("success"):
            raise RuntimeError("Google Apps Script との通信に失敗しました")
        st.session_state._ping_result = True  # type: ignore

    def _request(self, action: str, *, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        import requests  # ローカル import で起動高速化

        if method == "GET":
            resp = requests.get(self.endpoint, params={"action": action, **(data or {})}, timeout=15)
        else:
            payload = {"action": action, **(data or {})}
            resp = requests.post(self.endpoint, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------
    # パブリック API
    # ------------------------------

    def init_db(self) -> None:
        self._request("init_database", method="POST")

    def get_companies(self) -> pd.DataFrame:
        res = self._request("get_companies")
        return pd.DataFrame(res.get("companies", []))

    def add_company(self, company: Dict[str, Any]) -> str:
        res = self._request("add_company", method="POST", data={"company": company})
        return res.get("company_id", "")

    def update_status(self, company_id: str, new_status: str, note: str = "") -> None:
        self._request(
            "update_status", method="POST",
            data={"company_id": company_id, "new_status": new_status, "note": note},
        )

    def get_analytics(self) -> Dict[str, Any]:
        return self._request("get_analytics", method="POST")

# ---------------------------------------------------------------------------
# ビジネスロジック
# ---------------------------------------------------------------------------

class RelevanceCalculator:
    @staticmethod
    def score(text: str) -> int:
        text_lower = text.lower()
        return sum(10 for kw in PICOCELA_KEYWORDS if kw in text_lower)

    @classmethod
    def enrich(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        full_text = " ".join(str(row.get(k, "")) for k in ("company_name", "industry", "notes"))
        score = cls.score(full_text)
        row["picocela_relevance_score"] = min(score, 100)
        row["wifi_required"] = 1 if "wifi" in full_text else 0
        row["priority_score"] = min(score + (50 if row["wifi_required"] else 0), 150)
        return row

# ---------------------------------------------------------------------------
# Streamlit UI Sections
# ---------------------------------------------------------------------------

def ui_connection_settings() -> Optional[GoogleSheetsAPI]:
    """初回起動時に Apps Script URL を登録する UI"""

    if "gas_url" not in st.session_state:
        with st.expander("🔌 Google Apps Script URL を設定", expanded=True):
            url = st.text_input(
                "Google Apps Script の Web アプリ URL",
                placeholder="https://script.google.com/macros/s/XXXXX/exec",
            )
            if st.button("接続テスト", type="primary"):
                try:
                    api = GoogleSheetsAPI(url)
                    st.session_state.gas_url = url
                    st.success("接続成功！")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        return None

    # すでに URL 登録済み → API クライアント返却
    try:
        return GoogleSheetsAPI(st.session_state.gas_url)
    except Exception as e:
        st.error(str(e))
        del st.session_state.gas_url
        return None

def ui_dashboard(api: GoogleSheetsAPI) -> None:
    st.header("📊 ダッシュボード")
    df = api.get_companies()
    total = len(df)
    wifi_needed = len(df[df["wifi_required"] == 1]) if not df.empty else 0

    c1, c2 = st.columns(2)
    with c1:
        st.metric("総企業数", total)
    with c2:
        pct = f"{wifi_needed/total*100:.1f}%" if total else "0%"
        st.metric("WiFi 必要企業", wifi_needed, pct)

    analytics = api.get_analytics().get("analytics", {})
    status_breakdown = analytics.get("status_breakdown", {})
    if status_breakdown:
        s_df = pd.DataFrame({"status": list(status_breakdown.keys()), "count": list(status_breakdown.values())})
        fig = px.pie(s_df, values="count", names="status", title="ステータス別分布")
        st.plotly_chart(fig, use_container_width=True)


def ui_data_import(api: GoogleSheetsAPI) -> None:
    st.header("📁 データインポート")
    up = st.file_uploader("CSV / Excel を選択", type=["csv", "xlsx"])
    if not up:
        return

    try:
        if up.name.endswith(".csv"):
            df = pd.read_csv(up)
        else:
            df = pd.read_excel(up)
    except Exception as e:
        st.error(f"読込エラー: {e}")
        return

    st.write("プレビュー", df.head())
    if st.button("インポート実行", type="primary"):
        bar = st.progress(0)
        for i, row in df.iterrows():
            enriched = RelevanceCalculator.enrich(row.to_dict())
            api.add_company(enriched)
            bar.progress((i + 1) / len(df))
        st.success("取り込み完了！")
        st.balloons()

# ---------------------------------------------------------------------------
# Streamlit アプリ本体
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.title("🚀 " + PAGE_TITLE)

    api = ui_connection_settings()
    if not api:
        st.stop()

    api.init_db()  # 何度呼んでも問題ない設計（Apps Script 側で存在チェック）

    menu = st.sidebar.selectbox(
        "📚 メニュー",
        ["ダッシュボード", "データインポート"],
    )

    if menu == "ダッシュボード":
        ui_dashboard(api)
    elif menu == "データインポート":
        ui_data_import(api)


if __name__ == "__main__":
    main()
