#!/usr/bin/env python3
"""
web-scraper 統一 CLI
====================

用法（最常見）：
  python scrape.py doctor                                  # 環境檢查
  python scrape.py search "<query>" [--top N] [--fetch]    # TinyFish 搜尋
  python scrape.py fetch  <url> [--format md|html|text]    # 抓單頁
  python scrape.py stealthy <url> [--css "..."]            # 反爬蟲（Firefox 系）
  python scrape.py cloak    <url> [--css "..."]            # 隱形 Chromium（CloakBrowser）
  python scrape.py dynamic  <url> [--css "..."]            # JS 渲染
  python scrape.py agent    <url> --goal "..."             # 自然語言爬蟲
  python scrape.py crawl    <url> [--selector ...]         # 整站爬取
  python scrape.py news     [--topic tech|edu|both]        # 預設新聞來源
  python scrape.py to-pdf   <input.md|url|dir/> --out X.pdf

設計：依參數路由到 Scrapling（本地）或 TinyFish（雲端），
缺套件就提示安裝；缺 API Key 就 fallback 到本地引擎。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable

# 確保同目錄模組（captcha_solver）可被 import，不論用什麼方式啟動腳本。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --------- 全域 fallback：套件可能沒裝，先盡量別 import 死全部 ---------

def _has(mod: str) -> bool:
    """安靜檢查：靜音 stderr，避免某些套件 import 時的 ctypes / GTK 雜訊。"""
    import importlib
    import io
    import contextlib
    try:
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            importlib.import_module(mod)
        return True
    except Exception:
        return False


# ============================================================
# doctor：環境自我檢查
# ============================================================
def cmd_doctor(args: argparse.Namespace) -> int:
    print("=== web-scraper doctor ===\n")
    rows: list[tuple[str, bool, str]] = []

    rows.append(("Python", sys.version_info >= (3, 10), sys.version.split()[0]))
    rows.append(("requests", _has("requests"), "pip install requests"))
    rows.append(("scrapling", _has("scrapling"), "pip install \"scrapling[all]\" && scrapling install"))
    rows.append(("playwright (含 Chromium，PDF 輸出也用)", _has("playwright"), "scrapling install"))
    rows.append(("cloakbrowser (隱形 Chromium，選用)", _has("cloakbrowser"), "pip install cloakbrowser（首次跑會抓 ~200MB binary）"))
    rows.append(("youtube_transcript_api (for learn)", _has("youtube_transcript_api"), "pip install youtube-transcript-api"))
    rows.append(("markdown (PDF 排版)", _has("markdown"), "pip install markdown"))
    rows.append(("pandas (optional, tables)", _has("pandas"), "pip install pandas openpyxl"))
    rows.append(("weasyprint (optional, Linux/Mac 才推薦)", _has("weasyprint"), "Windows 不需要，PDF 用 Playwright"))

    api_key = os.environ.get("TINYFISH_API_KEY", "")
    rows.append(("TINYFISH_API_KEY", bool(api_key), "https://agent.tinyfish.ai → 註冊 → 設環境變數"))
    cap = os.environ.get("NOPECHA_API_KEY") or os.environ.get("TWOCAPTCHA_API_KEY")
    rows.append(("CAPTCHA 解碼金鑰（選用，--solve-captcha 才需）", bool(cap),
                 "設 NOPECHA_API_KEY 或 TWOCAPTCHA_API_KEY（付費服務，限授權場景）"))

    width = max(len(r[0]) for r in rows) + 2
    for name, ok, hint in rows:
        flag = "OK" if ok else "MISSING"
        print(f"  [{flag:>7}] {name.ljust(width)} {'' if ok else '→ ' + hint}")

    print("\n建議下一步：" + ("一切就緒，可以開爬！" if all(r[1] for r in rows[:3]) else "先補齊 MISSING 項。"))
    return 0


# ============================================================
# 共用：保存輸出
# ============================================================
def _save(content: str | bytes | list | dict, out: str, fmt_hint: str = "") -> None:
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (list, dict)):
        p.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    elif isinstance(content, bytes):
        p.write_bytes(content)
    else:
        p.write_text(content, encoding="utf-8")
    print(f"OK → {p.resolve()}")


def _now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ============================================================
# learn 快取
# ============================================================
def _learn_cache_dir() -> Path:
    return Path.home() / ".cache" / "web-scraper" / "learn"


def _learn_cache_key(args: argparse.Namespace) -> str:
    """根據會影響輸出內容的旗標計算 key（不含 out / pdf / cache 旗標本身）。"""
    parts = [
        (args.topic or "").strip().lower(),
        ",".join(sorted((args.include or "").split(","))),
        f"v{args.videos}",
        f"a{args.articles}",
        f"g{args.github}",
        f"x{args.arxiv}",
        f"ac{args.article_chars}",
        f"gc{args.github_readme_chars}",
    ]
    sig = "|".join(parts)
    return hashlib.sha256(sig.encode("utf-8")).hexdigest()[:16]


def _learn_cache_lookup(args: argparse.Namespace) -> tuple[Path | None, float]:
    """回傳 (有效快取檔, age_seconds)；無命中回 (None, 0)。"""
    if getattr(args, "no_cache", False):
        return None, 0.0
    cache_file = _learn_cache_dir() / f"{_learn_cache_key(args)}.md"
    if not cache_file.exists():
        return None, 0.0
    age = time.time() - cache_file.stat().st_mtime
    if age > args.cache_ttl:
        return None, age
    return cache_file, age


def _learn_cache_write(args: argparse.Namespace, content: str) -> Path:
    cache_dir = _learn_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{_learn_cache_key(args)}.md"
    cache_file.write_text(content, encoding="utf-8")
    return cache_file


# ============================================================
# 共用 helper：YouTube / arXiv / GitHub
# ============================================================
import re as _re


def _yt_video_id(url: str) -> str | None:
    """從各種 YouTube URL 抽 video id。"""
    if not url:
        return None
    patterns = [
        r"(?:v=|youtu\.be/|/embed/|/shorts/)([0-9A-Za-z_-]{11})",
        r"^([0-9A-Za-z_-]{11})$",
    ]
    for p in patterns:
        m = _re.search(p, url)
        if m:
            return m.group(1)
    return None


# ------------------------------------------------------------
# v1.2: retry-with-backoff
# ------------------------------------------------------------
def _retry(fn, *args, attempts: int = 3, base_delay: float = 1.0,
           label: str = "", **kwargs):
    """通用 retry-with-backoff。回傳 (result, error_str_or_None)。
    重試訊息會印到 stderr，不影響 stdout 結構化輸出。"""
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return fn(*args, **kwargs), None
        except Exception as e:
            last_err = e
            if i < attempts - 1:
                wait = base_delay * (2 ** i)
                if label:
                    print(f"   ⚠️  {label} 第 {i+1}/{attempts} 次失敗（{type(e).__name__}），{wait:.1f}s 後重試", file=sys.stderr)
                time.sleep(wait)
    return None, f"{type(last_err).__name__}: {last_err}" if last_err else "unknown"


# ------------------------------------------------------------
# v1.2: youtube-subtitle SKILL 委派（Whisper fallback）
# ------------------------------------------------------------
def _yt_subtitle_skill_path() -> Path | None:
    """偵測 youtube-subtitle SKILL 是否安裝。"""
    p = Path.home() / ".claude" / "skills" / "youtube-subtitle" / "scripts" / "yt_subtitle.py"
    return p if p.exists() else None


def _srt_to_plain(srt_text: str) -> str:
    """SRT 內容抽純文字（去序號、時間戳）。"""
    lines = []
    for block in srt_text.strip().split("\n\n"):
        rows = [
            r for r in block.strip().split("\n")
            if r and "-->" not in r and not r.strip().isdigit()
        ]
        if rows:
            lines.append(" ".join(rows))
    return "\n".join(lines)


def _yt_via_skill(url: str, timeout: int = 120) -> tuple[str | None, str | None]:
    """委派給 youtube-subtitle SKILL 抓字幕（會先試 CC、失敗自動 Whisper）。"""
    script = _yt_subtitle_skill_path()
    if not script:
        return None, "youtube-subtitle SKILL 未安裝於 ~/.claude/skills/youtube-subtitle/"
    import subprocess as _sp
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = _sp.run(
                [sys.executable, str(script), url, "-o", tmp, "-l", "zh", "-m", "tiny"],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace",
            )
            if r.returncode != 0:
                tail = (r.stderr or r.stdout or "")[-200:]
                return None, f"yt-subtitle exit={r.returncode}: {tail}"
            srts = list(Path(tmp).glob("*.srt"))
            if not srts:
                return None, "yt-subtitle 沒產生 SRT 檔"
            srt_text = srts[0].read_text(encoding="utf-8", errors="replace")
            return _srt_to_plain(srt_text), None
        except _sp.TimeoutExpired:
            return None, f"yt-subtitle 執行超時（>{timeout}s）"
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"


def _yt_transcript(video_id: str, langs: list[str] | None = None) -> tuple[str | None, str | None]:
    """抓字幕；中文優先 → 英文 fallback。回傳 (transcript, error)。"""
    langs = langs or ["zh-TW", "zh-Hant", "zh-CN", "zh", "zh-Hans", "en", "en-US", "en-GB"]
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        from youtube_transcript_api._errors import (   # type: ignore
            TranscriptsDisabled,
            NoTranscriptFound,
        )
    except ImportError:
        return None, "未安裝 youtube-transcript-api（pip install youtube-transcript-api）"
    try:
        try:
            ts = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
        except NoTranscriptFound:
            # 自動翻譯方式：拿任一可用語言再翻成中文
            tr_list = YouTubeTranscriptApi.list_transcripts(video_id)
            for t in tr_list:
                try:
                    ts = t.translate("zh-TW").fetch()
                    break
                except Exception:
                    continue
            else:
                return None, "找不到任何可翻譯字幕"
        return "\n".join(t["text"].strip() for t in ts if t["text"].strip()), None
    except TranscriptsDisabled:
        return None, "影片作者已停用字幕"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _arxiv_search(query: str, n: int = 3) -> list[dict]:
    """官方 API（無需 key、回 atom xml）。v1.2: 加 retry。"""
    import urllib.parse, urllib.request, xml.etree.ElementTree as ET

    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{urllib.parse.quote(query)}"
        f"&start=0&max_results={n}&sortBy=relevance"
    )

    def _fetch() -> str:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8")

    xml_data, err = _retry(_fetch, attempts=3, base_delay=1.0, label="arXiv API")
    if err:
        return [{"_error": err}]

    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    out: list[dict] = []
    for entry in root.findall("a:entry", ns):
        out.append({
            "title": (entry.find("a:title", ns).text or "").strip().replace("\n", " "),
            "summary": (entry.find("a:summary", ns).text or "").strip(),
            "authors": ", ".join(
                a.find("a:name", ns).text for a in entry.findall("a:author", ns)
            ),
            "published": (entry.find("a:published", ns).text or "")[:10],
            "link": next(
                (l.attrib["href"] for l in entry.findall("a:link", ns) if l.attrib.get("type") == "text/html"),
                "",
            ),
            "pdf": next(
                (l.attrib["href"] for l in entry.findall("a:link", ns) if l.attrib.get("title") == "pdf"),
                "",
            ),
        })
    return out


def _github_search(query: str, n: int = 3) -> list[dict]:
    """GitHub repository 搜尋。v1.2: 加 retry。"""
    import requests
    headers = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    def _fetch():
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": n},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("items", [])[:n]

    items, err = _retry(_fetch, attempts=3, base_delay=1.5, label="GitHub Search")
    if err:
        return [{"_error": err}]
    return items or []


def _github_readme(full_name: str, max_chars: int = 5000) -> str | None:
    """抓 GitHub repo 的 README。v1.2: 加 retry（404 不重試，5xx/429 重試）。"""
    import requests, base64
    headers = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    def _fetch() -> str | None:
        r = requests.get(
            f"https://api.github.com/repos/{full_name}/readme",
            headers=headers, timeout=15,
        )
        if r.status_code == 404:
            return None  # 不重試
        if r.status_code in (429, 500, 502, 503, 504):
            r.raise_for_status()  # 觸發重試
        if r.status_code != 200:
            return None
        data = r.json()
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")[:max_chars]

    content, _ = _retry(_fetch, attempts=3, base_delay=1.5, label=f"GitHub README {full_name}")
    return content


# ============================================================
# TinyFish: search / fetch / agent
# ============================================================
def _tinyfish_key() -> str | None:
    return os.environ.get("TINYFISH_API_KEY") or None


def _tinyfish_search(query: str, limit: int = 10) -> list[dict]:
    import requests
    key = _tinyfish_key()
    if not key:
        return []
    try:
        r = requests.get(
            "https://api.search.tinyfish.ai",
            params={"query": query, "limit": limit},
            headers={"X-API-Key": key},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception:
        return []


def _tinyfish_fetch_batch(urls: list[str], timeout: int = 60) -> list[dict]:
    import requests
    key = _tinyfish_key()
    if not key or not urls:
        return [{} for _ in urls]
    try:
        r = requests.post(
            "https://api.fetch.tinyfish.ai",
            json={"urls": urls},
            headers={"X-API-Key": key},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return [{} for _ in urls]


def cmd_search(args: argparse.Namespace) -> int:
    import requests
    key = _tinyfish_key()
    if not key:
        print("[錯誤] 沒設 TINYFISH_API_KEY。到 https://agent.tinyfish.ai 註冊（免費），然後設環境變數。")
        return 2

    r = requests.get(
        "https://api.search.tinyfish.ai",
        params={"query": args.query, "limit": args.top},
        headers={"X-API-Key": key},
        timeout=15,
    )
    r.raise_for_status()
    hits = r.json().get("results", [])

    # --prefer-domains 過濾
    if args.prefer_domains:
        prefs = [d.strip().lower() for d in args.prefer_domains.split(",") if d.strip()]
        hits = sorted(hits, key=lambda h: 0 if any(p in h.get("url", "").lower() for p in prefs) else 1)

    payload: list[dict] = hits[: args.top]

    if args.fetch:
        urls = [h["url"] for h in payload]
        rf = requests.post(
            "https://api.fetch.tinyfish.ai",
            json={"urls": urls},
            headers={"X-API-Key": key},
            timeout=60,
        )
        rf.raise_for_status()
        docs = rf.json()
        for h, d in zip(payload, docs):
            h["markdown"] = d.get("markdown", "")
            h["fetched_at"] = _now_iso()

    if args.out and args.out.endswith(".md") and args.fetch:
        lines = [f"# {args.query}\n\n_搜尋於：{_now_iso()}_\n"]
        for h in payload:
            lines.append(f"## [{h.get('title','(untitled)')}]({h.get('url','')})")
            if h.get("snippet"):
                lines.append(f"> {h['snippet']}")
            if h.get("markdown"):
                lines.append("\n" + h["markdown"] + "\n\n---\n")
        _save("\n".join(lines), args.out, "md")
    elif args.out:
        _save(payload, args.out, "json")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    """單頁擷取：優先 TinyFish（乾淨 markdown），無 key 時 fallback Scrapling。"""
    key = _tinyfish_key()
    fmt = args.format

    if key:
        import requests
        r = requests.post(
            "https://api.fetch.tinyfish.ai",
            json={"urls": [args.url]},
            headers={"X-API-Key": key},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            print("[錯誤] TinyFish 沒回資料")
            return 3
        d = data[0]
        content = d.get("markdown", "") if fmt == "md" else d.get("html", "") if fmt == "html" else d.get("text") or d.get("markdown", "")
    else:
        if not _has("scrapling"):
            print("[錯誤] 沒 TINYFISH_API_KEY，本地也沒裝 scrapling。請選一個來源：\n"
                  "  - 設環境變數 TINYFISH_API_KEY（雲端、免費）\n"
                  "  - 或 pip install \"scrapling[all]\" && scrapling install")
            return 2
        from scrapling.fetchers import Fetcher
        page = Fetcher.get(args.url, impersonate="chrome", timeout=30)
        content = page.body if fmt != "text" else page.get_all_text()

    if args.out:
        _save(content, args.out, fmt)
    else:
        print(content)
    return 0


def cmd_agent(args: argparse.Namespace) -> int:
    import requests
    key = _tinyfish_key()
    if not key:
        print("[錯誤] agent 子命令需要 TINYFISH_API_KEY（自然語言爬蟲走雲端）")
        return 2

    r = requests.post(
        "https://agent.tinyfish.ai/v1/automation/run",
        json={"url": args.url, "goal": args.goal},
        headers={"X-API-Key": key},
        timeout=args.timeout,
    )
    r.raise_for_status()
    payload = r.json()
    data = payload.get("data", payload)

    if args.out:
        _save(data, args.out, "json")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


# ============================================================
# Scrapling: stealthy / dynamic / crawl
# ============================================================
def _need_scrapling() -> bool:
    if not _has("scrapling"):
        print("[錯誤] 此命令需要 scrapling。請執行：")
        print('  pip install "scrapling[all]" && scrapling install')
        return False
    return True


def cmd_stealthy(args: argparse.Namespace) -> int:
    if not _need_scrapling():
        return 2
    from scrapling.fetchers import StealthyFetcher

    # 被擋有兩種樣貌：(a) 回傳挑戰頁；(b) goto 直接丟例外。兩者都要能觸發接手。
    page = None
    err: Exception | None = None
    try:
        page = StealthyFetcher.fetch(
            args.url,
            headless=not args.no_headless,
            solve_cloudflare=True,
            block_ads=True,
            google_search_referer=True,
            proxy=args.proxy,
            timeout=args.timeout * 1000,
        )
    except Exception as e:  # noqa: BLE001 — 反爬失敗態，交給下方判斷是否接手
        err = e

    # ---- 雙引擎自動切換：Firefox 系被擋 → Chromium 系（CloakBrowser）接手 ----
    status = getattr(page, "status", None)
    blocked = err is not None or _looks_blocked(status, getattr(page, "body", b""))
    if not args.no_fallback and blocked:
        if _has("cloakbrowser"):
            reason = f"例外 {type(err).__name__}" if err else f"status={status}"
            print(f"[自動切換] StealthyFetcher 疑似被擋（{reason}）"
                  f"→ 改用 CloakBrowser（Chromium 系）接手…", file=sys.stderr)
            proxies = _proxy_list(args.proxy, args.proxy_file)
            content, rc = _cloak_rotate(
                args.url, proxies, css=args.css, text=False,
                geoip=args.geoip, humanize=True, settle=args.fallback_settle,
                headless=not args.no_headless, timeout=args.timeout,
                solve_captcha=args.solve_captcha, captcha_provider=args.captcha_provider,
            )
            if rc != 0:
                return rc
            if args.out:
                _save(content, args.out)
            else:
                print(content if isinstance(content, str)
                      else json.dumps(content, ensure_ascii=False, indent=2))
            return 0
        print("[提示] 頁面疑似被擋，但未安裝 cloakbrowser，無法自動接手。"
              "請 `pip install cloakbrowser`，或加 --no-fallback 關閉此檢查。", file=sys.stderr)

    if err is not None:  # 沒接手成功又有原始例外 → 照實拋出，別吞錯
        raise err

    if args.css:
        # 抽出指定區段
        nodes = page.css(args.css)
        result = [str(n) for n in nodes] if isinstance(nodes, list) else [str(nodes)]
        content = "\n\n".join(result) if result else page.body
    else:
        content = page.body

    if args.out:
        _save(content, args.out)
    else:
        print(content)
    return 0


def cmd_dynamic(args: argparse.Namespace) -> int:
    if not _need_scrapling():
        return 2
    from scrapling.fetchers import DynamicFetcher

    page = DynamicFetcher.fetch(
        args.url,
        network_idle=True,
        wait_selector=args.wait or None,
        timeout=args.timeout * 1000,
    )
    if args.css:
        items = page.css(args.css + "::text").getall() or [str(n) for n in page.css(args.css)]
        result: Any = items
    else:
        result = page.body

    if args.out:
        _save(result, args.out)
    else:
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# ============================================================
# CloakBrowser: 原始碼級指紋修補的隱形 Chromium（drop-in Playwright）
# ============================================================
def _need_cloak() -> bool:
    if not _has("cloakbrowser"):
        print("[錯誤] 此命令需要 cloakbrowser。請執行：")
        print("  pip install cloakbrowser")
        print("（首次執行會自動下載隱形 Chromium binary，約 200MB；Windows x64 用免費 v146）")
        return False
    return True


# 被擋訊號：full HTML 出現這些字樣，多半是 challenge / 拒絕頁。
_BLOCK_MARKERS = (
    "just a moment", "checking your browser", "cf-challenge", "/cdn-cgi/challenge",
    "attention required", "access denied", "verify you are human",
    "enable javascript and cookies", "正在執行安全驗證", "請完成驗證",
)


def _looks_blocked(status: int | None, html: str | bytes) -> bool:
    """判斷 stealthy 抓回來的頁面是不是被擋（給雙引擎自動切換用）。"""
    if status is not None and status >= 400:
        return True
    if isinstance(html, bytes):  # scrapling page.body 回傳 bytes
        html = html.decode("utf-8", "ignore")
    low = (html or "").lower()
    if len(low.strip()) < 200:  # full HTML 卻短到不合理 → 多半是 challenge stub
        return True
    return any(m in low for m in _BLOCK_MARKERS)


# 偵測頁面上的 CAPTCHA widget（回傳 {type, sitekey} 或 None）
_CAPTCHA_DETECT_JS = r"""
() => {
  const q = (s) => document.querySelector(s);
  let el;
  if ((el = q('.cf-turnstile[data-sitekey], [class*="turnstile"][data-sitekey]')))
    return {type:'turnstile', sitekey: el.getAttribute('data-sitekey')};
  if ((el = q('.h-captcha[data-sitekey], [data-hcaptcha-sitekey]')))
    return {type:'hcaptcha', sitekey: el.getAttribute('data-sitekey') || el.getAttribute('data-hcaptcha-sitekey')};
  if ((el = q('.g-recaptcha[data-sitekey]')))
    return {type:'recaptcha2', sitekey: el.getAttribute('data-sitekey')};
  const if_ = q('iframe[src*="recaptcha"][src*="k="]');
  if (if_) { const m = if_.src.match(/[?&]k=([^&]+)/); if (m) return {type:'recaptcha2', sitekey: m[1]}; }
  if ((el = q('[data-sitekey]'))) return {type:'turnstile', sitekey: el.getAttribute('data-sitekey')};
  return null;
}
"""

# 把 token 注入各種常見的 response 欄位
_CAPTCHA_INJECT_JS = r"""
(token) => {
  const set = (sel) => document.querySelectorAll(sel).forEach(t => {
    t.value = token;
    t.dispatchEvent(new Event('input', {bubbles:true}));
    t.dispatchEvent(new Event('change', {bubbles:true}));
  });
  set('textarea[name="g-recaptcha-response"]');
  set('textarea#g-recaptcha-response');
  set('input[name="cf-turnstile-response"]');
  set('input[name="h-captcha-response"]');
  set('textarea[name="h-captcha-response"]');
  document.querySelectorAll('#g-recaptcha-response').forEach(t => t.style.display = 'block');
  return true;
}
"""


def _solve_captcha_on_page(page, url: str, ctype: str, provider: str,
                           proxy: str | None, timeout: int) -> dict | None:
    """偵測 → 解碼 → 注入 token。回傳結果摘要或 None（沒偵測到）。"""
    import captcha_solver  # 同目錄模組

    info = page.evaluate(_CAPTCHA_DETECT_JS)
    if not info or not info.get("sitekey"):
        print("[CAPTCHA] 頁面上沒偵測到已知的 widget（Turnstile/reCAPTCHA/hCaptcha）", file=sys.stderr)
        return None
    detected = info["type"] if ctype in ("auto", "", None) else ctype
    sitekey = info["sitekey"]
    print(f"[CAPTCHA] 偵測到 {detected}（sitekey={sitekey[:12]}…）→ 送解碼服務…", file=sys.stderr)
    token = captcha_solver.solve(detected, sitekey, url, provider=provider,
                                 proxy=proxy, timeout=timeout)
    page.evaluate(_CAPTCHA_INJECT_JS, token)
    print(f"[CAPTCHA] 已取得並注入 token（長度 {len(token)}）", file=sys.stderr)
    return {"type": detected, "sitekey": sitekey, "token_len": len(token)}


def _cloak_fetch(
    url: str, *, css: str | None = None, text: bool = False,
    wait: str | None = None, wait_until: str = "domcontentloaded", settle: float = 0,
    proxy: str | None = None, geoip: bool = False, humanize: bool = False,
    fingerprint: str | None = None, profile: str | None = None,
    headless: bool = True, screenshot: str | None = None, timeout: int = 60,
    solve_captcha: bool = False, captcha_provider: str = "auto",
    captcha_type: str = "auto", submit: bool = False,
) -> Any:
    """CloakBrowser 抓取核心：cmd_cloak 與 stealthy 自動接手共用。

    回傳：css → list[str]（innerHTML 或 innerText）；無 css → 整頁 HTML(str)。
    """
    from cloakbrowser import launch, launch_persistent_context

    kwargs: dict[str, Any] = dict(headless=headless)
    if humanize:
        kwargs["humanize"] = True
    if proxy:
        kwargs["proxy"] = proxy
    if geoip:
        kwargs["geoip"] = True
    if fingerprint:
        kwargs["args"] = [f"--fingerprint={fingerprint}"]

    ctx = browser = None
    try:
        if profile:
            ctx = launch_persistent_context(profile, **kwargs)
            page = ctx.new_page()
        else:
            browser = launch(**kwargs)
            page = browser.new_page()

        # 反爬/挑戰頁常持續發 beacon，networkidle 會永遠等不到 → 預設 domcontentloaded。
        page.goto(url, timeout=timeout * 1000, wait_until=wait_until)
        if wait:
            page.wait_for_selector(wait, timeout=timeout * 1000)
        if settle:
            page.wait_for_timeout(int(settle * 1000))  # 給挑戰頁時間自動解開

        if solve_captcha:
            solved = _solve_captcha_on_page(page, url, captcha_type,
                                            captcha_provider, proxy, timeout)
            if solved:
                if submit:
                    action = page.evaluate(
                        "() => { const b=document.querySelector('button[type=submit],input[type=submit]');"
                        " if(b){b.click();return 'clicked';}"
                        " const f=document.forms[0]; if(f){f.submit();return 'form';} return 'none'; }")
                    print(f"[CAPTCHA] 送出表單：{action}", file=sys.stderr)
                page.wait_for_timeout(2500)  # 等注入/送出後頁面更新

        if screenshot:
            Path(screenshot).parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=screenshot, full_page=True)
            print(f"OK（截圖）→ {Path(screenshot).resolve()}")

        if css:
            els = page.query_selector_all(css)
            return [(e.inner_text() if text else e.inner_html()) for e in els]
        return page.content()
    finally:
        if ctx is not None:
            ctx.close()
        if browser is not None:
            browser.close()


def _read_proxy_file(path: str) -> list[str]:
    """讀 proxy 清單檔：一行一個，# 開頭與空行略過。"""
    out: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def _proxy_list(proxy: str | None, proxy_file: str | None) -> list[str | None]:
    """決定要輪換的 proxy 清單。有清單檔優先；否則單一 --proxy（可能 None=直連）。"""
    if proxy_file:
        lst = _read_proxy_file(proxy_file)
        if lst:
            return list(lst)
    return [proxy]


