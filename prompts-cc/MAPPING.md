# K141 Claude Code 版改寫規範（prompts/ → prompts-cc/）

2026-11-17 使用者決定：K141 雖然是寫 Google Gemini Spark，這次演練**全部改成 Anthropic Claude Code**。
不再「請 Claude 扮演 Spark」，而是練習格的 Claude Code 直接當主角，**能實做的就真的在使用者的帳號上做**。

## 一、對照表（Spark → Claude Code）

| Spark | Claude Code 對應 | 練習格能不能自己做 |
| --- | --- | --- |
| 常駐規則（個人化設定） | 專案 `CLAUDE.md`／記憶 | ✅ 寫 `chNN/CLAUDE.md` 等檔 |
| 技能（Skills） | Claude Code Skills：`.claude/skills/<名稱>/SKILL.md`（frontmatter 含 name、description） | ✅ 寫在 `practice/.claude/skills/`，並可實際觸發 |
| 連結的應用程式（Gmail／日曆／雲端硬碟） | claude.ai 連接器（MCP）：`mcp__claude_ai_Gmail__*`、`mcp__claude_ai_Google_Calendar__*`、`mcp__claude_ai_Google_Drive__*` | ✅ 真的讀寫使用者帳號（受下方安全規則限制） |
| 排程（每天 7 點自動跑） | claude.ai 雲端排程 routines（`/schedule`）；本機 `/loop` | ❌ 練習格只寫出排程設定與提示詞存檔，**由控制台接手**建立再刪除 |
| 一次生成簡報／網頁成品 | claude.ai Artifact（簡報、頁面、試算表） | ❌ 練習格產出內容檔，**由控制台接手**發布 Artifact |
| 試算表 | Google 雲端硬碟建 Google 試算表（Drive `create_file`）或 CSV | ✅ |
| 上網辦事 | Claude in Chrome（瀏覽器擴充） | ❌ 練習格寫出操作步驟，**由控制台接手** |
| GAS（Apps Script） | 由 Claude Code 寫 GAS 程式碼，存檔供貼到 Apps Script | ✅ 寫檔 |
| 任務／工作列表 | Claude Code session、子 agent、任務清單 | ✅ 視情況 |
| 技能生成器 | 用 Claude Code 產生 SKILL.md（skill-creator 概念） | ✅ |

## 二、安全規則（每個會碰真實帳號的提示詞都要寫進去）

1. **信件只存草稿，絕不寄出**（不可用 send_message、reply 直接送出；要回信就 create_draft）。
2. 測試信件、草稿、日曆事件、雲端檔案，標題／主旨一律以「課程練習」開頭；雲端檔案放在雲端硬碟資料夾「K141-課程練習」。
3. 讀信時只處理主旨以「課程練習」開頭的信；其餘信件只能看標題統計，不改、不刪、不加標籤。
4. 不刪除、不封存任何非本次建立的東西。
5. 每個會建立真實物件的練習，最後要把「本次建立了哪些東西（類型、標題、ID）」附加寫進 `chNN/cleanup.md`，供控制台事後清除。
6. 需要「先有測試信」的練習：由練習格先用 create_draft 建草稿模擬收件，或在提示詞中說明「若收件匣沒有課程練習信，就用虛構資料示範並註明」。

## 三、檔案格式（drill.sh 會解析，務必完全照這個結構）

```
# chNN｜<章名（可改成 Claude Code 版說法）>

## 這章在講什麼

- 條列 3～5 點（改成 Claude Code 的說法；原書觀念保留）

## 作者做過的實驗／例子

- 條列 2～3 點（說明原書用 Spark 怎麼做，以及 Claude Code 版怎麼做）

## 演練

### 練習 1：<標題>

**目的**：一句話。
**控制台接手**：（只有需要 Artifact／排程／Chrome 時才寫這行，說明控制台要做什麼；不需要就整行省略）
**送給練習視窗的提示詞**：

```text
<給練習格 Claude Code 的完整提示詞；路徑相對於 practice/，產出放 chNN/>
```

**觀察重點**：

- 2～3 點

### 練習 2

## 教練解說要點

- 2～3 點

```

規則：
- 每個練習只能有**一個** ```text 程式碼區塊（drill.sh 只取第一個）。
- 練習數量與原章相同。
- 提示詞**不要**寫「請扮演 Gemini Spark」；直接下任務給 Claude Code。
- 不可貼書籍原文；引用每章最多一句、15 字內。全部繁體中文（台灣用語）。
- 提示詞要能在 1～2 分鐘內做完；不要要求寫超過 1 個大型檔案。
- 有日期需求時用「本週」「明天」等相對說法，讓 Claude Code 自己算今天日期。
