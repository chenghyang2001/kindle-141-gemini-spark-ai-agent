# OfficeCLI 完整指令參考

> 本檔為 SKILL.md 的延伸細節，只在主檔指示或需要更深資訊時載入。
> 唯一真相來源永遠是 `officecli help <format> <element>`；本檔可能隨版本落後。

## 效能：常駐模式（Resident Mode）

- 第一次存取任何檔案會自動起常駐（閒置 60 秒逾時），自動避開檔案鎖衝突。
- 長工作階段建議明確 `open`/`close`（閒置 12 分鐘逾時）：
  ```bash
  officecli open  report.docx      # 明確載入記憶體
  officecli set   report.docx ...  # 無檔案 I/O 負擔
  officecli close report.docx      # 存檔並釋放
  ```
- 關閉自動常駐：環境變數 `OFFICECLI_NO_AUTO_RESIDENT=1`。
- **只在「非 officecli 邊界」才需 flush**：officecli 自己的 `get/query/view/dump` 永遠看得到最新編輯；
  只有在其他程式（python-docx/openpyxl、Word、渲染器、上傳交付）要讀檔前才 `save`（留常駐）或 `close`（flush+釋放）。
  閒置階段數秒內會自動 flush；`OFFICECLI_RESIDENT_FLUSH=each` 可讓每次修改都先 flush 再回傳。

## L1：建立、讀取、檢查

```bash
officecli create <file>                 # 依副檔名建立空白 docx/xlsx/pptx
officecli view   <file> <mode>          # outline | stats | issues | text | annotated | html | screenshot | svg | pdf | forms
officecli get    <file> <path> --depth N  # 取節點與子節點 [--json]
officecli query  <file> <selector>      # CSS-like 查詢
officecli validate <file>               # 對 OpenXML schema 驗證
```

### view 模式

| 模式 | 說明 | 常用旗標 |
|------|------|---------|
| `outline` | 文件結構 | |
| `stats` | 統計（頁數、字數、圖形數） | |
| `issues` | 排版/內容/結構問題 | `--type format\|content\|structure`、`--limit N` |
| `text` | 純文字擷取 | `--start N --end N`、`--max-lines N` |
| `annotated` | 帶格式註記的文字 | |
| `html` | 靜態 HTML 快照（同 watch 渲染，免伺服器） | `--browser`、`--page N`(docx)、`--start/--end`(pptx) |
| `screenshot`/`svg`/`pdf`/`forms` | headless 截圖 PNG / SVG(單張投影片) / PDF(需 exporter 外掛) / 表單欄位 JSON | `-o`、`--screenshot-width/-height`、pptx `--grid N` |

### 穩定 ID 定址（多步驟工作優先用）

位置索引在插入/刪除後會位移；穩定 ID 不會。有穩定 ID 的元素回傳 `@attr=value` 路徑：

```
/slide[1]/shape[@id=550950021]                 # PPT 圖形
/slide[1]/table[@id=1388430425]/tr[1]/tc[2]    # PPT 表格
/body/p[@paraId=1A2B3C4D]                       # Word 段落
/comments/comment[@commentId=1]                 # Word 註解
```

PPT 亦接受 `@name=`。沒有穩定 ID 的（slide、run、tr/tc、row）退回位置索引。

### query 選擇器

CSS-like：`[attr=value]`、`[attr!=value]`、`[attr~=text]`、`[attr>=value]`、`[attr<=value]`、
`:contains("text")`、`:empty`、`:has(formula)`、`:no-alt`。支援布林 `and`/`or`：
`cell[value>5000 or value<100]`、`cell[(type=Number or type=Date) and value>0]`。
Excel 依欄名：`Sheet1!row[Salary>5000]`。

```bash
officecli query report.docx 'paragraph[style=Normal] > run[font!=Arial]'
officecli query slides.pptx 'shape[fill=FF0000]'
```

## Watch 與互動選取

即時 HTML 預覽，改檔自動刷新。瀏覽器可點選/框選圖形，CLI 可讀「瀏覽器目前選取」再動作。

```bash
officecli watch   <file> [--port N]    # 起預覽伺服器（預設 26315）
officecli unwatch <file>               # 停止
officecli goto    <file> <path>        # 捲動預覽到指定元素
officecli get     <file> selected [--json]   # 讀取使用者在瀏覽器點選的元素
```

範例：使用者在瀏覽器點了幾個圖形後說「把這些變紅」：
```bash
PATHS=$(officecli get deck.pptx selected --json | jq -r '.data.Results[].path')
for p in $PATHS; do officecli set deck.pptx "$p" --prop fill=FF0000; done
```

