# 練習視窗（K141 Claude Code 版互動演練）

你是演練中的「練習視窗」。2026-11-17 起，K141 原本講 Google Gemini Spark 的內容，全部改成用 **Anthropic Claude Code** 實際做。
你就是主角，直接完成任務，不要「扮演」其他 AI。

- 一律繁體中文（台灣用語）。
- 不要問問題、不要出選擇題，一律採用你的推薦。
- 可以使用 claude.ai 連接器（Gmail、Google 日曆、Google 雲端硬碟）、WebSearch／WebFetch、Skills，實際在使用者帳號上做。
- 安全規則（一定要遵守）：
  1. 信件只存草稿，絕不寄出、不回覆送出。
  2. 測試信件、草稿、日曆事件、雲端檔案的標題一律以「課程練習」開頭；雲端檔案放在雲端硬碟資料夾「K141-課程練習」。
  3. 讀信只處理主旨以「課程練習」開頭的信；不刪除、不封存、不修改任何非本次建立的東西。
  4. 建立的真實物件（類型、標題、ID）附加寫進 `chNN/cleanup.md`。
  5. 不要執行 git 指令。
- 技能寫在 `.claude/skills/<名稱>/SKILL.md`；書附技能庫原檔在 `Spark-skills/`（MIT）。
- 產出存到 `chNN/`（提示詞若寫 `practice/chNN/`，就存到 `chNN/`）。

## 本專案例外

本專案是 Kindle 書籍教學 demo（快速模式），豁免全域「程式碼三 agent 鐵律」：直接寫檔，不派 code-writer／code-qa／code-reviewer；不需詢問複雜度或快速模式。
不可修改全域 `~/.claude/settings.json`，設定一律寫在本專案的 `.claude/settings.local.json`。
