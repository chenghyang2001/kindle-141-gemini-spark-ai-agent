#!/usr/bin/env python3
"""
BGM 背景音樂混音器

將背景音樂與影片混合，支援自動降低 BGM 音量避免干擾旁白。

使用方式：
    python add_bgm.py --input video.mp4 --bgm bgm.mp3 --output final.mp4
    python add_bgm.py --input video.mp4 --bgm auto --output final.mp4
    python add_bgm.py --list-bgm

作者：阿亮老師・3A科技研究社
"""

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

# ── 內建免費 BGM 資源 ────────────────────────────────────
# 注意：以下為免費可商用的 BGM 建議來源，實際使用前請確認授權
BUILTIN_BGM_INFO = {
    "calm": {
        "name": "平靜輕音樂",
        "description": "適合教學、知識類影片",
        "note": "建議從以下免費音樂庫下載：",
        "sources": [
            "https://pixabay.com/music/ （免費可商用）",
            "https://www.bensound.com/free-music-for-videos （Creative Commons）",
            "https://freemusicarchive.org/ （多種授權）",
            "https://incompetech.com/ （Kevin MacLeod，CC BY）",
        ],
    },
    "upbeat": {
        "name": "輕快節奏",
        "description": "適合介紹、開場片段",
        "note": "建議搜尋關鍵字：upbeat, corporate, technology",
        "sources": [
            "https://pixabay.com/music/search/upbeat/",
            "https://www.youtube.com/audiolibrary （YouTube 創作者音樂庫）",
        ],
    },
    "ambient": {
        "name": "環境音效",
        "description": "適合長時間講解、冥想式教學",
        "note": "建議搜尋關鍵字：ambient, background, soft",
        "sources": [
            "https://pixabay.com/music/search/ambient/",
            "https://freesound.org/ （需註冊）",
        ],
    },
}

# 預設 BGM 目錄
DEFAULT_BGM_DIR = Path(__file__).parent.parent / "assets" / "bgm"


def list_builtin_bgm() -> None:
    """列出內建 BGM 資源資訊。"""
    print("\n" + "=" * 60)
    print("  BGM 背景音樂資源")
    print("  AI 教學影片生成器 — 阿亮老師・3A科技研究社")
    print("=" * 60)

    for key, info in BUILTIN_BGM_INFO.items():
        print(f"\n  [{key}] {info['name']}")
        print(f"    說明: {info['description']}")
        print(f"    {info['note']}")
        for src in info["sources"]:
            print(f"      - {src}")

    # 檢查本地 BGM 目錄
    if DEFAULT_BGM_DIR.is_dir():
        local_files = list(DEFAULT_BGM_DIR.glob("*.mp3")) + list(DEFAULT_BGM_DIR.glob("*.wav"))
        if local_files:
            print(f"\n  [本地 BGM 檔案] ({DEFAULT_BGM_DIR})")
            for f in local_files:
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"    - {f.name} ({size_mb:.1f} MB)")

    print(f"\n  使用方式：")
    print(f"    --bgm path/to/bgm.mp3    使用指定音檔")
    print(f"    --bgm auto               自動從 assets/bgm/ 目錄選取")
    print()


def find_auto_bgm() -> Path | None:
    """自動尋找可用的 BGM 檔案。"""
    # 優先從 assets/bgm/ 目錄找
    if DEFAULT_BGM_DIR.is_dir():
        for ext in ["*.mp3", "*.wav", "*.m4a", "*.ogg"]:
            files = sorted(DEFAULT_BGM_DIR.glob(ext))
            if files:
                return files[0]

    return None


