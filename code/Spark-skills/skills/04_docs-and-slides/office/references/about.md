# 關於 office 技能：來源、授權、整併緣由

## 這支是怎麼來的

`office` 由原本三支獨立技能 **`docx` / `xlsx` / `pptx`** 整併而成，並改用 **officecli** 當統一操作引擎。

**為什麼整併**：三支碰的檔案類型完全一樣（.docx/.xlsx/.pptx），觸發詞嚴重互撞——
使用者一句「幫我做 Word / 改這份簡報」就會有多支想跳出來。整併成一支後只有單一入口，
不再互搶；跨格式任務（同時要 Word + Excel + PPT）也能一支到底。

**保留了什麼**：三支原有的**引擎無關品質與設計知識**全數保留在 `references/`：
- `word-quality.md`、`excel-quality.md`：Word/Excel 的排版、財務模型配色、數字格式、零公式錯誤等規則。
- `ppt-design-system.md`、`ppt-slide-types.md`、`ppt-making-guide.md`、`ppt-pitfalls.md`：投影片設計系統與版型。
- `pptxgenjs.md`、`pptxgenjs-single-slide.md`：需要像素級版面時的替代產檔路徑。

**退場了什麼**：原三支的 python 機制（`unpack.py`/`pack.py`/`validate.py`/`recalc.py`/`comment.py`、
openpyxl/docx-js 範例、以及約 1MB×2 的 OOXML XSD schema 樹）被 officecli 原生功能取代
（officecli 內建 create/validate/render/追蹤修訂/公式自動運算）。這些檔案若日後需要，
都還在 git 歷史裡（整併前的 commit）可以還原。

## officecli 引擎

- 專案：**iOfficeAI / OfficeCLI**（GitHub，18k+ stars，活躍維護）。
- 授權：**Apache-2.0**。
- 特性：單一執行檔、免裝 Office、免 Python、跨平台（win/mac/linux · x64/arm64）、
  內建 HTML/PNG 渲染引擎（「給 AI 眼睛」）。
- 官網 / 安裝：https://officecli.ai　·　`irm https://d.officecli.ai/install.ps1 | iex`
- 官方也提供一份英文 `SKILL.md`（`curl -fsSL https://officecli.ai/SKILL.md`），本技能的
  `officecli-commands.md` 即改寫自它並補上繁中說明；**唯一真相來源永遠是 `officecli help`**。

## 授權注意

- 本技能的 SKILL.md 與 word-quality/excel-quality/about 為原創整併說明。
- `ppt-*.md`、`pptxgenjs*.md` folded 自原 pptx 技能參考；officecli 引擎本身為 Apache-2.0。
- 若要對外散布本技能，請確認各 folded 參考的原始授權條款。
