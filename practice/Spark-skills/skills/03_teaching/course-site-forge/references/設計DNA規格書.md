# 設計 DNA 規格書（本課程簡報卡片手繪風）

> 這份規格書的每一個數值，都是從本課程黃金範本 `CH06_教學簡報.html` 的原始碼**逐條抽出**的真實設定，不是憑印象寫的。
> 用途：把它連同三張樣板圖（`樣板_封面.png`、`樣板_內容頁.png`、`樣板_章節卡片.png`）一起交給 AI，AI 就能生出風格一致的簡報網站範本。
> ※ 三張樣板圖不在本技能包內，收錄於課程 **CH42 章成品**（`CH42_Canva畫樣板與設計DNA` 下載包）；本技能的 `build_site.py` 生站不需要這三張圖，只讀本規格書與 assets 範本。
> 對照原始碼：`CH06_資料洞察儀表板/簡報/CH06_教學簡報.html` 的 `<style>` 區段。

---

## 1. 色票（CSS 變數，`:root` 原文照抄）

```css
:root{
  --ink:#2b2620;    /* 主墨色：標題、邊框、按鈕底 */
  --ink2:#5b5348;   /* 次墨色：內文、說明文字 */
  --paper:#fbf7ef;  /* 紙色：亮面底色 */
  --paper2:#f3ecdf; /* 紙色2：漸層底、區塊底 */
  --card:#fffdf8;   /* 卡片底色 */
  --line:#e5dcc8;   /* 淺線色：分隔線 */
  --accent:#e07a3f; /* 主強調色（橘）：kicker、步驟圓號、複製鈕 */
  --accent2:#2f8f83;/* 次強調色（綠）：.do 標籤、下載鈕 */
  --blue:#3a6ea5;   /* 藍：.pill 膠囊標籤 */
  --yellow:#f0c04a; /* 黃：.say 左邊條與徽章 */
  --shadow:rgba(60,45,25,.14); /* 手繪硬陰影色 */
}
```

| 變數 | 色碼 | 用在哪 |
|---|---|---|
| `--ink` | `#2b2620` | 標題文字、所有 2px 實線邊框、深色按鈕 |
| `--ink2` | `#5b5348` | 內文段落、卡片說明字 |
| `--paper` | `#fbf7ef` | 亮面紙色 |
| `--paper2` | `#f3ecdf` | 頁面漸層的深端 |
| `--card` | `#fffdf8` | `.card` 卡片底 |
| `--line` | `#e5dcc8` | 淺色分隔線 |
| `--accent` | `#e07a3f` | `.kicker`、`.steps` 圓號、`.copy` 複製鈕、`.nextch` |
| `--accent2` | `#2f8f83` | `.do .tag`、頂部導覽「⬇ 下載」鈕 |
| `--blue` | `#3a6ea5` | `.pill` 膠囊標籤 |
| `--yellow` | `#f0c04a` | `.say` 左邊條 10px、「🎤 阿亮老師說」徽章底 |
| `--shadow` | `rgba(60,45,25,.14)` | `box-shadow: 4px 5px 0`（不模糊的手繪硬影） |

**頁面外底色**：`body{background:#c9bfa8}`（不在變數表內，原始碼直接寫死，抽規格時容易漏，特別列出）。

**投影片底**：兩層漸層疊加——
```css
background:
  radial-gradient(circle at 12% 8%, #fffdf8 0%, transparent 40%),
  linear-gradient(160deg,#fdfaf3 0%,#f6efe0 100%);
```

## 2. 字體

```css
font-family:'Microsoft JhengHei','PingFang TC',system-ui,sans-serif;  /* 內文全域 */
font-family:'Consolas','Courier New',monospace;                        /* pre 程式碼 */
```

| 元素 | 字級 | 其他 |
|---|---|---|
| `h1` | 40px | line-height 1.2 |
| `h2` | 30px | line-height 1.25 |
| `h3` | 20px | 色用 `--accent2` |
| `p, li` | 19px | line-height 1.7，色 `--ink2` |
| `.lead` | 22px | 色 `--ink` |
| `.kicker` | 14px | 粗體 800、白字 |
| `pre` | 15px | 深底 `#1e2a28`、字色 `#e8f3f0` |

## 3. 圓角與邊框（手繪感的關鍵）

