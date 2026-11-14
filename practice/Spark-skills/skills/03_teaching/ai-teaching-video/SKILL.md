---
name: ai-teaching-video
description: AI 教學影片自動生成器 — 從「文字主題/腳本」全自動產出完整 MP4 教學影片，無需任何原始素材。支援快速模式（HTML→Chrome→ffmpeg）與專業模式（Remotion 4K 渲染）。內建字幕、BGM、多 TTS 引擎、多平台比例。觸發：生成教學影片、從主題做影片、自動生成教學影片、教學影片生成、做教學影片、AI 教學影片、teaching video、video podcast、課程影片製作。✅ 適用：完整教學長片（≥1 分鐘）、含字幕/旁白/BGM、課程影片、podcast 影片。❌ 不適用：短素材影片（→ ai-media-generator）、HTML+GSAP 動態字卡片頭（→ hyperframes）、既有素材剪輯（→ video-use）、兩人對話影片（→ ai-dialogue-video）、Avatar 主講影片（→ heygen-avatar-flow）。
triggers:
  - 生成教學影片
  - 從主題做影片
  - 自動生成教學影片
  - 教學影片生成
  - 做教學影片
  - AI 教學影片
  - teaching video
  - video podcast
  - 課程影片製作
  - 教學影片腳本
author: 阿亮老師・3A科技研究社
version: 2.0.0
---

# AI 教學影片自動生成器 v2

> 從一個教學主題，全自動產出可上傳的 MP4 教學影片。
> 支援 **快速模式** 與 **專業模式** 雙軌並行。

## 環境檢查

使用前請先執行環境檢查，確認所有工具是否就緒：

```bash
python "C:/Users/user/.claude/skills/ai-teaching-video/scripts/env_check.py"
```

JSON 格式輸出：

```bash
python "C:/Users/user/.claude/skills/ai-teaching-video/scripts/env_check.py" --json
```

---

## 雙模式架構

### 快速模式 (Quick Mode)

> **無需 Node.js**，現有環境即可運作。

```
主題 → 腳本 JSON → HTML 投影片 + Chrome 截圖 → TTS 語音 → ffmpeg 合成 → MP4
```

**適用場景：** 快速產出、環境受限、不需要動畫效果

**需求：** Python 3.8+、Chrome、ffmpeg、edge-tts

### 專業模式 (Pro Mode)

> 基於 **Remotion**（React）的 4K 影片渲染，支援動畫、轉場效果。

```
主題 → 腳本 JSON → TTS 語音 → Remotion 合成（含動畫） → 4K MP4
```

**適用場景：** 高品質 4K 影片、需要動畫轉場、專業發布

**額外需求：** Node.js ≥18、Remotion

### 自動選擇邏輯

Claude 會依以下規則自動選擇模式：

1. 使用者明確指定 `--mode quick` 或 `--mode pro` → 採用指定模式
2. 偵測到 Node.js ≥18 且 Remotion 已安裝 → **專業模式**
3. 其他情況 → **快速模式**

---

## 先決條件

### 快速模式（必要）

