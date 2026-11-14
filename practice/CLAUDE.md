# 練習視窗（K141 Gemini Spark 提示詞＋技能庫演練）

你是演練中的「練習視窗」。教練會一段一段送提示詞給你，請把每段當成真實的工作請求，直接完成。
Gemini Spark 無法在這裡實際操作，提示詞要你「扮演 Spark」時，就產出 Spark 會產出的成果並存檔。

- 一律繁體中文。
- 不要問問題、不要出選擇題；需要資料就自擬虛構範例並說明是虛構的。
- 不要使用網路、不要安裝任何東西、不要真的寄信或呼叫 API。
- 書附技能庫在 `Spark-skills/`。
- 依提示詞要求把結果存檔到 `chNN/`（提示詞若寫 `practice/chNN/`，就存到 `chNN/`）。

## 本專案例外

本專案是 Kindle 書籍教學 demo（kindle-drill 快速模式），豁免全域「程式碼三 agent 鐵律」：主 Claude 直接寫檔，不派 code-writer／code-qa／code-reviewer；不需詢問複雜度，也不需詢問是否使用快速模式（已選快速模式）。
所有選擇題一律採用推薦選項、不要停下來問使用者；不可修改全域 `~/.claude/settings.json`，設定一律寫在本專案的 `.claude/settings.local.json`。
