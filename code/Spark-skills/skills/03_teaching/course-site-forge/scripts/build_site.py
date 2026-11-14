# -*- coding: utf-8 -*-
"""course-site-forge：規格化 md → mini 課程站（index.html＋每章可翻頁簡報）。

輸入格式（CH41 規格化文件）：
  #  (H1) ＝ 篇（整站標題）
  ## (H2) ＝ 章（一章一份簡報）
  ###(H3) ＝ 頁（一頁一張投影片）
  區塊標記：【講稿】→ .say 講稿框、【指令】→ .do＋pre＋複製鈕、
            【截圖位】→ .shotbox 占位框、【下載】→ .dlbox 下載說明框

用法：
  python build_site.py <輸入.md> <輸出資料夾>
  python build_site.py            # 用內建預設路徑（CH45 示範）
"""
import html
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "範本_教學簡報.html"

MARKERS = ("【講稿】", "【指令】", "【截圖位】", "【下載】")


# ---------- 解析 ----------

def parse_spec(md_text):
    """把規格化 md 解析成 {site, chapters:[{title, pages:[{title, blocks:[(kind, text)]}]}]}"""
    site = ""
    chapters = []
    cur_ch = None
    cur_pg = None
    cur_kind = None
    buf = []

    def flush_block():
        nonlocal cur_kind, buf
        if cur_kind and cur_pg is not None:
            text = "\n".join(buf).strip()
            if text:
                cur_pg["blocks"].append((cur_kind, text))
        cur_kind, buf = None, []

    in_fence = False
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            if cur_kind is not None:
                buf.append(line)
            continue
        if in_fence:  # 圍欄內的 # 是程式註解，不是標題
            if cur_kind is not None:
                buf.append(line)
            continue
        if s.startswith("# ") and not s.startswith("## "):
            flush_block()
            site = s[2:].strip()
        elif s.startswith("## ") and not s.startswith("### "):
            flush_block()
            cur_ch = {"title": s[3:].strip(), "pages": []}
            chapters.append(cur_ch)
            cur_pg = None
        elif s.startswith("### "):
            flush_block()
            if cur_ch is None:  # H3 出現在任何 H2 之前 → 視為格式錯誤但不炸掉
                cur_ch = {"title": "未命名章", "pages": []}
                chapters.append(cur_ch)
            cur_pg = {"title": s[4:].strip(), "blocks": []}
            cur_ch["pages"].append(cur_pg)
        elif s in MARKERS:
            flush_block()
            cur_kind = s.strip("【】")
        elif s.startswith(">"):
            continue  # 檔頭引言列不進頁面
        else:
            if cur_kind is not None:
                buf.append(line)
    flush_block()
    return {"site": site or "未命名課程", "chapters": chapters}


def extract_code(text):
    """從【指令】區塊取出 (語言, 程式碼)。支援 ``` 圍欄；無圍欄則整段當程式碼。"""
    m = re.search(r"```([\w.+-]*)\n(.*?)```", text, re.S)
    if m:
        return (m.group(1) or "text"), m.group(2).rstrip()
    return "text", text.strip()


# ---------- 生成 ----------

def esc(t):
    return html.escape(t, quote=False)


def render_page(ch_label, pg, idx):
    parts = [f'<section class="slide{" active" if idx == 0 else ""}">']
    parts.append(f'<span class="kicker">{esc(ch_label)}</span>')
    parts.append(f"<h2>{esc(pg['title'])}</h2>")
    for kind, text in pg["blocks"]:
        if kind == "講稿":
            parts.append(f'<div class="say"><p>{esc(text)}</p></div>')
        elif kind == "指令":
            lang, code = extract_code(text)
            parts.append(
                f'<div class="do"><span class="tag">複製貼上執行（{esc(lang)}）</span>\n'
                f"<pre><code>{html.escape(code)}</code></pre></div>"
            )
        elif kind == "截圖位":
            parts.append(
                '<div class="shotbox"><span class="cam">📷</span>'
                f"<b>截圖位（之後放真實截圖）</b><span>{esc(text)}</span></div>"
            )
        elif kind == "下載":
            parts.append(f'<div class="dlbox"><b>⬇ 本頁提供下載：</b>{esc(text)}</div>')
    parts.append("</section>")
    return "\n".join(parts)


