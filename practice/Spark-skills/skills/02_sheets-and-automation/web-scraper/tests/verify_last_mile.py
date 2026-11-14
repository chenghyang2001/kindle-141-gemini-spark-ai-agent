#!/usr/bin/env python3
"""最後一哩驗證：把「架構已到位但需付費依賴」的功能，在你設好金鑰/proxy 後一鍵驗。

跑法：
    python tests/verify_last_mile.py                      # 只做免費檢查（不花錢）
    python tests/verify_last_mile.py --proxy-file p.txt   # 一併驗 proxy 池輪換
    python tests/verify_last_mile.py --spend              # 允許真的解一題 CAPTCHA（會花錢）

設計原則：預設**不花錢**。CAPTCHA 金鑰只做免費的「餘額/狀態」驗證；
真正送解碼一題要明確 --spend。沒設金鑰/proxy 的階段會標 SKIP，不算失敗。

退出碼：所有「該跑的」階段都 PASS → 0；有 FAIL → 1。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPE = ROOT / "scripts" / "scrape.py"

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
results: list[tuple[str, str, str]] = []


def record(name: str, status: str, note: str = "") -> None:
    results.append((name, status, note))
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[status]
    print(f"{icon} [{status}] {name}" + (f" — {note}" if note else ""))


def run_cli(args: list[str], timeout: int = 180) -> tuple[int, str, str]:
    p = subprocess.run([sys.executable, str(SCRAPE), *args],
                       capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


# ---------------------------------------------------------------------------
# A. 引擎煙霧測試（免費，一定跑）
# ---------------------------------------------------------------------------
def stage_engines() -> None:
    print("\n=== A. 引擎煙霧測試（免費）===")
    rc, out, _ = run_cli(["doctor"])
    for eng in ("scrapling", "cloakbrowser"):
        record(f"doctor: {eng} 安裝", PASS if f"OK" in out and eng in out else FAIL)

    rc, out, err = run_cli(["cloak", "https://example.com", "--css", "h1", "--text"])
    ok = rc == 0 and "Example Domain" in out
    record("cloak 抓取 example.com", PASS if ok else FAIL,
           "" if ok else f"rc={rc} {err.strip()[:120]}")


# ---------------------------------------------------------------------------
# B. CAPTCHA：免費驗金鑰；--spend 才真的解一題
# ---------------------------------------------------------------------------
def _validate_captcha_key() -> tuple[str | None, str]:
    """回傳 (provider, 訊息)。免費呼叫帳號端點，不耗解碼次數。"""
    try:
        import requests
    except Exception:
        return None, "requests 未安裝"
    nop = os.environ.get("NOPECHA_API_KEY")
    two = os.environ.get("TWOCAPTCHA_API_KEY")
    if nop:
        r = requests.get("https://api.nopecha.com/status/", params={"key": nop}, timeout=20)
        if r.status_code == 200:
            return "nopecha", "NopeCHA 金鑰有效"
        return None, f"NopeCHA 金鑰無效（{r.status_code} {r.text[:80]}）"
    if two:
        r = requests.get("https://2captcha.com/res.php",
                         params={"key": two, "action": "getbalance", "json": 1}, timeout=20).json()
        if str(r.get("status")) == "1":
            return "2captcha", f"2captcha 金鑰有效，餘額 {r.get('request')}"
        return None, f"2captcha 金鑰無效（{r.get('request')}）"
    return None, "未設 NOPECHA_API_KEY / TWOCAPTCHA_API_KEY"


def stage_captcha(spend: bool, captcha_url: str) -> None:
    print("\n=== B. CAPTCHA 解碼 ===")
    provider, msg = _validate_captcha_key()
    if not provider:
        record("CAPTCHA 金鑰驗證", SKIP, msg)
        return
    record("CAPTCHA 金鑰驗證（免費）", PASS, msg)

    if not spend:
        record("CAPTCHA 實解一題", SKIP, "未加 --spend（避免花錢）")
        return
    rc, out, err = run_cli(["cloak", captcha_url, "--settle", "5",
                            "--solve-captcha", "--submit"], timeout=240)
    ok = "已取得並注入 token" in err
    record("CAPTCHA 實解一題（會花錢）", PASS if ok else FAIL,
           "" if ok else f"rc={rc} {err.strip()[-160:]}")


# ---------------------------------------------------------------------------
# C. proxy 池輪換（需提供清單檔）
# ---------------------------------------------------------------------------
def stage_proxy(proxy_file: str | None) -> None:
    print("\n=== C. proxy 池輪換 ===")
    pf = proxy_file or os.environ.get("WEBSCRAPER_PROXY_FILE")
    if not pf:
        record("proxy 池輪換", SKIP, "未提供 --proxy-file（或 WEBSCRAPER_PROXY_FILE）")
        return
    if not Path(pf).exists():
        record("proxy 池輪換", FAIL, f"清單檔不存在：{pf}")
        return
    rc, out, err = run_cli(["cloak", "https://example.com", "--css", "h1", "--text",
                            "--proxy-file", pf], timeout=240)
    ok = rc == 0 and "Example Domain" in out
    note = "（輪換訊息：有）" if "proxy 輪換" in err else "（單一 proxy，未觸發輪換）"
    record("proxy 池抓取 example.com", PASS if ok else FAIL,
           note if ok else f"rc={rc} {err.strip()[-160:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="web-scraper 最後一哩驗證")
    ap.add_argument("--spend", action="store_true", help="允許真的送解一題 CAPTCHA（會花錢）")
    ap.add_argument("--proxy-file", help="proxy 池清單檔（驗 C 階段）")
    ap.add_argument("--captcha-url", default="https://nopecha.com/demo/cloudflare",
                    help="驗 CAPTCHA 用的頁面（預設 nopecha demo）")
    args = ap.parse_args()

    print("web-scraper 最後一哩驗證")
    print(f"  Python {sys.version.split()[0]} | scrape.py: {SCRAPE}")

    stage_engines()
    stage_captcha(args.spend, args.captcha_url)
    stage_proxy(args.proxy_file)

    print("\n=== 總結 ===")
    n_pass = sum(1 for _, s, _ in results if s == PASS)
    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    n_skip = sum(1 for _, s, _ in results if s == SKIP)
    print(f"  PASS {n_pass} ｜ FAIL {n_fail} ｜ SKIP {n_skip}")
    if n_skip:
        print("  （SKIP = 該功能需你設金鑰/proxy 才驗；設好後再跑一次即可補上）")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
