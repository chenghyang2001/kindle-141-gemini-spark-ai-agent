---
name: otto-skill
description: 用 AI 透過 arduino-cli 控管 OTTO 機器人（UltiRobot V9 / Arduino Nano + Otto9 函式庫）。涵蓋「偵測連接埠 → 編譯 .ino → 燒錄真機」的韌體工作流，以及燒一支常駐韌體後用序列指令「即時遙控」OTTO 做動作（走路/轉彎/跳/唱歌/測距）。觸發詞：控制 OTTO、控管 OTTO、上傳 OTTO、燒錄 OTTO、編譯 ino、arduino-cli、遙控機器人、OTTO 序列指令、flash OTTO、把程式燒進機器人。
---

# otto-skill — 用 AI 控管 OTTO 機器人

OTTO 的主控是 **Arduino Nano（CH340 晶片）**，跑 **Otto9** 函式庫。AI 不能「直接」動馬達，控管 OTTO 一律透過 `arduino-cli`（官方命令列工具，本專案已內建 `_tools/arduino-cli.exe` 1.5.1）。

有兩種控管層次，先判斷使用者要哪種：

| 層次 | 做法 | 何時用 |
|------|------|--------|
| **A. 韌體工作流** | AI 改 `.ino` → 編譯 → 燒錄 → OTTO 執行新程式 | 大多數情況、課程燒錄、換動作程式 |
| **B. 即時遙控** | 先燒一次 `firmware/OttoRemote` 常駐韌體 → 之後往序列埠送指令，OTTO 即時反應，不用重燒 | 想「一句話讓它馬上走一步」、示範、除錯馬達 |

## 前置檢查（每次開工先做）

1. **確認硬體接著**：`python scripts/otto_ctl.py detect`
   - 列不出任何 serial 埠 → OTTO 沒插、或 CH340 驅動沒裝（見 `references/troubleshooting.md`）。
   - 列出多個埠且都「未知」是正常的（CH340 不回報板型），選 OTTO 那個 COM 號。
2. **找得到 arduino-cli**：腳本會自動往上層找專案的 `_tools/arduino-cli.exe`；找不到就退回 PATH 的 `arduino-cli`。可用 `--project <OTTO專案路徑>` 指定。
3. **沒有真機時**：只能做到 `build`（編譯驗證）。`flash`/`remote` 需要接著 OTTO 的電腦才能跑，本機無硬體時明講、不要假裝燒成功。

## 工作流 A — 編譯 / 燒錄

```bash
# 只編譯（驗證程式能過，沒硬體也能做）
python scripts/otto_ctl.py build <某支.ino 或 sketch 資料夾>

# 編譯 + 燒錄真機（自動抓唯一的 COM 埠；多個埠時用 -p 指定）
python scripts/otto_ctl.py flash <某支.ino> -p COM3

# 新版 bootloader 的板子（115200）加 --new-bootloader；預設走舊版 atmega328old（57600）
python scripts/otto_ctl.py flash <某支.ino> -p COM3 --new-bootloader
```

固定參數已包在腳本裡：FQBN `arduino:avr:nano:cpu=atmega328old`、`--libraries` 指向專案 `_tools/libraries`（含 Otto9）。**單一 .ino 檔會自動放進正確命名的暫存 sketch 資料夾**再編譯，不用手動整理。

## 工作流 B — 即時遙控

遙控韌體 `firmware/OttoRemote` **就是原廠 `Otto_Mblock_Scratch_Serial_V9`**（沒自己發明協定，和 mBlock/Scratch 相容），在 115200 監聽序列埠。

一次性：把常駐遙控韌體燒進 OTTO（之後不用再燒）：
```bash
python scripts/otto_ctl.py flash-remote -p COM3
```
之後就能即時下指令（需要 `pip install pyserial`）。**支援白話別名**，腳本自動翻成原廠協定：
```bash
python scripts/otto_ctl.py remote "forward" -p COM3   # 往前走（＝送 M 1 1000 15）
python scripts/otto_ctl.py remote "dist" -p COM3      # 讀距離（＝送 D，回 &&D 25%%）
python scripts/otto_ctl.py remote "gesture 11" -p COM3  # 揮手打招呼
python scripts/otto_ctl.py console -p COM3            # 互動主控台，一行一條
```
白話別名（forward/back/left/right/jump/swing/sing/gesture/dist/stop…）與原生協定（`M/H/K/D`）對照見 `references/serial-protocol.md`。

## 原廠範例庫 — 一鍵燒現成動作

`參考資料/` 內有原廠 **25 支 .ino**（跳舞、避障、唱歌、校正…），可直接調用：
```bash
python scripts/otto_ctl.py examples                    # 看全部 25 支清單
python scripts/otto_ctl.py flash-example happydance -p COM3   # 燒「開心跳舞」進真機
python scripts/otto_ctl.py build-example avoid         # 只編譯驗證「避障」
```
清單與 AI 改寫建議見 `references/original-examples.md`。要新動作時，讓 AI 拿某支當骨架、只改 `loop()`，比從零寫穩。

## 重要規則（本專案鐵律）

- **Otto9 函式庫勿改**：`_tools/libraries/Otto9` 是原廠 V9，不要動。
- **init 固定 9 參數寫法**：`Otto.init(2,3,4,5,true,A6,13,8,9);`（YL/YR/RL/RR、噪音 A6、蜂鳴器 13、Trig 8、Echo 9）。
- **改了課程生成器要重編 hex**：那是另一條線（`_tools/build_hex.py`），本技能不碰。
- 燒錄失敗時的排查順序：序列埠被占用 → 驅動 → bootloader 波特率（57600 ↔ 115200 互換）。詳見 `references/troubleshooting.md`。

## 檔案結構

```
otto-skill/
├── SKILL.md                       本檔
├── scripts/otto_ctl.py            arduino-cli 包裝：detect/build/flash/flash-remote/remote/console/examples/flash-example
├── firmware/OttoRemote/
│   └── OttoRemote.ino             常駐序列遙控韌體（＝原廠 mBlock 序列版）
└── references/
    ├── serial-protocol.md         即時遙控指令表（白話別名 ↔ M/H/K/D 協定）
    ├── original-examples.md       原廠 25 支範例目錄＋改寫建議
    └── troubleshooting.md         驅動/連接埠/燒錄/馬達 踩雷筆記
```
