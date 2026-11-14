# 黃金樣板 DNA：大器繪圖筆觸風・阿亮老師教學簡報

> 這是「阿亮老師教學簡報」的完整可重用規格（視覺語言＋版型元件＋互動 JS＋講稿格式）。
> 任何要做「翻頁式教學簡報、每頁一重點、老師照念、學員複製貼上實作」的任務，直接套這份 DNA。
> 來源基準：爬蟲學術研究課程 `CH34_AI生圖入門` 樣板。三環境（Claude Code／Codex／Antigravity）共用。

---

## 0. 一句話 DNA
暖米紙質背景 + 2px 黑框 + 虛線內框 + 位移實心投影 的**繪圖筆觸卡片風**；**翻頁式全螢幕**單頁簡報；每頁必有 **🎤 阿亮老師說** 講稿卡（好念）、**📋 一鍵複製** 程式碼區（好實做）、**編號步驟**（好教）；頂部導覽可回首頁/總覽/下載本章成品。

## 1. 檔案結構（每個 CH 六件套）
```
CHxx_主題/
  簡報/CHxx_教學簡報.html   ← 主簡報，≥16 頁
  CHxx講播稿.md            ← 逐頁照念稿＋🖥️螢幕動作＋⌨️喊學員貼的指令
  成品/  下載/  實作手冊/  教師手冊/  截圖/
```
總覽 `index.html` 卡片式串所有 CH（沿用課程首頁繪圖筆觸風）。

