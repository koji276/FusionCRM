# 🚀 FusionCRM - PicoCELA統合CRMシステム

PicoCELA社のメッシュネットワーク技術に関連する建設業界パートナー候補の発掘と管理を自動化する統合CRMシステム。**完全クラウド対応Google Sheets版 + 統合プラットフォーム**。

## ✨ 主要機能

* 🚀 **統合プラットフォーム** - 1つの画面でCRM + メール完結
* 📧 **Gmail統合メール配信システム**
* 🏢 **企業データ管理（リアルタイム同期）**
* 📊 **営業活動ダッシュボード**
* 🎯 **自動化メールキャンペーン**
* 📈 **データ分析・レポート**
* 🆕 **拡張ステータス管理（10段階）**
* ☁️ **完全クラウドベース（Google Sheets）**
* 🔐 **セキュア認証システム**

## 🛠️ システム構成（v12.0統合版）

### 🌟 新しい統合アーキテクチャ
```
fusion_crm_unified.py          # 🚀 統合ダッシュボード（メインエントリー）
├── pages/
│   ├── 01_🏢_CRM管理.py       # 企業管理システム
│   └── 02_📧_メール配信.py     # メール配信システム
├── modules/                   # メール関連モジュール
│   ├── email_customizers.py
│   ├── email_database.py
│   ├── email_sender.py
│   ├── batch_processing.py
│   └── data_manager.py
├── crm_modules/              # CRM関連モジュール
│   ├── constants.py
│   ├── google_sheets_api.py
│   ├── data_processor.py
│   ├── company_manager.py
│   ├── crm_dashboard.py
│   ├── data_import.py
│   └── ui_components.py
└── fusion_users.db           # ユーザー認証データベース
```

### Core Components
* **FusionReach**: ENR企業情報自動収集システム（完了）
* **FusionCRM Unified**: Streamlit Multipage統合プラットフォーム（稼働中）
* **Legacy Systems**: 個別システム（統合移行中）

### Technology Stack
* **Backend**: Python 3.10+ / Google Apps Script
* **Frontend**: Streamlit Multipage
* **Database**: Google Sheets（リアルタイム同期）+ SQLite（認証）
* **Email**: Gmail SMTP
* **Deployment**: Streamlit Cloud / Google Cloud

## 🚀 クイックスタート（5分で完了！）

### 1. リポジトリクローン
```bash
git clone https://github.com/koji276/FusionCRM.git
cd FusionCRM
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. 統合システム起動 🆕
```bash
# 統合プラットフォームを起動
streamlit run fusion_crm_unified.py
```

#### または個別システム起動
```bash
# CRM管理のみ
streamlit run fusion_crm_main.py

