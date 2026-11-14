# K141《Google Gemini Spark AI 代理人跨域落地師全攻略》提示詞＋技能庫演練

曾慶良（阿亮老師）著。Gemini Spark 是 Google 雲端的 AI 代理人，需要 Google AI Pro／Ultra 帳號與 Gemini 網頁操作，無法在演練視窗裡實際操作。
所以把每章的提示詞改寫成練習，由「教練」視窗送給「練習」視窗裡的 Claude，請它扮演 Spark 產出成果（郵件草稿、日曆、CSV、簡報大綱、技能檔、GAS 草稿等），再對照書中觀念解說。
第 19 章使用作者公開的技能庫 [Spark-skills](https://github.com/ChatGPT3a01/Spark-skills)（MIT 授權）。

> 練習內容為依各章重點原創撰寫，不含書籍原文。

## 結構

```
prompts/chNN.md          各章練習：章節重點、作者的例子、提示詞練習、觀察重點、教練解說要點
code/Spark-skills/       書附技能庫原檔（作者公開，MIT）
teaching/drill.json      章節清單
teaching/DRILL-PROMPT.md 教練開場提示詞
teaching/HANDOFF.md      演練進度表
practice/                練習視窗的工作目錄；產出存在 practice/chNN/，技能庫副本在 practice/Spark-skills/
```

| 章 | 主題 | 練習數 |
| --- | --- | --- |
| ch00 | 開課第一步：讓 Spark 認識你 | 2 |
| ch01 | 把需求講清楚，AI 才做得對 | 2 |
| ch02 | 收件匣不再爆炸 | 2 |
| ch03 | 行事曆與待辦自己排 | 2 |
| ch04 | 一句話登記，試算表自己長 | 2 |
| ch05 | 一次生成多頁可編輯簡報 | 2 |
| ch06 | 設好排程，早上 7 點自動報到 | 2 |
| ch07 | 教它一個新技能 | 2 |
| ch08 | 把調好的提示詞，變成拿得走的技能 | 2 |
| ch09 | 我的 AI 班級秘書 | 2 |
| ch10 | 每天早上的經營簡報與會議秘書 | 2 |
| ch11 | 上班族的個人工作流 | 2 |
| ch12 | 客戶關係與行銷小幫手 | 2 |
| ch13 | 接案工作室的自動化秘書 | 2 |
| ch14 | Spark + GAS 雲端神搭配 | 2 |
| ch15 | Spark 幫你上網辦事 | 2 |
| ch16 | 隱私、安全與團隊使用規範 | 2 |
| ch17 | 畢業製作：打造自己的 AI 秘書 | 2 |
| ch18 | Spark 指令與技能生成器 | 2 |
| ch19 | Spark 技能庫 | 3 |
| ch20 | 免費資料與 API 大補帖 | 1 |
| ch21 | 提示詞與指令資源 | 1 |
| ch22 | 素材與圖庫 | 1 |
| ch23 | 官方說明與更新怎麼追 | 1 |
| ch24 | 延伸學習 | 1 |
| ch25 | AI 模型 API 資源 | 1 |
| ch26 | NVIDIA Build 免費 AI API | 1 |
| ch27 | 全書總複習 | 1 |

## 怎麼演練

HP1 螢幕 3（橫式 1920×1080）左右兩半：左半「K141 教練」、右半「K141 練習-全書」。
由主 Claude 開好兩個視窗並送出 `teaching/DRILL-PROMPT.md`，教練一章一章跑完，每章 commit＋push。
