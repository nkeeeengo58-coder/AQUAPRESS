# Phase 5: GitHub Actions 自動実行

## 概要
毎日 UTC 08:00（日本時間 17:00）に GitHub Actions で自動実行されます。
- Crawler で最新情報取得
- Gemini Flash でスクリプト生成
- 生成データを自動コミット

## セットアップ手順

### 1. GitHub Secrets 設定

GitHub リポジトリの **Settings → Secrets and variables → Actions** で以下を追加：

| Secret 名 | 値 | 説明 |
|-----------|-----|------|
| `GEMINI_API_KEY` | あなたの API キー | [Google AI Studio](https://aistudio.google.com/app/apikey) から取得 |

**設定方法:**
1. GitHub リポジトリを開く
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** をクリック
4. Name: `GEMINI_API_KEY`
5. Secret: あなたの Gemini API キー をペースト
6. **Add secret** をクリック

### 2. ワークフロー実行確認

**手動トリガーでテスト:**
1. GitHub リポジトリの **Actions** タブを開く
2. **Daily AQUA PRESS Video Generation** を選択
3. **Run workflow** → **Run workflow** をクリック
4. 実行ログを確認

**スケジュール実行確認:**
- ワークフロー定義で `cron: '0 8 * * *'` に設定済み
- UTC 08:00 毎日自動実行開始

### 3. 実行ログ確認

GitHub Actions の実行ログは以下で確認：
- **Actions** タブ → **Daily AQUA PRESS Video Generation** → 各実行の詳細

ローカル環境でテストしたい場合：
```bash
# Crawler 実行
python src/main.py --crawler

# 指定日付のデータで実行
python src/main.py --crawler-date 2026-05-17
```

## ワークフロー内容

```yaml
トリガー: 毎日 UTC 08:00
├─ Crawler 実行（RSS + HTML）
├─ 情報をテキスト化
├─ Gemini Flash でスクリプト生成
└─ 結果を metadata/ に保存
```

## トラブルシューティング

### エラー: `ModuleNotFoundError: No module named 'feedparser'`
→ requirements.txt に依存関係が含まれている確認（既に追加済み）

### エラー: `Gemini API key is invalid`
→ GitHub Secrets に `GEMINI_API_KEY` が正しく設定されているか確認

### ワークフローが実行されない
→ **Settings** → **Actions** で **Allow GitHub Actions to create and approve pull requests** が有効か確認

## 実行結果

生成されたデータは以下の場所に保存：
```
metadata/
├── generated_script_YYYY-MM-DD_HH-MM-SS.json  # Gemini 生成スクリプト
└── crawler_data_YYYY-MM-DD.json               # Crawler データ
```

## 今後の拡張

- [ ] ビデオ生成を GitHub Actions に追加（MoviePy のみで VOICEVOX 不要版）
- [ ] YouTube への自動アップロード
- [ ] Slack 通知の追加
- [ ] 生成データの可視化ダッシュボード

## リファレンス

- [GitHub Actions スケジュール実行](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [GitHub Secrets 管理](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Python actions/setup-python](https://github.com/actions/setup-python)