# メール配信のみ
streamlit run email_webapp.py
```

### 4. 初回ユーザー登録
1. ブラウザで http://localhost:8501 にアクセス
2. 「新規ユーザー登録」をクリック
3. ユーザー情報を入力
4. 管理者承認後、ログイン可能

## 🎯 使用方法（統合プラットフォーム）

### 📊 統合ダッシュボード
1. **統合認証システム**: セキュアなログイン・権限管理
2. **リアルタイム統計**: 企業数・成約率・月次パフォーマンス
3. **システム状況**: 各コンポーネントの稼働状況表示
4. **クイックアクション**: CRM管理・メール送信・分析への1クリック移動

### 🏢 CRM管理（pages/01_🏢_CRM管理.py）
* **企業データ管理**: リアルタイム検索・フィルタリング
* **10段階ステータス管理**: New → Won まで詳細追跡
* **PicoCELA関連度スコア**: 自動計算・優先度付け
* **Google Sheets同期**: チーム全体でリアルタイム共有

### 📧 メール配信（pages/02_📧_メール配信.py）
* **CRM連携配信**: 企業ステータス別ターゲティング
* **AI業界特化**: GPT-3.5による自動カスタマイズ
* **一括送信**: WiFi需要企業への優先配信
* **送信結果追跡**: 自動ステータス更新

### 🔄 統合ワークフロー 🆕
1. **CRM画面で企業選定** → 2. **メール画面で一括生成** → 3. **送信実行** → 4. **ステータス自動更新**

## ⚙️ 初期設定

### Google Sheets接続
1. [Google Apps Script](https://script.google.com/)で新プロジェクト作成
2. `google_apps_script.gs`の内容をコピー&ペースト
3. ウェブアプリとして公開・URLコピー
4. 統合システムの設定画面でURL入力

### Gmail設定
1. Gmailアプリパスワード取得
2. メール配信画面で認証情報入力
3. 接続テスト実行

### 認証システム設定 🆕
```bash
# .streamlit/secrets.toml
admin_password = "your_admin_password"
google_apps_script_url = "YOUR_SCRIPT_URL"
gmail_username = "your_gmail@gmail.com"
gmail_password = "your_app_password"
```

## 📊 データ構造（Google Sheets）

### 企業シート（companies）
* `company_id`: 企業ID（自動生成）
* `company_name`: 企業名
* `email`: メールアドレス
* `phone`: 電話番号
* `website_url`: ウェブサイトURL
* `sales_status`: 営業ステータス（拡張10段階）
* `wifi_required`: WiFi需要フラグ
* `priority_score`: 優先度スコア（0-150）
* `picocela_relevance_score`: PicoCELA関連度スコア（0-100）

### ユーザー管理（SQLite） 🆕
* `user_id`: ユーザーID
* `username`: ユーザー名
* `email`: メールアドレス
* `password_hash`: パスワードハッシュ
* `role`: 権限（admin/user）
* `approved`: 承認状況
* `created_at`: 作成日時

## 🎯 拡張ステータス（10段階）

| ステータス | 説明 | 次のアクション | 自動メール |
|-----------|------|----------------|------------|
| New | 新規企業 | 初回連絡 | ✅ 初回提案 |
| Contacted | 初回連絡済み | フォローアップ | ⏱️ 3日後 |
| Replied | 返信あり | ミーティング設定 | ✅ ミーティング提案 |
| **Engaged** 🆕 | 継続対話中 | 現場訪問 | ⏱️ 1週間後 |
| Qualified | 有望企業確定 | 提案書作成 | ✅ 詳細提案 |
| **Proposal** 🆕 | 提案書提出済み | 検討フォロー | ⏱️ 2週間後 |
| **Negotiation** 🆕 | 契約交渉中 | 条件調整 | ✅ 条件調整 |
| **Won** 🆕 | 受注成功 | 導入支援 | ✅ 導入開始 |
| Lost | 失注 | 関係維持 | ⏱️ 3ヶ月後 |
| **Dormant** 🆕 | 休眠中 | 再活性化 | ⏱️ 6ヶ月後 |

## 🔐 セキュリティ・認証システム

### 実装済み機能 🆕
* **ユーザー登録・認証**: セキュアなパスワード管理
* **管理者権限システム**: 階層的権限管理
* **セッション管理**: 安全なログイン状態管理
* **データベース保護**: SQLインジェクション対策

### 管理者機能
* **ユーザー管理**: 承認・編集・削除
* **システム統計**: リアルタイム稼働状況
* **権限管理**: 管理者昇格・降格
* **緊急対応**: パスワードリセット・アカウント復旧

## 📈 プロジェクト進捗

### Phase 1: 基本システム開発 ✅
* FusionReach開発完了
* 基本CRM機能実装
* Gmail統合完了

### Phase 1.5: 統合基盤構築 ✅ 🆕
* **統合認証システム**: セキュア認証・管理者パネル
* **Multipage構成**: ページ分離・ナビゲーション統合
* **モジュール分離**: 保守性・拡張性向上
* **データベース互換性**: 新旧システム完全連携

### Phase 2: 実機能統合 🔄 **現在進行中**
* **CRM機能統合**: fusion_crm_main.py → 統合画面
* **メール機能統合**: email_webapp.py → 統合画面
* **データ統合**: Google Sheets ↔ SQLite 双方向同期
* **ワークフロー自動化**: 企業選定 → メール生成 → 送信

### Phase 3: 機能拡張 📅 **今後2週間**
* **英語メールテンプレート拡張**
* **自動返信検知システム**
* **Gmail制限対策強化**

### Phase 4: 高度分析 📅 **1-3ヶ月以内**
* **成約予測AI**
* **高度分析ダッシュボード**
* **効果測定機能**

## 🌐 クラウドアーキテクチャ

### 統合システム構成 🆕
```
Streamlit Cloud (fusion_crm_unified.py)
├── Multipage Navigation
│   ├── 📊 統合ダッシュボード
│   ├── 🏢 CRM管理
│   └── 📧 メール配信
├── Authentication System (SQLite)
└── Data Layer
    ├── Google Sheets (CRM Data)
    ├── Google Apps Script API
    └── Gmail SMTP