def _cloak_rotate(url: str, proxies: list[str | None], **fkw: Any) -> tuple[Any, int]:
    """對 proxy 清單逐一嘗試 CloakBrowser，回傳 (content, rc)。

    rc：0=取得內容（可能仍疑似被擋，已印升級建議）；3=CAPTCHA 金鑰錯；
        4=所有 proxy 都拋例外（→ 建議委派 browser-act）。
    這同時實作「proxy 池自動輪換」(item 2) 與「三段式升級信號」(item 3)。
    """
    from captcha_solver import CaptchaError

    content: Any = None
    last_err: Exception | None = None
    n = len(proxies)
    for i, px in enumerate(proxies):
        label = px or "(直連)"
        try:
            c = _cloak_fetch(url, proxy=px, **fkw)
        except CaptchaError as e:
            print(f"[CAPTCHA 錯誤] {e}", file=sys.stderr)
            return None, 3
        except Exception as e:  # noqa: BLE001 — 連線/逾時等，換下一個 proxy
            last_err = e
            if n > 1:
                print(f"[proxy 輪換 {i + 1}/{n}] {label} 例外 {type(e).__name__} → 換下一個", file=sys.stderr)
            continue

        content = c
        blocked = isinstance(c, str) and _looks_blocked(None, c)
        if not blocked:
            if n > 1:
                print(f"[proxy 輪換 {i + 1}/{n}] {label} 成功", file=sys.stderr)
            return content, 0
        if n > 1 and i < n - 1:
            print(f"[proxy 輪換 {i + 1}/{n}] {label} 仍被擋 → 換下一個", file=sys.stderr)

    if content is None:  # 全數例外
        print(f"[升級建議] cloak 試完 {n} 個 proxy 都連不上 → 建議改用 browser-act 技能"
              f"（多步互動／登入牆／真人接手）。最後錯誤：{last_err}", file=sys.stderr)
        return None, 4

    # 有拿到內容但仍疑似被擋
    print("[升級建議] cloak 仍疑似被擋 → 可改用 browser-act 技能；"
          "若卡互動式驗證碼，可加 --solve-captcha（需自備金鑰）", file=sys.stderr)
    return content, 0


