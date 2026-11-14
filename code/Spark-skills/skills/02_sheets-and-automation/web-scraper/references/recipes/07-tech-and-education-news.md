# 食譜 07：科技新聞 / 教育新聞 速報

**情境**：「找今天的科技新聞」「給我最新教育新聞」「整理本週教育界動態」。

**最快路徑**：直接用 CLI 內建的 `news` 子命令，已預先收錄 9 個科技 + 9 個教育來源。

---

## 一鍵速攻

```bash
# 兩類都要、中英都抓、輸出 markdown + PDF
python scripts/scrape.py news --topic both --pdf

# 只要科技新聞、英文來源、最多 5 個站
python scripts/scrape.py news --topic tech --lang en --max-sources 5

# 只要中文教育新聞
python scripts/scrape.py news --topic edu --lang zh-tw --out edu-news.md
```

輸出檔名預設：`news-tech-2026-05-09.md`（含日期，方便歸檔）。

---

## 內建來源清單

### 科技（tech）

**中文**
- [iThome 新聞](https://www.ithome.com.tw/news)
- [數位時代](https://www.bnext.com.tw/categories/tech)
- [INSIDE](https://www.inside.com.tw/category/ai)
- [T客邦](https://www.techbang.com)

**英文**
- [TechCrunch](https://techcrunch.com)
- [The Verge](https://www.theverge.com/tech)
- [Ars Technica](https://arstechnica.com)
- [Hacker News](https://news.ycombinator.com)
- [MIT Technology Review](https://www.technologyreview.com)

### 教育（edu）

**中文**
- [教育部即時新聞](https://www.edu.tw/News.aspx?n=9E7AC85F1954DDA8&sms=169B8E91BB75571F)
- [親子天下](https://www.parenting.com.tw/topic/edu)
- [翻轉教育](https://flipedu.parenting.com.tw)
- [未來 Family](https://gfamily.cwgv.com.tw)
- [聯合新聞網-教育](https://udn.com/news/cate/2/6898)

**英文**
- [EdSurge](https://www.edsurge.com/news)
- [Edutopia](https://www.edutopia.org)
- [EdWeek](https://www.edweek.org)
- [Inside Higher Ed](https://www.insidehighered.com)

> 想加自己的來源？編輯 `scripts/scrape.py` 裡的 `NEWS_SOURCES` dict。

---

## 進階：每天自動跑

把 `news` 接進 `ai-agent-orchestrator` 排程，配 LINE Bot 推送：

```yaml
# workflow.yaml
name: 每日科技教育新聞速報
schedule: "0 7 * * *"          # 每天早上 7 點
steps:
  - run: python scripts/scrape.py news --topic both --pdf --out daily.md
  - notify:
      channel: line
      message: "今日新聞速報已生成"
      attach: daily.pdf
```

---

## 加上 LLM 摘要

`news` 出來的 md 太長？接 Claude 做「每篇 3 行重點」：

```bash
python scripts/scrape.py news --topic both --out news.md

# 然後丟給 Claude 摘要（範例 prompt）
# "讀 news.md，把每個來源整理成 3 條重點，輸出新的 summary.md"
```

---

## 主題式找新聞（不只首頁）

要找特定關鍵字（例：「STEM 教育」「AI 教學」）：

```bash
python scripts/scrape.py search "STEM 教育 2026" --top 10 --fetch \
  --prefer-domains ".edu,.gov.tw,parenting.com.tw,edsurge.com" \
  --out stem-2026.md
```

`--prefer-domains` 會把這些網域的結果排到最前面。
