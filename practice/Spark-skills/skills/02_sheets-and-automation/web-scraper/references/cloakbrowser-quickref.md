# CloakBrowser 快速參考（隱形 Chromium）

> 來源：[CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)（wrapper MIT，免費 v146 binary）。
> 僅用於**合法授權**場景：自家網站測試、公開免登入資料、學術/個人研究、CTF。詳見 `legal-and-ethics.md`。

## 它是什麼

原始碼級（C++）指紋修補的 Chromium，編進 binary，所以偵測站看到的是「真瀏覽器」。
49 處 patch 涵蓋 Canvas / WebGL / audio / 字體 / GPU / 螢幕 / WebRTC / 網路時序 / 硬體回報 /
移除自動化訊號（`navigator.webdriver` 等）/ CDP 輸入行為擬人。
**drop-in Playwright 替代品**，預設即隱形、啟動隨機指紋種子，無需加任何 flag。

## 在本技能怎麼用（統一 CLI）

```bash
# 基本：抓整頁 HTML
python scripts/scrape.py cloak "https://example.com" --out page.html

# 只抓某區段（CSS）→ 純文字
python scripts/scrape.py cloak "https://example.com" --css ".article" --text --out text.json

# 等元素出現再抓（JS 重的頁面）
python scripts/scrape.py cloak "https://shop.com" --wait ".product-card" --css ".product-card" --text

# 整頁截圖
python scripts/scrape.py cloak "https://example.com" --screenshot shot.png

# 走 proxy + 依出口 IP 自動對齊時區/語系（最像當地真人）
python scripts/scrape.py cloak "https://example.com" \
  --proxy "http://user:pass@host:port" --geoip --humanize

# 固定指紋 + 持久化身份（cookie/session 保留，多帳號隔離研究）
python scripts/scrape.py cloak "https://example.com" \
  --fingerprint 12345 --profile ./profiles/id-a
```

## 何時用 cloak、何時用 stealthy？

| 情況 | 用哪個 |
|------|--------|
| 先試、多數反爬 | `stealthy`（Scrapling，Firefox/camoufox 系，已內建 `solve_cloudflare`） |
| 站方專測 **Chromium** 指紋、或 stealthy 仍被擋 | `cloak`（Chromium 系，換一套指紋面） |
| 要 **多身份隔離**、每身份固定指紋 + 各自 cookie | `cloak --fingerprint --profile`（自架版 Multilogin） |
| 要走住宅 proxy 並讓時區/語系/經緯度跟著 IP 走 | `cloak --proxy --geoip` |
| 純靜態、要最快 | 都不用，用 `fetch` / Scrapling Fetcher |

口訣：**Firefox 系打不過 → 換 Chromium 系再打一次。** 兩套指紋面，互為備援。

## 原生 Python API（要客製腳本時）

```python
from cloakbrowser import launch, launch_persistent_context

browser = launch(headless=True, proxy="http://...", geoip=True, humanize=True)
page = browser.new_page()
page.goto("https://example.com", wait_until="networkidle")
html = page.content()
browser.close()

# 持久化身份
ctx = launch_persistent_context("./my-profile", headless=False,
                                args=["--fingerprint=12345"])
```

`launch_async` / `await ...` 為 async 版。page 物件是 Playwright 介面，
`query_selector_all` / `inner_text` / `screenshot` / `wait_for_selector` 都可用。

## 平台與成本

- 平台：Linux x64/ARM64、macOS（Apple/Intel）、**Windows x64**。binary 首次自動下載 ~200MB，本機快取。
- 免費：wrapper MIT；binary v146（Chromium 146）免費。最新版（148）需 Pro 訂閱，爬蟲研究用免費版即足。
- Docker：官方有預建 image，要在容器/CI 跑時用。

## 能解什麼、不能解什麼（實測，重要）

| 偵測層 | 例子 | cloak 能不能 |
|--------|------|------------|
| **被動指紋偵測** | FingerprintJS、BrowserScan、`navigator.webdriver`、Canvas/WebGL/字體/GPU 比對 | ✅ 強項，這就是它的設計目標 |
| **Cloudflare 全頁 interstitial（非互動，真瀏覽器自動放行型）** | 「Just a moment…」自動轉跳 | ✅ 多半可，配 `--settle 6~10` 給它時間 |
| **互動式 Turnstile / CAPTCHA 勾選框（要點擊+發 token）** | `nopecha.com/demo/cloudflare` 那種一直顯示勾選框的 | ⚠️ 指紋偽裝**本身不解**；但可加 `--solve-captcha` 接解碼服務（見下），或改 `browser-act` 多步互動 |

> 別把「過 30/30 指紋偵測」誤讀成「自動解 CAPTCHA」——那是兩回事。指紋偽裝讓你「看起來像真人瀏覽器」，
> 但互動式 CAPTCHA 要的是「真的解出 token」，需另接解碼服務。

## 解互動式 CAPTCHA（`--solve-captcha`，預設關閉，需自備金鑰）

> ⚠️ 自動解 CAPTCHA 等於繞過網站「不准機器人」的明確關卡，**可能違反 ToS**。
> 僅限自家站測試／已授權研究／ToS 允許場景。費用與合規責任自負。詳見 `legal-and-ethics.md`。

可插拔兩家解碼服務，設哪個環境變數就用哪家（兩個都設時 NopeCHA 優先，或 `--captcha-provider` 指定）：

```bash
# 設金鑰（擇一）
export NOPECHA_API_KEY="..."      # 或
export TWOCAPTCHA_API_KEY="..."

# 偵測頁面 CAPTCHA → 送解碼 → 注入 token（→ 選用 --submit 送出表單）
python scripts/scrape.py cloak "https://your-site.com/protected" \
  --solve-captcha --submit --css "#after-login" --text
```

- 自動偵測題型：Turnstile / reCAPTCHA v2 / hCaptcha（也可 `--captcha-type` 指定）。
- 流程：`scripts/captcha_solver.py` 抓 sitekey → 呼叫服務拿 token → 注入 `cf-turnstile-response` /
  `g-recaptcha-response` / `h-captcha-response` 欄位 → `--submit` 嘗試送出。
- 走 proxy 時 token 會帶同一個 proxy 出口（IP 一致才不會被打回）。
- 也接進 `stealthy` 的自動切換：`stealthy ... --solve-captcha`，被擋接手 cloak 後一併解。

## 注意

- binary 較大、啟動比 `fetch` 慢，**別拿來抓靜態頁**；它是「被擋時才出場」的重武器。
- **反爬頁勿用 `--wait-until networkidle`**（挑戰頁持續發 beacon 會 timeout）；用預設 `domcontentloaded` + `--settle`。
- 仍要遵守 robots.txt / ToS、加延遲、不抓個資與付費內容。指紋換得再像，規範一樣要守。
