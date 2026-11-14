# 食譜 05：抓網頁表格 → CSV / Excel

**情境**：政府公報、課表、財報、選課系統等以 HTML `<table>` 呈現的資料。

---

## 最快路徑：pandas + Scrapling

```bash
pip install pandas openpyxl
```

```python
import pandas as pd
from scrapling.fetchers import Fetcher

page = Fetcher.get("https://example.gov.tw/stats/2026")

# 一行抽走所有表
tables = pd.read_html(page.body)
print(f"找到 {len(tables)} 張表")

for i, df in enumerate(tables):
    df.to_csv(f"table_{i}.csv", index=False, encoding="utf-8-sig")  # Windows Excel 友好
```

---

## 表格在 JS 後面才出現？

```python
from scrapling.fetchers import DynamicFetcher
import pandas as pd

page = DynamicFetcher.fetch(url, network_idle=True, wait_selector="table")
tables = pd.read_html(page.body)
```

---

## 結構化欄位（自訂解析）

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get("https://www.twse.com.tw/exchangeReport/STOCK_DAY?...")

rows = []
for tr in page.css("table.t_grid tr")[1:]:   # 跳掉表頭
    cols = [c.strip() for c in tr.css("td::text").getall()]
    if len(cols) >= 7:
        rows.append({
            "date": cols[0],
            "volume": cols[1].replace(",", ""),
            "open": cols[3],
            "high": cols[4],
            "low": cols[5],
            "close": cols[6],
        })

import csv
with open("twse.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
```

---

## 多檔合併寫進同一份 Excel

```python
import pandas as pd

with pd.ExcelWriter("report.xlsx", engine="openpyxl") as xw:
    pd.DataFrame(quotes).to_excel(xw, sheet_name="Quotes", index=False)
    pd.DataFrame(prices).to_excel(xw, sheet_name="Prices", index=False)
    pd.DataFrame(meta).to_excel(xw, sheet_name="Meta", index=False)
```

---

## TinyFish 版（懶得寫選擇器）

```bash
python scripts/scrape.py agent "https://example.gov.tw/stats" \
  --goal "Extract the main statistics table as JSON array. Each row should be an object with column names as keys." \
  --out stats.json

# 再轉 csv
python -c "import json,pandas as pd; pd.DataFrame(json.load(open('stats.json'))).to_csv('stats.csv', index=False, encoding='utf-8-sig')"
```