## 2. 完整 CSS（直接貼進 `<style>`，全 CH 共用，勿改骨架）
```css
:root{
  --ink:#2b2620; --ink2:#5b5348; --paper:#fbf7ef; --paper2:#f3ecdf;
  --card:#fffdf8; --line:#e5dcc8; --accent:#d0568a; --accent2:#2f8f83;
  --blue:#5b7bd6; --yellow:#f0c04a; --shadow:rgba(60,45,25,.14);
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Microsoft JhengHei','PingFang TC',system-ui,sans-serif;background:#c9bfa8;color:var(--ink);overflow:hidden}
.stage{width:100vw;height:100vh;display:flex;align-items:center;justify-content:center}
.slide{display:none;width:100vw;height:100vh;
  background:radial-gradient(circle at 12% 8%,#fffdf8 0%,transparent 40%),linear-gradient(160deg,#fdfaf3 0%,#f6efe0 100%);
  border:2px solid var(--ink);padding:52px 6vw 58px;position:relative;overflow:auto;flex-direction:column;justify-content:center;align-items:stretch}
.slide.active{display:flex;animation:pop .35s ease}
@keyframes pop{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.slide::after{content:'';position:absolute;inset:8px;border:1.5px dashed #d8ccb0;border-radius:16px;pointer-events:none}
.kicker{display:inline-block;align-self:flex-start;background:var(--accent);color:#fff;font-weight:800;padding:4px 14px;border-radius:20px;font-size:14px;transform:rotate(-1.5deg);border:2px solid var(--ink)}
h1{font-size:40px;line-height:1.2;margin:14px 0 6px}
h2{font-size:30px;line-height:1.25;margin:6px 0 14px}
h3{font-size:20px;margin:16px 0 8px;color:var(--accent2)}
p,li{font-size:19px;line-height:1.7;color:var(--ink2)}
.lead{font-size:22px;color:var(--ink)}
ul{margin:8px 0 8px 22px}li{margin:6px 0}
.cards{display:flex;gap:16px;flex-wrap:wrap;margin:14px 0}
.card{flex:1 1 220px;background:var(--card);border:2px solid var(--ink);border-radius:14px;padding:16px 18px;box-shadow:4px 5px 0 var(--shadow)}
.card .ico{font-size:30px}.card b{display:block;font-size:18px;margin:6px 0 2px;color:var(--ink)}.card span{font-size:15px;color:var(--ink2)}
.say{background:#fff7e6;border:2px solid var(--ink);border-left:10px solid var(--yellow);border-radius:12px;padding:14px 18px;margin:16px 0;box-shadow:4px 5px 0 var(--shadow);position:relative}
.say::before{content:'🎤 阿亮老師說';position:absolute;top:-14px;left:14px;background:var(--yellow);color:var(--ink);font-weight:800;font-size:14px;padding:2px 12px;border:2px solid var(--ink);border-radius:12px}
.say p{font-size:19px;color:var(--ink);margin-top:6px}
.do{background:#fbeef4;border:2px solid var(--ink);border-radius:12px;padding:12px 14px;margin:12px 0;box-shadow:4px 5px 0 var(--shadow)}
.do .tag{display:inline-block;background:var(--accent);color:#fff;font-weight:700;font-size:13px;padding:2px 10px;border-radius:8px;margin-bottom:8px}
pre{background:#1e2a28;color:#e8f3f0;padding:12px 14px;border-radius:8px;overflow-x:auto;font-family:'Consolas','Courier New',monospace;font-size:15px;line-height:1.6;position:relative}
pre code{white-space:pre}
.copy{position:absolute;top:6px;right:6px;background:var(--accent);color:#fff;border:1.5px solid var(--ink);border-radius:6px;font-size:12px;font-weight:700;padding:3px 9px;cursor:pointer}
.copy:active{transform:translateY(1px)}
.steps{counter-reset:s;list-style:none;margin:6px 0}
.steps li{counter-increment:s;position:relative;padding-left:44px;margin:10px 0;font-size:19px}
.steps li::before{content:counter(s);position:absolute;left:0;top:-2px;width:30px;height:30px;background:var(--accent);color:#fff;font-weight:800;border:2px solid var(--ink);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px}
.shot{width:100%;border:2px solid var(--ink);border-radius:12px;box-shadow:5px 6px 0 var(--shadow);margin:10px 0}
.pill{display:inline-block;background:var(--blue);color:#fff;padding:2px 10px;border-radius:20px;font-size:14px;font-weight:700;margin:2px}
.checklist li{list-style:none;position:relative;padding-left:34px}
.checklist li::before{content:'✅';position:absolute;left:0}
.warn{background:#fdeef5;border:2px solid var(--accent);border-radius:12px;padding:12px 16px;margin:12px 0}
.warn b{color:var(--accent)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px;align-items:start}
.route2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:14px 0}
.route2 .box{border:2px solid var(--ink);border-radius:14px;padding:16px 18px;box-shadow:4px 5px 0 var(--shadow)}
.route2 .free{background:#e9f6f2}.route2 .paid{background:#eef1fb}
.nav{position:fixed;bottom:16px;left:20px;display:flex;gap:8px;align-items:center;z-index:50}
.nav button{background:var(--ink);color:#fff;border:none;border-radius:10px;padding:8px 14px;font-size:16px;cursor:pointer;font-weight:700}
.nav button:disabled{opacity:.35}
.pg{font-weight:800;color:#4a4030;font-size:15px;margin-right:2px;white-space:nowrap}
.foot{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);color:#6b5f48;font-size:13px;z-index:40}
.dots{position:fixed;top:50px;left:50%;transform:translateX(-50%);display:flex;gap:6px;z-index:50}
.dots i{width:9px;height:9px;border-radius:50%;background:#a99e84;border:1.5px solid var(--ink);cursor:pointer}
.dots i.on{background:var(--accent)}
.topnav{position:fixed;top:0;left:0;right:0;height:44px;display:flex;align-items:center;gap:10px;padding:0 16px;background:rgba(43,38,32,.94);z-index:300;border-bottom:2px solid var(--ink)}
.topnav a{color:#fff;text-decoration:none;font-size:14px;font-weight:700;padding:5px 12px;border-radius:9px;border:1.5px solid rgba(255,255,255,.35)}
.topnav a:hover{background:rgba(255,255,255,.15)}
.topnav .dl{background:var(--accent2);border-color:var(--ink)}.topnav .sp{flex:1}.topnav .tt{color:#e8d9be;font-size:13px;font-weight:700}
.nextch{position:fixed;bottom:70px;left:50%;transform:translateX(-50%);z-index:60;display:none;background:var(--accent);color:#fff;text-decoration:none;font-weight:800;font-size:17px;padding:12px 26px;border-radius:14px;border:2px solid var(--ink);box-shadow:4px 5px 0 var(--shadow)}
.nextch:hover{transform:translateX(-50%) translateY(-2px)}
```