def render_cover(ch, ch_label, n_pages, n_cmds):
    return (
        '<section class="slide active">'
        f'<span class="kicker">{esc(ch_label)} · 章封面</span>'
        f"<h1>{esc(ch['title'])}</h1>"
        f'<p class="lead">本章共 {n_pages} 頁、{n_cmds} 段可複製指令。'
        "用左下按鈕或鍵盤 ←→ 翻頁，指令框右上角都有複製鈕。</p>"
        "</section>"
    )


def chapter_meta(ch, i):
    m = re.match(r"(CH\d+)\s*(.*)", ch["title"])
    code = m.group(1).lower() if m else f"ch{i + 1:02d}"
    label = m.group(1) if m else f"第 {i + 1} 章"
    name = (m.group(2) if m else ch["title"]).strip() or ch["title"]
    n_cmds = sum(1 for p in ch["pages"] for k, _ in p["blocks"] if k == "指令")
    stars = 1 if n_cmds <= 2 else (2 if n_cmds <= 4 else 3)
    first_say = next(
        (t for p in ch["pages"] for k, t in p["blocks"] if k == "講稿"), ""
    )
    brief = first_say.split("。")[0][:52] + "。" if first_say else "本章簡介。"
    return code, label, name, n_cmds, stars, brief


INDEX_TMPL = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__SITE__｜課程總覽</title><link rel="icon" href="data:,">
<style>
  :root{--ink:#2b2620;--ink2:#5b5348;--paper:#fbf7ef;--card:#fffdf8;--line:#e5dcc8;
    --accent:#e07a3f;--accent2:#2f8f83;--blue:#3a6ea5;--yellow:#f0c04a;--shadow:rgba(60,45,25,.14)}
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Microsoft JhengHei','PingFang TC',system-ui,sans-serif;background:#c9bfa8;color:var(--ink);
    min-height:100vh;padding:48px 6vw 64px}
  .wrap{max-width:1180px;margin:0 auto;background:
    radial-gradient(circle at 12% 8%, #fffdf8 0%, transparent 40%),
    linear-gradient(160deg,#fdfaf3 0%,#f6efe0 100%);
    border:2px solid var(--ink);border-radius:18px;padding:44px 48px 52px;position:relative;box-shadow:6px 7px 0 var(--shadow)}
  .wrap::after{content:'';position:absolute;inset:8px;border:1.5px dashed #d8ccb0;border-radius:14px;pointer-events:none}
  .kicker{display:inline-block;background:var(--accent);color:#fff;font-weight:800;
    padding:4px 14px;border-radius:20px;font-size:14px;transform:rotate(-1.5deg);border:2px solid var(--ink)}
  h1{font-size:38px;margin:14px 0 6px}
  .lead{font-size:19px;color:var(--ink2);margin-bottom:22px}
  .chs{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px;position:relative;z-index:1}
  .ch{background:var(--card);border:2px solid var(--ink);border-radius:14px;padding:18px 20px;
    box-shadow:4px 5px 0 var(--shadow);position:relative}
  .no{position:absolute;top:-12px;left:14px;background:var(--yellow);border:2px solid var(--ink);
    border-radius:10px;font-weight:800;font-size:14px;padding:2px 10px;transform:rotate(-2deg)}
  .ch h3{font-size:20px;margin:10px 0 6px}
  .ch p{font-size:15px;color:var(--ink2);line-height:1.6;min-height:48px}
  .meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px}
  .stars{color:var(--accent);font-size:15px;letter-spacing:2px}
  .pillx{background:var(--blue);color:#fff;padding:2px 10px;border-radius:20px;font-size:13px;font-weight:700}
  .go{margin-left:auto;background:var(--ink);color:#fff;text-decoration:none;font-weight:700;font-size:14px;
    padding:7px 14px;border-radius:10px;border:2px solid var(--ink)}
  .go:hover{background:var(--accent)}
  .dl2{background:var(--accent2);color:#fff;text-decoration:none;font-weight:700;font-size:14px;
    padding:7px 12px;border-radius:10px;border:2px solid var(--ink)}
  .foot{text-align:center;margin-top:26px;color:#6b5f48;font-size:13px;position:relative;z-index:1}
</style>
</head>
<body>
<div class="wrap">
  <span class="kicker">course-site-forge 一鍵生站</span>
  <h1>__SITE__</h1>
  <p class="lead">共 __NCH__ 章 __NPG__ 頁。點「開始上課 ▶」進入可翻頁簡報；星等代表本章指令量（動手強度）。</p>
  <div class="chs">
__CARDS__
  </div>
  <div class="foot">本站由 course-site-forge 依規格化教材自動生成 · 設計 DNA 沿用課程卡片手繪風</div>
</div>
</body>
</html>
"""

CARD_TMPL = (
    '    <div class="ch"><div class="no">__LABEL__</div><h3>__NAME__</h3>'
    "<p>__BRIEF__</p>"
    '<div class="meta"><span class="stars">__STARS__</span>'
    '<span class="pillx">__NPG__ 頁</span><span class="pillx">__NCMD__ 段指令</span>'
    '<a class="go" href="__HREF__">開始上課 ▶</a>'
    '<a class="dl2" href="__HREF__" title="示範站不含成品包，下載鈕連到本章簡報">⬇ 下載</a></div></div>'
)


def build(md_path, out_dir):
    md_path, out_dir = Path(md_path), Path(out_dir)
    spec = parse_spec(md_path.read_text(encoding="utf-8"))
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)

    metas = [chapter_meta(ch, i) for i, ch in enumerate(spec["chapters"])]
    files = []
    for i, ch in enumerate(spec["chapters"]):
        code, label, name, n_cmds, stars, brief = metas[i]
        ch_label = f"{spec['site'].split('：')[0]} · {label}"
        slides = [render_cover(ch, label, len(ch["pages"]), n_cmds)]
        for j, pg in enumerate(ch["pages"]):
            slides.append(render_page(f"{label} · 第 {j + 1} 頁", pg, -1))
        if i + 1 < len(metas):
            nxt = metas[i + 1]
            next_url, next_label = f"{nxt[0]}.html", f"下一章：{nxt[1]} {nxt[2]} →"
        else:
            next_url, next_label = "index.html", "🎉 回課程首頁 →"
        out = (
            tmpl.replace("{{CHAPTER_TITLE}}", f"{label} {name}")
            .replace("{{SITE_TITLE}}", spec["site"])
            .replace("{{SLIDES}}", "\n\n".join(slides))
            .replace("{{NEXT_URL}}", next_url)
            .replace("{{NEXT_LABEL}}", next_label)
        )
        fp = out_dir / f"{code}.html"
        fp.write_text(out, encoding="utf-8")
        files.append((fp.name, len(ch["pages"]) + 1))

    cards = []
    for i, ch in enumerate(spec["chapters"]):
        code, label, name, n_cmds, stars, brief = metas[i]
        cards.append(
            CARD_TMPL.replace("__LABEL__", esc(label))
            .replace("__NAME__", esc(name))
            .replace("__BRIEF__", esc(brief))
            .replace("__STARS__", "★" * stars + "☆" * (3 - stars))
            .replace("__NPG__", str(len(ch["pages"])))
            .replace("__NCMD__", str(n_cmds))
            .replace("__HREF__", f"{code}.html")
        )
    total_pages = sum(len(c["pages"]) for c in spec["chapters"])
    index = (
        INDEX_TMPL.replace("__SITE__", esc(spec["site"]))
        .replace("__NCH__", str(len(spec["chapters"])))
        .replace("__NPG__", str(total_pages))
        .replace("__CARDS__", "\n".join(cards))
    )
    (out_dir / "index.html").write_text(index, encoding="utf-8")

    print(f"站名：{spec['site']}")
    print(f"章數：{len(spec['chapters'])}　規格頁數：{total_pages}")
    for name, n in files:
        print(f"  產出 {name}（{n} 張投影片，含章封面）")
    print(f"  產出 index.html（{len(cards)} 張章節卡片）")
    print(f"輸出資料夾：{out_dir}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        src, dst = sys.argv[1], sys.argv[2]
    else:  # CH45 示範預設（僅在 CH45 章資料夾／下載包解壓結構內有效）
        ch45 = SKILL_DIR.parent.parent  # .../CH45_封裝SKILL一鍵生站
        src = ch45 / "範例資料" / "課程內容規格化範本_完整範例.md"
        dst = ch45 / "成品" / "示範輸出_開放資料入門站"
        if not Path(src).is_file():
            print("找不到內建示範輸入：", src)
            print("「不帶參數」模式僅限在 CH45 章資料夾（下載包解壓結構）內執行；")
            print("技能單獨安裝到 skills 目錄後請帶兩個參數：")
            print("  python build_site.py <輸入規格化.md> <輸出資料夾>")
            sys.exit(2)
    sys.exit(build(src, dst))
