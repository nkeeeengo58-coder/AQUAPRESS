# AQUA PRESS

AQUA PRESS は、YouTube Shorts / TikTok / Instagram Reels 向けの半自動動画生成プロジェクトです。  
無料〜低コスト中心で、情報系ショート動画を継続的に作ることを目的にしています。

## 目的

- 毎日1本を低コストで継続投稿できる状態を目指す
- API費用を抑える
- GitHubで管理しやすい構成にする
- Python中心で実装する
- 将来的に高性能AIへ切り替え可能にする

## v0.1 の目的

v0.1 では API連携や自動投稿は行わず、以下の最小構成を作ります。

- 画像2枚 + 台本テキスト + 任意の音声/BGM からショート動画を生成
- 1080x1920 / 40秒前後 / mp4 を出力
- 黒・白・赤ベースの AQUA PRESS 風デザイン

## 無料〜低コスト中心の方針

- 高額なAI動画生成は使わない
- まずは静止画 + テロップ + 音声 + BGM で運用
- 8割自動の半自動運用を先に確立
- 収益化後に高性能AIを段階導入

## セットアップ

```bash
cd aqua-press
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 実行方法

```bash
cd aqua-press
python src/main.py
```

- 入力: `input/sample_data/sample_video.json`
- 出力: `output/videos/aqua_press_sample.mp4`

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

## 現在できること（v0.1）

- JSON入力からショート動画を1本生成
- 画像がなくてもプレースホルダーで続行
- ナレーション音声/BGMがなければ無音で続行
- 出力フォルダを自動作成

## 今後の拡張予定

- Gemini API（台本生成）
- VOICEVOX（音声生成）
- GitHub Actions（自動化）
- YouTube API（投稿連携）
- TikTok / Reels 対応の運用最適化
- OpenAI API
- Claude API
- ElevenLabs
- Runway
- Veo