## 3. 版型元件速查（HTML 片段語意）
- `.kicker`：橘/桃色旋轉小標籤（每頁左上角標篇章/類型）
- `h1/h2` + `.lead`：大標與導言
- `.cards > .card(.ico/b/span)`：三欄重點卡
- `.say > p`：🎤 阿亮老師講稿卡（**每頁必放**，口語照念）
- `.do(.tag)`：實作提示卡
- `pre > code`：程式/指令/提示詞（JS 自動加 📋 複製鈕）
- `.steps > li`：編號步驟（做什麼→預期畫面）
- `.warn`：卡關排除
- `.checklist`：成果檢核表
- `.route2 .free/.paid`：免費/付費雙欄對比
- `.shot`：Playwright 實機截圖
- `.pill`：小藍標（快捷鍵/代號）

## 4. 固定骨架（body 結構）
```
.topnav（🏠回首頁 / 📚課程總覽 / ⬇下載本章成品 / 章名）
.dots（圓點導覽，JS 生成）
.stage > 多個 <section class="slide">（第一個加 active）
.foot（課程名 · CHxx）
.nav（頁碼 + 上一頁 + 下一頁）
JS：翻頁(go)、鍵盤←→/空白/PageUp/Down、圓點、pre 自動加複製鈕、最後一頁顯示 .nextch
```

## 5. 互動 JS（貼在 body 末，勿改）
```javascript
const slides=[...document.querySelectorAll('.slide')];let i=0;
const pg=document.getElementById('pg'),dots=document.getElementById('dots');
slides.forEach((_,k)=>{const d=document.createElement('i');d.onclick=()=>go(k);dots.appendChild(d)});
function go(n){i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>s.classList.toggle('active',k===i));
  [...dots.children].forEach((d,k)=>d.classList.toggle('on',k===i));
  pg.textContent=`${i+1} / ${slides.length}`;
  document.getElementById('prev').disabled=i===0;
  document.getElementById('next').disabled=i===slides.length-1;
  document.querySelector('.slide.active').scrollTop=0;}
document.getElementById('prev').onclick=()=>go(i-1);
document.getElementById('next').onclick=()=>go(i+1);
document.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' ')go(i+1);if(e.key==='ArrowLeft'||e.key==='PageUp')go(i-1);});
document.querySelectorAll('pre').forEach(pre=>{const b=document.createElement('button');b.className='copy';b.textContent='📋 複製';
  b.onclick=()=>{navigator.clipboard.writeText(pre.innerText.replace(/📋 複製$/,'').trim());b.textContent='✔ 已複製';setTimeout(()=>b.textContent='📋 複製',1200)};pre.appendChild(b);});
go(0);
```

## 6. 每頁鋪陳節奏（≥16 頁）
封面 → 先看成果 → 為什麼學 → 觀念/地圖 → 帶著做 Step1..N（每步一頁、含可複製區與預期畫面）→ 進階密技 → 常見卡關(.warn) → 成品下載 → 🔧 交給 Codex/Antigravity 這樣改 → 成果檢核表(.checklist) → 結尾鼓勵。

## 7. 講播稿格式（CHxx講播稿.md）
```
### 📑 簡報 Pn｜頁標題
🖥️ （老師螢幕動作，如：停在封面／指向左邊）
> **照念：** （一段口語旁白，像對學員說話，照念就能講完這頁）
⌨️ （若有指令，喊學員一起貼：「大家把這行貼到終端機」）
```
- 講稿卡（.say）內文與講播稿「照念」段一致，口語、鼓勵、不書面。
- 健康/安全/著作權等提醒用日常口吻帶過。

## 8. 鐵律
繁中台灣用語；不寫版本號與時間預估；截圖用 Playwright 真實操作（雲端工具用示意並標「示意」）；金鑰不進散布檔；頁尾放阿亮老師作者卡＋授權（見 aliang-author-info）。
