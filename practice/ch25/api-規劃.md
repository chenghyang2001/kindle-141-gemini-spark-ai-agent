# AI 模型 API 規劃（草稿）

> 本檔**沒有連網、沒有執行任何程式**，也沒有填入任何金鑰；需要金鑰的地方一律寫成佔位符【YOUR_KEY】。
> 文中不寫具體價格與確切模型名稱，提到「便宜／快／強」都是相對比較，實際規格**需自行查證**。

## 一、三個老師情境與選模型的考量

| 情境 | 說明 | 成本 | 速度 | 是否需要推理 | 中文品質 | 建議方向 |
| --- | --- | --- | --- | --- | --- | --- |
| **A. 批改短文給回饋** | 國中國文課，每次 30 篇 300 字短文，依評分規準給 3 點回饋 | 中：篇數多，每篇都要讀完全文，建議選中價位模型並先用 3 篇試算費用 | 不急，放學後批次處理即可 | **需要**：要對照評分規準判斷優缺點，最好選推理能力較好的等級 | **很重要**：回饋要用自然的繁體中文、台灣用語 | 選中高階、中文表現好的模型；回饋僅供老師參考，分數由老師決定 |
| **B. 家長通知翻成英文** | 給新住民或外籍家長的通知，約 200 字 | 低：字數少，次數也少，選便宜的等級即可 | 希望快，貼上就要拿到結果 | 幾乎不需要，主要是翻譯 | 要能正確讀懂中文原文；英文要簡單易懂 | 選便宜、快速的模型；日期、時間、金額一定要人工核對 |
| **C. 一週課表整理成表格** | 把老師貼上的文字課表轉成固定欄位的表格 | 低：一週一次 | 中等即可 | 不太需要，主要是格式轉換 | 中等：只要看得懂科目與節次 | 選便宜的模型，要求輸出固定格式（例如 JSON 或 CSV），並檢查節數是否一致 |

**共同原則：**

- 先用小量資料試跑，確認品質與費用，再擴大使用。
- 學生姓名、座號等個資，送出前先去識別化（例如以「學生 01」代替）。
- 各家模型的價格、速度、中文表現、能否用於教育場景，都會變動，**需自行查證**最新官方說明。

## 二、Apps Script 呼叫草稿（請勿執行）

**事前設定（不寫在程式裡）：**

1. 在 Apps Script 編輯器左側選「專案設定」→「指令碼屬性」→「新增指令碼屬性」。
2. 新增三個屬性：
   - `AI_API_KEY`：值填【YOUR_KEY】（換成你自己的金鑰，只填在這裡）
   - `AI_API_ENDPOINT`：值填【API_ENDPOINT】（依服務商官方文件）
   - `AI_MODEL_NAME`：值填【MODEL_NAME】（依服務商官方文件）

