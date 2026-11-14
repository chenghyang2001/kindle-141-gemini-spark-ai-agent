---
name: presentation-templates
description: 簡報模板與設計系統技能。除了原本的統整頁與內容頁 HTML 模板，也加入配色、字體搭配、圓角、間距與整體視覺風格規則。適用於：建立簡報模板、簡報美化、簡報排版、挑選簡報配色、字體搭配、統一簡報風格、教學課程互動式 HTML 簡報。關鍵詞：簡報、投影片、模板、配色、字體、風格、圓角、間距、簡報美化、簡報排版、側邊箭頭、底部圓點、導覽、互動式。需要產出 .pptx 檔案請改用 pptx。
---

# 簡報模板與設計系統

這個技能現在同時提供兩種能力：

1. 原本可直接套用的 HTML 簡報模板
2. 新增的簡報設計系統規則，包含配色、字體與風格配方

## 既有模板

- `assets/templates/slide-cover.html`
  用於標題頁、概述頁、總結頁
- `assets/templates/slide-content.html`
  用於一般內容頁、資訊頁、數據呈現頁

## 新增的設計系統參考

- `references/color-font-skill.md`
  提供多組簡報配色方案、字體搭配與系統字體建議
- `references/design-style-skill.md`
  提供 Sharp、Soft、Rounded、Pill 四套風格配方，涵蓋圓角、間距與元件層級規則

## 建議使用方式

### 情境 1：我要直接做一頁模板

先決定要用：

- 統整頁模板
- 內容頁模板

再依需求修改標題、內容與 CSS。

### 情境 2：我要做整份簡報的視覺統一

先讀：

- `references/color-font-skill.md`
- `references/design-style-skill.md`

先決定：

- 配色系統
- 字體組合
- 圓角與間距風格

再回來套到模板或投影片頁面。

## 工作流程

1. 先確認這次要做的是統整頁、內容頁，還是整份簡報的設計系統
2. 若是做單頁模板，直接從 `assets/templates/` 選模板
3. 若是做整份簡報風格，先讀 `references/` 兩份設計規範
4. 套用一致的配色、字體、圓角、間距，再進行內容填寫

## 重點規則

- 模板可直接修改，但建議保留整體版面骨架
- 簡報若超過 3 頁，優先先決定配色與風格，再做各頁內容
- 同一份簡報內，盡量不要混用多套圓角和間距規則
- 需要做品牌感或高一致性簡報時，優先參考 `references/` 內的新規則

---

## 教學課程互動式 HTML 簡報風格（阿亮老師風格）

> 適用情境：技術書籍、教學課程、工作坊，要投影在大螢幕上現場教學。
> 參考來源：`D:\AI教學與專案實作\自己架設AI_零基礎到大師\CH0_Vibecoding氛圍編程\簡報\Part1_認識VibeCoding.html`
> 實作範例：`D:\AI教學與專案實作\專案_Claude_Code\Claude Code 聖經：從入門到實戰全攻略\簡報\Part0_第零篇_CH00.html`

### 核心設計原則（最重要，必須遵守）

1. **每個章節（或每篇）一個獨立 HTML 檔案**：`Part0_第零篇.html`、`Part1_第一篇.html`，不要把所有章節塞進一個檔案。
2. **每章 25–40 張投影片（硬性下限 25）**：每個步驟、每段說明、每個指令都要各自展開成獨立一張，不要壓縮（2026 標準已從 15–20 提升到 ≥25）。
3. **每張投影片有完整說明段落**：文字要夠完整，老師可以直接唸出來給學生聽懂，不只是 bullet point。
4. **程式碼完整可貼**：所有指令、程式碼要完整顯示在投影片上，學生可以直接複製貼上實作。
5. **概念卡片（concept-card）搭配說明**：用 grid 排列，每張卡片要有 emoji、h3 標題和完整段落說明。

### 字體規格（HTML px，投影時清晰）

