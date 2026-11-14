# 食譜 02：繞過 Cloudflare / Turnstile

**情境**：開頁回 403、403 ChallengePage、JavaScript Challenge、HCaptcha 等。

**第一選擇**：Scrapling **StealthyFetcher** + `solve_cloudflare=True`。

> ⚠️ 法律邊界請看 `references/legal-and-ethics.md`。本食譜假設你針對的是自家系統、公開資料、或已獲授權的研究對象。

---

## CLI 速攻

```bash
python scripts/scrape.py stealthy "https://target.com/protected" \
  --css "#main-content" --out content.html

# 看不到內容就改：
python scripts/scrape.py stealthy "https://target.com/protected" \
  --css "#main-content" --out content.html \
  --no-headless --proxy "http://user:pass@proxy:8000"
```

---

## Python 範本

```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    "https://target.com/protected",
    headless=True,                  # 失敗時改 False（顯示瀏覽器）
    solve_cloudflare=True,
    block_ads=True,
    google_search_referer=True,     # 偽造從 Google 來
    proxy=None,                     # 需要時填
    timeout=60_000,
)

if page.status >= 400:
    raise RuntimeError(f"被擋了，status={page.status}")

# 後續解析跟一般 page 一樣
items = page.css("article .price::text").getall()
print(items)
```

---

## 還是過不了？依序試

1. `headless=False`：肉眼看到底卡哪一關。
2. 換 IP（`proxy=`）：住宅代理 > 機房代理。
3. 加 `wait_until_visible=".some-real-element"`，避免提早判定通過。
4. **換引擎面：CloakBrowser（Chromium 系）**。StealthyFetcher 是 Firefox/camoufox 系；
   若站方專測 Chromium 指紋或 Firefox 系剛好被列黑，換一套指紋面常常就過。
   ```bash
   python scripts/scrape.py cloak "https://target.com/protected" \
     --css "#main-content" --text --proxy "http://user:pass@proxy:8000" --geoip
   # 卡在驗證關 → 加 --no-headless 肉眼操作，或 --humanize 模擬人類軌跡
   ```
   詳見 `references/cloakbrowser-quickref.md`。
5. 反向走：用 **TinyFish Agent** + goal "解開驗證並回傳內容" — agent 會自己判斷。
6. 終極：對方故意阻擋 → 改用官方資料源 / API / 直接寄信給對方索取。

---

## 整合到 Spider（自動 fallback）

```python
class TargetSpider(Spider):
    name = "target"
    start_urls = ["https://target.com/list"]

    async def parse(self, response):
        if response.status == 403:
            # 切到 stealthy session 重試
            yield response.retry(session_id="stealthy")
            return
        for item in response.css(".item"):
            yield {"name": item.css(".name::text").get()}

    sessions = {
        "default": Fetcher(),
        "stealthy": StealthyFetcher(solve_cloudflare=True),
    }
```