```

### メリット
* **1つの画面で完結**: CRM + メール管理
* **セキュア認証**: ユーザー管理・権限制御
* **リアルタイム同期**: チーム全体データ共有
* **完全無料運用**: Google無料枠活用

## 📊 実績データ

### 営業成果（実証済み）
* **50社自動送信** → **副社長即日返信獲得**
* **NASDAQ上場企業副社長**からの休日即日返信
* **関連度スコア110点企業**での成功実証
* **パートナーシップ提案アプローチ**の威力実証

### 効率化実績
* **従来**: 450社DM作成に1.5ヶ月（300時間）
* **現在**: 50社自動送信（待機のみ）
* **ROI**: 効率的な営業活動を実現

## 💡 戦略的考慮事項

### スケーラビリティ対応
* **現在**: Google Sheets（~1万社対応可能）
* **将来選択肢**:
  * SQLite復活 + ファイルベースDBホスティング
  * 低コストクラウドDB（Railway.app/Render.com等）
  * ハイブリッド構成（Google Sheets + SQLite併用）
* **AWS回避**: コスト最適化戦略（月額$10-30 vs AWS $50+）

## 🔗 システムURL

### 稼働中システム
* **統合プラットフォーム**: [fusion_crm_unified.py] - メイン統合システム
* **CRMシステム**: [fusion_crm_main.py] - 企業管理システム  
* **メールシステム**: [email_webapp.py] - メール配信システム
* **GitHub**: https://github.com/koji276/FusionCRM

## 🎯 今後のNext Actions

### 今週完了目標
1. **CRM機能統合**: fusion_crm_main.pyの機能を統合画面に実装
2. **メール機能統合**: email_webapp.pyの機能を統合画面に実装  
3. **統合テスト**: 全機能の動作確認

### 今月達成目標
1. **完全統合システム**: 1つの画面でCRM + メール操作
2. **1000社対応**: 本格的な英語メール配信開始
3. **商用化準備**: FusionCRM Pro ローンチ準備完了

## 🏆 開発チーム

* **プロジェクトリーダー**: 徳田
* **開発チーム**: PicoCELA開発チーム
* **連絡先**: tokuda@picocela.com

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🆘 サポート

### トラブルシューティング
1. **統合システム接続エラー**: 認証情報・ポート確認
2. **CRM連携エラー**: Google Apps Script URL確認
3. **メール送信エラー**: Gmail認証・制限確認
4. **認証エラー**: ユーザー承認状況・権限確認

### よくある質問
* **Q: 統合システムとは？** A: 1つの画面でCRM+メール管理できる新システム
* **Q: 既存システムは使える？** A: はい、個別起動も可能です
* **Q: データは同期される？** A: 統合システムで完全同期予定
* **Q: セキュリティは？** A: ユーザー認証・権限管理実装済み

### 連絡先
* **Email**: tokuda@picocela.com
* **GitHub**: https://github.com/koji276/FusionCRM
* **Issues**: [GitHub Issues](https://github.com/koji276/FusionCRM/issues)

## 📅 更新履歴

### v12.0 (2025-07-27) 🆕 **統合プラットフォーム完成**
* ✅ **統合認証システム**: セキュア認証・管理者パネル実装
* ✅ **Multipage構成**: ページ分離・統合ナビゲーション
* ✅ **モジュール分離**: 完全モジュール化・保守性向上
* ✅ **データベース互換性**: 新旧システム完全連携
* 🔄 **実機能統合**: CRM + メール機能統合（進行中）

### v2.0.0 (2025-01-XX)
* ✅ Google Sheets完全移行
* ✅ 拡張ステータス（10段階）実装
* ✅ リアルタイム同期対応
* ✅ 自動スコアリング機能

### v1.0.0 (2025-07-16)
* ✅ 基本システム完成
* ✅ Gmail統合実装
* ✅ エラー修正・安定化

---

## 🚀 FusionCRM v12.0 - 革新的統合プラットフォームで営業活動を変革
