# Spark Skills｜阿亮老師的教學現場技能庫

> 25 個在教學與工作現場真的用得上的 AI 技能（Agent Skill）。
> 每一個都是一份純文字的 `SKILL.md`——Gemini Spark、Claude Code、Codex 都讀得懂。

**這個庫是《Google Spark AI 代理人跨域落地師全攻略》第 19 章的示範對象。**
你可以直接拿去用，也可以挑一個最像的、改成你自己的版本。

---

## 這是什麼

**技能（Skill）就是一份寫給 AI 看的工作說明書。**

你把「我希望你每次都這樣做」寫成一份純文字檔，AI 讀完就會照做——不用你每次重講一遍規則。

這裡收的不是展示用的範本，而是**被真實工作磨過的版本**：備課要用的、做教材要用的、
處理文件要用的、抓資料要用的。每一個都在教學現場跑過。

---

## 怎麼用

### 三步驟

1. 到下面的分類，找一個**跟你手上那件事最像的**
2. 打開它的 `SKILL.md`，看三個地方：`name`、`description`、正文
3. 把裡面的情境換成你自己的，貼進你的 AI 工具

> **挑選的原則只有一句：找最像的，不是找最厲害的。**
> 愈像，你要改的地方愈少，愈快能用。

### SKILL.md 長什麼樣

```markdown
---
name: meeting-secretary
description: 把雜亂的會議筆記整理成正式會議紀錄。當我提供會議筆記，
             或要求整理會議決議與待辦時使用。
---

# Meeting Secretary｜會議秘書

## 主要目標
（這個技能要產出什麼）

## 工作流程
（我說什麼，它做什麼）

## 輸出格式
（回答要長什麼樣子）

## 權限邊界
（哪些事情絕對不准做）
```

**`description` 是最容易寫壞的一欄。** 寫「整理會議紀錄」不夠——那是在說它**做什麼**。
要寫「**當我提供會議筆記⋯時使用**」，講清楚**觸發時機**，AI 才知道什麼時候該拿出來用。

---

## 分類

### 01_start-here｜先看這裡（3 個）

| 技能 | 做什麼 |
|---|---|
| `skill-installer` | 安裝與管理技能 |
| `otto-skill` | 技能骨架產生器——想從零寫一個時用這個 |
| `aliang-author-info` | 自動把作者資訊套進 README |

### 02_sheets-and-automation｜試算表與自動化（6 個）

| 技能 | 做什麼 |
|---|---|
| `google-sheets-gas-builder` | 用自然語言產生 Google Apps Script |
| `gemini-api` | 呼叫 Gemini API 的標準做法 |
| `tavily-search` | 網路搜尋與資料查證 |
| `web-scraper` | 抓網頁資料 |
| `browser-automation` | 瀏覽器自動化的路由與選擇 |
| `playwright` | 逐步操作瀏覽器 |

### 03_teaching｜教學與教材（7 個）

| 技能 | 做什麼 |
|---|---|
| `teaching-design-adaptive-learning-design` | 適性學習的教學設計 |
| `teaching-design-gamified-learning` | 遊戲化學習的教學設計 |
| `teaching-design-project-based-learning` | 專題式學習的教學設計 |
| `teaching-slide-dna` | 教學簡報的結構設計 |
| `ai-teaching-video` | 教學影片的腳本與製作流程 |
| `edu-cert-maker` | 研習證書批次產生 |
| `course-site-forge` | 課程網站生成 |

### 04_docs-and-slides｜文件與簡報（7 個）

| 技能 | 做什麼 |
|---|---|
| `office` | Word／Excel／PowerPoint 檔案處理 |
| `pdf` | PDF 讀取、拆合、轉檔 |
| `markitdown` | 各種格式轉 Markdown |
| `presentation-templates` | 簡報模板套用 |
| `slide-ebook-forge` | 電子書產線 |
| `humanizer-zh-tw` | 把 AI 味的中文改成自然的繁體中文 |
| `speech` | 文字轉語音 |

### 05_image｜生圖（2 個）

| 技能 | 做什麼 |
|---|---|
| `imagegen` | 生成圖片 |
| `ai-media-generator` | 生成圖片與影片（需要 API 金鑰） |

---

## 使用前請注意

### 1. 權限邊界一定要自己讀一遍

每個技能都有「權限邊界」那一段，寫的是**它絕對不會做的事**（例如不寄信、不刪資料）。

**別人寫的預設值不一定符合你的習慣。** 拿去用之前，那一段請自己看過。

### 2. 先用虛構資料試一次

確認它真的照你想的做，再拿真實資料上去。這個習慣可以省掉很多麻煩。

### 3. 內容會變動

AI 工具的介面與功能一直在改。技能裡提到的操作步驟，**以你當下看到的畫面為準**。

---

## 延伸閱讀：其他值得看的技能資源

除了這個庫，這幾個地方也值得看。

> **以下都是連結，本庫未收錄它們的任何檔案。**
> 這是刻意的——別人的東西放在別人家，你要用就去它家看，
> 這樣才符合各自的授權，也是這一行該有的習慣。

| 來源 | 網址 |
|---|---|
| Anthropic Skills（Claude 官方） | https://github.com/anthropics/skills |
| Google Workspace 提示詞資源 | https://workspace.google.com/resources/ai/ |
| Awesome Gemini Spark Skills（社群） | https://github.com/aiagentslibrary/awesome-gemini-spark-skills |

**看別人的資源前，先做一件事：找 LICENSE 或「使用條款」。**

同樣叫「免費」，條件差很多：有的可以商業使用，有的只能個人用；
有的可以改、可以散布，有的連檔案都不准轉貼。
**找不到授權說明的，就當成「只能自己看，不要散布」。**

---

## 授權

**MIT License** — 你可以自由使用、修改、散布，商業使用也可以，
唯一的要求是保留授權聲明。詳見 [LICENSE](LICENSE)。

換句話說：**拿去用，改成你的，不用問我。** 覺得有用的話，給顆星就很開心了。

---

## 關於作者

### 曾慶良（阿亮老師）

長期投入教育現場與 AI 落地教學，專長把最新的 AI 工具轉譯成教師、企業與一般工作者
「照做就會」的實戰流程。

**現任職務**

- 新興科技推廣中心主任
- 教育部學科中心研究教師
- 臺北市資訊教育輔導員

**獲獎紀錄**

- SETEAM 教學專業講師認證
- 教育部人工智慧講師認證
- 指導學生 XR 專題競賽特優
- VR 教材開發教師組特優
- 百大資訊人才獎
- 親子天下創新 100 教師
- 臺北市特殊優良教師
- 教育部行動學習優等

**著作**

- 《ChatGPT × Codex 全攻略》
- 《Claude Code 全攻略》
- 《Google Spark AI 代理人跨域落地師全攻略》

**教學資源**

| 項目 | 連結 |
|---|---|
| YouTube | https://www.youtube.com/@Liang-yt02 |
| Facebook 社團 | https://www.facebook.com/groups/2754139931432955 |

---

<div align="center">

**如果這個庫對你有幫助，歡迎給一顆星 ⭐**

</div>
