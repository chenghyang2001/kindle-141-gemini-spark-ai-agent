# 安裝與環境設定

第一次使用 web-scraper 技能時，依下方檢查清單一次設定好。

---

## 0. 先決條件

| 必要 | 版本 | 檢查指令 |
|------|------|---------|
| Python | 3.10+ | `python --version` |
| pip | 23+ | `python -m pip --version` |
| Node.js（選用，TinyFish CLI 才需要）| 18+ | `node --version` |

---

## 1. 安裝 Scrapling（本地引擎）

### Windows / PowerShell

```powershell
# 建議用 venv 隔離
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 全套（含 fetcher、stealth、AI/MCP、shell）
pip install "scrapling[all]"

# 安裝瀏覽器（首次必跑）
scrapling install
```

### macOS / Linux

```bash
python -m venv .venv && source .venv/bin/activate
pip install "scrapling[all]"
scrapling install
```

驗證：

```bash
scrapling --version
scrapling extract get https://example.com /tmp/example.md
```

### 只需要某部分？

```bash
pip install scrapling                 # 只要 parser（最輕）
pip install "scrapling[fetchers]"     # parser + 三大 fetcher
pip install "scrapling[all]"          # 全套
```

---

## 1b. 安裝 CloakBrowser（隱形 Chromium，選用第二引擎）

Chromium 系的隱形引擎，當 Scrapling StealthyFetcher（Firefox 系）被擋時換它再打一次。
drop-in Playwright，**Windows x64 原生支援**。

```bash
pip install cloakbrowser
```

首次執行任一 `cloak` 命令時，會自動下載隱形 Chromium binary（~200MB，本機快取）。
免費版用 Chromium v146 即可，無需訂閱。驗證：

```bash
python scripts/scrape.py cloak "https://example.com" --screenshot /tmp/cloak-test.png
```

> 詳細用法與「何時用 cloak vs stealthy」見 `cloakbrowser-quickref.md`。

---

## 2. 設定 TinyFish（雲端 API）

1. 到 <https://agent.tinyfish.ai/> 註冊（**免信用卡**）。
2. 拿到 API Key 後設環境變數：

### Windows（永久）

```powershell
[Environment]::SetEnvironmentVariable("TINYFISH_API_KEY", "tf_xxx", "User")
# 開新 terminal 才會生效；或當前 session：
$env:TINYFISH_API_KEY = "tf_xxx"
```

### macOS / Linux

```bash
echo 'export TINYFISH_API_KEY="tf_xxx"' >> ~/.zshrc   # 或 ~/.bashrc
source ~/.zshrc
```

### 驗證

```bash
python -c "import os, requests; print(requests.get('https://api.search.tinyfish.ai', params={'query':'test'}, headers={'X-API-Key': os.environ['TINYFISH_API_KEY']}, timeout=10).status_code)"
# 應該印 200
```

### MCP 整合（Claude Code）

把以下加進 `~/.claude/mcp.json`（或全域 settings）：

```json
{
  "mcpServers": {
    "tinyfish": {
      "url": "https://mcp.tinyfish.ai",
      "env": { "TINYFISH_API_KEY": "tf_xxx" }
    }
  }
}
```

之後 Claude Code 對話中可直接呼叫 `tinyfish_search`、`tinyfish_fetch`、`tinyfish_agent`。

---

## 3. 額外選用工具

| 工具 | 用途 | 安裝 |
|------|------|------|
| `weasyprint` | Markdown / HTML → PDF | `pip install weasyprint` |
| `cloakbrowser` | 隱形 Chromium 第二引擎（`cloak` 命令） | `pip install cloakbrowser` |
| CAPTCHA 解碼（選用） | `--solve-captcha` 才需；自備付費金鑰，限授權場景 | 設 `NOPECHA_API_KEY` 或 `TWOCAPTCHA_API_KEY`（見 `legal-and-ethics.md` 界線） |
| `playwright` | Spider 換引擎 / 截圖 | `pip install playwright && playwright install` |
| `pandas` | CSV / Excel 後處理 | `pip install pandas openpyxl` |
| `lxml` | XML / 高速 XPath | `pip install lxml` |
| `tinyfish` SDK | 原生 Python SDK | `pip install tinyfish` |
| `@tiny-fish/cli` | TinyFish 互動 CLI | `npm install -g @tiny-fish/cli` |

一鍵裝齊（建議寫進專案 `requirements.txt`）：

```bash
pip install "scrapling[all]" tinyfish weasyprint pandas lxml
scrapling install
```

---

## 4. 常用代理（Proxy）設定

許多反爬蟲網站需要乾淨 IP。建議：

```bash
# 環境變數（Scrapling 自動讀）
export SCRAPLING_PROXY="http://user:pass@proxy.example.com:8000"
```

或在程式中：

```python
StealthyFetcher.fetch(url, proxy="http://user:pass@host:port", solve_cloudflare=True)
```

推薦的住宅代理服務（自行評估，**請遵守 ToS**）：BrightData、Smartproxy、Oxylabs、Webshare（便宜入門）。

---

## 5. 疑難排解

| 症狀 | 原因 | 處理 |
|------|------|------|
| `playwright._impl._errors.Error: Executable doesn't exist` | 沒裝瀏覽器 | `scrapling install --force` |
| `ModuleNotFoundError: scrapling.fetchers` | 只裝了 core | `pip install "scrapling[fetchers]"` |
| `401` from TinyFish | API Key 沒讀到 | 重開 terminal、檢查環境變數作用域 |
| Scrapling 在 Windows 出 `OSError: [WinError 10038]` | 老舊 asyncio 政策 | 升級 Python 至 3.11+ |
| Cloudflare 永遠不過 | IP 被列黑名單 | 加 proxy、改 `headless=False`、加 `google_search_referer=True` |
| 中文 markdown 變亂碼 | 寫檔沒指定編碼 | 寫檔時 `encoding="utf-8"` |

---

## 6. 一鍵自我檢測

跑技能附帶的 doctor 指令（寫在 `scripts/scrape.py`）：

```bash
python C:\Users\user\.claude\skills\web-scraper\scripts\scrape.py doctor
```

輸出會逐項檢查 Python、Scrapling、Playwright 瀏覽器、TinyFish API Key 是否就緒。

### 最後一哩驗證（付費依賴功能）

CAPTCHA 解碼與 proxy 池是「架構已到位、需付費帳號才能驗」的功能。設好金鑰/proxy 後一鍵驗：

```bash
# 預設只做免費檢查（引擎煙霧 + 金鑰有效性 + proxy 輪換），不花錢
python tests/verify_last_mile.py

# 一併驗 proxy 池輪換
python tests/verify_last_mile.py --proxy-file my-proxies.txt

# 允許真的送解一題 CAPTCHA（會花錢，需先 export NOPECHA_API_KEY 或 TWOCAPTCHA_API_KEY）
python tests/verify_last_mile.py --spend
```

未設金鑰/proxy 的階段會標 SKIP（不算失敗）。全部該跑的 PASS → 退出碼 0。
