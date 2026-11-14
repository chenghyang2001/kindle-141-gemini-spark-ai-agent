#!/usr/bin/env python3
"""
階段 3：TTS 語音合成器（多引擎版）
從 JSON 腳本讀取旁白文字，使用指定 TTS 引擎生成語音檔。
支援 edge-tts（免費預設）、Azure Speech、OpenAI TTS。

使用方式：
    python generate_tts.py --input script.json --output-dir audio/
    python generate_tts.py --input script.json --output-dir audio/ --engine azure
    python generate_tts.py --input script.json --output-dir audio/ --engine openai

作者：阿亮老師・3A科技研究社
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

# ── 可用聲音 ────────────────────────────────────────────
VOICES = {
    "female": "zh-TW-HsiaoChenNeural",
    "male": "zh-TW-YunJheNeural",
}

VOICE_PREVIEW_INFO = """
可用的繁體中文 (zh-TW) 聲音：

  [edge-tts 引擎]
  zh-TW-HsiaoChenNeural  女聲（預設，適合教學）
  zh-TW-HsiaoYuNeural    女聲（年輕活潑）
  zh-TW-YunJheNeural     男聲（沉穩專業）

  [Azure Speech 引擎]（需要 AZURE_SPEECH_KEY）
  zh-TW-HsiaoChenNeural  女聲
  zh-TW-YunJheNeural     男聲
  zh-TW-HsiaoYuNeural    女聲

  [OpenAI TTS 引擎]（需要 OPENAI_API_KEY）
  alloy    中性（預設）
  echo     男聲
  fable    故事風格
  onyx     低沉男聲
  nova     女聲
  shimmer  溫暖女聲