| 元素 | 大小 | 備註 |
|------|------|------|
| `h1`（封面大標）| 52–56px | bold，主標題 |
| `h2`（章節標題）| 36px | bold |
| `h3`（子標題）| 26px | semi-bold |
| `p` / `li`（正文）| **22px** | 最小不得低於 20px |
| 說明小字 | 18px | caption / note |
| 終端機模擬 | 17px monospace | `Fira Code`, `Consolas` |
| 程式碼區塊 | 18px monospace | 可複製貼上 |

> **核心原則**：課堂投影時 p/li 必須 22px，後排才看得清楚。低於 20px 一律不行。

---

### 導覽系統（側邊箭頭 + 底部圓點）

#### 側邊箭頭（left / right）
```css
.nav-btn {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  width: 48px; height: 48px;
  border-radius: 50%;           /* 圓形 */
  background: rgba(255,255,255,0.15);
  border: 2px solid rgba(255,255,255,0.3);
  font-size: 20px;
  cursor: pointer;
  z-index: 100;
}
.prev-btn { left: 16px; }
.next-btn { right: 16px; }
```

#### 底部圓點指示器（可點擊跳頁）
```css
.dots-container {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex; gap: 8px;
}
.dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.4);
  cursor: pointer;
}
.dot.active { background: #fff; }
```

#### JavaScript 導覽（鍵盤 + 點擊）
```javascript
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') nextSlide();
  if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   prevSlide();
  if (e.key === 'f' || e.key === 'F') toggleFullscreen();
});
// 每次切換投影片後同步更新 dots active 狀態
```

---

### 投影片類型與設計規則

#### 1. 封面頁
- 深色漸層背景：`linear-gradient(135deg, #0f0c29, #302b63, #24243e)`
- 主標題 h1 52px，副標題 h2 26px，白色或淡藍色
- 右下角：作者名、日期（小字 16px）

#### 2. Part 分隔頁
- 深色漸層（可與封面同色系，略有變化）
- Part 編號：金色/橙色 `#F5A623` 大字（64px），`font-weight: 900`
- Part 標題：白色 h1 40px
- 功能：分隔章節，視覺節奏感強

#### 3. 章節內容頁（一般教學頁）
- 背景：白色或極淺灰（`#f8f9fa`）
- 頂部彩色條：4–6px，顏色對應該 Part 的主題色
- 左右兩欄 grid（`grid-template-columns: 1fr 1fr`）
  - 左欄：說明文字、步驟清單
  - 右欄：截圖、終端機模擬、或圖示

#### 4. 步驟清單（CSS Counter）
```css
.step-list { counter-reset: step; list-style: none; }
.step-list li { counter-increment: step; }
.step-list li::before {
  content: counter(step);
  background: #4A90D9;
  color: white;
  border-radius: 50%;
  width: 28px; height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 10px;
}
```

#### 5. 概念卡片 Grid（Overview / 總覽頁）
```css
.concept-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);  /* 或 2x3 */
  gap: 20px;
}
.concept-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border-top: 4px solid <主題色>;
}
```

#### 6. 終端機模擬方塊
```css
.mock-terminal {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
  font-family: 'Fira Code', monospace;
  font-size: 14px;
  color: #d4d4d4;
}
.mock-terminal::before {
  content: '● ● ●';
  color: #ff5f57;
  display: block;
  margin-bottom: 12px;
  letter-spacing: 4px;
}
```

#### 7. 截圖嵌入
- 路徑格式：`../images/fig-XX-XX.png`（相對路徑，相對於簡報 HTML 所在目錄）
- 樣式：`max-width: 100%; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.15);`
- 若截圖不存在，顯示佔位方塊：灰色背景 + 居中說明文字

---

### 整頁 HTML 簡報結構

```html
<body>
  <!-- 側邊導覽箭頭 -->
  <button class="nav-btn prev-btn">◀</button>
  <button class="nav-btn next-btn">▶</button>

  <!-- 投影片容器 -->
  <div class="slides-container">
    <div class="slide active" data-slide="0">...</div>
    <div class="slide" data-slide="1">...</div>
  </div>

  <!-- 底部圓點 -->
  <div class="dots-container">
    <div class="dot active"></div>
    <div class="dot"></div>
  </div>
</body>
```

