# 🚀 FusionCRM - PicoCELA統合CRMシステム

PicoCELA社のメッシュネットワーク技術に関連する建設業界パートナー候補の発掘と管理を自動化する統合CRMシステム。**完全クラウド対応Google Sheets版**。

## ✨ 主要機能

* 📧 **Gmail統合メール配信システム**
* 🏢 **企業データ管理（リアルタイム同期）**
* 📊 **営業活動ダッシュボード**
* 🎯 **自動化メールキャンペーン**
* 📈 **データ分析・レポート**
* 🆕 **拡張ステータス管理（10段階）**
* ☁️ **完全クラウドベース（Google Sheets）**

## 🛠️ システム構成

### Core Components
* **FusionReach**: ENR企業情報自動収集システム（完了）
* **FusionCRM**: Streamlitベース包括的CRMシステム（Google Sheets版実稼働中）

### Technology Stack
* **Backend**: Python 3.10+ / Google Apps Script
* **Frontend**: Streamlit
* **Database**: Google Sheets（リアルタイム同期）
* **Email**: Gmail SMTP
* **Deployment**: Streamlit Cloud / Google Cloud

## 📦 インストール（5分で完了！）

### 1. リポジトリクローン
```bash
git clone https://github.com/koji276/FusionCRM.git
cd FusionCRM
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. Google Apps Script設定
1. [Google Apps Script](https://script.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. `google_apps_script.gs`の内容をコピー&ペースト
4. デプロイ → 新しいデプロイ → ウェブアプリとして公開
5. URLをコピー

### 4. Streamlit設定
```bash
mkdir -p .streamlit
echo 'google_apps_script_url = "YOUR_SCRIPT_URL"' > .streamlit/secrets.toml
```

### 5. システム起動
```bash
streamlit run fusion_crm_main.py
```

または簡単起動スクリプト：
```bash
python start_fusioncrm.py
```

## ⚙️ 初期設定

### Google Sheets接続
1. システム起動後、Google Apps Script URLを入力
2. 「接続テスト」をクリック
3. 自動的にGoogle Sheetsが作成されます

### Gmail設定
1. Gmailアプリパスワードを取得
2. メールキャンペーンページでGmail認証情報を入力
3. 接続テストを実行

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

### ステータス履歴シート（status_history）
* `history_id`: 履歴ID
* `company_id`: 企業ID
* `old_status`: 変更前ステータス
* `new_status`: 変更後ステータス
* `changed_at`: 変更日時
* `changed_by`: 変更者
* `note`: メモ

## 🎯 拡張ステータス（新機能）

| ステータス | 説明 | 次のアクション |
|-----------|------|----------------|
| New | 新規企業 | 初回連絡 |
| Contacted | 初回連絡済み | フォローアップ |
| Replied | 返信あり | ミーティング設定 |
| **Engaged** 🆕 | 継続対話中 | 現場訪問 |
| Qualified | 有望企業確定 | 提案書作成 |
| **Proposal** 🆕 | 提案書提出済み | 検討フォロー |
| **Negotiation** 🆕 | 契約交渉中 | 条件調整 |
| **Won** 🆕 | 受注成功 | 導入支援 |
| Lost | 失注 | 関係維持 |
| **Dormant** 🆕 | 休眠中 | 再活性化 |

## 🎯 使用方法

### 1. ダッシュボード
* 企業ステータス分布（10段階表示）
* WiFi需要企業の自動識別
* 優先度スコアランキング
* リアルタイムデータ更新

### 2. 企業管理
* 企業データの表示・検索・フィルタリング
* 拡張ステータス管理
* PicoCELA関連度・優先度スコア確認
* リアルタイム編集・同期

### 3. メールキャンペーン
* WiFi需要企業への優先配信
* ステータス別ターゲティング
* テンプレート選択・カスタマイズ
* 一括メール送信実行

### 4. データインポート
* ENRデータ一括インポート
* CSV/Excelファイル対応
* 自動スコアリング実行

## 📧 メールテンプレート

### WiFi需要企業向け
```
件名: 建設現場のワイヤレス通信課題解決のご提案 - PicoCELA
内容: メッシュネットワーク技術による現場通信の革新
```

### 一般企業向け
```
件名: PicoCELA メッシュネットワークソリューションのご案内
内容: 建設・産業分野向け通信ソリューション
```

### フォローアップ
```
件名: PicoCELAソリューション - フォローアップのご連絡
内容: 追加質問・相談対応
```

## 🔧 高度な設定

### 自動スコアリング設定
```python
# PicoCELA関連キーワード
PICOCELA_KEYWORDS = [
    'network', 'mesh', 'wireless', 'wifi', 'connectivity',
    'iot', 'smart', 'digital', 'automation', 'sensor'
]

