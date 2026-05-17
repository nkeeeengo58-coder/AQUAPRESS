"""
Generate multi-language AQUA PRESS videos using sample data with localized narration.
Creates videos for Japanese, English, Chinese, and Thai.
"""

import json
import subprocess
import sys
from pathlib import Path

def create_language_sample(base_sample, language):
    """Create language-specific sample data with localized content."""
    
    lang_content = {
        "ja": {
            "title": "【速報】極上紅龍が入荷",
            "description": "本日のAQUA PRESS速報。大型魚・アロワナ好き向けに最新情報を毎日発信中。",
            "hook": "【速報】\n極上紅龍 入荷",
            "narration_text": "AQUA PRESS 速報です。本日の注目個体をお届けします。",
            "voicevox_speaker": 3,  # Japanese
        },
        "en": {
            "title": "【BREAKING NEWS】Premium Red Arowana Arrived",
            "description": "AQUA PRESS breaking news today. Daily updates for arowana enthusiasts and large fish lovers.",
            "hook": "【BREAKING NEWS】\nPremium Red\nArowana Arrived",
            "narration_text": "AQUA PRESS Breaking News. Today we bring you our featured specimen.",
            "voicevox_speaker": None,  # English not yet supported
        },
        "zh": {
            "title": "【速报】极品红龙已到货",
            "description": "今日的AQUA PRESS速报。为大型鱼和红龙爱好者每天提供最新信息。",
            "hook": "【速报】\n极品红龙\n已到货",
            "narration_text": "AQUA PRESS速报。今天为您介绍我们的特色品种。",
            "voicevox_speaker": None,
        },
        "th": {
            "title": "【ข่าวด่วน】ปลาโรนินสีแดงขั้นเทพ",
            "description": "AQUA PRESS ข่าวด่วนวันนี้ ข้อมูลประจำวันสำหรับผู้รักปลาโรนินและปลาบาทน้ำจืด",
            "hook": "【ข่าวด่วน】\nปลาโรนิน\nสีแดง",
            "narration_text": "AQUA PRESS ข่าวด่วน วันนี้เรานำเสนอตัวอย่างพิเศษของเรา",
            "voicevox_speaker": None,
        },
    }
    
    content = lang_content.get(language, lang_content["ja"])
    
    # Clone the base sample and update with language-specific content
    sample = base_sample.copy()
    sample["title"] = content["title"]
    sample["description"] = content["description"]
    sample["hook"] = content["hook"]
    sample["narration_text"] = content["narration_text"]
    sample["output"] = f"output/videos/aqua_press_{language}.mp4"
    
    # Update VOICEVOX speaker if supported
    if sample.get("voicevox"):
        if content["voicevox_speaker"] is not None:
            sample["voicevox"]["speaker"] = content["voicevox_speaker"]
            sample["voicevox"]["output"] = f"output/videos/narration_{language}.wav"
        else:
            # Disable VOICEVOX for unsupported languages
            sample["voicevox"]["enabled"] = False
    
    return sample

def run_command(cmd, description):
    """Execute command and report status."""
    print(f"\n{'='*70}")
    print(f"🎬 {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode == 0:
        print(f"\n✅ {description} - SUCCESS")
        return True
    else:
        print(f"\n❌ {description} - FAILED (exit code: {result.returncode})")
        return False

def main():
    """Generate videos for each supported language."""
    root = Path(__file__).parent
    
    # Load base sample data
    sample_path = root / "input" / "sample_data" / "sample_video.json"
    if not sample_path.exists():
        print(f"❌ Sample data not found: {sample_path}")
        return 1
    
    with open(sample_path, encoding="utf-8") as f:
        base_sample = json.load(f)
    
    languages = ["ja", "en", "zh", "th"]
    results = {}
    lang_names_map = {
        "ja": "Japanese (日本語)",
        "en": "English (英語)",
        "zh": "Chinese (中国語)",
        "th": "Thai (タイ語)"
    }
    
    for lang in languages:
        # Create language-specific sample
        lang_sample = create_language_sample(base_sample, lang)
        
        # Save to temporary file
        lang_sample_path = root / f"input/sample_data/sample_video_{lang}.json"
        with open(lang_sample_path, "w", encoding="utf-8") as f:
            json.dump(lang_sample, f, ensure_ascii=False, indent=2)
        
        # Run video generation
        cmd = [
            sys.executable,
            str(root / "src" / "main.py"),
            str(lang_sample_path),
            "--language", lang,
        ]
        
        success = run_command(cmd, f"Generate {lang_names_map[lang]} Video")
        results[lang] = success
        
        # Verify output
        video_path = root / f"output/videos/aqua_press_{lang}.mp4"
        if video_path.exists():
            file_size = video_path.stat().st_size / (1024 * 1024)  # MB
            print(f"📹 Generated: {video_path.relative_to(root)} ({file_size:.1f} MB)")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 GENERATION SUMMARY")
    print(f"{'='*70}\n")
    
    for lang in languages:
        success = results[lang]
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {lang_names_map[lang]:20} {status}")
    
    total = len(results)
    success_count = sum(1 for s in results.values() if s)
    print(f"\n  Total: {success_count}/{total} videos generated successfully")
    
    if success_count == total:
        print("\n🎉 All multi-language videos generated successfully!")
        print(f"📂 Output folder: {root / 'output' / 'videos'}")
        return 0
    else:
        print(f"\n⚠️  {total - success_count} video(s) failed to generate")
        return 1

if __name__ == "__main__":
    sys.exit(main())
