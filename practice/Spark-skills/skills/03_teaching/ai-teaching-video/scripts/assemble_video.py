#!/usr/bin/env python3
"""
階段 4：影片合成器
使用 ffmpeg 將投影片 PNG + TTS 語音合成為完整影片。

使用方式：
    python assemble_video.py --slides-dir slides/ --audio-dir audio/ --output output.mp4

作者：阿亮老師・3A科技研究社
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def check_ffmpeg() -> bool:
    """檢查 ffmpeg 是否可用。"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


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
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def create_segment(
    slide_path: Path, audio_path: Path, output_path: Path, index: int,
    duration: float = 0.0,
) -> bool:
    """將單張投影片 + 語音合成為一個影片片段。

    注意：-loop 1 搭配 -shortest 時，ffmpeg 的視訊常比音訊多拖數秒，
    多段累積會讓字幕時間軸嚴重漂移，因此改用 -t 鎖定精確時長；
    僅在量不到音檔長度時才退回 -shortest。
    """
    cmd = [
        "ffmpeg",
        "-y",                       # 覆蓋輸出
        "-loop", "1",               # 循環顯示圖片
        "-i", str(slide_path),      # 輸入圖片
        "-i", str(audio_path),      # 輸入音檔
        "-c:v", "libx264",          # H.264 視訊編碼
        "-tune", "stillimage",      # 靜態圖片優化
        "-c:a", "aac",              # AAC 音訊編碼
        "-b:a", "192k",             # 音訊位元率
        "-pix_fmt", "yuv420p",      # 像素格式（相容性）
        "-vf", "scale=1920:1080",   # 確保解析度一致
    ]
    if duration > 0:
        cmd += ["-t", f"{duration:.3f}"]  # 以音檔實測長度為準
    else:
        cmd += ["-shortest"]
    cmd.append(str(output_path))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and output_path.is_file():
            return True
        print(f"  [警告] 片段 {index} 合成失敗: {result.stderr[:300]}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"  [警告] 片段 {index} ffmpeg 逾時", file=sys.stderr)
        return False


def concatenate_segments(segment_paths: list[Path], output_path: Path) -> bool:
    """串接所有影片片段為最終影片。"""
    # 建立 concat 檔案清單（使用 UTF-8 編碼處理中日韓字元路徑）
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        for seg in segment_paths:
            # ffmpeg concat 需要用正斜線，且路徑中的單引號需要跳脫
            abs_path = seg.resolve().as_posix()
            # 跳脫路徑中的單引號（若有）
            abs_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{abs_path}'\n")
        filelist_path = Path(f.name)

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(filelist_path),
            "-c", "copy",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and output_path.is_file():
            return True
        print(f"[錯誤] 串接失敗: {result.stderr[:300]}", file=sys.stderr)
        return False
    finally:
        try:
            filelist_path.unlink()
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="使用 ffmpeg 合成教學影片")
    parser.add_argument("--slides-dir", "-s", default="slides", help="投影片 PNG 目錄（預設: slides/）")
    parser.add_argument("--audio-dir", "-a", default="audio", help="語音 MP3 目錄（預設: audio/）")
    parser.add_argument("--output", "-o", default="output.mp4", help="輸出影片路徑（預設: output.mp4）")
    parser.add_argument("--keep-segments", action="store_true", help="保留中間片段檔案")
    args = parser.parse_args()

    if not check_ffmpeg():
        print("[錯誤] ffmpeg 未安裝或不在 PATH 中。請安裝: winget install ffmpeg", file=sys.stderr)
        sys.exit(1)

    slides_dir = Path(args.slides_dir)
    audio_dir = Path(args.audio_dir)

    # 收集匹配的投影片和語音檔
    slides = sorted(slides_dir.glob("slide_*.png"))
    audios = sorted(audio_dir.glob("audio_*.mp3"))

    if not slides:
        print(f"[錯誤] 在 {slides_dir}/ 中找不到投影片 PNG 檔案", file=sys.stderr)
        sys.exit(1)
    if not audios:
        print(f"[錯誤] 在 {audio_dir}/ 中找不到語音 MP3 檔案", file=sys.stderr)
        sys.exit(1)

    # 確認數量匹配
    count = min(len(slides), len(audios))
    if len(slides) != len(audios):
        print(f"[警告] 投影片 ({len(slides)}) 與語音 ({len(audios)}) 數量不一致，取前 {count} 組")

    print(f"[影片合成] 共 {count} 個片段")

    # 建立暫存目錄
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    segments_dir = output_dir / "_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    # 生成每個片段
    segment_paths: list[Path] = []
    total_duration = 0.0

    for i in range(count):
        slide = slides[i]
        audio = audios[i]
        segment_out = segments_dir / f"segment_{i + 1:02d}.mp4"

        duration = get_audio_duration(audio)
        total_duration += duration

        print(f"  [{i + 1}/{count}] 合成片段 ({duration:.1f}s)...", end=" ")
        if create_segment(slide, audio, segment_out, i + 1, duration=duration):
            print("OK")
            segment_paths.append(segment_out)
        else:
            print("FAILED")

    if not segment_paths:
        print("[錯誤] 沒有成功合成任何片段", file=sys.stderr)
        sys.exit(1)

    # 串接所有片段
    print(f"\n[串接] 合併 {len(segment_paths)} 個片段...")
    if concatenate_segments(segment_paths, output_path):
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        print(f"\n[完成] 影片已輸出: {output_path}")
        print(f"  時長: {minutes}:{seconds:02d}")
        print(f"  大小: {file_size_mb:.1f} MB")
    else:
        print("[錯誤] 影片串接失敗", file=sys.stderr)
        sys.exit(1)

    # 清理暫存片段
    if not args.keep_segments:
        for seg in segment_paths:
            try:
                seg.unlink()
            except OSError:
                pass
        try:
            segments_dir.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