```javascript
/**
 * 呼叫 AI 模型 API 的草稿（未執行、未驗證）
 * 請求與回傳格式以常見的「聊天補全」格式撰寫；實際欄位名稱請依服務商官方文件修改。
 * 金鑰、端點、模型名稱都從指令碼屬性讀取，程式裡不寫任何金鑰。
 */

// 中文每個字消耗的 token 通常比英文單字多，上限要預留空間（實際值需依模型測試）
const DEFAULT_MAX_TOKENS = 2000;

function callAiModel(promptText) {
  // 1. 先檢查輸入，空白就不要浪費一次呼叫
  if (!promptText || String(promptText).trim() === '') {
    return fail_('輸入內容是空的，沒有呼叫 API。');
  }

  // 2. 從指令碼屬性讀取設定；缺任何一項就停止，並說明缺哪一項
  const props = PropertiesService.getScriptProperties();
  const apiKey = props.getProperty('AI_API_KEY');
  const endpoint = props.getProperty('AI_API_ENDPOINT');
  const modelName = props.getProperty('AI_MODEL_NAME');
  const missing = [];
  if (!apiKey) missing.push('AI_API_KEY');
  if (!endpoint) missing.push('AI_API_ENDPOINT');
  if (!modelName) missing.push('AI_MODEL_NAME');
  if (missing.length > 0) {
    return fail_('指令碼屬性缺少：' + missing.join('、') + '，請到「專案設定」新增。');
  }

  const payload = {
    model: modelName,
    max_tokens: DEFAULT_MAX_TOKENS,
    messages: [{ role: 'user', content: String(promptText) }]
  };

  try {
    // 3. muteHttpExceptions：讓 4xx/5xx 也能拿到內容，自己判斷，而不是直接拋出看不懂的錯誤
    const response = UrlFetchApp.fetch(endpoint, {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + apiKey }, // 驗證方式依服務商文件調整
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const status = response.getResponseCode();
    const bodyText = response.getContentText();

    // 4. 依狀態碼給出看得懂的訊息；注意不要把金鑰印到紀錄裡
    if (status === 401 || status === 403) {
      return fail_('驗證失敗（' + status + '）：金鑰可能錯誤、過期或沒有權限。');
    }
    if (status === 429) {
      return fail_('呼叫太頻繁或額度用完（429），請稍後再試或檢查用量。');
    }
    if (status < 200 || status >= 300) {
      return fail_('API 回傳錯誤（' + status + '）：' + bodyText.slice(0, 300));
    }

    const data = JSON.parse(bodyText);
    const choice = data.choices && data.choices[0];
    if (!choice) {
      return fail_('回傳格式和預期不同，找不到結果；請對照官方文件的回傳欄位。');
    }

    const content = (choice.message && choice.message.content) || '';
    const finishReason = choice.finish_reason || '未提供';

    // 5. 檢查結束原因：length 代表被字數上限截斷，內容可能不完整甚至是空的
    if (finishReason === 'length') {
      const hint = content.trim() === ''
        ? '回傳內容是空的：上限可能被思考過程或前面的內容用完了。'
        : '回傳內容被截斷，後半段遺失。';
      return fail_(hint + '請調高 max_tokens（目前 ' + DEFAULT_MAX_TOKENS + '），或縮短輸入、要求精簡回答。', content);
    }
    if (content.trim() === '') {
      return fail_('回傳內容是空的（結束原因：' + finishReason + '），請檢查輸入或服務商說明。');
    }

    Logger.log('呼叫成功，結束原因：' + finishReason);
    return { ok: true, text: content, finishReason: finishReason };
  } catch (error) {
    // JSON 解析失敗、網路中斷等意外都會到這裡
    return fail_('呼叫過程發生錯誤：' + error.message);
  }
}

// 統一的失敗回報：寫入紀錄，並回傳可讀訊息（partialText 保留被截斷的內容供參考）
function fail_(message, partialText) {
  Logger.log(message);
  return { ok: false, message: message, partialText: partialText || '' };
}
```

## 三、排錯速查：內容是空的，結束原因是 length

| 問題 | 說明 |
| --- | --- |
| **現象** | API 回傳成功（200），但內容是空字串或只有半句，結束原因顯示 `length` |
| **原因** | 模型在寫完之前就碰到 `max_tokens` 上限被截斷。內容完全空白時，常見原因是：上限設得太小；或模型有「先思考再回答」的機制，思考過程先把額度用光，正式回答還沒開始就停了；也可能是輸入太長，留給輸出的空間不夠（實際計算方式依服務商而異，**需自行查證**） |
| **怎麼處理** | (1) 先調高 `max_tokens`，例如加倍再試一次；(2) 縮短輸入，或把大量資料分批送；(3) 在提示詞裡要求「300 字以內」「只列 3 點」；(4) 如果模型有思考強度設定，調低思考強度；(5) 程式一定要檢查結束原因，不要把空白或被截斷的結果當成成功 |
| **為什麼中文要開更大** | 模型是用 token 計算長度，而不是用「字」。英文常常一個單字是一個 token，中文則常常**一個字就要一個以上的 token**，所以同樣的上限，中文能寫出的內容比英文少很多。用英文經驗設定的上限，換成中文很容易被截斷；中文輸出建議預留更大的上限，並用實際資料測一次（各模型的換算比例不同，**需自行查證**） |

## 四、金鑰安全檢查表

- [ ] 程式碼、試算表儲存格、文件裡**都沒有出現金鑰本體**，只用指令碼屬性讀取。
- [ ] 金鑰**沒有貼到聊天室、Email、截圖或公開的 GitHub**；分享程式前搜尋一次，確認找不到金鑰。
- [ ] 程式的錯誤訊息與紀錄**不會印出金鑰**（例如不把 headers 整段寫進 Logger）。
- [ ] 在服務商後台**設定用量上限或預算提醒**，避免程式出錯一直重複呼叫，產生大量費用。
- [ ] 每一個專案用**獨立的金鑰**，不要全部共用；不用時就刪除或停用。
- [ ] 一旦懷疑外洩，**立刻到服務商後台撤銷金鑰、重新產生**，並檢查近期用量是否有異常。

---

> **這份草稿從未實際執行，欄位與端點須人工驗證。**請照服務商官方文件確認：請求網址、驗證標頭格式、`max_tokens` 等參數名稱、回傳結果與結束原因的欄位名稱（不同服務商可能不叫 `choices`、`finish_reason`），以及結束原因可能的值。