def cmd_cloak(args: argparse.Namespace) -> int:
    """用 CloakBrowser 抓頁面：原始碼級（C++）指紋修補的隱形 Chromium。

    定位（三段式升級鏈）：stealthy（Firefox 系）→ cloak（Chromium 系，本命令）
      →（用盡 proxy 仍失敗）委派 browser-act（登入牆／多步互動／真人接手）。
    互動式 Turnstile/CAPTCHA 指紋偽裝不自動解，需 --solve-captcha 或 browser-act。
    支援 --proxy-file 做住宅 proxy 池輪換（被擋自動換下一個）。
    """
    if not _need_cloak():
        return 2

    proxies = _proxy_list(args.proxy, args.proxy_file)
    content, rc = _cloak_rotate(
        args.url, proxies,
        css=args.css, text=args.text, wait=args.wait, wait_until=args.wait_until,
        settle=args.settle, geoip=args.geoip, humanize=args.humanize,
        fingerprint=args.fingerprint, profile=args.profile, headless=not args.no_headless,
        screenshot=args.screenshot, timeout=args.timeout, solve_captcha=args.solve_captcha,
        captcha_provider=args.captcha_provider, captcha_type=args.captcha_type, submit=args.submit,
    )
    if rc != 0:
        return rc

    if args.out:
        _save(content, args.out)
    elif not (args.screenshot and not args.css):
        print(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2))
    return 0


