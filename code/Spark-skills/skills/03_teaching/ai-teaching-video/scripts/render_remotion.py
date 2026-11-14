#!/usr/bin/env python3
"""
Remotion 專業模式渲染器：使用 Remotion 將 JSON 腳本 + 音檔渲染為 4K 影片。
若 Remotion 不可用則自動回退到 ffmpeg 快速模式。

使用方式：
    python render_remotion.py --input script.json --audio-dir audio/ --output video.mp4
    python render_remotion.py --input script.json --audio-dir audio/ --output video.mp4 --resolution 4k

作者：阿亮老師・3A科技研究社
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# Remotion 設定檔路徑（由 setup_remotion.py 產生）
CONFIG_PATH = Path(__file__).parent / ".remotion_config.json"

# 解析度對應
RESOLUTIONS = {
    "1080p": {"width": 1920, "height": 1080, "composition": "TeachingVideo"},
    "4k": {"width": 3840, "height": 2160, "composition": "TeachingVideo4K"},
}


def load_remotion_config() -> dict:
    """讀取 Remotion 設定檔。"""
    if CONFIG_PATH.is_file():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def check_remotion_ready() -> tuple:
    """檢查 Remotion 環境是否就緒。回傳 (是否就緒, 專案路徑, 訊息)。"""
    config = load_remotion_config()
    project_dir = config.get("remotion_project_dir", "")

    if not project_dir:
        return False, "", "Remotion 設定檔不存在，請先執行 setup_remotion.py"

    project_path = Path(project_dir)
    if not project_path.is_dir():
        return False, "", f"Remotion 專案目錄不存在: {project_dir}"

    # 檢查 node_modules
    if not (project_path / "node_modules").is_dir():
        return False, "", "Remotion 依賴未安裝，請重新執行 setup_remotion.py"

    # 檢查 src/index.ts
    if not (project_path / "src" / "index.ts").is_file():
        return False, "", "Remotion 入口檔不存在，請重新執行 setup_remotion.py"

    # 檢查 Node.js
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return False, "", "Node.js 不可用"
        version_str = result.stdout.strip().lstrip("v")
        major = int(version_str.split(".")[0])
        if major < 18:
            return False, "", f"Node.js 版本 {version_str} 太舊（需要 >= 18）"
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return False, "", "Node.js 不可用"

    return True, str(project_path), "Remotion 環境就緒"


def get_audio_duration(audio_path: Path) -> float:
    """使用 ffprobe 取得音檔時長（秒）。"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return 10.0


def generate_remotion_props(script: dict, audio_dir: Path, fps: int = 30) -> dict:
    """從 JSON 腳本生成 Remotion 渲染用的 props。"""
    sections = script.get("sections", [])
    slides_data = []
    total_frames = 0

    for i, section in enumerate(sections, 1):
        audio_path = audio_dir / f"audio_{i:02d}.mp3"
        duration = get_audio_duration(audio_path) if audio_path.is_file() else 10.0
        frame_count = int(duration * fps)

        slides_data.append({
            "id": i,
            "title": section.get("slide_title", ""),
            "content": section.get("slide_content", ""),
            "narration": section.get("narration", ""),
            "audioFile": str(audio_path.resolve()) if audio_path.is_file() else "",
            "durationInFrames": frame_count,
            "startFrame": total_frames,
        })
        total_frames += frame_count

    return {
        "videoTitle": script.get("title", "AI 教學影片"),
        "author": script.get("author", ""),
        "slides": slides_data,
        "totalFrames": total_frames,
        "fps": fps,
    }


