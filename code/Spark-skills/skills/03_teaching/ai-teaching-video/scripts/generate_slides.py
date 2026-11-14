#!/usr/bin/env python3
"""
階段 2：投影片生成器（視覺升級版 v2）
從 JSON 腳本生成 HTML 投影片，並使用 Chrome headless 截圖為 PNG。
支援 4 種版面配置輪替、4 種色彩主題、裝飾元素、AI 背景圖。
新增多平台比例支援（16:9 / 9:16 / 1:1 / 4:3）和 4K 解析度。

使用方式：
    python generate_slides.py --input script.json --output-dir slides/
    python generate_slides.py --input script.json --output-dir slides/ --theme cinematic --ai-bg
    python generate_slides.py --input script.json --output-dir slides/ --ratio 9:16 --resolution 4k

作者：阿亮老師・3A科技研究社
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ── 跨平台 Chrome 執行檔路徑 ──────────────────────────────
CHROME_PATHS_WINDOWS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

CHROME_PATHS_LINUX = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]

CHROME_PATHS_MACOS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

# ── 主題定義（含裝飾色彩） ────────────────────────────────
THEMES = {
    "cinematic": {
        "body_bg": "linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0d0d0d 100%)",
        "overlay_bg": "linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.7) 100%)",
        "title_color": "#ffd700",
        "title_shadow": "0 2px 20px rgba(255,215,0,0.4), 0 0 60px rgba(0,0,0,0.8)",
        "content_color": "#e8e8e8",
        "content_shadow": "0 1px 10px rgba(0,0,0,0.6)",
        "meta_color": "rgba(255,255,255,0.25)",
        "glow_color_1": "rgba(255,180,50,0.12)",
        "glow_color_2": "rgba(200,100,30,0.10)",
        "accent_color": "#ffd700",
        "accent_color_2": "#ff8c00",
        "quote_color": "rgba(255,215,0,0.10)",
        "bottom_bar_colors": "#ffd700, #ff8c00, #ffd700",
        "deco_line_color": "rgba(255,215,0,0.3)",
    },
    "dark": {
        "body_bg": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        "overlay_bg": "rgba(10,10,30,0.55)",
        "title_color": "#ffffff",
        "title_shadow": "0 2px 20px rgba(0,0,0,0.8), 0 0 40px rgba(233,69,96,0.3)",
        "content_color": "#f0f0f0",
        "content_shadow": "0 1px 8px rgba(0,0,0,0.5)",
        "meta_color": "rgba(255,255,255,0.3)",
        "glow_color_1": "rgba(100,130,255,0.12)",
        "glow_color_2": "rgba(233,69,96,0.10)",
        "accent_color": "#e94560",
        "accent_color_2": "#6c8cff",
        "quote_color": "rgba(233,69,96,0.08)",
        "bottom_bar_colors": "#e94560, #6c8cff, #e94560",
        "deco_line_color": "rgba(233,69,96,0.3)",
    },
    "light": {
        "body_bg": "linear-gradient(135deg, #ffffff 0%, #f8f6f2 50%, #f0ece4 100%)",
        "overlay_bg": "rgba(255,255,255,0.6)",
        "title_color": "#1a1a2e",
        "title_shadow": "0 2px 10px rgba(0,0,0,0.08)",
        "content_color": "#333333",
        "content_shadow": "0 1px 4px rgba(0,0,0,0.06)",
        "meta_color": "rgba(0,0,0,0.2)",
        "glow_color_1": "rgba(100,180,255,0.08)",
        "glow_color_2": "rgba(255,180,100,0.06)",
        "accent_color": "#1565c0",
        "accent_color_2": "#ff8f00",
        "quote_color": "rgba(21,101,192,0.06)",
        "bottom_bar_colors": "#1565c0, #ff8f00, #1565c0",
        "deco_line_color": "rgba(21,101,192,0.2)",
    },
    "nature": {
        "body_bg": "linear-gradient(135deg, #0b1a0f 0%, #132a13 50%, #1a3a1a 100%)",
        "overlay_bg": "rgba(10,30,15,0.50)",
        "title_color": "#a8e6cf",
        "title_shadow": "0 2px 20px rgba(168,230,207,0.3), 0 0 50px rgba(0,0,0,0.7)",
        "content_color": "#e8f5e9",
        "content_shadow": "0 1px 8px rgba(0,0,0,0.5)",
        "meta_color": "rgba(255,255,255,0.25)",
        "glow_color_1": "rgba(100,200,150,0.12)",
        "glow_color_2": "rgba(50,180,100,0.08)",
        "accent_color": "#66bb6a",
        "accent_color_2": "#a8e6cf",
        "quote_color": "rgba(102,187,106,0.08)",
        "bottom_bar_colors": "#66bb6a, #a8e6cf, #66bb6a",
        "deco_line_color": "rgba(168,230,207,0.25)",
    },
}

# ── 版面配置定義（4 種輪替） ──────────────────────────────
# 每種版面定義 CSS 覆寫與 HTML 結構差異
LAYOUTS = {
    # 版面 A：標題與內容置中（經典勵志風格）
    "center": {
        "content_justify": "center",
        "content_align": "center",
        "text_align": "center",
        "content_padding": "80px 160px",
        "title_size": 78,
        "content_size": 40,
        "title_max_width": "1400px",
        "content_max_width": "1100px",
        "extra_css": "",
    },
    # 版面 B：左對齊，右側留白裝飾空間
    "left": {
        "content_justify": "center",
        "content_align": "flex-start",
        "text_align": "left",
        "content_padding": "80px 120px 80px 140px",
        "title_size": 72,
        "content_size": 38,
        "title_max_width": "1100px",
        "content_max_width": "950px",
        "extra_css": """
        .side-accent {
            position: absolute; right: 80px; top: 50%; transform: translateY(-50%);
            width: 4px; height: 400px; z-index: 2;
            background: linear-gradient(to bottom, transparent, {accent_color}, transparent);
        }
        """,
    },
    # 版面 C：下三分之一字幕風格
    "bottom": {
        "content_justify": "flex-end",
        "content_align": "center",
        "text_align": "center",
        "content_padding": "0 160px 120px 160px",
        "title_size": 72,
        "content_size": 36,
        "title_max_width": "1400px",
        "content_max_width": "1200px",
        "extra_css": """
        .top-vignette {
            position: absolute; top: 0; left: 0; width: 100%; height: 50%;
            background: linear-gradient(to bottom, rgba(0,0,0,0.15), transparent);
            z-index: 1;
        }
        """,
    },
    # 版面 D：分割版面（標題左大、內容右小）
    "split": {
        "content_justify": "center",
        "content_align": "flex-start",
        "text_align": "left",
        "content_padding": "80px 100px",
        "title_size": 84,
        "content_size": 34,
        "title_max_width": "900px",
        "content_max_width": "750px",
        "extra_css": """
        .split-divider {
            position: absolute; left: 55%; top: 15%; width: 2px; height: 70%;
            background: linear-gradient(to bottom, transparent, {accent_color}, transparent);
            opacity: 0.4; z-index: 2;
        }
        .content-layer .title {
            width: 50%; padding-right: 60px;
        }
        .content-layer .content {
            position: absolute; right: 100px; top: 50%; transform: translateY(-50%);
            width: 38%; text-align: left;
        }
        """,
    },
}

# 版面輪替順序
LAYOUT_ORDER = ["center", "left", "bottom", "split"]

# ── 多平台比例與解析度支援 ──────────────────────────────
ASPECT_RATIOS = {
    "16:9": {"desc": "YouTube/Bilibili 標準橫式", "factor": (16, 9)},
    "9:16": {"desc": "抖音/Shorts/TikTok 直式", "factor": (9, 16)},
    "1:1":  {"desc": "Instagram 正方形", "factor": (1, 1)},
    "4:3":  {"desc": "傳統 4:3 比例", "factor": (4, 3)},
}

RESOLUTION_PRESETS = {
    "1080p": {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1":  (1080, 1080),
        "4:3":  (1440, 1080),
    },
    "4k": {
        "16:9": (3840, 2160),
        "9:16": (2160, 3840),
        "1:1":  (2160, 2160),
        "4:3":  (2880, 2160),
    },
}


def get_slide_dimensions(ratio: str = "16:9", resolution: str = "1080p") -> tuple[int, int]:
    """根據比例和解析度取得投影片寬高。"""
    presets = RESOLUTION_PRESETS.get(resolution, RESOLUTION_PRESETS["1080p"])
    return presets.get(ratio, presets["16:9"])


def _build_html(
    title: str,
    content: str,
    slide_number: str,
    author: str,
    theme: dict,
    layout: dict,
    layout_name: str,
    bg_image_url: str = "",
    is_title_slide: bool = False,
) -> str:
    """組合完整的 HTML 投影片。所有樣式內建於 HTML/CSS 中，無需外部圖檔。"""

    # 標題投影片用更大字體
    t_size = layout["title_size"] + 10 if is_title_slide else layout["title_size"]
    c_size = layout["content_size"] + 4 if is_title_slide else layout["content_size"]

    # 處理版面專屬 CSS 中的主題變數替換
    extra_css = layout["extra_css"].replace("{accent_color}", theme["accent_color"])

    # 版面專屬 HTML 元素
    extra_html = ""
    if layout_name == "left":
        extra_html = '<div class="side-accent"></div>'
    elif layout_name == "bottom":
        extra_html = '<div class="top-vignette"></div>'
    elif layout_name == "split":
        extra_html = '<div class="split-divider"></div>'

    # 背景圖片樣式
    bg_image_style = ""
    if bg_image_url:
        bg_image_style = f"background-image: url('{bg_image_url}');"

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920, height=1080">
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;700;900&display=swap');

/* 重置 */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

/* 畫布 */
body {{
    width: 1920px; height: 1080px;
    font-family: 'Noto Sans TC', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
    color: #fff; overflow: hidden; position: relative;
    background: {theme["body_bg"]};
}}

/* 背景圖層 */
.bg-image {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background-size: cover; background-position: center; z-index: 0;
    {bg_image_style}
}}
.bg-overlay {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: {theme["overlay_bg"]}; z-index: 1;
}}

/* 裝飾性光暈球 */
.glow-orb {{
    position: absolute; border-radius: 50%; filter: blur(80px);
    z-index: 1; pointer-events: none;
}}
.glow-1 {{
    width: 600px; height: 600px;
    background: {theme["glow_color_1"]};
    top: -200px; right: -100px;
}}
.glow-2 {{
    width: 400px; height: 400px;
    background: {theme["glow_color_2"]};
    bottom: -150px; left: -50px;
}}
.glow-3 {{
    width: 300px; height: 300px;
    background: {theme["glow_color_1"]};
    bottom: 200px; right: 300px; opacity: 0.5;
}}

/* 裝飾線條（頂部與底部） */
.deco-line {{
    position: absolute; z-index: 2; pointer-events: none;
    background: linear-gradient(90deg, transparent, {theme["deco_line_color"]}, transparent);
    height: 1px;
}}
.deco-top {{ top: 60px; left: 50%; transform: translateX(-50%); width: 500px; }}
.deco-bottom {{ bottom: 60px; left: 50%; transform: translateX(-50%); width: 400px; }}

/* 引號裝飾 */
.quote-mark {{
    position: absolute; font-size: 220px;
    font-family: 'Noto Sans TC', Georgia, serif;
    color: {theme["quote_color"]}; z-index: 2;
    line-height: 1; pointer-events: none; user-select: none;
}}
.quote-open {{ top: 40px; left: 80px; }}
.quote-close {{ bottom: 0px; right: 80px; }}

/* 內容層 */
.content-layer {{
    position: relative; z-index: 3;
    display: flex; flex-direction: column;
    justify-content: {layout["content_justify"]};
    align-items: {layout["content_align"]};
    width: 100%; height: 100%;
    padding: {layout["content_padding"]};
}}

/* 標題 */
.title {{
    font-size: {t_size}px; font-weight: 900;
    text-align: {layout["text_align"]};
    margin-bottom: 30px; line-height: 1.3;
    letter-spacing: 6px;
    color: {theme["title_color"]};
    text-shadow: {theme["title_shadow"]};
    max-width: {layout["title_max_width"]};
}}

/* 內文 */
.content {{
    font-size: {c_size}px; font-weight: 300;
    text-align: {layout["text_align"]};
    line-height: 2.0; letter-spacing: 2px;
    color: {theme["content_color"]};
    text-shadow: {theme["content_shadow"]};
    max-width: {layout["content_max_width"]};
}}

/* 頁碼/作者 */
.meta {{
    position: absolute; bottom: 30px; right: 50px;
    font-size: 16px; color: {theme["meta_color"]};
    z-index: 3; letter-spacing: 1px;
}}

/* 底部漸層裝飾條 */
.bottom-bar {{
    position: absolute; bottom: 0; left: 0; width: 100%; height: 5px;
    background: linear-gradient(90deg, {theme["bottom_bar_colors"]});
    z-index: 3;
}}

/* 版面專屬樣式 */
{extra_css}
</style>
</head>
<body>
    <!-- 背景圖層 -->
    <div class="bg-image"></div>
    <div class="bg-overlay"></div>

    <!-- 裝飾光暈 -->
    <div class="glow-orb glow-1"></div>
    <div class="glow-orb glow-2"></div>
    <div class="glow-orb glow-3"></div>

    <!-- 裝飾線條 -->
    <div class="deco-line deco-top"></div>
    <div class="deco-line deco-bottom"></div>

    <!-- 角落裝飾線 -->
    <div style="position:absolute;top:50px;left:60px;width:60px;height:60px;border-top:2px solid {theme["deco_line_color"]};border-left:2px solid {theme["deco_line_color"]};z-index:2;"></div>
    <div style="position:absolute;bottom:50px;right:60px;width:60px;height:60px;border-bottom:2px solid {theme["deco_line_color"]};border-right:2px solid {theme["deco_line_color"]};z-index:2;"></div>

    <!-- 版面專屬裝飾 -->
    {extra_html}

    <!-- 主要內容 -->
    <div class="content-layer">
        <div class="title">{title}</div>
        <div class="content">{content}</div>
    </div>

    <!-- 頁碼 -->
    <div class="meta">{author} &nbsp;|&nbsp; {slide_number}</div>

    <!-- 底部裝飾條 -->
    <div class="bottom-bar"></div>
</body>
</html>"""
    return html