def cmd_crawl(args: argparse.Namespace) -> int:
    if not _need_scrapling():
        return 2
    from scrapling.spiders import Spider, Response

    selector = args.selector
    next_sel = args.next
    max_pages = args.max_pages
    out = args.out or "crawl_output.jsonl"

    class CLISpider(Spider):
        name = "cli_crawl"
        start_urls = [args.url]
        concurrent_requests = args.concurrency
        download_delay = args.delay
        respect_robots_txt = not args.ignore_robots
        page_count = 0

        async def parse(self, response: Response):
            type(self).page_count += 1
            for el in response.css(selector):
                yield {"_url": response.url, "_text": el.get_all_text(), "_html": str(el)}
            if next_sel and type(self).page_count < max_pages:
                nxt = response.css(f"{next_sel}::attr(href)").get()
                if nxt:
                    yield response.follow(nxt)

    crawldir = "./.crawl" if args.resume else None
    result = CLISpider(crawldir=crawldir).start()
    result.items.to_jsonl(out)
    print(f"OK → {out}（共 {len(result.items)} 筆，{CLISpider.page_count} 頁）")
    return 0


# ============================================================
# news：科技 / 教育新聞預設來源
# ============================================================
NEWS_SOURCES: dict[str, list[dict]] = {
    "tech": [
        # 中文
        {"name": "iThome 新聞",    "url": "https://www.ithome.com.tw/news",            "lang": "zh-tw"},
        {"name": "數位時代",       "url": "https://www.bnext.com.tw/categories/tech",  "lang": "zh-tw"},
        {"name": "INSIDE",         "url": "https://www.inside.com.tw/category/ai",     "lang": "zh-tw"},
        {"name": "T客邦",          "url": "https://www.techbang.com",                  "lang": "zh-tw"},
        # 英文
        {"name": "TechCrunch",     "url": "https://techcrunch.com",                    "lang": "en"},
        {"name": "The Verge",      "url": "https://www.theverge.com/tech",             "lang": "en"},
        {"name": "Ars Technica",   "url": "https://arstechnica.com",                   "lang": "en"},
        {"name": "Hacker News",    "url": "https://news.ycombinator.com",              "lang": "en"},
        {"name": "MIT Tech Review","url": "https://www.technologyreview.com",          "lang": "en"},
    ],
    "edu": [
        # 中文
        {"name": "教育部即時新聞",  "url": "https://www.edu.tw/News.aspx?n=9E7AC85F1954DDA8&sms=169B8E91BB75571F", "lang": "zh-tw"},
        {"name": "親子天下",       "url": "https://www.parenting.com.tw/topic/edu",    "lang": "zh-tw"},
        {"name": "翻轉教育",       "url": "https://flipedu.parenting.com.tw",          "lang": "zh-tw"},
        {"name": "未來 Family",     "url": "https://gfamily.cwgv.com.tw",               "lang": "zh-tw"},
        {"name": "聯合新聞網-教育", "url": "https://udn.com/news/cate/2/6898",          "lang": "zh-tw"},
        # 英文
        {"name": "EdSurge",        "url": "https://www.edsurge.com/news",              "lang": "en"},
        {"name": "Edutopia",       "url": "https://www.edutopia.org",                  "lang": "en"},
        {"name": "EdWeek",         "url": "https://www.edweek.org",                    "lang": "en"},
        {"name": "Inside Higher Ed","url": "https://www.insidehighered.com",            "lang": "en"},
    ],
}