def get_video_duration(video_path: Path) -> float:
    """取得影片時長（秒）。"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def mix_bgm(
    video_path: Path,
    bgm_path: Path,
    output_path: Path,
    bgm_volume: float = 0.15,
    fade_in: float = 2.0,
    fade_out: float = 3.0,
) -> bool:
    """使用 ffmpeg 混合背景音樂與影片。

    參數：
        video_path: 輸入影片路徑
        bgm_path: BGM 音檔路徑
        output_path: 輸出影片路徑
        bgm_volume: BGM 音量（0.0-1.0，預設 0.15）
        fade_in: BGM 淡入秒數
        fade_out: BGM 淡出秒數
    """
    # 取得影片時長，用於計算淡出起點
    video_duration = get_video_duration(video_path)
    if video_duration <= 0:
        print("[警告] 無法取得影片時長，跳過淡出效果", file=sys.stderr)
        fade_out_start = 9999
    else:
        fade_out_start = max(0, video_duration - fade_out)

    # ffmpeg 音頻濾鏡：
    # 1. BGM 降低音量
    # 2. BGM 淡入淡出
    # 3. 混合旁白與 BGM
    filter_complex = (
        f"[1:a]volume={bgm_volume},"
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={fade_out_start}:d={fade_out}"
        f"[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-c:v", "copy",       # 視訊直接複製（不重新編碼）
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path),
    ]

    try:
        print(f"  [BGM] 混合背景音樂（音量 {bgm_volume:.0%}）...")
        print(f"  [BGM] 淡入 {fade_in}s / 淡出 {fade_out}s")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and output_path.is_file():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  [BGM] 完成: {output_path} ({size_mb:.1f} MB)")
            return True
        print(f"  [錯誤] BGM 混音失敗: {result.stderr[:300]}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("  [錯誤] ffmpeg BGM 混音逾時", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="BGM 背景音樂混音器 — AI 教學影片生成器"
    )
    parser.add_argument("--input", "-i", help="輸入影片路徑")
    parser.add_argument(
        "--bgm", "-b",
        help="BGM 音檔路徑，或 'auto' 自動選取",
    )
    parser.add_argument("--output", "-o", help="輸出影片路徑")
    parser.add_argument(
        "--volume", type=float, default=0.15,
        help="BGM 音量比例（0.0-1.0，預設: 0.15）",
    )
    parser.add_argument(
        "--fade-in", type=float, default=2.0,
        help="BGM 淡入秒數（預設: 2.0）",
    )
    parser.add_argument(
        "--fade-out", type=float, default=3.0,
        help="BGM 淡出秒數（預設: 3.0）",
    )
    parser.add_argument(
        "--list-bgm", action="store_true",
        help="列出可用的 BGM 資源",
    )
    args = parser.parse_args()

    if args.list_bgm:
        list_builtin_bgm()
        return

    if not args.input or not args.output:
        parser.print_help()
        print("\n[錯誤] 需要 --input 和 --output 參數", file=sys.stderr)
        sys.exit(1)

    video_path = Path(args.input)
    output_path = Path(args.output)

    if not video_path.is_file():
        print(f"[錯誤] 找不到影片: {video_path}", file=sys.stderr)
        sys.exit(1)

    # 處理 BGM 來源
    if not args.bgm:
        print("[錯誤] 需要 --bgm 參數（檔案路徑或 'auto'）", file=sys.stderr)
        sys.exit(1)

    if args.bgm == "auto":
        bgm_path = find_auto_bgm()
        if bgm_path is None:
            print("[錯誤] 找不到可用的 BGM 檔案", file=sys.stderr)
            print(f"  請將 BGM 檔案放入: {DEFAULT_BGM_DIR}/")
            print(f"  或使用 --list-bgm 查看推薦資源")
            sys.exit(1)
        print(f"[BGM] 自動選取: {bgm_path}")
    else:
        bgm_path = Path(args.bgm)
        if not bgm_path.is_file():
            print(f"[錯誤] 找不到 BGM 檔案: {bgm_path}", file=sys.stderr)
            sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ok = mix_bgm(
        video_path, bgm_path, output_path,
        bgm_volume=args.volume,
        fade_in=args.fade_in,
        fade_out=args.fade_out,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
