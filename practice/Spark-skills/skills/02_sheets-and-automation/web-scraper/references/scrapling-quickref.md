# Scrapling 速查表

> 官方：<https://github.com/D4Vinci/Scrapling> ｜ License: BSD-3-Clause

Scrapling 是 Python 爬蟲框架，主打「**反偵測 + 適應性 + 高效能**」，可取代 / 搭配 BeautifulSoup、Parsel、Scrapy、Playwright。

## 安裝

```bash
# 只要 parser
pip install scrapling

# 含 fetcher（HTTP 引擎、stealth 引擎）
pip install "scrapling[fetchers]"
scrapling install              # 下載瀏覽器（Chromium / Firefox）

# 全套（含 AI/MCP、shell）
pip install "scrapling[all]"
```

驗證：

```bash
scrapling --version
scrapling extract get https://example.com out.md
```

---

## 三大 Fetcher 對照

| 引擎 | 啟動成本 | JS | 反爬蟲能力 | 何時用 |
|------|---------|----|-----------|-------|
| `Fetcher` | 極低（純 HTTP）| ❌ | TLS 指紋偽裝 | 一般靜態頁、API、最快 |
| `DynamicFetcher` | 中（無頭瀏覽器）| ✅ | 中 | SPA、需登入、需點擊 |
| `StealthyFetcher` | 高 | ✅ | **高（Cloudflare、Turnstile）** | 被擋、要繞 anti-bot |

### 1) Fetcher — 一般 HTTP

```python
from scrapling.fetchers import Fetcher, FetcherSession

# 單次
page = Fetcher.get("https://quotes.toscrape.com/", impersonate="chrome")
texts = page.css(".quote .text::text").getall()

# 帶 cookie / state（持久 session）
with FetcherSession(impersonate="chrome") as s:
    s.get("https://example.com/login", params={"u":"x","p":"y"})
    page = s.get("https://example.com/dashboard")
```

支援 `impersonate=` 完整 TLS/JA3 指紋偽裝，自動套 HTTP/2、HTTP/3。

### 2) DynamicFetcher — 跑 JS

```python
from scrapling.fetchers import DynamicFetcher

page = DynamicFetcher.fetch(
    "https://quotes.toscrape.com/js/",
    network_idle=True,         # 等網路安靜
    wait_selector=".quote",    # 等元素出現
    timeout=30_000,
)
quotes = page.css(".quote .text::text").getall()
```

進階：`page.click("...")`、`page.fill("input[name=q]", "AI")`、`page.screenshot("a.png")`。

### 3) StealthyFetcher — 繞反爬蟲

```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    "https://target.com/protected",
    headless=True,
    solve_cloudflare=True,     # 自動解 Turnstile
    block_ads=True,
    google_search_referer=True,
    proxy="http://user:pass@proxy.example.com:8000",
)
print(page.status, len(page.body))
```

**fallback 建議**：StealthyFetcher 失敗 → 改 DynamicFetcher 加長 timeout；仍失敗 → 換 proxy 或人機驗證解題服務。

---

## Selector / 元素操作

回傳的 `Selector` 物件支援多種風格，混用無妨：

```python
# CSS（含偽元素 ::text、::attr(href)）
page.css(".quote .text::text").getall()
page.css("a::attr(href)").getall()

# XPath
page.xpath('//div[@class="quote"]/span/text()').getall()

# BeautifulSoup 風格
for q in page.find_all("div", class_="quote"):
    print(q.find("small").text)

# 文字搜尋（精確/模糊）
page.find_by_text("Sign in", tag="a", first_match=True)

# 適應式：原選擇器掛了會嘗試「相似元素重新定位」
page.css(".price", adaptive=True)

# DOM 漫遊
node.parent, node.next_sibling, node.children, node.path
```

提取時：`get()`、`getall()`、`re(r"...")`、`re_first(r"...")`、`attrib`。

---

## Spider — 整站爬取

```python
from scrapling.spiders import Spider, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10
    download_delay = 0.5
    respect_robots_txt = True

    async def parse(self, response: Response):
        for q in response.css(".quote"):
            yield {
                "text": q.css(".text::text").get(),
                "author": q.css(".author::text").get(),
                "tags": q.css(".tag::text").getall(),
            }
        nxt = response.css(".next a::attr(href)").get()
        if nxt:
            yield response.follow(nxt)

result = QuotesSpider(crawldir="./.crawl").start()
result.items.to_jsonl("quotes.jsonl")
result.items.to_json("quotes.json")
```

特色：
- **暫停／續傳**：`crawldir` 一旦設定，Ctrl+C 後再跑會從斷點繼續。
- **多 Session**：`response.follow(url, session_id="stealthy")` 可在單一 spider 內混用 Fetcher / Stealthy。
- **開發模式**：`Spider(dev_mode=True)` 第一次跑會 cache 回應，反覆改解析邏輯時不再重打網站。
- **串流消費**：`async for item in spider.stream(): ...`

---

## CLI（不寫程式也能用）

```bash
# 抓主要內容轉 markdown
scrapling extract get "https://example.com/article" out.md

# 指定 CSS 選擇器
scrapling extract get "https://example.com" out.html --css-selector "#main"

# 反爬蟲版
scrapling extract stealthy-fetch "https://target.com" out.html \
  --css-selector "#content" --solve-cloudflare

# 互動 shell（IPython）
scrapling shell https://quotes.toscrape.com
# >>> page.css(".quote .text::text").getall()
```

---

## 常見坑

| 症狀 | 處理 |
|------|------|
| `RuntimeError: Browser not installed` | 跑 `scrapling install`（首次） |
| Cloudflare 不過 | `headless=False`、`google_search_referer=True`、加 proxy |
| 選擇器隔天就壞 | 改用 `adaptive=True`，並把舊 HTML snapshot 存起來訓練 |
| 速度慢 | 換 `Fetcher`（不需 JS 時）、開 `concurrent_requests`、用 `dev_mode` 開發 |
| 中文亂碼 | `Fetcher.get(url, encoding="utf-8")` 或讀 `page.encoding` |

---

## 何時 *不* 該用 Scrapling

- 你只是想「快速看一眼某網頁文字」 → 用 TinyFish Fetch（雲端、零安裝、回 markdown）。
- 你想用「自然語言告訴 AI 抓什麼」 → 用 TinyFish Agent。
- 已有官方 API（YouTube Data API、Twitter API、Reddit API、政府開放資料平台）→ 直接打 API。