注意：`.xlsx` 不發出 `data-path`，xlsx 的 `mark`/`selection` 一律 `stale=true`。

### Marks（改動提案，等人審）

```bash
officecli mark    <file> <path> [--prop find=... color=... note=... tofix=... regex=true]
officecli unmark  <file> [--path <p> | --all]
officecli get-marks <file> [--json]
```

改動需人工審核才進檔時用 `mark`；一次性直接改用 `set`；永久註記用 `add --type comment`（Word 原生）。

## L2：DOM 操作

### set 改屬性

```bash
officecli set <file> <path> --prop key=value [--prop ...]
```

任何 XML 屬性都能設（即使目前不存在）。無 `--find` 時，`set` 套用格式到整個元素。

**值格式**：

| 型別 | 格式 | 範例 |
|------|------|------|
| 顏色 | Hex（含/不含 `#`）、名稱、RGB、主題 | `FF0000`、`#FF0000`、`red`、`rgb(255,0,0)`、`accent1`..`accent6` |
| 間距 | 帶單位 | `12pt`、`0.5cm`、`1.5x`、`150%` |
| 尺寸 | EMU 或帶後綴 | `914400`、`2.54cm`、`1in`、`72pt`、`96px` |

點號別名：`font.color=red`、`font.bold=true`、`font.size=14pt`（可用於 shape/run/paragraph/table/row/cell/section/styles）。

### find 找字：格式化或取代

```bash
officecli set doc.docx '/body/p[1]' --find 天氣 --prop bold=true --prop color=red   # 格式化（自動切 run）
officecli set doc.docx '/body/p[1]' --find '\d+%' --prop regex=true --prop color=red # 正規表示式
officecli set doc.docx / --find 草稿 --replace 定稿                                   # 取代（/ = 整份）
officecli set doc.docx / --find 草稿 --replace 定稿 --prop revision.author=Alice      # docx 追蹤修訂取代
officecli set slides.pptx / --find 草稿 --replace 定稿                                # PPT 同語法
```

- 路徑控制搜尋範圍：`/`=整份、`/body/p[1]` 或 `/slide[N]/shape[M]`=特定元素、`/header[1]`/`/footer[1]`=頁首頁尾。
- 預設區分大小寫；不分大小寫：`--prop 'find=(?i)error' --prop regex=true`。
- 跨 run 邊界也能配對；無配對＝靜默成功（`--json` 有 `"matched": N`）。
- **Excel 只支援 find + replace**（不支援 find + 格式屬性）。

### add 加元素 / 複製

```bash
officecli add <file> <parent> --type <type> [--prop ...]
officecli add <file> <parent> --type <type> --after  <path> [--prop ...]   # 插在錨點後
officecli add <file> <parent> --type <type> --before <path> [--prop ...]   # 插在錨點前
officecli add <file> <parent> --type <type> --index N [--prop ...]          # 0-based 位置（Excel row/col 為 1-based）
officecli add <file> <parent> --from <path>                                 # 複製既有元素
```

`--after`/`--before`/`--index` 互斥；不給位置＝附加到最後。

**各格式元素型別（概覽，細節查 `help`）**：
- **pptx**：slide、shape、picture、chart、table、row、connector、group、video/audio、equation、notes、comment、animation、transition、paragraph、run、zoom、ole、placeholder、model3d(.glb)、smartart、diagram(mermaid)。
- **docx**：paragraph、run、table、row、cell、image、header/footer、section、bookmark、comment、footnote、endnote、formfield、sdt、chart、equation、field(28 型)、hyperlink、style、toc、watermark、break、ole、num/abstractNum/lvl、tab、textbox/shape、diagram。支援 i18n/RTL、追蹤修訂 `revision.type/action`。
- **xlsx**：sheet、row、col、cell、chart、image、comment、table、namedrange、pivottable、sparkline、validation、autofilter、shape、textbox、CF(條件格式)、ole、csv。公式 350+ 函式自動運算。

### 文字錨點插入

```bash
officecli add doc.docx '/body/p[1]' --type run  --after find:天氣 --prop text="（晴）"      # 段內插入
officecli add doc.docx '/body/p[1]' --type table --after "find:第一句。" --prop rows=2 --prop cols=2  # 自動切段
```

### 樞紐分析（xlsx）