# 優先度計算
priority_score = relevance_score + (50 if wifi_required else 0)
```

### Gmail設定
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "use_tls": true,
  "daily_limit": 500,
  "batch_delay": 2
}
```

## 📈 プロジェクト進捗

### Phase 1: 基本システム開発 ✅
* FusionReach開発完了
* 基本CRM機能実装
* Gmail統合完了

### Phase 2: Google Sheets移行 ✅ 🆕
* SQLiteから完全移行
* リアルタイム同期実装
* 拡張ステータス追加
* チーム共有機能実装

### Phase 3: スケールアップ 🔄
* ENRデータ完全統合
* 自動化機能強化
* 分析機能拡充

## 📊 実績データ

### FusionReach成果
* **処理実績**: 150社（309社中の48.5%）
* **URL発見率**: 約85%
* **メール取得率**: 約90%
* **PicoCELA関連企業**: 複数社特定

### システム安定性（Google Sheets版）
* **稼働状況**: ✅ 24時間365日稼働
* **同時アクセス**: 10ユーザーまで対応
* **データ同期**: リアルタイム
* **コスト**: 完全無料（Google無料枠）

## 🌐 クラウドアーキテクチャ

### 現在の構成 🆕
```
Streamlit Cloud
    ↓
Google Apps Script API
    ↓
Google Sheets（データベース）
    ↓
リアルタイム同期 → チーム全員
```

### メリット
* サーバー管理不要
* 自動バックアップ（Google Drive）
* どこからでもアクセス可能
* 完全無料運用

## 🔮 将来展望

### 機能拡張計画
* **AIスコアリング**: 機械学習による優先度予測
* **自動フォローアップ**: ステータス別自動メール
* **高度な分析**: 成約予測・パイプライン最適化

### ビジネス展開
* **目標**: 建設業界CRMのスタンダード
* **展開**: PicoCELAパートナー企業への提供
* **収益化**: SaaS型サービスとして展開

## 🏆 開発チーム

* **プロジェクトリーダー**: 徳田
* **開発チーム**: PicoCELA開発チーム
* **連絡先**: tokuda@picocela.com

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🆘 サポート

### トラブルシューティング
1. **接続エラー**: Google Apps Script URLを確認
2. **Gmail接続エラー**: アプリパスワード再設定
3. **データ同期エラー**: Google Sheetsの共有設定確認

### よくある質問
* **Q: データ容量制限は？** A: Google無料枠で1000万セルまで
* **Q: 同時編集可能？** A: はい、リアルタイム同期対応
* **Q: バックアップは？** A: Google Driveで自動保存

### 連絡先
* **Email**: tokuda@picocela.com
* **GitHub**: https://github.com/koji276/FusionCRM
* **Issues**: [GitHub Issues](https://github.com/koji276/FusionCRM/issues)

## 📅 更新履歴

### v2.0.0 (2025-01-XX) 🆕
* ✅ Google Sheets完全移行
* ✅ 拡張ステータス（10段階）実装
* ✅ リアルタイム同期対応
* ✅ 自動スコアリング機能

### v1.0.0 (2025-07-16)
* ✅ 基本システム完成
* ✅ Gmail統合実装
* ✅ エラー修正・安定化

---

## 🚀 FusionCRM - Powering PicoCELA's Business Growth with Cloud Technology