def cmd_news(args: argparse.Namespace) -> int:
    """抓預設的科技 / 教育新聞首頁，整理為 markdown。"""
    topics: list[str] = []
    if args.topic == "both":
        topics = ["tech", "edu"]
    else:
        topics = [args.topic]

    sources = []
    for t in topics:
        sources += NEWS_SOURCES[t]

    if args.lang and args.lang != "all":
        sources = [s for s in sources if s["lang"] == args.lang]

    sources = sources[: args.max_sources]

    print(f"=== 抓取 {len(sources)} 個來源 ===")

    key = _tinyfish_key()
    out_lines: list[str] = []
    out_lines.append(f"# {'/'.join(topics).upper()} 新聞速報")
    out_lines.append(f"\n_生成時間：{_now_iso()}_\n")

    docs: list[dict] = []
    if key:
        # 優先用 TinyFish Fetch（最乾淨）
        import requests
        urls = [s["url"] for s in sources]
        try:
            r = requests.post(
                "https://api.fetch.tinyfish.ai",
                json={"urls": urls},
                headers={"X-API-Key": key},
                timeout=120,
            )
            r.raise_for_status()
            docs = r.json()
        except Exception as e:
            print(f"[警告] TinyFish 失敗，改 fallback 本地：{e}")
            docs = []

    if not docs:
        # Fallback: scrapling 本地抓
        if not _has("scrapling"):
            print("[錯誤] TinyFish 不可用且本地沒裝 scrapling，無法繼續。")
            return 2
        from scrapling.fetchers import Fetcher
        for s in sources:
            try:
                page = Fetcher.get(s["url"], impersonate="chrome", timeout=20)
                docs.append({"markdown": page.get_all_text()[:4000], "title": s["name"]})
            except Exception as e:
                docs.append({"markdown": f"_(抓取失敗：{e})_", "title": s["name"]})

    for src, doc in zip(sources, docs):
        out_lines.append(f"\n## [{src['name']}]({src['url']}) `{src['lang']}`\n")
        md = (doc.get("markdown") or "").strip()
        # 截斷避免一份檔案過長
        snippet = md[: args.per_source_chars] if md else "_(無內容)_"
        out_lines.append(snippet)
        out_lines.append("\n---")

    out_path = args.out or f"news-{topics[0] if len(topics)==1 else 'tech-edu'}-{_dt.date.today().isoformat()}.md"
    _save("\n".join(out_lines), out_path, "md")

    if args.pdf:
        pdf_path = out_path.rsplit(".", 1)[0] + ".pdf"
        _md_to_pdf(out_path, pdf_path)
    return 0


# ============================================================
# learn：給定主題 → 抓 YT 字幕 + 教學文章 + GitHub + arXiv → 一份長 Markdown
# v1.2 重構：cmd_learn 變 orchestrator，每段抽成 _learn_*_section helper
# ============================================================