```bash
officecli add data.xlsx /Sheet1 --type pivottable \
  --prop source="Sheet1!A1:E100" --prop rows=Region,Category \
  --prop cols=Year --prop values="Sales:sum,Qty:count" \
  --prop grandTotals=rows --prop subtotals=off --prop sort=asc
```

聚合函式：sum、count、average、max、min、product、stdDev、var 等。日期欄自動分組。完整參數 `officecli help xlsx pivottable`。

### 文件層級屬性（所有格式）

```bash
officecli set doc.docx / --prop docDefaults.font=Arial --prop docDefaults.fontSize=11pt
officecli set data.xlsx / --prop calc.mode=manual
officecli set slides.pptx / --prop defaultFont=Arial --prop show.loop=true
```

### 排序（xlsx）

```bash
officecli set data.xlsx /Sheet1 --prop sort="C desc" --prop sortHeader=true
officecli set data.xlsx '/Sheet1/A1:D100' --prop sort="A asc" --prop sortHeader=true
```

格式 `COL DIR[, COL DIR ...]`。含合併儲存格或公式的範圍會被拒。超連結/註解/條件格式等會跟著列走。

### move / swap / remove

```bash
officecli move   <file> <path> [--to <parent>] [--index N] [--after <path>] [--before <path>]
officecli swap   <file> <path1> <path2>
officecli remove <file> '/body/p[4]'
```

`--after`/`--before` 時可省略 `--to`，容器由錨點推斷。

### batch 批次（一個存檔週期多操作）

預設遇錯續跑（有任何失敗回傳 exit 1）；`--stop-on-error` 第一個錯就中止；`--force` 繞過 docx 保護。

```bash
echo '[
  {"command":"set","path":"/Sheet1/A1","props":{"value":"姓名","bold":"true"}},
  {"command":"set","path":"/Sheet1/B1","props":{"value":"分數","bold":"true"}}
]' | officecli batch data.xlsx --json

officecli batch data.xlsx --input updates.json --force --json
```

`officecli dump <file> [<path>]` 匯出可重放的 batch JSON（round-trip）。
`officecli refresh <file.docx>` 重算 TOC 頁碼／PAGE／交互參照。
`officecli plugins list` 可擴充支援 `.doc`、`.hwpx`、`.pdf` 匯出。

## L3：原始 XML（L2 表達不了時）

```bash
officecli raw     <file> <part>                          # 看原始 XML
officecli raw-set <file> <part> --xpath "..." --action replace --xml '<w:p>...</w:p>'
officecli add-part <file> <parent>                       # 建立新文件部件（回傳 rId）
```

`raw-set` 動作：`append`、`prepend`、`insertbefore`、`insertafter`、`replace`、`remove`、`setattr`。
不需宣告 xmlns，前綴自動註冊。可用部件：`officecli help <format> raw`。

## 常見陷阱

| 陷阱 | 正確做法 |
|------|---------|
| `--name "foo"` | 用 `--prop name="foo"`，所有屬性都走 `--prop` |
| 未引號的 `[N]` 路徑 | 一律引號：`'/slide[1]'`（shell 會展開中括號） |
| PPT 用 `shape[1]` 放內容 | `shape[1]` 通常是標題佔位符，內容用 `shape[2]+` |
| `/shape[myname]` | 不支援名稱索引；用數字索引或 `@name=`（僅 PPT） |
| 猜屬性名 | 跑 `officecli help <format> <element>` |
| 改開啟中的檔 | 先在 Word/WPS 關閉該檔 |
| shell 字串裡的 `\n` | `--prop text="..."` 內用 `\\n` |
| shell 字串裡的 `$` | `--prop text="$15M"` 會吃掉 `$15`，改單引號 `'$15M'` 或用 heredoc batch |

## 專門子技能（load_skill）

`officecli load_skill <name>` 會輸出一份 SKILL.md，依其規則走。**一個產出只載一支，別疊加**：

- Word：`word`（一般文件）、`academic-paper`（論文引用/公式/交互參照）
- PPT：`pptx`（一般簡報）、`pitch-deck`（募資）、`morph-ppt`(Morph 動畫)、`morph-ppt-3d`(3D)
- Excel：`excel`（一般）、`financial-model`（財務模型）、`data-dashboard`（KPI 儀表板）

## 備忘

- 路徑 **1-based**（`'/body/p[3]'`＝第 3 段）；`--index` **0-based**；Excel `add row/col --index` 例外為 **1-based**。
- 改完用 `validate` 和/或 `view issues` 驗證。
- 不確定就 `officecli help <format> <element>`，不要猜。