"""

DEFAULT_VOICE = VOICES["female"]

# 重試設定
MAX_RETRIES = 3
TTS_TIMEOUT_SECONDS = 30


# ── edge-tts 引擎（免費） ────────────────────────────────
async def _edge_tts_generate(
    text: str, output_path: Path, voice: str, rate: str = "+0%",
) -> bool:
    """使用 edge-tts 生成單一語音檔，含指數退避重試機制。"""
    try:
        import edge_tts
    except ImportError:
        print("[錯誤] 請先安裝 edge-tts: pip install edge-tts", file=sys.stderr)
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
            await asyncio.wait_for(
                communicate.save(str(output_path)),
                timeout=TTS_TIMEOUT_SECONDS,
            )
            if output_path.is_file() and output_path.stat().st_size > 0:
                return True
            print(f"  [警告] 第 {attempt} 次嘗試：檔案為空或不存在", file=sys.stderr)
        except asyncio.TimeoutError:
            print(
                f"  [警告] 第 {attempt} 次嘗試：TTS 生成逾時（{TTS_TIMEOUT_SECONDS}s）",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"  [警告] 第 {attempt} 次嘗試：TTS 生成失敗: {e}", file=sys.stderr)

        if attempt < MAX_RETRIES:
            wait_seconds = 2 ** attempt
            print(f"  [重試] {wait_seconds} 秒後重試...", file=sys.stderr)
            await asyncio.sleep(wait_seconds)

    print(
        f"  [錯誤] TTS 生成在 {MAX_RETRIES} 次嘗試後仍然失敗，跳過此段",
        file=sys.stderr,
    )
    return False


# ── Azure Speech 引擎 ───────────────────────────────────
def _azure_tts_generate(
    text: str, output_path: Path, voice: str, rate: str = "+0%",
) -> bool:
    """使用 Azure Cognitive Services Speech SDK 生成語音。"""
    speech_key = os.environ.get("AZURE_SPEECH_KEY", "")
    speech_region = os.environ.get("AZURE_SPEECH_REGION", "eastasia")

    if not speech_key:
        print("[錯誤] AZURE_SPEECH_KEY 環境變數未設定", file=sys.stderr)
        return False

    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError:
        print(
            "[錯誤] 請先安裝 Azure Speech SDK: pip install azure-cognitiveservices-speech",
            file=sys.stderr,
        )
        return False

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region,
        )
        speech_config.speech_synthesis_voice_name = voice
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
        )

        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config,
        )

        # 使用 SSML 以支援語速調整
        ssml = (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">'
            f'<voice name="{voice}">'
            f'<prosody rate="{rate}">{text}</prosody>'
            f'</voice></speak>'
        )

        result = synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return output_path.is_file() and output_path.stat().st_size > 0

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"  [Azure] 取消: {cancellation.reason}", file=sys.stderr)
            if cancellation.error_details:
                print(f"  [Azure] 錯誤: {cancellation.error_details}", file=sys.stderr)

        return False
    except Exception as e:
        print(f"  [Azure] 生成失敗: {e}", file=sys.stderr)
        return False


# ── OpenAI TTS 引擎 ─────────────────────────────────────
def _openai_tts_generate(
    text: str, output_path: Path, voice: str = "alloy", rate: str = "+0%",
) -> bool:
    """使用 OpenAI TTS API 生成語音。"""
    import urllib.request

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[錯誤] OPENAI_API_KEY 環境變數未設定", file=sys.stderr)
        return False

    # OpenAI TTS 聲音對應
    openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    # 如果使用者傳入的是 edge-tts 格式的聲音名稱，自動對應
    if voice not in openai_voices:
        if "female" in voice.lower() or "Hsiao" in voice:
            voice = "nova"
        elif "male" in voice.lower() or "Yun" in voice:
            voice = "onyx"
        else:
            voice = "alloy"

    # 語速對應：將 "+10%" 轉為 1.1 等
    speed = 1.0
    try:
        rate_clean = rate.replace("%", "").replace("+", "")
        if rate_clean:
            speed = 1.0 + (float(rate_clean) / 100.0)
            speed = max(0.25, min(4.0, speed))
    except ValueError:
        pass

    payload = json.dumps({
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "speed": speed,
        "response_format": "mp3",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(output_path, "wb") as f:
                f.write(resp.read())
        return output_path.is_file() and output_path.stat().st_size > 0
    except Exception as e:
        print(f"  [OpenAI] 生成失敗: {e}", file=sys.stderr)
        return False


# ── 統一生成介面 ─────────────────────────────────────────
async def generate_audio(
    text: str, output_path: Path, voice: str, rate: str, engine: str,
) -> bool:
    """根據引擎選擇呼叫對應的 TTS 生成函式。"""
    if engine == "edge":
        return await _edge_tts_generate(text, output_path, voice, rate)
    elif engine == "azure":
        return _azure_tts_generate(text, output_path, voice, rate)
    elif engine == "openai":
        return _openai_tts_generate(text, output_path, voice, rate)
    else:
        print(f"[錯誤] 不支援的 TTS 引擎: {engine}", file=sys.stderr)
        return False


async def generate_all(
    sections: list, output_dir: Path, voice: str, rate: str, engine: str,
) -> int:
    """依序生成所有語音檔。"""
    success = 0
    total = len(sections)

    for i, section in enumerate(sections, 1):
        narration = section.get("narration", "").strip()
        if not narration:
            print(f"  [{i}/{total}] 跳過（無旁白文字）")
            continue

        output_path = output_dir / f"audio_{i:02d}.mp3"
        title_preview = section.get("slide_title", "")[:25]
        print(f"  [{i}/{total}] 生成語音: {title_preview}...", end=" ")

        ok = await generate_audio(narration, output_path, voice, rate, engine)
        if ok:
            size_kb = output_path.stat().st_size / 1024
            print(f"OK ({size_kb:.0f} KB)")
            success += 1
        else:
            print("FAILED")

    return success


def main():
    parser = argparse.ArgumentParser(
        description="從 JSON 腳本生成 TTS 語音檔（多引擎支援）— AI 教學影片生成器"
    )
    parser.add_argument("--input", "-i", required=True, help="輸入的 JSON 腳本檔案路徑")
    parser.add_argument("--output-dir", "-o", default="audio", help="輸出目錄（預設: audio/）")
    parser.add_argument(
        "--voice", "-v",
        default=DEFAULT_VOICE,
        help=f"TTS 聲音（預設: {DEFAULT_VOICE}）",
    )
    parser.add_argument(
        "--rate", "-r",
        default="+0%",
        help="語速調整（預設: +0%%）。加快: +10%%，放慢: -10%%",
    )
    parser.add_argument(
        "--engine", "-e",
        default="edge",
        choices=["edge", "azure", "openai"],
        help="TTS 引擎（預設: edge）。edge=免費, azure=需要AZURE_SPEECH_KEY, openai=需要OPENAI_API_KEY",
    )
    parser.add_argument("--list-voices", action="store_true", help="列出所有可用的聲音及說明")
    args = parser.parse_args()

    if args.list_voices:
        print(VOICE_PREVIEW_INFO)
        sys.exit(0)

    # 讀取腳本
    input_path = Path(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    sections = script.get("sections", [])
    if not sections:
        print("[錯誤] JSON 腳本中沒有 sections", file=sys.stderr)
        sys.exit(1)

    total = len(sections)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[TTS 語音合成] 共 {total} 段語音")
    print(f"[引擎] {args.engine}")
    print(f"[聲音] {args.voice}")
    print(f"[語速] {args.rate}")

    # 引擎專屬提示
    if args.engine == "azure":
        if not os.environ.get("AZURE_SPEECH_KEY"):
            print("[錯誤] 使用 Azure 引擎需要設定 AZURE_SPEECH_KEY 環境變數", file=sys.stderr)
            sys.exit(1)
        print(f"[Azure] Region: {os.environ.get('AZURE_SPEECH_REGION', 'eastasia')}")
    elif args.engine == "openai":
        if not os.environ.get("OPENAI_API_KEY"):
            print("[錯誤] 使用 OpenAI 引擎需要設定 OPENAI_API_KEY 環境變數", file=sys.stderr)
            sys.exit(1)
    elif args.engine == "edge":
        print(f"[重試] 最多 {MAX_RETRIES} 次，每次逾時 {TTS_TIMEOUT_SECONDS} 秒")

    success = asyncio.run(
        generate_all(sections, output_dir, args.voice, args.rate, args.engine)
    )

    print(f"\n[完成] 成功 {success}/{total} 段語音，輸出至 {output_dir}/")
    if success == 0 and total > 0:
        sys.exit(1)
    elif success < total:
        print(f"[警告] 有 {total - success} 段語音生成失敗，流水線將繼續執行")


if __name__ == "__main__":
    main()