- 每次只顯示一頁（`display:flex` vs `display:none`）
- `transition: opacity 0.3s ease` 切換動畫
- 鍵盤 + 點擊 + 箭頭三種導覽方式同步

---

### 顏色系統（Claude Code 聖經版）

| 用途 | 顏色 | Hex |
|------|------|-----|
| 封面/Part 背景 | 深紫漸層 | `#0f0c29 → #302b63` |
| Part 金色強調 | 金橙色 | `#F5A623` |
| Part 1 主題色 | 藍色 | `#4A90D9` |
| Part 2 主題色 | 綠色 | `#27AE60` |
| Part 3 主題色 | 橙色 | `#E67E22` |
| Part 4 主題色 | 紫色 | `#8E44AD` |
| Part 5 主題色 | 紅色 | `#E74C3C` |
| Part 6 主題色 | 青色 | `#16A085` |
| 結語 主題色 | 金色 | `#F39C12` |
| 正文背景 | 極淡灰 | `#f8f9fa` |
| 卡片背景 | 白色 | `#ffffff` |

---

## 🏆 實證版進階互動元件（HermesAgent 課程 · 2026）

> 最新實作範例（強烈建議直接參考）：`D:\AI教學與專案實作\專案_龍蝦書籍和專案執行\新版課程\教學簡報\CH01_*.html`（已上線 https://aliang-hermes-course.netlify.app）
> 這套元件在 36 章課程實戰驗證過，**做新教學簡報時優先沿用**。每章獨立 HTML，single-file，CSS+JS 內嵌。

### 必備五大互動元件（缺一不可）

#### ① 頂部導覽列 `.top-bar`（固定 48px）
含：🏠 首頁(→index.html)、章節標題、▶YouTube、f社群、✉Email、⚙設定、⛶全螢幕。
```css
.top-bar{position:fixed;top:0;left:0;right:0;height:48px;background:rgba(10,8,30,.92);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.1);display:flex;align-items:center;justify-content:space-between;padding:0 16px;z-index:9999;gap:8px}
.tb-btn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:rgba(255,255,255,.85);padding:5px 12px;border-radius:20px;font-size:13px;cursor:pointer;text-decoration:none;display:flex;align-items:center;gap:4px}
/* 投影片要下移避開頂部列 */
.slide{top:48px!important;height:calc(100vh - 48px)!important}
```

#### ② 上下頁按鈕「明顯圓框」（關鍵！淺色頁也要看得清）
> ⚠️ 半透明白色按鈕在淺色內容頁上幾乎看不到 → 一律用**深色實心圓 + 白色粗圓框 + 陰影**。
```css
.nav-btn{position:fixed;top:50%;transform:translateY(-50%);width:54px;height:54px;border-radius:50%;background:rgba(40,36,90,.9);border:3px solid rgba(255,255,255,.92);color:#fff;font-size:24px;font-weight:900;cursor:pointer;z-index:100;box-shadow:0 5px 18px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center}
.nav-btn:hover{background:#4A90D9;transform:translateY(-50%) scale(1.12)}
.prev-btn{left:16px}.next-btn{right:16px}
```

#### ③ 設定面板（字體大小 4 段 + 配色 5 種 · 存 localStorage）
右上「⚙ 設定」開關，跨章記住偏好。
```css
body.fs-lg .sh h2{font-size:35px}body.fs-lg .sl li{font-size:23px}body.fs-lg .card p,body.fs-lg .card li{font-size:22px}/* fs-sm/fs-xl 同理 */
body.bg-beige .cs{background:#f7f1e3}body.bg-blue .cs{background:#eef3f9}
/* 夜間模式技巧：反白濾鏡，圖片再反白還原（解決 inline 樣式文字無法變色問題）*/
body.bg-night .cs{filter:invert(.92) hue-rotate(180deg)}
body.bg-night .cs img{filter:invert(1) hue-rotate(180deg)}
```
```javascript
function applyFs(v){['fs-sm','fs-lg','fs-xl'].forEach(c=>document.body.classList.remove(c));if(v!=='md')document.body.classList.add('fs-'+v);localStorage.setItem('slide-fs',v);}
function applyBg(v){['bg-white','bg-beige','bg-blue','bg-night'].forEach(c=>document.body.classList.remove(c));if(v!=='default')document.body.classList.add('bg-'+v);localStorage.setItem('slide-bg',v);}
applyFs(localStorage.getItem('slide-fs')||'md');applyBg(localStorage.getItem('slide-bg')||'default');
```

