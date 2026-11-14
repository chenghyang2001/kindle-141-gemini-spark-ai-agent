---
name: ai-media-generator
description: "AI 生圖與生短影片，按量計費。生圖用 FLUX 或 Ideogram；生影片用 Kling、Hailuo、Wan（省錢）或 FAL Seedance 2.0（電影感、原生音頻、多鏡頭）。觸發：生圖、畫一張、text to image、生影片、text to video、做動畫、Seedance、Dreamina、FAL、高品質或電影感影片。適用短影片（10 秒內）單鏡頭素材級。完整教學片走 ai-teaching-video，動態字卡走 hyperframes，既有素材剪輯走 video-use。生圖需 FAL_KEY，未設走 imagegen（免費）。"
author: 阿亮老師・3A科技研究社
version: 2.1.0
tags: [生圖, 生影片, AI繪圖, FLUX, Kling, Hailuo, Dreamina, Seedance, FAL, 圖片生成, 影片生成, 原生音頻]
---

# AI 多媒體生成器

> 按量計費，用多少付多少。生圖 $0.03/張，生影片 $0.07/秒。

## 環境需求

- 環境變數 `FAL_KEY` 已設定（Windows 使用者環境變數）
- curl（已內建）

## 生圖（Text-to-Image）

### 可用模型

| 模型 | Endpoint | 價格 | 適用場景 |
|:---|:---|:---:|:---|
| FLUX.1 Dev | `fal-ai/flux/dev` | ~$0.025/張 | 通用、高品質（推薦） |
| FLUX.1 Pro | `fal-ai/flux-pro/v1.1` | ~$0.05/張 | 最高品質 |
| FLUX.1 Schnell | `fal-ai/flux/schnell` | ~$0.003/張 | 快速草稿、最便宜 |
| Ideogram V3 | `fal-ai/ideogram/v3` | $0.03~0.09/張 | 文字渲染強 |
| Recraft V3 | `fal-ai/recraft-v3` | ~$0.04/張 | 設計風格 |

### 呼叫方式（同步）

```bash
curl -s -X POST "https://fal.run/{MODEL_ENDPOINT}" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "你的提示詞（英文效果最好）",
    "image_size": "landscape_16_9",
    "num_images": 1
  }'
```

### image_size 選項

| 值 | 尺寸 |
|:---|:---|
| `square` | 1024x1024 |
| `square_hd` | 1536x1536 |
| `landscape_4_3` | 1024x768 |
| `landscape_16_9` | 1024x576 |
| `portrait_4_3` | 768x1024 |
| `portrait_16_9` | 576x1024 |

### 回應格式

```json
{
  "images": [
    {
      "url": "https://v3b.fal.media/files/...",
      "width": 1024,
      "height": 576,
      "content_type": "image/jpeg"
    }
  ],
  "seed": 12345,
  "prompt": "..."
}
```

### 圖片下載

```bash
curl -s -o "output.jpg" "{IMAGE_URL}"
```

## 生影片（Text-to-Video）

### 可用模型

#### 快速省錢（curl 同步呼叫）

| 模型 | Endpoint | 價格 | 說明 |
|:---|:---|:---:|:---|
| Kling V2.1 Master | `fal-ai/kling-video/v2.1/master/text-to-video` | ~$0.07/秒 | 人臉表情最強 |
| Hailuo 2.3 | `fal-ai/minimax-video/hailuo-ai-video-01-director/text-to-video` | ~$0.28/6秒 | 電影感 |
| Wan 2.1 | `fal-ai/wan/v2.1/text-to-video` | ~$0.10/秒 | 便宜 |

#### 高品質電影感 — Seedance 2.0

| 平台 | 模型 | 解析度 | 價格 | 特色 |
|:---|:---|:---:|:---:|:---|
| **FAL**（推薦） | Seedance 2.0 標準 | 720p | ~$0.30/秒 | 原生音頻、多鏡頭、鏡頭控制，用 FAL_KEY |
| **FAL**（推薦） | Seedance 2.0 標準 | 1080p | ~$0.60/秒 | 頂級畫質 |
| Dreamina | Seedance 2.0 標準 | 720p | ~$0.30/秒 | 需另外申請 |
| Dreamina | Seedance 2.0 Fast | 720p | ~$0.15/秒 | 快速草稿 |