def _learn_youtube_section(args: argparse.Namespace) -> tuple[list[str], dict]:
    """回傳 (markdown 片段 list, 統計 dict)。"""
    md: list[str] = ["\n## 🎬 YouTube 教學影片\n"]
    stats = {"requested": args.videos, "found": 0, "transcripts_ok": 0, "failures": []}

    if not _tinyfish_key():
        md.append("_(沒設 TINYFISH_API_KEY，無法搜尋 YouTube)_\n")
        stats["failures"].append("no_tinyfish_key")
        return md, stats

    print("🎬 [1/4] 搜尋 YouTube 教學...")
    results = _tinyfish_search(f"site:youtube.com {args.topic} 教學", limit=15)
    if len(results) < args.videos * 2:
        results += _tinyfish_search(f"site:youtube.com {args.topic} tutorial", limit=10)

    seen: set[str] = set()
    videos: list[dict] = []
    for r in results:
        url = r.get("url", "")
        vid = _yt_video_id(url)
        if not vid or vid in seen:
            continue
        if "youtube.com/watch" not in url and "youtu.be/" not in url:
            continue
        seen.add(vid)
        r["_vid"] = vid
        videos.append(r)
        if len(videos) >= args.videos:
            break

    stats["found"] = len(videos)
    if not videos:
        md.append("_(沒找到合適的 YouTube 影片)_\n")
        return md, stats

    use_skill = getattr(args, "whisper_fallback", False) and _yt_subtitle_skill_path() is not None

    for i, v in enumerate(videos, 1):
        print(f"   {i}/{len(videos)} 抓字幕：{v['_vid']}")
        transcript, err = _yt_transcript(v["_vid"])

        # v1.2: 主路徑失敗 + 啟用 whisper-fallback → 委派給 youtube-subtitle SKILL
        if not transcript and use_skill:
            print(f"      ↳ 主流程失敗（{err}），改用 youtube-subtitle SKILL（含 Whisper）...")
            transcript, err2 = _yt_via_skill(v["url"], timeout=180)
            if transcript:
                err = None
            else:
                err = f"主流程：{err}；yt-skill：{err2}"

        md.append(f"\n### {i}. [{v.get('title','(無標題)')}]({v['url']})\n")
        if v.get("snippet"):
            md.append(f"> {v['snippet']}\n")
        if transcript:
            md.append("\n<details><summary>📜 完整字幕（點擊展開）</summary>\n")
            md.append(f"\n```\n{transcript}\n```\n")
            md.append("\n</details>\n")
            stats["transcripts_ok"] += 1
        else:
            md.append(f"_(字幕取得失敗：{err})_\n")
            stats["failures"].append(f"{v['_vid']}: {err}")
        md.append("\n---\n")

    return md, stats


def _learn_articles_section(args: argparse.Namespace) -> tuple[list[str], dict]:
    md: list[str] = ["\n## 📰 網路教學文章\n"]
    stats = {"requested": args.articles, "found": 0, "fetched": 0, "failures": []}

    if not _tinyfish_key():
        md.append("_(沒設 TINYFISH_API_KEY，無法搜尋文章)_\n")
        stats["failures"].append("no_tinyfish_key")
        return md, stats

    print("📰 [2/4] 搜尋教學文章...")
    raw = _tinyfish_search(f"{args.topic} 教學 OR 入門 OR 教程 OR tutorial", limit=20)
    filtered = [
        a for a in raw
        if "youtube.com" not in a.get("url", "") and "youtu.be" not in a.get("url", "")
    ]
    zh_pref = [".tw", "ithome.com", "ithelp.ithome", "csdn.net", "juejin", "jianshu", "medium.com/@", "wikipedia.org"]
    filtered.sort(key=lambda a: 0 if any(z in a.get("url", "").lower() for z in zh_pref) else 1)
    articles = filtered[: args.articles]
    stats["found"] = len(articles)

    if not articles:
        md.append("_(沒找到合適的文章)_\n")
        return md, stats

    urls = [a["url"] for a in articles]
    print(f"   批次抓取 {len(urls)} 篇全文...")
    docs = _tinyfish_fetch_batch(urls, timeout=120)
    for i, (a, d) in enumerate(zip(articles, docs), 1):
        md.append(f"\n### {i}. [{a.get('title','(無標題)')}]({a['url']})\n")
        if a.get("snippet"):
            md.append(f"> {a['snippet']}\n")
        body = (d.get("markdown") or "").strip()
        if not body:
            md.append("\n_(全文抓取失敗)_\n")
            stats["failures"].append(f"fetch failed: {a['url']}")
        else:
            stats["fetched"] += 1
            if len(body) > args.article_chars:
                body = body[: args.article_chars] + "\n\n_...（內容截斷，原文請看連結）_"
            md.append(f"\n{body}\n")
        md.append("\n---\n")
    return md, stats


def _learn_github_section(args: argparse.Namespace) -> tuple[list[str], dict]:
    md: list[str] = ["\n## 🐙 GitHub 相關專案\n"]
    stats = {"requested": args.github, "found": 0, "readmes": 0, "failures": []}

    print("🐙 [3/4] 搜尋 GitHub repo...")
    repos = _github_search(args.topic, n=args.github)
    if repos and "_error" in repos[0]:
        md.append(f"_(GitHub API 失敗：{repos[0]['_error']})_\n")
        stats["failures"].append(repos[0]["_error"])
        return md, stats
    if not repos:
        md.append("_(沒找到合適的 repo)_\n")
        return md, stats

    stats["found"] = len(repos)
    for i, r in enumerate(repos, 1):
        full = r.get("full_name", "")
        md.append(
            f"\n### {i}. [{full}]({r.get('html_url','')}) "
            f"⭐{r.get('stargazers_count', 0):,} ｜ {r.get('language') or '—'}\n"
        )
        if r.get("description"):
            md.append(f"> {r['description']}\n")
        readme = _github_readme(full, max_chars=args.github_readme_chars)
        if readme:
            md.append("\n<details><summary>📄 README（點擊展開）</summary>\n\n")
            md.append(readme)
            md.append("\n\n</details>\n")
            stats["readmes"] += 1
        md.append("\n---\n")
    return md, stats


def _learn_arxiv_section(args: argparse.Namespace) -> tuple[list[str], dict]:
    md: list[str] = ["\n## 📑 arXiv 相關論文\n"]
    stats = {"requested": args.arxiv, "found": 0, "failures": []}

    print("📑 [4/4] 搜尋 arXiv 論文...")
    papers = _arxiv_search(args.topic, n=args.arxiv)
    if papers and "_error" in papers[0]:
        md.append(f"_(arXiv API 失敗：{papers[0]['_error']})_\n")
        stats["failures"].append(papers[0]["_error"])
        return md, stats
    if not papers:
        md.append("_(沒找到合適的論文)_\n")
        return md, stats

    stats["found"] = len(papers)
    for i, p in enumerate(papers, 1):
        md.append(f"\n### {i}. [{p['title']}]({p['link']})\n")
        md.append(f"_作者：{p['authors']} ｜ 發表：{p['published']}_ ")
        if p.get("pdf"):
            md.append(f"｜ [PDF]({p['pdf']})\n")
        md.append(f"\n> {p['summary']}\n")
        md.append("\n---\n")
    return md, stats


# orchestrator: 路由 → section helpers → 寫檔 → 失敗摘要
SECTION_DISPATCH: dict[str, tuple[str, callable]] = {
    "yt":      ("YouTube",  _learn_youtube_section),
    "article": ("文章",     _learn_articles_section),
    "github":  ("GitHub",   _learn_github_section),
    "arxiv":   ("arXiv",    _learn_arxiv_section),
}