#### ④ 終端機指令一鍵複製 `.term-copy`
每個 `.term` 區塊右上角加複製鈕，複製其中所有 `.c`（指令行）。學員可直接貼上實作。

#### ⑤ 底部圓點 + 頁碼 + 完整導覽 JS（minified single-file 版）
```javascript
var s=document.querySelectorAll(".slide"),c=0;
function go(i){s[c].classList.remove("active");c=i;s[c].classList.add("active");up()}
function ch(dir){var i=c+dir;if(i>=0&&i<s.length)go(i)}
function up(){/* 更新 dots active、頁碼 (c+1)/s.length、首尾頁 disable 上下鈕 */}
document.addEventListener("keydown",e=>{if(e.key==="ArrowRight"||e.key==="ArrowDown")ch(1);if(e.key==="ArrowLeft"||e.key==="ArrowUp")ch(-1)});
```

### 每章最後一頁：兩顆按鈕
- **↺ 回到第一頁**：`<button onclick="go(0)">`（灰漸層）
- **→ 下一章**：`<a href="CH下一章.html">`（綠漸層 `135deg,#27AE60,#2ECC71`）
- 最後一章（CH36）改為「↺ 回到第一頁」+「🏠 返回課程首頁(index.html)」。

### 截圖嵌入與重用策略（省時關鍵）
- 命名：`chXX-YY_語意描述.png`，存 `images/`，相對路徑 `images/chXX-YY_xxx.png`。
- **重用通用畫面**：開 PowerShell、`hermes skills list`、桌面 App 主畫面、技能與工具頁、設定模型頁、訊息平台、工具與金鑰頁、金鑰申請頁、商店頁等「基礎畫面」一張可多章共用，**不要叫使用者重拍**。
- **示範成品不可亂套**：LINE 收到的生圖/影片/音樂/報告等各章獨有成果，必須各自截圖，不同就保留待截圖框。
- 截圖一律加 `onerror` 退場（圖片缺失時顯示 `[ 截圖待補 ]` 灰框）：
```html
<div class="img-box"><img src="images/chXX-YY_xxx.png" alt="說明" style="max-width:100%;max-height:320px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.15)" onerror="this.style.display='none';this.nextElementSibling.style.display='block'"><div style="display:none;padding:20px;background:#e0e6ee;border-radius:8px;color:#888">[ 截圖待補 ]</div><div style="margin-top:8px;font-size:13px;color:#888">圖說</div></div>
```
- 待截圖佔位框（未拍時）：黃色虛線框 `border:2px dashed #F5A623;background:#fff8e1` + 「📸 待截圖 / 請截圖：[明確描述要截哪個畫面]」。

