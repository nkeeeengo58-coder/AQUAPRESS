# AQUA PRESS

AQUA PRESS は、YouTube Shorts / TikTok / Instagram Reels 向けの、アクアリウム情報に特化した半自動ショート動画生成プロジェクトです。

黒ベース、白文字、赤アクセントの落ち着いたニュースメディア風の世界観で、セール速報、生体入荷速報、アクアリウム小ネタを短尺で継続投稿することを目指します。

## 目的

- 無料〜低コスト中心で運用する
- 毎日1本の継続投稿を目指す
- 最初から完全自動化せず、まずは 8割自動 にする
- 将来的に Gemini API や VOICEVOX、自動投稿へ拡張しやすい構成にする
- GitHub で管理しやすい Python 中心の構成にする

## v0.1 の目的

v0.1 では、外部 API 連携や自動クローリングはまだ行わず、以下の最小構成を動かします。

- 入力: 画像2枚、台本テキスト、タイトル、説明文、任意のナレーション音声、任意の BGM
- 出力: 1080x1920 の mp4 動画
- 形式: 黒背景、白文字、赤アクセント、静止画 + テロップ + 音声 + BGM
- 実行: `python src/main.py` でサンプル動画を生成

## 現在できること

- `input/sample_data/sample_video.json` を読み込んで mp4 を生成する
- 画像が存在しない場合でも、黒背景 + プレースホルダーで継続する
- テロップを Pillow で生成し、MoviePy に渡して合成する
- 任意のナレーション音声と BGM を合成する
- 簡易サムネイルを PNG で出力する
- 出力フォルダを自動作成する

## セットアップ

### 1. Python を用意する

Python 3.10 以上を推奨します。

### 2. 仮想環境を作る

```bash
python -m venv .venv
```

### 3. 仮想環境を有効化する

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. 依存関係を入れる

```bash
pip install -r requirements.txt
```

## 実行方法

サンプル動画を生成します。

```bash
python src/main.py
```

見た目確認用の高速プレビューを生成する場合は、以下を実行します。

```powershell
$env:AQUAPRESS_PREVIEW="1"
python src/main.py
Remove-Item Env:AQUAPRESS_PREVIEW
```

生成物は次の場所に出力されます。

- `output/videos/aqua_press_sample.mp4`
- `output/videos/preview_aqua_press_sample.mp4` (プレビューモード)
- `output/thumbnails/aqua_press_thumbnail.png`

## フォルダ構成

```text
aqua-press/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ config/
│  └─ video_style.yaml
├─ assets/
│  ├─ bgm/
│  ├─ backgrounds/
│  ├─ fonts/
│  └─ logos/
├─ input/
│  ├─ images/
│  ├─ audio/
│  └─ sample_data/
├─ output/
│  ├─ videos/
│  ├─ thumbnails/
│  └─ metadata/
├─ src/
│  ├─ main.py
│  ├─ video/
│  │  ├─ generator.py
│  │  ├─ captions.py
│  │  └─ thumbnail.py
│  ├─ audio/
│  │  └─ bgm.py
│  ├─ ai/
│  │  └─ README.md
│  ├─ crawler/
│  │  └─ README.md
│  └─ utils/
│     └─ paths.py
└─ tests/
   └─ test_video.py
```

## 設定

`config/video_style.yaml` で、画面サイズ、色、フォントサイズ、BGM音量などを調整できます。

`.env.example` は将来の API 用です。v0.1 では使いません。

## 今後の拡張予定

- Gemini API: 台本生成、要約、情報整理
- VOICEVOX: 無料のナレーション生成
- GitHub Actions: 定期実行や自動ビルド
- YouTube API: 投稿・予約投稿
- TikTok / Reels 対応: 半自動から段階的に拡張
- OpenAI API: 収益化後の高品質生成
- Claude API: 代替 AI として検討
- ElevenLabs: 高品質音声
- Runway: 映像素材の高度化
- Veo: 将来的な高品質動画生成

## 低コスト方針

- まずは無料枠とローカル生成を優先する
- AI 動画生成サービスは最初から使わない
- 静止画 + テロップ + 音声 + BGM で成立させる
- 完全自動化より継続運用を優先する

## 将来の AI 連携

将来的には、`src/ai/README.md` の方針に沿って Gemini Flash を中心に台本生成を組み込みます。さらに収益化後は、OpenAI API、Claude API、ElevenLabs、Runway、Veo などを必要に応じて追加します。

## 将来の情報取得

`src/crawler/README.md` にある通り、requests、BeautifulSoup、feedparser、RSS を中心に情報取得モジュールを追加する予定です。SNS 取得は規約に注意して段階的に扱います。
