#!/usr/bin/env python3
"""
完整流水線：一鍵從 JSON 腳本生成教學影片
依序執行：投影片生成 → TTS 語音合成 → 影片合成 → 輸出描述與標籤

使用方式：
    python full_pipeline.py --input script.json --output-dir project_output/
    python full_pipeline.py --input script.json --output-dir project_output/ --voice zh-TW-YunJheNeural

作者：阿亮老師・3A科技研究社
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run_step(label: str, cmd: list, timeout: int = 600) -> bool:
    """執行一個流水線步驟。"""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,  # 直接輸出到終端
            timeout=timeout,
        )
        elapsed = time.time() - start
        if result.returncode == 0:
            print(f"\n  [OK] {label} 完成 ({elapsed:.1f}s)")
            return True
        else:
            print(f"\n  [失敗] {label} 失敗 (exit code: {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n  [逾時] {label} 超過 {timeout} 秒")
        return False
    except Exception as e:
        print(f"\n  [錯誤] {label}: {e}")
        return False


def find_chrome_for_check() -> bool:
    """跨平台檢查 Chrome 是否可用（與 generate_slides.py 邏輯一致）。"""
    system = platform.system()

    # 依作業系統選擇候選路徑
    if system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif system == "Linux":
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
    else:
        candidates = []

    # 逐一檢查候選路徑
    for path in candidates:
        expanded = os.path.expandvars(path)
        if os.path.isfile(expanded):
            return True

    # 使用 shutil.which 作為備援
    for cmd_name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"]:
        if shutil.which(cmd_name):
            return True

    return False


def check_prerequisites() -> list:
    """檢查先決條件，回傳缺少的工具清單。"""
    missing = []

    # Python edge-tts
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        missing.append("edge-tts (pip install edge-tts)")

    # ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, timeout=10
        )
        if result.returncode != 0:
            missing.append("ffmpeg")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        missing.append("ffmpeg (winget install ffmpeg)")

    # Chrome（跨平台偵測）
    if not find_chrome_for_check():
        missing.append("Google Chrome")

    return missing


def generate_youtube_metadata(script: dict, output_dir: Path):
    """生成 YouTube 描述和標籤檔案。"""
    title = script.get("title", "AI 教學影片")
    description = script.get("description", "")
    tags = script.get("tags", [])
    author = script.get("author", "")
    sections = script.get("sections", [])

    # 生成描述
    desc_lines = [
        f"# {title}",
        "",
        description if description else f"本影片介紹「{title}」的相關知識與應用。",
        "",
        "## 章節目錄",
    ]
    # 粗估時間戳（每段約 20 秒）
    cumulative_seconds = 0
    for i, section in enumerate(sections):
        minutes = cumulative_seconds // 60
        seconds = cumulative_seconds % 60
        slide_title = section.get("slide_title", f"第 {i+1} 段")
        desc_lines.append(f"{minutes:02d}:{seconds:02d} {slide_title}")
        # 估算：每 20 字約 5 秒
        narration_len = len(section.get("narration", ""))
        cumulative_seconds += max(10, narration_len // 4)

    desc_lines.extend([
        "",
        f"講者：{author}" if author else "",
        "",
        "---",
        "本影片由 AI 教學影片自動生成器製作",
        "工具：Claude Code + edge-tts + ffmpeg",
        "#AI教學 #教育科技 #數位學習",
    ])

    desc_path = output_dir / "description.txt"
    with open(desc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(desc_lines))
    print(f"  YouTube 描述: {desc_path}")

    # 生成標籤
    default_tags = ["AI", "教學", "教育科技", "數位學習", "人工智慧"]
    all_tags = list(dict.fromkeys(tags + default_tags))  # 去重保序
    tags_path = output_dir / "tags.txt"
    with open(tags_path, "w", encoding="utf-8") as f:
        f.write(", ".join(all_tags))
    print(f"  YouTube 標籤: {tags_path}")


def main():
    parser = argparse.ArgumentParser(description="AI 教學影片全自動流水線")
    parser.add_argument("--input", "-i", required=True, help="輸入的 JSON 腳本檔案路徑")
    parser.add_argument("--output-dir", "-o", default="output", help="輸出目錄（預設: output/）")
    parser.add_argument(
        "--voice", "-v",
        default="zh-TW-HsiaoChenNeural",
        help="TTS 聲音（預設: zh-TW-HsiaoChenNeural）",
    )
    parser.add_argument("--rate", "-r", default="+0%", help="語速調整（預設: +0%%）")
    parser.add_argument(
        "--duration", default="medium",
        choices=["short", "medium", "long"],
        help="影片長度建議（供 Claude 生成腳本時參考）。short=1-2分鐘/5-8段, medium=3-5分鐘/12-20段, long=8-10分鐘/30+段",
    )
    parser.add_argument(
        "--theme", default="cinematic",
        choices=["cinematic", "dark", "light", "nature"],
        help="投影片主題（預設: cinematic）。cinematic=電影級金色(推薦), dark=深藍冷調, light=白底淡雅, nature=深綠自然",
    )
    parser.add_argument(
        "--ai-bg", action="store_true",
        help="使用 AI 生成投影片背景圖（需要 FAL_KEY 環境變數，每張約 $0.003）",
    )
    parser.add_argument("--skip-check", action="store_true", help="跳過先決條件檢查")
    parser.add_argument("--html-only", action="store_true", help="投影片僅生成 HTML 不截圖（除錯用）")
    # ── v2 新增參數 ──
    parser.add_argument(
        "--subtitles", action="store_true", default=True,
        help="生成並燒錄字幕（預設: 開啟）",
    )
    parser.add_argument("--no-subtitles", action="store_true", help="停用字幕")
    parser.add_argument(
        "--bgm", default=None,
        help="BGM 背景音樂路徑，或 'auto' 自動選取（預設: 無）",
    )
    parser.add_argument(
        "--engine", default="edge",
        choices=["edge", "azure", "openai"],
        help="TTS 引擎（預設: edge）",
    )
    parser.add_argument(
        "--ratio", default="16:9",
        choices=["16:9", "9:16", "1:1", "4:3"],
        help="畫面比例（預設: 16:9）",
    )
    parser.add_argument(
        "--resolution", default="1080p",
        choices=["1080p", "4k"],
        help="解析度（預設: 1080p）",
    )
    parser.add_argument(
        "--mode", default="auto",
        choices=["auto", "quick", "pro"],
        help="渲染模式（預設: auto 自動偵測）",
    )
    parser.add_argument(
        "--platform", default=None,
        choices=["youtube", "bilibili", "douyin", "instagram"],
        help="目標平台（自動設定比例和格式）",
    )
    args = parser.parse_args()

    # 平台預設值覆蓋
    PLATFORM_DEFAULTS = {
        "youtube":   {"ratio": "16:9", "resolution": "1080p"},
        "bilibili":  {"ratio": "16:9", "resolution": "1080p"},
        "douyin":    {"ratio": "9:16", "resolution": "1080p"},
        "instagram": {"ratio": "1:1",  "resolution": "1080p"},
    }
    if args.platform and args.platform in PLATFORM_DEFAULTS:
        defaults = PLATFORM_DEFAULTS[args.platform]
        # 只在使用者未明確指定時覆蓋
        if args.ratio == "16:9":  # 預設值表示未指定
            args.ratio = defaults["ratio"]
        if args.resolution == "1080p":
            args.resolution = defaults["resolution"]

    # 處理字幕開關
    if args.no_subtitles:
        args.subtitles = False

    script_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    skill_dir = Path(__file__).parent

    print("=" * 60)
    print("  AI 教學影片自動生成器")
    print("  阿亮老師・3A科技研究社")
    print("=" * 60)

    # 先決條件檢查
    if not args.skip_check:
        print("\n[步驟 0] 檢查先決條件...")
        missing = check_prerequisites()
        if missing:
            print("[錯誤] 缺少以下工具：")
            for m in missing:
                print(f"  - {m}")
            print("\n請安裝後重試，或使用 --skip-check 跳過檢查。")
            sys.exit(1)
        print("  所有先決條件已就緒！")

    # 驗證輸入檔案
    if not script_path.is_file():
        print(f"[錯誤] 找不到腳本檔案: {script_path}", file=sys.stderr)
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    sections = script.get("sections", [])
    title = script.get("title", "教學影片")
    total_slides = len(sections)
    print(f"\n[腳本] {title}")
    print(f"  共 {total_slides} 個段落")

    # 建立子目錄
    slides_dir = output_dir / "slides"
    audio_dir = output_dir / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.time()

    # 用於追蹤各階段成功狀態
    step_results = {}

    # 顯示影片長度建議
    duration_info = {"short": "1-2 分鐘 / 5-8 段", "medium": "3-5 分鐘 / 12-20 段", "long": "8-10 分鐘 / 30+ 段"}
    print(f"[長度建議] {args.duration}（{duration_info.get(args.duration, '')}）")
    print(f"[主題] {args.theme}")
    print(f"[比例] {args.ratio}  [解析度] {args.resolution}  [引擎] {args.engine}")
    if args.platform:
        print(f"[平台] {args.platform}")
    print(f"[字幕] {'開啟' if args.subtitles else '關閉'}  [BGM] {args.bgm or '無'}")
    print(f"[模式] {args.mode}")

    # 階段 2：投影片生成
    slide_cmd = [
        sys.executable,
        str(skill_dir / "generate_slides.py"),
        "--input", str(script_path),
        "--output-dir", str(slides_dir),
        "--theme", args.theme,
        "--ratio", args.ratio,
        "--resolution", args.resolution,
    ]
    if args.html_only:
        slide_cmd.append("--html-only")
    if args.ai_bg:
        slide_cmd.append("--ai-bg")

    slide_ok = run_step("階段 2：投影片生成", slide_cmd)
    step_results["投影片生成"] = slide_ok
    if not slide_ok:
        print("\n  [警告] 投影片生成有部分失敗，嘗試繼續後續步驟...", file=sys.stderr)

    # 階段 3：TTS 語音合成
    tts_cmd = [
        sys.executable,
        str(skill_dir / "generate_tts.py"),
        "--input", str(script_path),
        "--output-dir", str(audio_dir),
        "--voice", args.voice,
        "--rate", args.rate,
        "--engine", args.engine,
    ]
    tts_ok = run_step("階段 3：TTS 語音合成", tts_cmd)
    step_results["TTS 語音合成"] = tts_ok
    if not tts_ok:
        print("\n  [警告] TTS 語音合成有部分失敗，嘗試繼續後續步驟...", file=sys.stderr)

    # 檢查是否有足夠的檔案可以合成影片
    slides_count = len(list(slides_dir.glob("slide_*.png"))) if slides_dir.exists() else 0
    audios_count = len(list(audio_dir.glob("audio_*.mp3"))) if audio_dir.exists() else 0
    usable_count = min(slides_count, audios_count)

    # 如果是 html-only 模式，跳過影片合成
    if args.html_only:
        print("\n[提示] HTML-only 模式，跳過影片合成。")
        step_results["影片合成"] = True
    elif usable_count == 0:
        print("\n[錯誤] 沒有可用的投影片或語音檔，無法合成影片", file=sys.stderr)
        step_results["影片合成"] = False
    else:
        # 階段 4：影片合成
        video_output = str(output_dir / "output.mp4")
        video_cmd = [
            sys.executable,
            str(skill_dir / "assemble_video.py"),
            "--slides-dir", str(slides_dir),
            "--audio-dir", str(audio_dir),
            "--output", video_output,
        ]
        video_ok = run_step("階段 4：影片合成", video_cmd)
        step_results["影片合成"] = video_ok
        if not video_ok:
            print("\n  [警告] 影片合成失敗", file=sys.stderr)

    # 階段 4b：字幕生成與燒錄（v2 新增）
    video_output_path = output_dir / "output.mp4"
    if args.subtitles and not args.html_only and video_output_path.is_file():
        srt_path = output_dir / "subtitles.srt"
        srt_cmd = [
            sys.executable,
            str(skill_dir / "generate_subtitles.py"),
            "--input", str(script_path),
            "--audio-dir", str(audio_dir),
            "--output", str(srt_path),
        ]
        srt_ok = run_step("階段 4b：字幕生成", srt_cmd)
        step_results["字幕生成"] = srt_ok

        if srt_ok and srt_path.is_file():
            # 燒錄字幕
            video_with_subs = output_dir / "output_subs.mp4"
            burn_cmd = [
                sys.executable,
                str(skill_dir / "generate_subtitles.py"),
                "--burn",
                "--video", str(video_output_path),
                "--srt", str(srt_path),
                "--output", str(video_with_subs),
            ]
            burn_ok = run_step("階段 4b：字幕燒錄", burn_cmd)
            if burn_ok and video_with_subs.is_file():
                # 替換原影片
                video_output_path.unlink(missing_ok=True)
                video_with_subs.rename(video_output_path)
                step_results["字幕燒錄"] = True
            else:
                step_results["字幕燒錄"] = False

    # 階段 4c：BGM 背景音樂混音（v2 新增）
    if args.bgm and not args.html_only and video_output_path.is_file():
        video_with_bgm = output_dir / "output_bgm.mp4"
        bgm_cmd = [
            sys.executable,
            str(skill_dir / "add_bgm.py"),
            "--input", str(video_output_path),
            "--bgm", args.bgm,
            "--output", str(video_with_bgm),
        ]
        bgm_ok = run_step("階段 4c：BGM 混音", bgm_cmd)
        if bgm_ok and video_with_bgm.is_file():
            video_output_path.unlink(missing_ok=True)
            video_with_bgm.rename(video_output_path)
            step_results["BGM 混音"] = True
        else:
            step_results["BGM 混音"] = False

    # 階段 5：生成 YouTube 描述和標籤
    print(f"\n{'='*60}")
    print(f"  階段 5：輸出 YouTube 資訊")
    print(f"{'='*60}")
    try:
        generate_youtube_metadata(script, output_dir)
        step_results["YouTube 資訊"] = True
    except Exception as e:
        print(f"  [警告] YouTube 資訊生成失敗: {e}", file=sys.stderr)
        step_results["YouTube 資訊"] = False

    # 總結報告
    total_elapsed = time.time() - total_start
    minutes = int(total_elapsed // 60)
    seconds = int(total_elapsed % 60)

    print(f"\n{'='*60}")
    print(f"  執行總結")
    print(f"{'='*60}")
    print(f"  總耗時: {minutes}m {seconds}s")
    print(f"  輸出目錄: {output_dir}")

    # 顯示各階段結果摘要
    print(f"\n  各階段結果：")
    success_steps = 0
    total_steps = len(step_results)
    for step_name, ok in step_results.items():
        status = "OK" if ok else "FAILED"
        print(f"    {step_name}: {status}")
        if ok:
            success_steps += 1

    # 顯示投影片成功率
    print(f"\n  成功 {usable_count}/{total_slides} 張投影片")
    print(f"  階段完成率: {success_steps}/{total_steps}")

    # 列出產出檔案
    if output_dir.exists():
        print(f"\n  產出檔案：")
        for p in sorted(output_dir.rglob("*")):
            if p.is_file() and not p.name.startswith("_"):
                size = p.stat().st_size
                if size > 1024 * 1024:
                    size_str = f"{size / (1024*1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.0f} KB"
                else:
                    size_str = f"{size} B"
                rel = p.relative_to(output_dir)
                print(f"    {rel} ({size_str})")

    # 只有全部關鍵步驟都失敗才回傳錯誤碼
    if success_steps == 0:
        print("\n[錯誤] 所有步驟都失敗了", file=sys.stderr)
        sys.exit(1)
    elif success_steps < total_steps:
        print(f"\n[警告] 有 {total_steps - success_steps} 個步驟失敗，但流水線已盡可能完成")
    else:
        print("\n  全部完成！")


if __name__ == "__main__":
    main()