> 詳細定價與省錢技巧見 `references/pricing.md`  
> Prompt 寫作指南（cinematic 關鍵字）見 `references/prompt-guide.md`

### 呼叫方式 A：curl 同步（Kling / Hailuo / Wan）

```bash
curl -s -X POST "https://fal.run/{MODEL_ENDPOINT}" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "描述影片內容（英文）",
    "duration": "5",
    "aspect_ratio": "16:9"
  }'
```

### 呼叫方式 B：FAL Seedance 2.0（推薦，用既有 FAL_KEY）

```bash
# 提交任務（非同步）
curl -s -X POST "https://queue.fal.run/fal-ai/bytedance/seedance-2.0/text-to-video" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "完整英文提示詞",
    "duration": 5,
    "resolution": "720p",
    "aspect_ratio": "16:9"
  }'

# 輪詢結果（用回傳的 request_id）
curl -s "https://queue.fal.run/fal-ai/bytedance/seedance-2.0/text-to-video/requests/{REQUEST_ID}" \
  -H "Authorization: Key ${FAL_KEY}"
```

> ⚠️ 使用前告知費用（720p ~$0.30/秒），確認後再執行。

### 呼叫方式 C：Python 腳本（Dreamina Seedance 2.0，備用）

```bash
python scripts/generate_video.py \
  --prompt "完整英文提示詞" \
  --duration 5 \
  --resolution 720p \
  --aspect_ratio 16:9 \
  --model seedance-2.0 \
  --output ./videos/
```

> ⚠️ Dreamina 需另外申請帳號，一般優先用方式 B（FAL）。

### 回應格式

```json
{
  "video": {
    "url": "https://v3b.fal.media/files/...",
    "content_type": "video/mp4"
  }
}
```

### 影片下載

```bash
curl -s -o "output.mp4" "{VIDEO_URL}"
```

## 圖片轉影片（Image-to-Video）

```bash
curl -s -X POST "https://fal.run/fal-ai/kling-video/v2.1/master/image-to-video" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "the cat starts walking",
    "image_url": "https://...",
    "duration": "5",
    "aspect_ratio": "16:9"
  }'
```

## 讀圖 / OCR

不需要額外 API。使用以下方式：
1. **Claude Code 內建**：直接在對話中提供圖片路徑，Claude 可以直接讀取和分析圖片
2. **Gemini Vision**：使用者已有 Gemini API Key，可透過 Gemini 的多模態功能免費讀圖

## 工作流程

### 使用者說「生圖」時：
1. 確認 `FAL_KEY` 環境變數存在
2. 將中文提示詞翻譯為英文（效果更好）
3. 選擇適合的模型（預設 FLUX.1 Dev）
4. 用 curl 同步呼叫 `https://fal.run/{endpoint}`
5. 從回應取得圖片 URL
6. 用 curl 下載到本地
7. 用 Read 工具展示圖片給使用者

### 使用者說「生影片」時：
1. 確認 `FAL_KEY` 環境變數存在
2. 將中文提示詞翻譯為英文
3. 提醒使用者影片會花費 $0.07~0.28（確認後再執行）
4. 用 curl 同步呼叫影片端點（可能需要較長等待時間）
5. 下載影片到本地

## 🖥️ 地端生影音：MiniMax-H3（ComfyUI，免 FAL 費）

> 使用者本機（ComfyUI）裝了 **MiniMax-H3** 模型，能**地端生「帶語音的直式影片」**，跑本機 GPU、不花 FAL API 錢。特別適合 **AI 短劇**：用「同一張參考圖」鎖角色，每顆鏡頭角色不換臉。

**何時用地端 H3（vs FAL）：**
- ✅ 要省錢、量大、做短劇連載、要角色一致性（參考圖鎖臉）、要原生語音 → **地端 H3**
- ✅ 要最高畫質單張、快速一次性、本機沒 GPU → 走 FAL（上面章節）

**呼叫方式：**
1. 先確認 ComfyUI 有啟動（`http://127.0.0.1:8000`），且 MiniMax-H3 模型已載入
2. 用 `scripts/minimax_h3_local.py`：

