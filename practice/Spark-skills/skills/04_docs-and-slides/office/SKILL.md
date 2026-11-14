---
name: office
description: "建立、讀取、檢查、校對、修改 Word(.docx)、Excel(.xlsx/.csv/.tsv)、PowerPoint(.pptx) 檔案的統一技能。主引擎為 officecli（單一執行檔、免 Office、免 Python、跨格式、能渲染成 HTML/PNG 讓 AI 看長相）。觸發詞：Word/word 文件/.docx、報告/memo/信件/合約/範本、頁碼/目次/TOC/頁首頁尾、追蹤修訂/註解、find-and-replace；Excel/試算表/.xlsx/.csv、公式/函式/樞紐分析/圖表/財務模型/清理資料；PowerPoint/簡報/投影片/slides/deck/.pptx、募資簡報/pitch deck。任何要『產出或改動 Office 檔案』的需求都用本技能。不處理：PDF（用 pdf 技能）、Google Docs/Sheets、單純 HTML 網頁。若使用者只要純資料分析而非產出試算表檔，走 python/pandas。"
license: 本 SKILL.md 為原創整併說明；officecli 引擎為 iOfficeAI 開源 Apache-2.0，folded 進來的設計參考版權見 references/about.md
---

# office — Word / Excel / PowerPoint 統一技能

**一支包三種格式**。主引擎是 **officecli**：單一執行檔、免裝 Office、免 Python、跨平台，
還能把文件**渲染成 HTML/PNG 讓 AI「看得到」長相**，做到 `產檔 → 看長相 / 抓問題 → 修` 的閉環。

> 本技能整併自原 `docx` / `xlsx` / `pptx` 三支。操作機制統一走 officecli；
> 三支原有的**引擎無關品質與設計規則**（財務模型配色、數字格式、表格雙寬度、投影片設計系統…）
> 都保留在 `references/`，是產出品質的核心，該讀就讀。

## 第 0 步：先安裝／確認 officecli

```powershell
officecli --version                                   # 先確認
irm https://d.officecli.ai/install.ps1 | iex          # Windows 沒裝才跑
```
（macOS/Linux：`curl -fsSL https://d.officecli.ai/install.sh | bash`）
裝完仍找不到就開新終端機。GitHub Releases 也可直接抓單一執行檔。

## 核心心法：L1 → L2 → L3

- **L1 讀取檢查**：`create` / `view`(outline·stats·issues·text·html·screenshot) / `get` / `query` / `validate`
- **L2 DOM 編輯**：`set` / `add` / `move` / `swap` / `remove` / `batch`（能用這層就別碰 raw XML）
- **L3 原始 XML**：`raw` / `raw-set` / `add-part`（L2 表達不了時才用）

所有指令可加 `--json`。**不確定屬性名/值格式/語法時先跑 `officecli help <format> <element>`，不要猜。**
格式別名：`word`→docx、`excel`→xlsx、`ppt`/`powerpoint`→pptx。

## 標準工作流程（render → 看 → 修）

1. **建立或開啟**：`officecli create out.pptx`（依副檔名決定格式）。
2. **依格式先讀對應品質規則**（見下方路由表），再動手加內容。
3. **產出後看長相**：`officecli view out.pptx html`（或 `screenshot -o p.png`）＋ `view out.pptx issues` 抓排版/結構問題。
4. **修**：用 `set` / `add` 調整 → 再看一次。
5. **驗證**：`officecli validate out.pptx`。
6. **交付前存檔**：只有在「非 officecli 程式要讀這個檔之前」才 `close`（存檔釋放）。

## 路由：依格式讀哪份參考

| 你要做的事 | 先讀 | 引擎操作查 |
|-----------|------|-----------|
| **Word**：報告/信件/合約/範本/追蹤修訂/註解/目次 | `references/word-quality.md` | `references/officecli-commands.md` |
| **Word 繁中/CJK 教材、論文** 排版（中英混排、標點、字距） | `references/word-cjk-typography.md`＋`references/word-cjk-university-template.md` | 同上 |
| **Word 版面設計原則**（層級、留白、對齊、色彩） | `references/word-design-principles.md` | 同上 |
| **Excel**：公式/樞紐/圖表/清理資料 | `references/excel-quality.md` | `references/officecli-commands.md` |
| **Excel 財務模型**（配色/數字格式/零錯誤） | `references/excel-quality.md`（財務模型段） | 同上；或 `officecli load_skill financial-model` |
| **PowerPoint** 版面/設計/投影片類型 | `references/ppt-design-system.md`＋`references/ppt-slide-types.md`＋`references/ppt-making-guide.md` | `references/officecli-commands.md`；`officecli load_skill pptx` |
| **PPT 常見坑** | `references/ppt-pitfalls.md` | |
| **需要精細像素級版面**（officecli 表達不了時的替代路徑） | `references/pptxgenjs.md`／`pptxgenjs-single-slide.md` | 用 pptxgenjs 產檔，再用 officecli 檢查 |

一份產出只需讀最相關的 1～2 份參考，不要一次全載。

## 快速上手

```bash
# PowerPoint
officecli create slides.pptx
officecli add slides.pptx / --type slide --prop title="Q4 報告" --prop background=1A1A2E
officecli add slides.pptx '/slide[1]' --type shape --prop text="營收成長 25%" \
  --prop x=2cm --prop y=5cm --prop font=Arial --prop size=24 --prop color=FFFFFF

# Word
officecli create report.docx
officecli add report.docx /body --type paragraph --prop text="重點摘要" --prop style=Heading1
officecli add report.docx /body --type paragraph --prop text="營收年增 25%。"

# Excel（公式自動運算）
officecli create data.xlsx
officecli set data.xlsx /Sheet1/A1 --prop value="姓名" --prop bold=true
officecli set data.xlsx /Sheet1/B10 --prop value="=SUM(B2:B9)"
```

## 關鍵備忘

- 路徑要引號：`'/slide[1]'`；路徑 **1-based**，`--index` **0-based**（Excel `add row/col --index` 例外 1-based）。
- **繁體中文輸出**：不可省略使用者給的任何文字，要完整輸出；字體用 Arial 等通用字體，排版乾淨。
- **Excel 一定用公式，不要在外面算好硬填數字**；財務模型遵守配色與數字格式規範（見 excel-quality）。
- **Word 表格要雙寬度、用 DXA 不用百分比、項目符號用清單格式不要打 `•`**（見 word-quality）。
- 改完 `validate` + `view issues` 驗證。不確定就 `officecli help`，不要猜。
- 完整指令、各格式屬性、L3 raw XML、常見陷阱、專門子技能：見 `references/officecli-commands.md`。
- 工具來源／授權／整併緣由：見 `references/about.md`。