| 元件 | 圓角 | 邊框 | 陰影 |
|---|---|---|---|
| `.kicker` | 20px（膠囊） | `2px solid var(--ink)` | 無，但 `transform:rotate(-1.5deg)` 歪貼紙 |
| `.card` | 14px | `2px solid var(--ink)` | `4px 5px 0 var(--shadow)` |
| `.say` | 12px | `2px solid var(--ink)` + `border-left:10px solid var(--yellow)` | `4px 5px 0` |
| `.do` | 12px | `2px solid var(--ink)` | `4px 5px 0` |
| `.shot`（截圖框） | 12px | `2px solid var(--ink)` | `5px 6px 0` |
| `pre` | 8px | 無 | 無 |
| `.pill` | 20px | 無 | 無 |
| 手繪內框 | 16px | `1.5px dashed #d8ccb0`，`inset:8px`（`.slide::after`） | 無 |

**手繪風三要素**：①所有邊框一律 `2px solid var(--ink)` 深墨線；②陰影一律「位移不模糊」（`4px 5px 0`）像麥克筆畫的；③頁面內縮 8px 一圈虛線框（`.slide::after`）。

## 4. 版面

```css
.slide{width:100vw;height:100vh;padding:60px 5vw 64px;overflow:auto}
.slide.active{display:block;animation:pop .35s ease}
@keyframes pop{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
```
- 全頁寬滿版，禁置中窄卡。
- 兩欄用 `.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}`。
- 卡片列用 `.cards{display:flex;gap:16px;flex-wrap:wrap}`＋`.card{flex:1 1 220px}`。

## 5. 元件清單（class 名固定，AI 生成時必須沿用）

| class | 名稱 | 長相重點 |
|---|---|---|
| `.kicker` | 斜貼紙標籤 | 橘底白字膠囊、rotate(-1.5deg)、墨線框 |
| `.say` | 阿亮老師說框（講稿框） | 米黃底 `#fff7e6`、左 10px 黃邊、`::before` 浮出「🎤 阿亮老師說」黃徽章 |
| `.do` + `.tag` | 複製貼上區（指令框） | 淺綠底 `#eef6f4`、綠色小標籤、內含 `pre` |
| `pre` + `.copy` | 程式碼與複製鈕 | 深底淺字、右上橘色「📋 複製」鈕 |
| `.steps` | 圓號步驟 | `counter` 自動編號、橘底白字圓圈、墨線框 |
| `.shot` | 全寬截圖框 | `width:100%`、墨線框、硬陰影 |
| `.cards` / `.card` | 手繪卡片組 | 白底墨框硬陰影、`.ico` 30px 圖示、`b` 標題、`span` 說明 |
| `.warn` | 警示框 | 淺橘底 `#fdeee6`、橘框、`b` 橘字 |
| `.checklist` | 打勾清單 | `li::before` 放 ✅ |
| `.pill` | 膠囊標籤 | 藍底白字小膠囊 |
| `.grid2` | 兩欄格線 | 1fr 1fr、gap 18px |
| `.dots` | 頂部進度圓點 | 9px 圓點、目前頁橘色 |
| `.nav` + `.pg` | 左下翻頁列 | 墨底白字按鈕＋頁碼 |
| `.foot` | 底部課名 | 置中 13px 淺墨字 |
| `.topnav` | 頂部固定導覽列 | 深墨半透明底、🏠 回首頁／📚 課程總覽／⬇ 下載本章成品（綠底） |
| `.nextch` | 下一章浮動鈕 | 橘底墨框硬陰影，只在最後一頁顯示 |

## 6. 互動規格（JS 行為）

1. 翻頁：`.slide` 全部隱藏、目前頁加 `.active`；左下「‹ 上一頁／下一頁 ›」按鈕。
2. 鍵盤：`ArrowRight / PageDown / 空白鍵` 下一頁；`ArrowLeft / PageUp` 上一頁。
3. 進度圓點：每頁一顆，可點跳頁，目前頁 `.on` 亮橘。
4. 複製鈕：每個 `pre` 自動插入「📋 複製」，按下寫入剪貼簿並回饋「✔ 已複製」。
5. 下一章鈕：`#nextch` 只在最後一頁顯示（監聽 keydown/click 後延遲判斷）。

## 7. 頁面結構順序（每頁固定）

```
<section class="slide">
  .kicker（這一頁的段落標籤）
  h1 或 h2（一頁一重點）
  內容（cards / steps / do / shot / warn 擇用）
  .say（頁尾一定收在「阿亮老師說」講稿框）
</section>
```

---

*本規格書由 CH06 原始碼實際抽出，供 CH43「AI 產出第一個範本」直接餵給 Gemini／Codex 使用。*
