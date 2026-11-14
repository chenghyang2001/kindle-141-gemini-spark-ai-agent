# 進階：後端方案選擇

預設使用純前端 + students.js，但有些情境需要後端：

## 何時需要後端？

| 情境 | 是否需要後端 |
|------|------|
| 名單包含成績、學號等敏感資料 | ✅ 需要 |
| 學生人數 > 5000 名（前端 JSON 太大） | ✅ 需要 |
| 要追蹤誰下載過、何時下載 | ✅ 需要 |
| 證書有真正的「驗證查詢」（輸入編號驗真） | ✅ 需要 |
| 一般教育場域、500-2000 名以內 | ❌ 不需要 |

## 方案 A：Google Apps Script（最簡單）

**優點：** 學生名單就在 Google Sheet，新增直接改 Sheet
**缺點：** 有配額限制、回應較慢（1-3 秒）

```javascript
// Apps Script Web App
function doPost(e) {
  const { name, email } = JSON.parse(e.postData.contents);
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const nameCol = headers.indexOf("姓名");
  const emailCol = headers.indexOf("Email");
  const agreeCol = headers.indexOf("同意聲明");

  const match = data.slice(1).find(row =>
    row[emailCol].toLowerCase() === email.toLowerCase() &&
    row[nameCol].trim() === name.trim() &&
    !row[agreeCol].includes("不同意")
  );

  return ContentService.createTextOutput(JSON.stringify({
    found: !!match,
    student: match ? { name: match[nameCol], school: match[2] } : null
  })).setMimeType(ContentService.MimeType.JSON);
}
```

部署為 Web App → 取得 URL → 前端 fetch 此 URL。

## 方案 B：Cloudflare Workers + KV

**優點：** 全球邊緣節點、免費額度大、毫秒級回應
**缺點：** 要學 Workers KV、需要 Cloudflare 帳號

```javascript
// worker.js
export default {
  async fetch(request, env) {
    const { name, email } = await request.json();
    const student = await env.STUDENTS_KV.get(email.toLowerCase(), "json");
    if (!student || student.name !== name) {
      return Response.json({ found: false });
    }
    return Response.json({ found: true, student });
  }
};
```

學生資料以 `email → JSON` 形式存入 KV。

## 方案 C：Supabase + RLS

**優點：** 真正資料庫、可做 admin 後台、有 auth
**缺點：** 重型方案，學生人數 < 1000 不划算

詳見 `supabase-fullstack` SKILL。

## 方案 D：Firebase Firestore

跟 Supabase 類似，但 Google 生態系。詳見 `firebase-firestore-basics` SKILL。

---

## 推薦決策

```
名單 < 200 人 + 不敏感       → 純前端 (預設)
名單 200-2000 人 + 不敏感   → 純前端 (預設)
名單 > 2000 人 或要追蹤    → Google Apps Script
有 admin 管理需求           → Supabase / Firebase
全球用戶 + 高流量            → Cloudflare Workers
```

教育場域 90% 用純前端就夠。
