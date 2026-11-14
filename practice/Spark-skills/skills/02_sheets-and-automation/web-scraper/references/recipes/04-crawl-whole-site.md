# 食譜 04：整站爬取（上千頁、需續傳）

**情境**：要把某個網站的所有商品 / 文章 / 公告全部抓下來建本地知識庫。

**最佳解**：Scrapling **Spider**（Scrapy 風格、原生 async、內建續傳）。

---

## CLI 速攻

```bash
python scripts/scrape.py crawl "https://quotes.toscrape.com" \
  --selector ".quote" \
  --next ".next a" \
  --max-pages 50 \
  --concurrency 8 \
  --delay 1.0 \
  --out quotes.jsonl

# 中途 Ctrl+C 沒關係，下次同樣指令會自動續傳：
python scripts/scrape.py crawl "https://quotes.toscrape.com" \
  --selector ".quote" --resume
```

---

## Python 客製範本

複製 `templates/spider.py.j2` 到專案：

```python
from scrapling.spiders import Spider, Response

class SiteSpider(Spider):
    name = "mysite"
    start_urls = ["https://example.com/articles?page=1"]
    concurrent_requests = 8
    download_delay = 1.0
    respect_robots_txt = True

    async def parse(self, response: Response):
        for art in response.css("article"):
            yield {
                "title": art.css("h2::text").get(),
                "url":   art.css("h2 a::attr(href)").get(),
                "date":  art.css("time::attr(datetime)").get(),
                "tags":  art.css(".tag::text").getall(),
                "content_url": art.css("h2 a::attr(href)").get(),
            }
        nxt = response.css(".pagination a.next::attr(href)").get()
        if nxt:
            yield response.follow(nxt)

result = SiteSpider(crawldir="./.crawl_articles", dev_mode=False).start()
result.items.to_jsonl("articles.jsonl")
result.items.to_csv("articles.csv")
print(f"抓到 {len(result.items)} 筆")
```

---

## 兩段式：先抓列表、再抓詳情

```python
class ArticleSpider(Spider):
    name = "articles"
    start_urls = ["https://example.com/articles"]

    async def parse(self, response):
        for a in response.css("article h2 a"):
            yield response.follow(a.attrib["href"], callback=self.parse_detail)
        nxt = response.css(".next::attr(href)").get()
        if nxt:
            yield response.follow(nxt)

    async def parse_detail(self, response):
        yield {
            "url": response.url,
            "title": response.css("h1::text").get(),
            "body": response.css("article .body").get(),  # 整段 HTML
            "author": response.css(".author::text").get(),
        }
```

---

## 加速與穩定性

| 旋鈕 | 預設 | 建議 |
|------|------|------|
| `concurrent_requests` | 16 | 對方友善 → 16；謹慎 → 4 |
| `download_delay` | 0 | 1.0~2.0 秒比較有禮貌 |
| `autothrottle` | True | 保持開啟，遇 5xx 自動降速 |
| `dev_mode` | False | **開發時開啟**，cache 第一次回應 |
| `crawldir` | None | 大量爬時務必設，可暫停／續傳 |

---

## 失敗重試

```python
class RobustSpider(Spider):
    retry_times = 3
    retry_http_codes = [429, 500, 502, 503, 504]
    download_timeout = 30
```

---

## 大量資料寫法（不要全部塞記憶體）

```python
async for item in MySpider().stream():
    write_to_db(item)        # 即寫即丟，不留 in-memory
```
