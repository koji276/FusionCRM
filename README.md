# 🚀 FusionCRM - PicoCELA統合CRMシステム

PicoCELA社のメッシュネットワーク技術に関連する建設業界パートナー候補の発掘と管理を自動化する統合CRMシステム。

## ✨ 主要機能

- 📧 **Gmail統合メール配信システム**
- 🏢 **企業データ管理**
- 📊 **営業活動ダッシュボード**
- 🎯 **自動化メールキャンペーン**
- 📈 **データ分析・レポート**

## 🛠️ システム構成

### Core Components
- **FusionReach**: ENR企業情報自動収集システム（完了）
- **FusionCRM**: Streamlitベース包括的CRMシステム（実稼働中）

### Technology Stack
- **Backend**: Python 3.10+
- **Frontend**: Streamlit
- **Database**: SQLite
- **Email**: Gmail SMTP
- **Deployment**: Streamlit Cloud

## 📦 インストール

### 1. リポジトリクローン
```bash
git clone https://github.com/koji276/FusionCRM.git
cd FusionCRM
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. システム起動
```bash
streamlit run fusion_crm_main.py --server.port 8504
```

## ⚙️ 初期設定

### Gmail設定
1. Gmailアプリパスワードを取得
2. システム起動後、「設定」ページでGmail認証情報を入力
3. 接続テストを実行

### データベース初期化
- 初回起動時に自動的にSQLiteデータベースが作成されます
- ENRデータのインポートは「データ管理」ページから実行

## 📊 データ構造

### 企業テーブル
- `company_name`: 企業名
- `email_address`: メールアドレス
- `website`: ウェブサイトURL
- `phone`: 電話番号
- `status`: ステータス（New/Contacted/Replied/Qualified）
- `picocela_relevance_score`: PicoCELA関連度スコア

### メール履歴テーブル
- `company_id`: 企業ID
- `email_type`: メールタイプ
- `status`: 送信ステータス
- `sent_at`: 送信日時

## 🎯 使用方法

### 1. ダッシュボード
- 企業ステータス分布
- メール送信トレンド
- 主要メトリクス表示

### 2. 企業管理
- 企業データの表示・検索・フィルタリング
- ステータス管理
- 関連度スコア確認

### 3. メールキャンペーン
- 対象企業選択（ステータス別）
- テンプレート選択
- 一括メール送信実行

### 4. 設定
- Gmail SMTP設定
- データインポート（CSV/Excel）
- システム設定

## 📧 メールテンプレート

### Initial Contact
```
件名: PicoCELA メッシュネットワークソリューションのご案内
内容: 建設現場での通信インフラ構築提案
```

### Follow-up
```
件名: PicoCELA メッシュネットワーク - フォローアップ
内容: 追加質問・相談対応
```

## 🔧 高度な設定

### バッチサイズ調整
```json
{
  "email_distribution": {
    "batch_size": 20,
    "daily_limit": 500,
    "delay_range": [3, 8]
  }
}
```

### Gmail設定ファイル
```json
{
  "email": "tokuda@picocela.com",
  "sender_name": "PicoCELA Inc.",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

## 📈 プロジェクト進捗

### Phase 1: 基本システム開発 ✅
- [x] FusionReach開発完了
- [x] 基本CRM機能実装
- [x] Gmail統合完了

### Phase 2: 安定化・クラウド展開 🔄
- [x] エラー修正・安定化
- [x] Streamlit Cloud準備
- [ ] ENRデータ完全統合
- [ ] チーム利用開始

### Phase 3: スケールアップ 📋
- [ ] HubSpot代替機能
- [ ] 300社同時対応
- [ ] 商用展開準備

## 📊 実績データ

### FusionReach成果
- **処理実績**: 150社（309社中の48.5%）
- **URL発見率**: 約85%
- **メール取得率**: 約90%
- **PicoCELA関連企業**: 複数社特定

### システム安定性
- **稼働状況**: ✅ 8日間継続稼働
- **エラー率**: 0%
- **送信成功率**: 95%以上

## 🌐 クラウド展開計画

### 推奨構成
- **データ保存**: Google Drive（CSV/Excel）
- **システム**: Streamlit Cloud（有料版）
- **認証**: OAuth（Google Cloudプロジェクト）
- **利用者**: PicoCELAチーム（数名）

### メリット
- 完全無料（Streamlit有料版活用）
- 24時間稼働
- チーム全員アクセス可能
- 既存データ活用

## 🔮 将来展望

### FusionCRM Pro
- **目標**: HubSpot代替（月3-8万円 → 月1万円）
- **特徴**: 機能追加永久無料
- **市場**: 300社獲得（年間売上3,600万円）

### 技術戦略
- Streamlit有料版による300社同時対応
- 段階的プライシング（従業員数制限型）
- Google Drive/Sheets完全統合

## 🏆 開発チーム

- **プロジェクトリーダー**: 徳田様
- **開発チーム**: PicoCELA開発チーム
- **連絡先**: tokuda@picocela.com

## 📝 ライセンス

このプロジェクトはPicoCELA社の内部使用を目的としています。

## 🆘 サポート

### トラブルシューティング
1. **Streamlitエラー**: キャッシュクリア実行
2. **Gmail接続エラー**: アプリパスワード再設定
3. **データベースエラー**: SQLiteファイル権限確認

### 連絡先
- **Email**: tokuda@picocela.com
- **GitHub**: https://github.com/koji276/FusionCRM

---

## 📅 更新履歴

### v1.0.0 (2025-07-16)
- ✅ 基本システム完成
- ✅ Gmail統合実装
- ✅ エラー修正・安定化
- ✅ クラウド展開準備

---

**🚀 FusionCRM - Powering PicoCELA's Business Growth**