| 工具 | 安裝方式 | 用途 |
|------|----------|------|
| Python 3.8+ | 系統內建或 python.org | 執行腳本 |
| edge-tts | `pip install edge-tts` | 免費 TTS 語音合成 |
| ffmpeg | `winget install ffmpeg` 或 [官網](https://ffmpeg.org/) | 影片合成 |
| Chrome | 已安裝 Google Chrome | 投影片截圖（headless 模式） |

### 專業模式（額外）

| 工具 | 安裝方式 | 用途 |
|------|----------|------|
| Node.js ≥18 | [nodejs.org](https://nodejs.org/) 或 `winget install OpenJS.NodeJS.LTS` | Remotion 渲染 |
| Remotion | 執行 `setup_remotion.py`（見下方） | React 影片合成 |

### 可選 TTS 引擎

| 引擎 | 環境變數 | 說明 |
|------|----------|------|
| edge-tts | 無需設定 | 免費，預設引擎 |
| Azure Speech | `AZURE_SPEECH_KEY`、`AZURE_SPEECH_REGION` | 高品質商業語音 |
| OpenAI TTS | `OPENAI_API_KEY` | GPT-4o 級別語音 |

### Remotion 專業模式初始化

```bash
python "C:/Users/user/.claude/skills/ai-teaching-video/scripts/setup_remotion.py"
```

---

## 腳本格式

Claude 根據使用者提供的教學主題，生成結構化 JSON 腳本：

```json
{
  "title": "認識生成式 AI",
  "author": "阿亮老師",
  "sections": [
    {
      "id": 1,
      "slide_title": "什麼是生成式 AI？",
      "slide_content": "生成式 AI 能夠創造全新的文字、圖片、音樂與程式碼",
      "narration": "大家好，今天我們來認識生成式 AI...",
      "notes": "開場，建立基本概念"
    }
  ],
  "description": "本影片介紹生成式 AI 的基本概念...",
  "tags": ["AI", "生成式AI", "教學", "人工智慧"]
}
```

**腳本規範：**
- 每個 section 對應一張投影片 + 一段語音
- `slide_title`：投影片標題（簡短有力）
- `slide_content`：投影片內容（關鍵重點，不超過 3 行）
- `narration`：旁白文字（口語化，60-120 字，約 15-30 秒）
- 建議 8-15 個 sections，總長 3-8 分鐘
- 第一張為標題頁，最後一張為總結頁

---

## 完整流水線（一鍵執行）

```bash
python "C:/Users/user/.claude/skills/ai-teaching-video/scripts/full_pipeline.py" \
  --input script.json \
  --output-dir output/ \
  --subtitles \
  --bgm auto \
  --platform youtube
```

### 新增參數一覽

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `--mode quick\|pro` | 渲染模式 | 自動偵測 |
| `--subtitles` / `--no-subtitles` | 字幕開關 | 開啟 |
| `--bgm PATH\|auto` | 背景音樂 | 無 |
| `--engine edge\|azure\|openai` | TTS 引擎 | edge |
| `--ratio 16:9\|9:16\|1:1\|4:3` | 畫面比例 | 16:9 |
| `--resolution 1080p\|4k` | 解析度 | 1080p |
| `--platform youtube\|bilibili\|douyin\|instagram` | 目標平台 | youtube |
| `--theme cinematic\|dark\|light\|nature` | 投影片主題 | cinematic |
| `--voice` | TTS 聲音 | zh-TW-HsiaoChenNeural |
| `--rate` | 語速調整 | +0% |

### 平台預設值

| 平台 | 比例 | 解析度 | 說明 |
|------|------|--------|------|
| youtube | 16:9 | 1080p | YouTube 標準橫式 |
| bilibili | 16:9 | 1080p | Bilibili 知識影片 |
| douyin | 9:16 | 1080p | 抖音/TikTok/Shorts 直式 |
| instagram | 1:1 | 1080p | Instagram 正方形 |

---

## 個別腳本使用

### 投影片生成（支援多比例、4K）

```bash
python scripts/generate_slides.py --input script.json --output-dir slides/ \
  --ratio 16:9 --resolution 1080p --theme cinematic
```

### TTS 語音合成（多引擎）

```bash
# edge-tts（免費，預設）
python scripts/generate_tts.py --input script.json --output-dir audio/

# Azure Speech
python scripts/generate_tts.py --input script.json --output-dir audio/ --engine azure

# OpenAI TTS
python scripts/generate_tts.py --input script.json --output-dir audio/ --engine openai
```

### 字幕生成

```bash
python scripts/generate_subtitles.py --input script.json --audio-dir audio/ --output subs.srt
```

### BGM 混音

```bash
python scripts/add_bgm.py --input video.mp4 --bgm bgm.mp3 --output final.mp4
# 或使用內建 BGM
python scripts/add_bgm.py --input video.mp4 --bgm auto --output final.mp4
```

### Remotion 渲染（專業模式）

```bash
python scripts/render_remotion.py --input script.json --audio-dir audio/ \
  --output output.mp4 --resolution 4k
```

### Remotion 環境設定

```bash
python scripts/setup_remotion.py
```

---

## 完整工作流程（Claude 操作步驟）

當使用者要求生成教學影片時，依照以下步驟：

1. **確認主題與需求**
   - 詢問教學主題、目標對象、預計長度
   - 確認語音偏好（男聲/女聲）
   - 確認目標平台（YouTube/Bilibili/抖音/Instagram）

2. **生成腳本 JSON**
   - 根據主題生成結構化腳本
   - 將 JSON 寫入工作目錄的 `script.json`

3. **檢查環境**
   ```bash
   python "C:/Users/user/.claude/skills/ai-teaching-video/scripts/env_check.py" --json
   ```

4. **執行完整流水線**
   ```bash
   python "C:/Users/user/.claude/skills/ai-teaching-video/scripts/full_pipeline.py" \
     --input script.json \
     --output-dir output/ \
     --subtitles \
     --bgm auto \
     --platform youtube
   ```

5. **回報結果**
   - 顯示產出檔案清單
   - 提供 YouTube 描述與標籤
   - 告知影片路徑
   - 提示可使用 `yt-auto-publisher` 技能上傳

---

## 腳本位置

```
C:/Users/user/.claude/skills/ai-teaching-video/
├── SKILL.md                          # 本說明檔
└── scripts/
    ├── env_check.py                  # 環境檢查（含 Node.js / Remotion 狀態）
    ├── generate_slides.py            # 投影片生成（多比例 + 4K）
    ├── generate_tts.py               # TTS 語音合成（edge / azure / openai）
    ├── assemble_video.py             # ffmpeg 影片合成（快速模式）
    ├── generate_subtitles.py         # SRT 字幕生成
    ├── add_bgm.py                    # BGM 背景音樂混音
    ├── setup_remotion.py             # Remotion 環境初始化（專業模式）
    ├── render_remotion.py            # Remotion 4K 渲染（專業模式）
    └── full_pipeline.py              # 一鍵執行完整流水線
```

## 與 yt-auto-publisher 整合

影片生成完成後，可使用 `yt-auto-publisher` 技能自動上傳：

```
完成影片生成後，請幫我上傳到 YouTube
```

Claude 會自動讀取 `description.txt` 和 `tags.txt` 用於上傳設定。

## 注意事項

- Chrome 路徑預設自動偵測，如需自訂可用 `--chrome` 參數
- edge-tts 需要網路連線（使用微軟 Edge 線上 TTS 服務）
- ffmpeg 必須在 PATH 中可用
- 專業模式需要先執行 `setup_remotion.py` 初始化
- 建議先用短腳本（2-3 張投影片）測試流程是否正常
- 4K 渲染需要較多記憶體與時間，建議先用 1080p 預覽
