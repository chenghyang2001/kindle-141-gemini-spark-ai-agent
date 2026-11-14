---
name: markitdown
description: >
  用微軟 markitdown 把各種檔案「淨化」成乾淨的 Markdown 純文字，餵給 AI 前先去除雜亂排版。
  支援 Word（.docx）、PowerPoint（.pptx）、Excel（.xlsx/.csv）、HTML、圖片、音檔、EPUB、ZIP 等。
  當使用者說「轉成 Markdown」「把這份 Word/PPT/Excel 轉純文字」「淨化教材餵 AI」
  「markitdown」「檔案轉 md」「把亂排版的文件變乾淨」「批次轉 Markdown」時使用。
  ❌ 例外：來源是 PDF 時優先用 pdf_to_md（含 OCR 與表格處理更完整）；
  只抽 PDF 內圖片走 pdf-extract-images；要「產生」Word/PDF 走 docx / pdf；
  Markdown 轉回 Word/PDF 走 md-to-docx / md-to-pdf。
license: MIT
metadata:
  version: "1.0"
  category: document-processing
---

# markitdown 通用檔案轉 Markdown

把 Office 文件、網頁、圖片、音檔等一律轉成結構化 Markdown，讓 AI 好讀好解析、少產生幻覺。底層是微軟開源的 `markitdown` 套件。

## 為什麼要用它

書商 PDF、Word 講義、PPT 題庫的原始排版對 AI 不友善，直接餵容易誤讀。先轉成乾淨 Markdown（保留標題、清單、表格結構），AI 解題、出題、重排的精準度會明顯提升。

## 能力邊界（誠實揭露）

- ✅ Word / PowerPoint / Excel / CSV / HTML / EPUB / ZIP → Markdown
- ✅ 圖片、音檔 → 文字描述或轉錄（依 markitdown 內建能力，可能需額外相依）
- ✅ 批次轉整個資料夾
- ⚠️ PDF 雖可轉，但**表格與 OCR 品質不如 `pdf_to_md`** → PDF 一律建議改走 `pdf_to_md`
- ❌ 不做 Markdown → Word/PDF 的反向轉檔（走 `md-to-docx` / `md-to-pdf`）

## 決策：先看副檔名

| 來源副檔名 | 走哪支 |
|---|---|
| `.pdf` | **`pdf_to_md`**（本技能不搶，除非使用者指名要 markitdown） |
| `.docx .pptx .xlsx .csv .html .epub .zip .jpg .png .mp3 .wav …` | **本技能** |

## 工作流程

### Step 1：環境自動就緒

腳本開頭 `ensure` markitdown（缺才裝，帶 `--break-system-packages`）。

### Step 2：判斷單檔或批次

- 單檔：給一個檔案路徑
- 批次：給資料夾路徑加 `--batch`，轉換夾內所有支援的檔案

### Step 3：執行轉換

```bash
# 單檔：Word 講義轉 Markdown
python scripts/to_markdown.py lecture.docx

# 指定輸出
python scripts/to_markdown.py quiz.pptx -o ./out/quiz.md

# 批次：整個資料夾
python scripts/to_markdown.py ./materials/ --batch -o ./out/
```

### Step 4：回報產出

回報輸出檔路徑與（批次時）成功／失敗清單。失敗檔不中斷其餘轉換。

## CLI 參數速查

| 參數 | 說明 | 預設 |
|---|---|---|
| `input` | 檔案或資料夾路徑 | （必填） |
| `-o, --output` | 輸出檔或資料夾 | 同名 `.md` |
| `--batch` | 批次轉整個資料夾 | 關閉 |
| `--force-pdf` | 允許用 markitdown 轉 PDF（否則擋下並提示改用 pdf_to_md） | 關閉 |

## 安全規則

- MUST 保留來源檔，NEVER 刪改原檔
- MUST 以 UTF-8 輸出
- 遇 `.pdf` 且未加 `--force-pdf` → 中止並提示改用 `pdf_to_md`
- 批次部分失敗 → 記錄清單、不中斷

## 範例

**使用者：** 這份 Word 考卷幫我轉成 Markdown 我要餵 AI 改題
**動作：** `python scripts/to_markdown.py exam.docx`，產出 `exam.md`。

**使用者：** materials 資料夾裡的 PPT 和 Excel 全轉 md
**動作：** `--batch`，逐檔轉換並彙報結果。
