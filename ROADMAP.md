# AQUA PRESS ロードマップ

## 現在の状況
- ✅ **v0.1 完了**：動画生成パイプライン、テロップ、BGM、サムネイル、テスト動作
- ❌ **未実装**：VOICEVOX、Gemini、情報取得、自動投稿

---

## 実装順序と優先度

### **Phase 1: 見た目確認と微調整（即座・推奨）**

**目的**：実画像での見た目を確認し、色・配置・フォントを最適化

**実装内容**
- `input/images/sample1.jpg`、`sample2.jpg` を用意（水族館やアロワナの画像）
- `config/video_style.yaml` で以下を試験的に調整：
  - フォントサイズ、テロップ背景透明度
  - 赤アクセントラインの配置位置
  - 画像と字幕の距離
- サンプル mp4 を再生して世界観が AQUA PRESS らしいか検証

**所要時間**：30分

**次ステップへの影響**：高（見た目が完成していないと、その後の展開に支障）

---

### **Phase 2: VOICEVOX 連携（v0.2・推奨優先度 1）**

**目的**：無料で高品質なナレーション音声を毎日自動生成

**実装内容**
- `src/audio/voicevox.py` を追加
  - VOICEVOX HTTP API（localhost:50021）連携
  - テキスト → wav 変換機能
  - 話者選択（女性ニュース風推奨）、速度調整
- `sample_video.json` に `narration_text` フィールドを追加
- ナレーション音声自動生成→動画合成の流れを実装
- エラー処理：VOICEVOX が起動していない場合は警告で継続

**関連変更**
- `src/main.py`：VOICEVOX 有効化フラグ
- `tests/test_video.py`：VOICEVOX モック テスト追加

**所要時間**：2～3時間

**次ステップへの影響**：高（毎日回す準備が整う）

---

### **Phase 3: Gemini Flash 連携（v0.3）**

**目的**：台本テキストを自動生成し「8割自動」に近づく

**実装内容**
- `src/ai/gemini_script.py` を追加
  - 情報テキスト（URL、ニュース、セール情報など）から 40秒向けショート台本生成
  - プロンプト：「AQUA PRESS 風の落ち着いたニュース調」を指定
  - 出力スキーマ：hook, sections, narration_text, cta など
- `.env` に `GEMINI_API_KEY` を設定
- 無料枠（日次呼び出し回数など）を管理する方針をドキュメント化
- `generate_video()` に新しい入力モード対応（URL → 動画）

**関連変更**
- `README.md`：Gemini API キーの取得方法を記載
- `.env.example`：`GEMINI_API_KEY=` を記入例として示す
- `tests/test_video.py`：Gemini API モック テスト

**所要時間**：3～4時間

**次ステップへの影響**：高（台本作成の手作業が大幅削減）

---

### **Phase 4: 情報取得モジュール（Crawler・v0.4）**

**目的**：アクアリウム関連の情報をリアルタイムで取得し、毎日素材供給

**実装内容**
- `src/crawler/aquarium_sources.py` を追加
  - 特定のアクアリウム店サイト、RSS フィード、ニュースサイトをスクレイピング
  - 生体入荷速報、セール情報、トレンドの抽出
  - 構造化データ（タイトル、説明、URL など）に変換
  - `input/sample_data/` に JSON 形式で自動保存
- `requirements.txt` に `requests`, `BeautifulSoup4`, `feedparser` を追加
- エラー処理：スクレイピング失敗時の通知、リトライ機構

**関連変更**
- `.github/workflows/` に Crawler スケジューラを追加検討
- `tests/test_video.py`：Crawler のモック テスト

**所要時間**：4～5時間

**次ステップへの影響**：中（GitHub Actions の前提）

---

### **Phase 5: GitHub Actions による自動化（v0.5）**

**目的**：毎日自動で情報取得 → 台本生成 → ナレーション → 動画生成

**実装内容**
- `.github/workflows/daily_video.yml` を追加
  - 毎朝 9:00 UTC（日本時間 18:00）に実行
  - 1. Crawler で情報取得
  - 2. Gemini で台本生成
  - 3. VOICEVOX でナレーション音声生成
  - 4. `generate_video()` で mp4 生成
  - 5. Slack / メール通知（生成完了）
- 半自動運用：GitHub Actions で生成、人間が確認して投稿

**関連変更**
- リポジトリ設定：Secrets に `GEMINI_API_KEY` を登録
- `README.md`：GitHub Actions の有効化方法を記載

**所要時間**：2～3時間

**次ステップへの影響**：高（継続投稿体制の確立）

---

### **Phase 6: 投稿自動化（v1.0・長期目標）**

**目的**：YouTube、TikTok、Instagram Reels への自動投稿

**実装内容**
- `src/posting/youtube_poster.py`：YouTube API 連携
- `src/posting/tiktok_poster.py`：TikTok API 連携（可能なら）
- `src/posting/instagram_poster.py`：Instagram Graph API 連携
- メタデータ（説明文、ハッシュタグ、カテゴリ）の自動設定
- 予約投稿スケジュール管理

**関連変更**
- `.env.example`：各プラットフォームの API キーを記載
- `requirements.txt`：各プラットフォームのライブラリ追加

**所要時間**：各プラットフォーム 2～3時間

**次ステップへの影響**：中（収益化後に検討）

---

## 優先度マトリックス

| Phase | タスク | 時間 | 難度 | 次への影響 | 推奨 |
|-------|--------|------|------|----------|------|
| 1 | 見た目調整 | 30分 | 低 | **高** | 🔴 今すぐ |
| 2 | VOICEVOX | 2-3h | 中 | **高** | 🔴 次週内 |
| 3 | Gemini | 3-4h | 中 | **高** | 🟡 2週間内 |
| 4 | Crawler | 4-5h | 高 | 中 | 🟡 3週間内 |
| 5 | GitHub Actions | 2-3h | 中 | **高** | 🟡 1ヶ月内 |
| 6 | 投稿自動化 | 2-3h/各 | 高 | 中 | 🟢 長期目標 |

---

## 次ステップの推奨

### **最短経路（推奨）**
1. **Phase 1**（見た目確認）→ 30分で完了、モチベーション UP
2. **Phase 2**（VOICEVOX）→ 2-3時間、毎日回す準備完了
3. **Phase 3**（Gemini）→ 3-4時間、「8割自動」実現
4. **Phase 5**（GitHub Actions）→ 2-3時間、完全自動投稿体制

### **最短時間でプロトタイプ完成**
Phase 1 → Phase 2 → Phase 5（投稿は手動） = 約 5-6時間

### **最初の 1 週間の目安**
- 月：Phase 1（見た目調整）
- 火～水：Phase 2（VOICEVOX 連携）
- 木～金：Phase 3（Gemini 連携）
- 土日：テスト、微調整、ドキュメント化

---

## 判断ポイント

- **「今これやりたい」なら**→ Phase 2（VOICEVOX）から始めるのが吉
- **「見た目が心配」なら**→ Phase 1（見た目調整）を先にやる
- **「毎日自動にしたい」なら**→ Phase 5（GitHub Actions）をスキップせず含める
- **「収益化まで見据える」なら**→ Phase 6（投稿自動化）をロードマップに追加

---

## 参考リンク・情報

- VOICEVOX：https://voicevox.hiroshiba.jp/ （無料、API ドキュメント有）
- Gemini API：https://ai.google.dev/docs （無料枠月 900 リクエスト）
- YouTube Data API：https://developers.google.com/youtube/v3
- GitHub Actions：https://docs.github.com/ja/actions
