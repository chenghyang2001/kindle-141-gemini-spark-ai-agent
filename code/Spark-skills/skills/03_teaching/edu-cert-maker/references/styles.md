# 證書視覺風格指南

## 風格 1：米黃褐色學院風（warm-academic）— 預設

**適用情境：** 教育類認證、課程結業、學校頒發、傳統正式場合

**色票：**
```
--primary:    #5C3D2E  (深棕，主色)
--gold:       #c9a84c  (古銅金，強調邊框)
--accent:     #8a2b00  (深紅褐，學生姓名)
--bg:         #FDF8F0  (米黃，網頁底色)
--cert-bg:    #fffef0 → #fff8e1 (證書漸層底)
```

**字體：**
- 內文：Noto Sans TC
- 證書本體：Noto Serif TC + Georgia（襯線增加正式感）

**特徵元素：**
- `❧` 角飾符號（左右上角）
- 燙金色雙線邊框（3px 實線 + 8px 光暈陰影）
- 學生姓名底線（金色 2.5px）
- 虛線分隔（簽署區）

**模板檔：** `templates/cert-warm-academic.html`

---

## 風格 2：深藍金色官方風（navy-formal）

**適用情境：** 政府單位、公部門研習、正式國家級認證

**色票：**
```
--primary:    #0a2540  (深藏青)
--gold:       #d4af37  (純金)
--accent:     #c9302c  (硃砂紅，印章感)
--bg:         #f5f6fa
--cert-bg:    #ffffff → #f0f4fb (淺藍漸層)
```

**特徵元素：**
- 雙重金線邊框（外粗內細）
- 國徽/校徽圖標位於頂部
- 紅色「印鑑」浮水印（CSS transform + opacity）
- 中央居中布局，左右對稱

**待擴充模板：** `templates/cert-navy-formal.html`（尚未實作）

---

## 風格 3：海洋藍漸層科技風（ocean-tech）

**適用情境：** 科技類活動、現代化議題（AI、永續、太空、海洋）、青年活動

**色票：**
```
--primary:    #1B3A4B  (深海藍)
--accent:     #4A90D9  (天空藍)
--gold:       #5B7FA5  (霧藍)
--bg:         #E8ECF1
--cert-bg:    #ffffff → #d4e4f0 (海藍漸層)
```

**特徵元素：**
- 漸層底色（從上到下深藍 → 淺藍）
- 幾何線條裝飾（左下角的 SVG 波浪線）
- 學生姓名以「無襯線粗體」呈現
- 證書編號使用 mono 等寬字體

**待擴充模板：** `templates/cert-ocean-tech.html`（尚未實作）

---

## 風格選擇建議

| 情境 | 推薦風格 |
|------|---------|
| 高中生 AI 認證 | 米黃褐色學院風 |
| 教師研習 | 深藍金色官方風 |
| 學術會議 | 深藍金色官方風 |
| 科技營隊 | 海洋藍漸層科技風 |
| 兒童成就獎 | 改用粉橘色（自訂） |
| 公司內訓 | 深藍金色官方風 |

---

## 客製化建議

### 加上單位 LOGO

在 `.cert-design` 內加入 `<img>`：

```html
<img src="logo.png" style="max-height: 60px; margin: 0 auto 16px;" alt="單位 LOGO">
```

LOGO 圖檔放 `assets/` 目錄。建議使用 PNG 透明背景，高度 60-80px。

### 加上電子簽章

把「曾 慶 良」這類純文字改成手寫風簽名圖片：

```html
<img src="signature.png" style="height:40px;" alt="簽名">
```

或使用書法字體：
```css
.cert-sig-name {
  font-family: "Ma Shan Zheng", "DFKai-SB", cursive;
}
```

### 加上印章浮水印

```html
<div style="position:absolute; bottom:50px; right:80px;
            font-family:'KaiTi'; color:rgba(201,42,42,0.4);
            border:3px solid rgba(201,42,42,0.4); padding:20px;
            transform:rotate(-15deg); font-size:14px;">
  教育部國教署<br>太空教育中心<br>認證專用章
</div>
```

### 多頁長式證書

長條形（A4 直印）改為橫式（A4 橫印）：

```css
.cert-design { aspect-ratio: 1.414 / 1; }  /* A4 橫 */
```
