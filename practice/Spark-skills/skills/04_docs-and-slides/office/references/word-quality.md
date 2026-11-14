# Word（.docx）品質與設計規則

> 這些是**引擎無關**的規則：不管用 officecli 還是別的工具產檔都適用。
> 操作語法查 `officecli-commands.md`；這裡管「怎樣才做得好看、不出錯」。

## 繁體中文輸出要求

- 不可省略使用者提供的任何文字內容，要完整產出。
- 字體用通用字體（Arial／新細明體／微軟正黑等），確保排版與斷行乾淨。
- 標題保持黑色以利閱讀。

## 頁面與版面

- **頁面尺寸要明確設定**：很多工具預設 A4；美式文件用 US Letter。
  DXA 單位（1440 DXA = 1 英吋）：
  - US Letter：寬 12240 × 高 15840，1" 邊界時內容寬 9360
  - A4：寬 11906 × 高 16838，內容寬 9026
- 橫向（landscape）：傳直向尺寸讓工具內部翻轉（短邊當寬、長邊當高）。
- 邊界預設 1 英吋（top/right/bottom/left = 1440 DXA）。

## 樣式與標題

- 覆寫內建標題樣式時用**精確 ID**：`Heading1`、`Heading2`…（大小寫與數字要對）。
- 標題要帶 `outlineLevel`（H1=0、H2=1…），否則目次抓不到。
- 預設內文字級 12pt 左右，標題明顯大一級並加粗。
- **⚠ 空白 docx 沒有內建標題樣式**：officecli `create` 出來的新檔，直接 `--prop style=Heading1`
  會警告「style not found」（仍會引用，但 Word 裡沒定義）。先用 `--type style` 建好 `Heading1`/`Heading2`
  （或直接對段落設 `font.size`/`font.bold`/`outlineLevel`），再套用。查 `officecli help docx style`。

## 清單（絕不手打項目符號）

- **不要**自己插 `•` 或 `•` 當項目符號 —— 用清單編號設定（`LevelFormat.BULLET` / 十進位）。
- 同一個 reference 會延續編號（1,2,3→4,5,6）；不同 reference 會重新起算（1,2,3→1,2,3）。
- officecli 走 `num/abstractNum/lvl` 元素；查 `officecli help docx num`。

## 表格（最容易出錯）

- **雙寬度**：表格要設 `columnWidths`，每個 cell 也要設 `width`，兩者要對得上，否則某些平台會亂掉。
- **一律用 DXA，不要用百分比**（百分比在 Google Docs 會壞）。表格總寬 = 各欄寬相加 = 內容寬。
- **儲存格底色用 CLEAR 不要 SOLID**（SOLID 會變黑底）。
- **一定加儲存格內距**（如 top/bottom 80、left/right 120 DXA）以利閱讀。
- **不要拿表格當分隔線／橫線**：空 cell 有最小高度會變成空盒子；改用段落下框線
  （`border.bottom`）。兩欄式頁尾用 tab stop，不要用表格。

## 智慧引號（專業排版）

新增含引號/撇號的文字時用智慧引號，別用直引號：

| 實體 | 字元 |
|------|------|
| `&#x2018;` / `&#x2019;` | ‘ ’（左/右單引號、撇號） |
| `&#x201C;` / `&#x201D;` | “ ”（左/右雙引號） |

## 目次（TOC）

- 目次要抓得到，標題段落**只能用內建 HeadingLevel**，不要套自訂樣式。
- officecli：`--type toc`；改完頁碼用 `officecli refresh file.docx` 重算 PAGE/交互參照。

## 追蹤修訂與註解

- 作者名預設用 **"Claude"**，除非使用者指定別的。
- officecli 原生支援：`--prop revision.type=ins|del|format|moveFrom|moveTo`、
  `revision.action=accept|reject`、`revision.author=...`；追蹤式取代：
  `officecli set doc.docx / --find 草稿 --replace 定稿 --prop revision.author=Claude`。
- 最小化修訂：只標動到的字，不要整段重打。
- 註解用 `--type comment`（Word 原生、永久註記）。

## 圖片

- 內嵌圖片要有 alt text（title/description/name）。officecli：`--type image`（PNG/JPG/GIF/SVG）。
- 尺寸用 EMU（914400 EMU = 1 英吋）或帶單位（`2.54cm`/`1in`/`72pt`）。

## 交付前檢查

1. `officecli view out.docx html`（或 `screenshot`）看實際長相。
2. `officecli view out.docx issues` 抓排版/內容/結構問題。
3. `officecli validate out.docx`。
4. 確認：頁面尺寸對、標題有 outlineLevel、表格雙寬度且 DXA、無手打項目符號、智慧引號。
