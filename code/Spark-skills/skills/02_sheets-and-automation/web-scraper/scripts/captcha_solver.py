#!/usr/bin/env python3
"""可插拔 CAPTCHA 解碼轉接器：2captcha / NopeCHA。

⚠️ 合規前提（務必先讀）
----------------------
自動解 CAPTCHA 等於繞過網站「不准機器人」的明確關卡，**可能違反該網站服務條款**。
本模組僅供：自家網站測試、已取得授權的滲透/研究、無障礙用途、或 ToS 明確允許的場景。
預設關閉，需自備該服務的**付費 API key**（環境變數），費用與合規責任由使用者自負。

供應商自動偵測（設哪個就用哪個；兩個都設時用 --captcha-provider 指定，預設 nopecha 優先）：
  - NOPECHA_API_KEY     → NopeCHA
  - TWOCAPTCHA_API_KEY  → 2captcha

支援題型：turnstile（Cloudflare）、recaptcha2、hcaptcha。
回傳 token 字串；注入頁面與送出由呼叫端負責（見 scrape.py cloak --solve-captcha）。
"""
from __future__ import annotations

import os
import time

try:
    import requests
except Exception:  # pragma: no cover - requests 幾乎必裝
    requests = None  # type: ignore


class CaptchaError(RuntimeError):
    pass


def detect_provider(explicit: str | None = None) -> str | None:
    """決定要用哪家。explicit='auto'/None → 看環境變數。"""
    if explicit and explicit not in ("auto", ""):
        return explicit
    if os.environ.get("NOPECHA_API_KEY"):
        return "nopecha"
    if os.environ.get("TWOCAPTCHA_API_KEY"):
        return "2captcha"
    return None


# ---------------------------------------------------------------------------
# 2captcha：in.php 提交 → res.php 輪詢
# ---------------------------------------------------------------------------
_2CAPTCHA_METHOD = {
    "turnstile": ("turnstile", "sitekey"),
    "recaptcha2": ("userrecaptcha", "googlekey"),
    "hcaptcha": ("hcaptcha", "sitekey"),
}


def _solve_2captcha(ctype: str, sitekey: str, pageurl: str, key: str,
                    proxy: str | None, poll: float, timeout: float) -> str:
    if ctype not in _2CAPTCHA_METHOD:
        raise CaptchaError(f"2captcha 不支援題型：{ctype}")
    method, key_param = _2CAPTCHA_METHOD[ctype]
    params = {"key": key, "method": method, key_param: sitekey,
              "pageurl": pageurl, "json": 1}
    if proxy:
        params["proxy"] = proxy
        params["proxytype"] = "HTTP"
    r = requests.get("https://2captcha.com/in.php", params=params, timeout=30).json()
    if str(r.get("status")) != "1":
        raise CaptchaError(f"2captcha 提交失敗：{r.get('request')}")
    rid = r["request"]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(poll)
        res = requests.get("https://2captcha.com/res.php",
                           params={"key": key, "action": "get", "id": rid, "json": 1},
                           timeout=30).json()
        if str(res.get("status")) == "1":
            return res["request"]
        if res.get("request") not in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
            raise CaptchaError(f"2captcha 解碼錯誤：{res.get('request')}")
    raise CaptchaError("2captcha 逾時未取得 token")


# ---------------------------------------------------------------------------
# NopeCHA：POST /token/ 提交 → GET /token/ 輪詢
# ---------------------------------------------------------------------------
_NOPECHA_TYPE = {"turnstile": "turnstile", "recaptcha2": "recaptcha2", "hcaptcha": "hcaptcha"}


def _solve_nopecha(ctype: str, sitekey: str, pageurl: str, key: str,
                   proxy: str | None, poll: float, timeout: float) -> str:
    if ctype not in _NOPECHA_TYPE:
        raise CaptchaError(f"NopeCHA 不支援題型：{ctype}")
    payload = {"key": key, "type": _NOPECHA_TYPE[ctype], "sitekey": sitekey, "url": pageurl}
    if proxy:
        payload["proxy"] = proxy
    r = requests.post("https://api.nopecha.com/token/", json=payload, timeout=30).json()
    job = r.get("data")
    if not job:
        raise CaptchaError(f"NopeCHA 提交失敗：{r.get('message') or r}")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(poll)
        res = requests.get("https://api.nopecha.com/token/",
                           params={"key": key, "id": job}, timeout=30).json()
        if res.get("data"):
            return res["data"]
        if res.get("error") not in (14, None):  # 14 = Incomplete job（繼續等）
            raise CaptchaError(f"NopeCHA 解碼錯誤：{res.get('message') or res.get('error')}")
    raise CaptchaError("NopeCHA 逾時未取得 token")


def solve(ctype: str, sitekey: str, pageurl: str, *,
          provider: str = "auto", proxy: str | None = None,
          poll: float = 5, timeout: float = 180) -> str:
    """解一題 CAPTCHA，回傳 token。

    ctype: 'turnstile' | 'recaptcha2' | 'hcaptcha'
    provider: 'auto' | 'nopecha' | '2captcha'
    """
    if requests is None:
        raise CaptchaError("需要 requests：pip install requests")
    prov = detect_provider(provider)
    if not prov:
        raise CaptchaError("未偵測到解碼服務金鑰，請設 NOPECHA_API_KEY 或 TWOCAPTCHA_API_KEY")
    if prov == "nopecha":
        key = os.environ.get("NOPECHA_API_KEY", "")
        if not key:
            raise CaptchaError("指定 nopecha 但未設 NOPECHA_API_KEY")
        return _solve_nopecha(ctype, sitekey, pageurl, key, proxy, poll, timeout)
    if prov == "2captcha":
        key = os.environ.get("TWOCAPTCHA_API_KEY", "")
        if not key:
            raise CaptchaError("指定 2captcha 但未設 TWOCAPTCHA_API_KEY")
        return _solve_2captcha(ctype, sitekey, pageurl, key, proxy, poll, timeout)
    raise CaptchaError(f"未知 provider：{prov}")