def cmd_learn(args: argparse.Namespace) -> int:
    """主題式學習包 orchestrator。中文優先，缺源時 fallback 英文。"""
    topic = args.topic
    include = [k for k in args.include.split(",") if k.strip()]
    out_path = args.out or f"learn-{_re.sub(r'[^A-Za-z0-9一-龥_-]+', '_', topic).strip('_')}.md"

    print(f"📚 主題：{topic}")
    print(f"   來源：{', '.join(include)}")

    # ---- 快取 ----
    cache_hit, age = _learn_cache_lookup(args)
    if cache_hit is not None:
        print(f"📦 命中快取（{age/3600:.1f}h 前生成）→ 從 {cache_hit} 直接讀取\n")
        cached = cache_hit.read_text(encoding="utf-8")
        _save(cached, out_path, "md")
        if args.pdf:
            _md_to_pdf(out_path, str(Path(out_path).with_suffix(".pdf")))
        return 0
    print("🔁 強制重抓...\n" if args.no_cache else "📭 沒命中有效快取，開始抓取...\n")

    # ---- 撰寫表頭 ----
    out: list[str] = [
        f"# 📚 {topic} ── 學習包\n",
        f"_生成時間：{_now_iso()}_\n",
        "> 包含：YouTube 教學字幕、網路教學文章、GitHub 專案、arXiv 論文。中文優先。\n",
        "\n---\n",
    ]

    # ---- 各 section ----
    all_stats: dict[str, dict] = {}
    for key in include:
        if key not in SECTION_DISPATCH:
            print(f"⚠️  未知來源：{key}，跳過")
            continue
        label, fn = SECTION_DISPATCH[key]
        block, stats = fn(args)
        out.extend(block)
        all_stats[label] = stats

    # ---- 失敗摘要（v1.2 新增）----
    failures = sum(len(s.get("failures", [])) for s in all_stats.values())
    if failures:
        out.append("\n## ⚠️ 抓取摘要（含失敗項目）\n")
        for label, s in all_stats.items():
            out.append(f"\n- **{label}**：")
            line_parts = []
            if "requested" in s and "found" in s:
                line_parts.append(f"請求 {s['requested']}、找到 {s['found']}")
            if "transcripts_ok" in s:
                line_parts.append(f"字幕 OK {s['transcripts_ok']}")
            if "fetched" in s:
                line_parts.append(f"全文 OK {s['fetched']}")
            if "readmes" in s:
                line_parts.append(f"README OK {s['readmes']}")
            if s.get("failures"):
                line_parts.append(f"失敗 {len(s['failures'])}")
            out.append("、".join(line_parts))
            for f in s.get("failures", [])[:5]:
                out.append(f"\n  - {f}")
        out.append("\n")

    out.append(f"\n_本學習包由 web-scraper SKILL 自動產生於 {_now_iso()}。請尊重來源版權，僅供個人學習與教學備課使用。_\n")
    final_md = "\n".join(out)

    _save(final_md, out_path, "md")
    cache_path = _learn_cache_write(args, final_md)
    print(f"💾 已寫入快取：{cache_path}")

    # console 摘要
    print("\n📊 抓取摘要：")
    for label, s in all_stats.items():
        ok = s.get("transcripts_ok", s.get("fetched", s.get("readmes", s.get("found", 0))))
        req = s.get("requested", 0)
        print(f"   {label}: {ok}/{req}" + (f" ｜ 失敗 {len(s['failures'])} 項" if s.get("failures") else ""))

    if args.pdf:
        _md_to_pdf(out_path, str(Path(out_path).with_suffix(".pdf")))
    return 0


# ============================================================
# to-pdf
# ============================================================
def _md_to_pdf(md_path: str, pdf_path: str) -> None:
    """Markdown → PDF。優先用 Playwright（Chromium 通常已隨 Scrapling 裝好），
    Windows 缺 GTK 時 weasyprint 會失敗，自動 fallback。"""
    try:
        import markdown as _md  # type: ignore
        html_body = _md.markdown(
            Path(md_path).read_text(encoding="utf-8"),
            extensions=["extra", "toc", "fenced_code", "tables"],
        )
    except ImportError:
        # 沒裝 markdown 套件就 raw 處理
        raw = Path(md_path).read_text(encoding="utf-8")
        html_body = "<pre>" + raw.replace("<", "&lt;").replace(">", "&gt;") + "</pre>"

    css = """
    @page { size: A4; margin: 1.5cm; }
    body { font-family: 'Noto Sans TC', 'Microsoft JhengHei', 'PingFang TC', sans-serif;
           line-height: 1.7; color: #222; max-width: 100%; }
    h1 { color: #1a4480; border-bottom: 2px solid #1a4480; padding-bottom: 6px; }
    h2 { color: #1a4480; border-bottom: 1px solid #ccd; padding-bottom: 4px; margin-top: 1.5em; }
    h3 { color: #224477; }
    code { background: #f5f5f7; padding: 2px 6px; border-radius: 4px; font-size: 90%; }
    pre { background: #f5f5f7; padding: 12px; border-radius: 6px; overflow-x: auto; }
    blockquote { border-left: 4px solid #1a4480; padding: 6px 14px; color: #555;
                 background: #f8f9fb; margin: 1em 0; }
    a { color: #1a4480; text-decoration: none; }
    hr { border: none; border-top: 1px solid #ccd; margin: 2em 0; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
    th, td { border: 1px solid #ccd; padding: 6px 10px; }
    th { background: #f0f4f8; }
    details { background: #f8f9fb; padding: 10px; border-radius: 6px; margin: 1em 0; }
    summary { font-weight: bold; cursor: pointer; }
    """
    html = (
        f"<!doctype html><html lang='zh-TW'><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body>{html_body}</body></html>"
    )

    # 1) 優先用 Playwright（含 Chromium，無系統依賴）
    if _has("playwright"):
        try:
            import asyncio
            from playwright.async_api import async_playwright  # type: ignore

            async def render():
                async with async_playwright() as p:
                    browser = await p.chromium.launch()
                    page = await browser.new_page()
                    await page.set_content(html, wait_until="domcontentloaded")
                    await page.pdf(
                        path=pdf_path,
                        format="A4",
                        margin={"top": "1.5cm", "right": "1.5cm", "bottom": "1.5cm", "left": "1.5cm"},
                        print_background=True,
                    )
                    await browser.close()

            asyncio.run(render())
            print(f"OK → {pdf_path}（Playwright）")
            return
        except Exception as e:
            print(f"[警告] Playwright PDF 失敗，改試 weasyprint：{e}")

    # 2) Fallback: weasyprint
    if _has("weasyprint"):
        try:
            from weasyprint import HTML  # type: ignore
            HTML(string=html).write_pdf(pdf_path)
            print(f"OK → {pdf_path}（weasyprint）")
            return
        except Exception as e:
            print(f"[錯誤] weasyprint 也失敗：{e}")

    # 3) 都不行
    print("[錯誤] 沒可用的 PDF 引擎。建議：")
    print("  pip install playwright && playwright install chromium")
    print("  或 (Linux/Mac) pip install weasyprint")


def cmd_to_pdf(args: argparse.Namespace) -> int:
    src = args.input
    if src.startswith("http"):
        # 先 fetch 成 md，再轉 pdf
        tmp = Path(args.out).with_suffix(".tmp.md")
        ns = argparse.Namespace(url=src, format="md", out=str(tmp))
        cmd_fetch(ns)
        _md_to_pdf(str(tmp), args.out)
        tmp.unlink(missing_ok=True)
    elif Path(src).is_dir():
        # 合併資料夾下所有 md
        merged = Path(args.out).with_suffix(".tmp.md")
        with merged.open("w", encoding="utf-8") as f:
            for md in sorted(Path(src).glob("*.md")):
                f.write(md.read_text(encoding="utf-8") + "\n\n---\n\n")
        _md_to_pdf(str(merged), args.out)
        merged.unlink(missing_ok=True)
    else:
        _md_to_pdf(src, args.out)
    return 0