def find_chrome() -> str:
    """跨平台尋找 Chrome 執行檔路徑。"""
    system = platform.system()

    # 依作業系統選擇候選路徑
    if system == "Windows":
        candidates = CHROME_PATHS_WINDOWS
    elif system == "Darwin":
        candidates = CHROME_PATHS_MACOS
    elif system == "Linux":
        candidates = CHROME_PATHS_LINUX
    else:
        candidates = []

    # 逐一檢查候選路徑
    for path in candidates:
        expanded = os.path.expandvars(path)
        if os.path.isfile(expanded):
            return expanded

    # 使用 shutil.which 作為備援（跨平台通用）
    for cmd_name in [
        "google-chrome", "google-chrome-stable",
        "chromium-browser", "chromium", "chrome",
    ]:
        found = shutil.which(cmd_name)
        if found:
            return found

    # Windows 額外嘗試 where 指令
    if system == "Windows":
        try:
            result = subprocess.run(
                ["where", "chrome"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

    return ""


def generate_ai_image(prompt: str, output_path: Path) -> bool:
    """使用 fal.ai FLUX Schnell 生成 AI 背景圖片（每張約 $0.003）。需要 FAL_KEY 環境變數。"""
    import urllib.request

    fal_key = os.environ.get("FAL_KEY", "")
    if not fal_key:
        return False

    api_url = "https://fal.run/fal-ai/flux/schnell"
    payload = json.dumps({
        "prompt": prompt,
        "image_size": "landscape_16_9",
        "num_images": 1,
    }).encode("utf-8")

    req = urllib.request.Request(api_url, data=payload, method="POST")
    req.add_header("Authorization", f"Key {fal_key}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            image_url = result.get("images", [{}])[0].get("url", "")
            if not image_url:
                return False
            # 下載圖片到本地
            urllib.request.urlretrieve(image_url, str(output_path))
            return output_path.is_file()
    except Exception as e:
        print(f"  [AI 圖片] 生成失敗: {e}", file=sys.stderr)
        return False


def generate_image_prompt(slide_title: str, slide_content: str, video_title: str) -> str:
    """根據投影片內容生成符合主題意象的背景圖提示詞。避開會產生文字的場景。"""
    # 用投影片標題和影片主題推導視覺意象
    return (
        f"Cinematic photograph, visual metaphor for '{slide_title}', "
        f"in the context of '{video_title}'. "
        f"Beautiful natural scenery or abstract environment, "
        f"soft cinematic lighting, shallow depth of field, warm color grading, "
        f"emotional and atmospheric mood, professional photography, "
        f"NO text, NO letters, NO characters, NO words, NO signs, NO writing, "
        f"NO storefronts, NO banners, NO posters, NO books, NO screens, "
        f"NO watermark, avoid any readable content, "
        f"8K resolution, suitable as video background"
    )


def generate_html(
    section: dict,
    index: int,
    total: int,
    author: str,
    is_title: bool = False,
    theme_name: str = "cinematic",
    bg_image_path: str = "",
) -> str:
    """根據 section 資料生成 HTML 投影片。使用 index % 4 自動輪替版面配置。"""
    title = section.get("slide_title", "")
    content = section.get("slide_content", "").replace("\n", "<br>")

    # 取得主題
    theme = THEMES.get(theme_name, THEMES["cinematic"])

    # 根據 index 輪替版面（標題投影片固定用置中版面）
    if is_title:
        layout_name = "center"
    else:
        layout_name = LAYOUT_ORDER[(index - 1) % len(LAYOUT_ORDER)]
    layout = LAYOUTS[layout_name]

    # 背景圖片 URL
    bg_image_url = ""
    if bg_image_path and Path(bg_image_path).is_file():
        bg_image_url = Path(bg_image_path).resolve().as_uri()

    return _build_html(
        title=title,
        content=content,
        slide_number=f"{index}/{total}",
        author=author,
        theme=theme,
        layout=layout,
        layout_name=layout_name,
        bg_image_url=bg_image_url,
        is_title_slide=is_title,
    )


def screenshot_html(
    html_path: Path, png_path: Path, chrome_path: str,
    width: int = 1920, height: int = 1080,
) -> bool:
    """使用 Chrome headless 模式將 HTML 截圖為 PNG。支援自訂解析度。"""
    file_url = html_path.resolve().as_uri()
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-software-rasterizer",
        f"--screenshot={png_path.resolve()}",
        f"--window-size={width},{height}",
        "--hide-scrollbars",
        file_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if png_path.is_file():
            return True
        print(f"  [警告] 截圖失敗: {result.stderr[:200]}", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print(f"  [警告] Chrome 截圖逾時: {html_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  [錯誤] 截圖異常: {e}", file=sys.stderr)
        return False


def main():
    """主程式：解析參數、生成投影片 HTML 與 PNG 截圖。"""
    parser = argparse.ArgumentParser(
        description="從 JSON 腳本生成 YouTube 品質的 HTML 投影片並截圖為 PNG"
    )
    parser.add_argument("--input", "-i", required=True, help="輸入的 JSON 腳本檔案路徑")
    parser.add_argument("--output-dir", "-o", default="slides", help="輸出目錄（預設: slides/）")
    parser.add_argument("--chrome", default="", help="Chrome 執行檔路徑（選填，自動偵測）")
    parser.add_argument("--html-only", action="store_true", help="僅生成 HTML，不截圖")
    parser.add_argument(
        "--theme", default="cinematic",
        choices=list(THEMES.keys()),
        help="投影片主題（預設: cinematic）。cinematic=電影級金色(推薦), dark=深藍冷調, light=白底淡雅, nature=深綠自然",
    )
    parser.add_argument(
        "--ai-bg", action="store_true",
        help="使用 AI 生成每張投影片的背景圖（需要 FAL_KEY 環境變數，每張約 $0.003）",
    )
    parser.add_argument(
        "--ratio", default="16:9",
        choices=list(ASPECT_RATIOS.keys()),
        help="畫面比例（預設: 16:9）。16:9=YouTube, 9:16=抖音/Shorts, 1:1=Instagram, 4:3=傳統",
    )
    parser.add_argument(
        "--resolution", default="1080p",
        choices=list(RESOLUTION_PRESETS.keys()),
        help="解析度（預設: 1080p）。1080p=標準, 4k=超高畫質",
    )
    args = parser.parse_args()

    # 取得投影片尺寸
    slide_width, slide_height = get_slide_dimensions(args.ratio, args.resolution)

    # 讀取 JSON 腳本
    input_path = Path(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    sections = script.get("sections", [])
    if not sections:
        print("[錯誤] JSON 腳本中沒有 sections", file=sys.stderr)
        sys.exit(1)

    author = script.get("author", "")
    video_title = script.get("title", "")
    total = len(sections)

    # 建立輸出目錄
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bg_dir = output_dir / "bg_images"

    # AI 背景圖：檢查 FAL_KEY 並提示
    use_ai_bg = args.ai_bg
    fal_key = os.environ.get("FAL_KEY", "")
    if use_ai_bg:
        if not fal_key:
            print("[警告] FAL_KEY 未設定，無法生成 AI 背景圖，改用純色背景", file=sys.stderr)
            use_ai_bg = False
        else:
            bg_dir.mkdir(parents=True, exist_ok=True)
            est_cost = total * 0.003
            print(f"[AI 背景] 將生成 {total} 張 AI 背景圖（預估費用 ${est_cost:.3f}）")
    elif fal_key:
        # 有 FAL_KEY 但未啟用 --ai-bg，提示使用者
        print("[提示] 偵測到 FAL_KEY，可加上 --ai-bg 參數啟用 AI 背景圖生成")

    # 尋找 Chrome
    chrome_path = args.chrome or find_chrome()
    if not args.html_only and not chrome_path:
        print(
            "[錯誤] 找不到 Chrome。請用 --chrome 指定路徑，或使用 --html-only 僅生成 HTML。",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[投影片生成] 共 {total} 張投影片")
    print(f"[解析度] {slide_width}x{slide_height}（{args.ratio}, {args.resolution}）")
    if not args.html_only:
        print(f"[Chrome] {chrome_path}")
    print(f"[主題] {args.theme}")
    print(f"[版面] 4 種版面自動輪替（center → left → bottom → split）")

    success_count = 0
    for i, section in enumerate(sections, 1):
        is_title = (i == 1)
        slide_title = section.get("slide_title", "")
        slide_content = section.get("slide_content", "")

        # AI 背景圖生成
        bg_image_path = ""
        if use_ai_bg:
            bg_path = bg_dir / f"bg_{i:02d}.jpg"
            prompt = generate_image_prompt(slide_title, slide_content, video_title)
            print(f"  [{i}/{total}] AI 背景圖...", end=" ", flush=True)
            if generate_ai_image(prompt, bg_path):
                bg_image_path = str(bg_path)
                print("OK")
            else:
                print("跳過（使用純色背景）")

        # 生成 HTML
        html_content = generate_html(
            section, i, total, author, is_title,
            theme_name=args.theme, bg_image_path=bg_image_path,
        )

        html_path = output_dir / f"slide_{i:02d}.html"
        png_path = output_dir / f"slide_{i:02d}.png"

        # 寫入 HTML 檔案
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 截圖或僅輸出 HTML
        if not args.html_only:
            layout_name = "center" if is_title else LAYOUT_ORDER[(i - 1) % len(LAYOUT_ORDER)]
            print(f"  [{i}/{total}] 截圖 [{layout_name}]: {slide_title[:30]}...", end=" ")
            if screenshot_html(html_path, png_path, chrome_path, slide_width, slide_height):
                print("OK")
                success_count += 1
            else:
                print("FAILED")
        else:
            print(f"  [{i}/{total}] HTML: {html_path}")
            success_count += 1

    print(f"\n[完成] 成功 {success_count}/{total} 張投影片，輸出至 {output_dir}/")
    if success_count < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