```bash
# 參考圖生影片+語音（短劇最常用，turbo 加速）
python scripts/minimax_h3_local.py \
  --prompt "（用下方提示詞知識庫寫好的英文/中文視覺提示詞）" \
  --ref 角色參考圖.png \
  --out 第1集_鏡01.mp4 \
  --workflow r2v_voice_turbo

# 可選：--audio 語音檔.wav（配旁白/對白）  --width 576 --height 768（直式9:16）
```

**可用 workflow（範本在 ComfyUI 根目錄）：**
| workflow | 用途 |
|---|---|
| `r2v_voice_turbo` | 參考圖→影片+語音（加速，**短劇推薦**）|
| `r2v_voice` | 參考圖→影片+語音（品質）|
| `i2v_teacher` | 圖生影片 |

**短劇角色一致性鐵則**：同一角色的每顆鏡頭，`--ref` 都用**同一張參考圖**；提示詞只描述動作/表情/鏡位，不重新描述長相。搭配 `ai-short-drama` 的 entity registry（角色固定 ID）效果最好。

**環境變數**（如路徑不同可覆蓋）：`COMFYUI_URL`（預設 http://127.0.0.1:8000）、`COMFYUI_DIR`（預設 C:\Users\user\Documents\ComfyUI）。

## 進階提示詞知識庫（references/）

> 本 skill 用 FAL API 生成，但「提示詞寫得好不好」決定成品品質。要寫高品質提示詞、模擬特定風格、做角色一致性或多鏡頭時，**先查對應知識檔再寫 prompt**，不要憑空亂寫。各平台吃的 token 不同，切勿共用同一套提示詞。

**依需求查表（按需 lazy load，不要一次全讀）：**

| 需求 | 讀哪個 reference |
|---|---|
| 不知道用哪個模型／平台 | `model-picker.md`、`selector.md` |
| 各模型簽名 token、長度甜蜜點、禁忌詞 | `community-prompt-patterns.md`、`proven-prompts.md`、`prompt-craft-engine.md` |
| 先想清楚概念再寫詞 | `concept-first-prompting.md` |
| 鏡頭語言、運鏡 | `camera-language.md` |
| 電影感、打光、DP 風格 | `cinematic-direction.md`、`aesthetic-grade.md` |
| 模擬某導演／品牌風格（⚠️ Flux/Nano 會洗掉導演名）| `director-style-library.md` |
| 商業／廣告／產品／建築片 | `commercial-direction.md` |
| **圖生影片、角色一致性、首鏡鎖定** | `image-to-video-workflow.md`、`seedance-longform-continuity.md` |
| 剪輯、轉場 | `editing-transitions.md` |
| 特效／VFX | `vfx-effects.md` |
| 聲音設計、配樂 | `sound-design.md` |
| 品質檢查、修瑕疵 | `quality-control.md`、`advanced-hd-reconstruct.md` |

**各平台專屬提示詞公式（用哪個平台就讀哪個）：**

| 平台 | reference |
|---|---|
| Seedance（含社群案例／垂直領域／長片連續性）| `seedance.md`、`seedance-2-5-community-playbook.md`、`seedance-domain-playbook.md`、`seedance-longform-continuity.md` |
| Kling | `kling.md` | 
| Midjourney | `midjourney.md` |
| Flux | `flux.md` |
| Runway | `runway.md` |
| Google Veo | `veo.md` |
| Ideogram | `ideogram.md` |
| Hailuo | `hailuo.md` |
| Seedream | `seedream.md` |
| Vidu | `vidu.md` |
| Sora | `sora.md`（⚠️ Sora 2 已停運，改推 Runway/Veo/Kling）|
| Stable Diffusion | `stable-diffusion.md` |
| Nano Banana（超短廣告 <30 token）| `nano-banana.md` |
| OiiOii、Gemini Omni | `oiioii.md`、`gemini-omni.md` |
| 多模型省成本招式 | `multimodel-video-cheatsheet.md` |
| Suno（音樂）| `suno.md` |

> 註：以上知識庫來自社群開源（Hao0321/ai-media-generator）整合。做 AI 短劇／連載時，故事層交給 `ai-short-drama` skill，本 skill 只負責逐鏡提示詞與 FAL 生成。

## 注意事項

- 提示詞用**英文**效果最好，中文會自動翻譯但品質可能下降
- 生影片比生圖貴很多，執行前先確認使用者意願
- 圖片 URL 是暫時的，務必下載到本地保存
- 帳戶餘額可在 https://fal.ai/dashboard 查看