# ============================================================
# main / argparse
# ============================================================
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scrape", description="web-scraper 統一 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("doctor", help="檢查環境")
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("search", help="TinyFish 搜尋")
    sp.add_argument("query")
    sp.add_argument("--top", type=int, default=10)
    sp.add_argument("--fetch", action="store_true", help="同時抓每筆全文")
    sp.add_argument("--prefer-domains", default="", help="逗號分隔的優先網域")
    sp.add_argument("--out", help="輸出檔（.md / .json）")
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("fetch", help="抓單頁")
    sp.add_argument("url")
    sp.add_argument("--format", choices=["md", "html", "text"], default="md")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_fetch)

    sp = sub.add_parser("stealthy", help="繞反爬蟲（Scrapling，Firefox 系；被擋自動切 CloakBrowser）")
    sp.add_argument("url")
    sp.add_argument("--css", help="只抓符合 CSS 的元素")
    sp.add_argument("--no-headless", action="store_true", help="顯示瀏覽器（除錯用）")
    sp.add_argument("--proxy", help="http://user:pass@host:port")
    sp.add_argument("--proxy-file", help="proxy 池清單檔（一行一個）；接手時被擋自動換下一個")
    sp.add_argument("--geoip", action="store_true", help="接手 CloakBrowser 時依 proxy IP 對齊時區/語系")
    sp.add_argument("--no-fallback", action="store_true",
                    help="被擋時不自動切換到 CloakBrowser（預設會自動接手）")
    sp.add_argument("--fallback-settle", type=float, default=8,
                    help="接手後等幾秒讓挑戰頁自解（預設 8）")
    sp.add_argument("--solve-captcha", action="store_true",
                    help="接手 CloakBrowser 時，偵測到 CAPTCHA 送解碼服務（需自備 API key）")
    sp.add_argument("--captcha-provider", choices=["auto", "nopecha", "2captcha"], default="auto",
                    help="解碼供應商（auto=看環境變數）")
    sp.add_argument("--timeout", type=int, default=60)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_stealthy)

    sp = sub.add_parser("dynamic", help="JS 渲染（Scrapling DynamicFetcher）")
    sp.add_argument("url")
    sp.add_argument("--css")
    sp.add_argument("--wait", help="等指定 selector 出現")
    sp.add_argument("--timeout", type=int, default=30)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_dynamic)

    sp = sub.add_parser("cloak", help="隱形 Chromium（CloakBrowser，原始碼級指紋修補，drop-in Playwright）")
    sp.add_argument("url")
    sp.add_argument("--css", help="只抓符合 CSS 的元素（預設回傳 innerHTML）")
    sp.add_argument("--text", action="store_true", help="搭配 --css：回傳純文字而非 HTML")
    sp.add_argument("--wait", help="等指定 selector 出現再抓")
    sp.add_argument("--wait-until", choices=["domcontentloaded", "load", "networkidle", "commit"],
                    default="domcontentloaded", help="goto 等待條件（反爬頁勿用 networkidle）")
    sp.add_argument("--settle", type=float, default=0,
                    help="載入後再等幾秒（給 Cloudflare/Turnstile 自動解開），例：6")
    sp.add_argument("--no-headless", action="store_true", help="顯示瀏覽器（除錯／手動過驗證用）")
    sp.add_argument("--proxy", help="http(s):// 或 socks5:// proxy")
    sp.add_argument("--proxy-file", help="proxy 池清單檔（一行一個）；被擋/連不上自動換下一個")
    sp.add_argument("--geoip", action="store_true", help="依 proxy 出口 IP 自動對齊時區/語系/經緯度")
    sp.add_argument("--humanize", action="store_true", help="模擬人類滑鼠/輸入軌跡")
    sp.add_argument("--fingerprint", help="固定指紋種子（同一身份可重現），例：12345")
    sp.add_argument("--profile", help="持久化 profile 目錄（cookie/session 保留，多身份隔離）")
    sp.add_argument("--screenshot", help="另存整頁截圖到此路徑（.png）")
    sp.add_argument("--solve-captcha", action="store_true",
                    help="偵測到 Turnstile/reCAPTCHA/hCaptcha 時送解碼服務（需自備 API key，預設關閉）")
    sp.add_argument("--captcha-provider", choices=["auto", "nopecha", "2captcha"], default="auto",
                    help="解碼供應商（auto=看環境變數 NOPECHA_API_KEY / TWOCAPTCHA_API_KEY）")
    sp.add_argument("--captcha-type", choices=["auto", "turnstile", "recaptcha2", "hcaptcha"],
                    default="auto", help="CAPTCHA 題型（預設自動偵測）")
    sp.add_argument("--submit", action="store_true", help="注入 token 後嘗試送出表單/點 submit")
    sp.add_argument("--timeout", type=int, default=60)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_cloak)

    sp = sub.add_parser("agent", help="自然語言爬蟲（TinyFish Agent）")
    sp.add_argument("url")
    sp.add_argument("--goal", required=True)
    sp.add_argument("--timeout", type=int, default=180)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_agent)

    sp = sub.add_parser("crawl", help="整站爬取（Scrapling Spider）")
    sp.add_argument("url")
    sp.add_argument("--selector", required=True, help="每頁要抓的項目 selector")
    sp.add_argument("--next", help="下一頁 selector")
    sp.add_argument("--max-pages", type=int, default=50)
    sp.add_argument("--concurrency", type=int, default=8)
    sp.add_argument("--delay", type=float, default=1.0)
    sp.add_argument("--ignore-robots", action="store_true")
    sp.add_argument("--resume", action="store_true", help="可暫停／續傳")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_crawl)

    sp = sub.add_parser("news", help="抓預設的科技/教育新聞")
    sp.add_argument("--topic", choices=["tech", "edu", "both"], default="both")
    sp.add_argument("--lang", choices=["zh-tw", "en", "all"], default="all")
    sp.add_argument("--max-sources", type=int, default=10)
    sp.add_argument("--per-source-chars", type=int, default=2000)
    sp.add_argument("--pdf", action="store_true", help="同時輸出 PDF")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_news)

    sp = sub.add_parser("learn", help="主題學習包：YT 字幕 + 教學文章 + GitHub + arXiv → 一份 Markdown")
    sp.add_argument("topic", help="想學什麼，例：'Python 裝飾器'、'光合作用'")
    sp.add_argument("--include", default="yt,article,github,arxiv",
                    help="要包含的來源（逗號分隔）：yt,article,github,arxiv（預設全部）")
    sp.add_argument("--videos", type=int, default=3, help="YouTube 影片數")
    sp.add_argument("--articles", type=int, default=5, help="教學文章數")
    sp.add_argument("--article-chars", type=int, default=4000, help="每篇文章保留字數上限")
    sp.add_argument("--github", type=int, default=3, help="GitHub repo 數")
    sp.add_argument("--github-readme-chars", type=int, default=4000, help="每個 README 保留字數")
    sp.add_argument("--arxiv", type=int, default=3, help="arXiv 論文數")
    sp.add_argument("--out", help="輸出檔（預設 learn-<topic>.md）")
    sp.add_argument("--pdf", action="store_true", help="同時輸出 PDF（用 Playwright/Chromium）")
    sp.add_argument("--no-cache", action="store_true", help="強制重抓，忽略快取")
    sp.add_argument("--cache-ttl", type=int, default=86400,
                    help="快取有效秒數（預設 24h=86400）；超過則重抓")
    sp.add_argument("--whisper-fallback", action="store_true",
                    help="當 YT CC 字幕失敗時，委派給 youtube-subtitle SKILL（會跑 Whisper，慢但可救沒字幕的影片）")
    sp.set_defaults(func=cmd_learn)

    sp = sub.add_parser("to-pdf", help="把 md 檔/網址/資料夾轉 PDF")
    sp.add_argument("input")
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_to_pdf)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