### 核心 CSS 類別命名（沿用這套，跨章一致）
`.slide`(每頁) / `.cover`(封面深紫漸層) / `.cs`(內容頁 #f8f9fa) / `.sh`+`.sh h2`(標題列) / `.tc`(兩欄 grid) / `.oc`(單欄) / `.card`.g.o.p.r(彩色卡，border-top 主題色) / `.term`+`.cm`(註解綠).c(指令藍).out(輸出).hl(高亮金) / `.sl`(步驟清單) / `.cg`.cc(概念卡 grid) / `.warn-box`(黃).ok-box(綠) / `.img-box`(截圖框) / `.tbl`(表格) / `.checklist`(驗收) / `.links`(資源連結) / `.goals`(學習目標)。

### 字體標準（2026 更新）
正文 ≥18px（投影後排可讀），設定面板可放大到「大/特大」。比舊版「最低 20px」務實——18px 起跳、可調大。

---

## 風格擴充：卡片式繪畫筆觸（HTML 網頁入口風）

明亮暖色雜誌卡片 + 水彩手繪插畫的 HTML 入口頁風格。當使用者說「卡片式繪畫筆觸」「Vista 風」「明亮雜誌卡片風」時，讀 `references/style-card-painterly.md` 取完整設計 token 與元件規格（米白暖底＋白卡＋Noto Serif TC 襯線標題＋紅色重點＋FAL 水彩插畫＋跑馬燈＋編輯部目錄列）。適用課程首頁/landing/目錄頁；深色簡報內頁不套用。

---

## 風格擴充：橫向翻頁網頁 PPT（雜誌風 / 瑞士風）

> 適用情境：線下分享、產品發表、demo day、有強烈個人風格的演講——「一次做完、不用翻頁工具」的單檔 HTML slides。**不適合**：大量表格數據、培訓課件、多人協作。
> 規則來源：概念與配色/版型方法整理自 op7418/guizang-ppt-skill（歸藏，授權 **AGPL-3.0**）。此處僅萃取設計方法與色值等事實層並自行重寫，**未複製其 HTML/CSS 原始碼**；若要用它的完整模板/WebGL 引擎，請另裝原 repo 並遵守 AGPL。

兩種可選視覺基調，做之前先擇一並鎖定，不中途混搭：

### 風格 A · 電子雜誌 × 電子墨水（預設，暖色雜誌感）
- 襯線標題（Noto Serif SC + Playfair Display）＋ 無襯線正文 ＋ 等寬元數據；美學錨點「像 Monocle 雜誌貼上了代碼」。
- **配色只從預設挑，不允許自訂 hex（配錯即崩）**。常用預設（ink 墨 / paper 紙）：
  - 墨水經典（Monocle 通用）：`--ink:#0a0a0b` / `--paper:#f1efea`
  - 靛藍瓷（科技/研究）：`--ink:#0a1f3d` / `--paper:#f1f3f5`
  - 森林墨（自然/文化）：`--ink:#1a2e1f` / `--paper:#f5f1e8`
  - （原庫共 5 套，另有暖褐/酒紅系；同一份 deck 只用一套）

### 風格 B · 瑞士國際主義（Swiss，資訊驅動）
- 全程無襯線（Inter + Helvetica + Noto Sans SC）＋ 極致字級對比；灰白底 ＋ **單一**高飽和高亮色（不可混多個高亮）：
  - 克萊因藍 IKB `#002FA7`（最穩、通用）／檸檬黃／檸檬綠／安全橙（四選一）
- **Swiss locked mode**：正文頁只從原庫 22 個登記版式（S01–S22）選用，別自繪新頁；標題預設**貼左上內容軸、不置中**（statement/split 版式除外）。

### 共用硬規則
- 橫向翻頁：鍵盤 ← →、滾輪、觸控、ESC 出索引；Lucide 圖示、Motion One 入場動效。
- **主題節奏（生成後自檢）**：❌ 禁連續 3 頁以上同主題；❌ 8 頁以上 deck 至少要有 1 個 hero dark + 1 個 hero light；✅ 每 3–4 頁插一個 hero（封面/幕封/大引用）當呼吸點。
- hero 頁做章節封面/開場/收束/轉場（讓背景大面積透出）；非 hero 頁放正文。

### 社群封面 / 配圖比例規則
- 章節封面 / 全屏主視覺 → **16:9**；瑞士風頂部橫幅 / Image Hero → **16:9 或 21:9**。
- 配圖類型分：人文紀實、雜誌風資訊圖、流程/Pipeline、對比圖、系統關係圖、截圖再設計/UI 情景、數據大字報。
- 來源不可控的原始截圖優先 `fit-contain`（避免裁掉文字）；紀實照片用 `cover` 保張力；同一組多圖面板用同一高度類、別混高度。