def render_with_remotion(
    project_dir: str, props: dict, output_path: Path,
    resolution: str = "1080p",
) -> bool:
    """使用 Remotion 渲染影片。"""
    res_config = RESOLUTIONS.get(resolution, RESOLUTIONS["1080p"])
    composition_id = res_config["composition"]

    # 將 props 寫入暫存 JSON
    props_path = Path(project_dir) / "render_props.json"
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",
        composition_id,
        str(output_path.resolve()),
        "--props", str(props_path),
        "--overwrite",
        "--video-bitrate", "16M",
    ]

    try:
        print(f"  [Remotion] 渲染中（{resolution}）...", flush=True)
        start = time.time()
        result = subprocess.run(
            cmd, cwd=project_dir,
            capture_output=False,  # 直接輸出到終端
            timeout=1800,  # 30 分鐘逾時
        )
        elapsed = time.time() - start

        if result.returncode == 0 and output_path.is_file():
            print(f"  [Remotion] 渲染完成（{elapsed:.1f}s）")
            return True

        print(f"  [Remotion] 渲染失敗（exit code: {result.returncode}）", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("  [Remotion] 渲染逾時（超過 30 分鐘）", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  [Remotion] 渲染異常: {e}", file=sys.stderr)
        return False
    finally:
        # 清理暫存 props
        try:
            props_path.unlink(missing_ok=True)
        except OSError:
            pass


def fallback_ffmpeg(script: dict, audio_dir: Path, output_path: Path) -> bool:
    """回退到 ffmpeg 快速模式。"""
    skill_dir = Path(__file__).parent
    assemble_script = skill_dir / "assemble_video.py"
    slides_dir = output_path.parent / "slides"

    if not assemble_script.is_file():
        print("  [回退] assemble_video.py 不存在", file=sys.stderr)
        return False

    # 檢查投影片是否已生成
    if not slides_dir.is_dir() or not list(slides_dir.glob("slide_*.png")):
        print("  [回退] 投影片目錄不存在，嘗試先生成投影片...", file=sys.stderr)
        generate_slides = skill_dir / "generate_slides.py"
        if generate_slides.is_file():
            # 將 script 寫入暫存檔
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8",
            ) as tmp:
                json.dump(script, tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name

            try:
                subprocess.run(
                    [sys.executable, str(generate_slides), "--input", tmp_path,
                     "--output-dir", str(slides_dir)],
                    timeout=300,
                )
            finally:
                try:
                    Path(tmp_path).unlink()
                except OSError:
                    pass

    # 使用 assemble_video.py
    cmd = [
        sys.executable,
        str(assemble_script),
        "--slides-dir", str(slides_dir),
        "--audio-dir", str(audio_dir),
        "--output", str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=False, timeout=600)
        return result.returncode == 0 and output_path.is_file()
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"  [回退] ffmpeg 合成失敗: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="使用 Remotion 渲染教學影片（專業模式）— AI 教學影片生成器"
    )
    parser.add_argument("--input", "-i", required=True, help="輸入的 JSON 腳本檔案路徑")
    parser.add_argument("--audio-dir", "-a", required=True, help="音檔目錄")
    parser.add_argument("--output", "-o", default="output.mp4", help="輸出影片路徑（預設: output.mp4）")
    parser.add_argument(
        "--resolution", "-r",
        default="1080p", choices=["1080p", "4k"],
        help="影片解析度（預設: 1080p）",
    )
    parser.add_argument("--fps", type=int, default=30, help="影片幀率（預設: 30）")
    parser.add_argument(
        "--no-fallback", action="store_true",
        help="禁用 ffmpeg 回退（Remotion 失敗時直接報錯）",
    )
    args = parser.parse_args()

    # 讀取腳本
    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"[錯誤] 找不到腳本檔案: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    audio_dir = Path(args.audio_dir)
    if not audio_dir.is_dir():
        print(f"[錯誤] 音檔目錄不存在: {audio_dir}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Remotion 專業模式渲染器")
    print("  AI 教學影片生成器 — 阿亮老師・3A科技研究社")
    print("=" * 60)

    # 步驟 1：檢查 Remotion 環境
    print("\n[步驟 1] 檢查 Remotion 環境...")
    ready, project_dir, message = check_remotion_ready()
    print(f"  {message}")

    if ready:
        # 步驟 2：生成 Remotion props
        print(f"\n[步驟 2] 生成 Remotion 渲染參數...")
        props = generate_remotion_props(script, audio_dir, fps=args.fps)
        print(f"  共 {len(props['slides'])} 張投影片")
        print(f"  總幀數: {props['totalFrames']}（約 {props['totalFrames'] / args.fps:.1f} 秒）")

        # 步驟 3：Remotion 渲染
        print(f"\n[步驟 3] 開始 Remotion 渲染（{args.resolution}）...")
        success = render_with_remotion(project_dir, props, output_path, args.resolution)

        if success:
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"\n[完成] 影片已輸出: {output_path} ({file_size_mb:.1f} MB)")
            return
        else:
            print("\n[警告] Remotion 渲染失敗", file=sys.stderr)
            if args.no_fallback:
                sys.exit(1)
    else:
        if args.no_fallback:
            print("[錯誤] Remotion 不可用，且已禁用回退模式", file=sys.stderr)
            sys.exit(1)

    # 步驟 4：回退到 ffmpeg 快速模式
    print("\n[步驟 4] 回退到 ffmpeg 快速模式...")
    print("  [提示] 若要使用 Remotion 專業模式，請先執行 setup_remotion.py")
    success = fallback_ffmpeg(script, audio_dir, output_path)

    if success:
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n[完成] 影片已輸出（快速模式）: {output_path} ({file_size_mb:.1f} MB)")
    else:
        print("[錯誤] 影片渲染失敗（Remotion 和 ffmpeg 皆失敗）", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
