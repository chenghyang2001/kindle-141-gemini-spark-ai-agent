# 原廠 25 支範例目錄（UltiRobot V9）

來源：`參考資料/OTTO機器人/原廠資料/Code/`（基本款 19 支）＋ `otto-plus/Codes/`（PLUS 6 支）。
用 `otto_ctl.py flash-example <名稱>` 一句話燒進真機，`build-example <名稱>` 只編譯驗證。

## 基本款（Code/，用內建 Otto9＋Servo 即可編譯）

| 名稱 | 資料夾 | 用途 |
|------|--------|------|
| allmoves | Otto_allmoves_V9 | 依序展示全部內建動作，最佳「動作總覽」demo |
| avoid | Otto_avoid_V9 | 超音波自動避障（前方有障礙就轉向） |
| distance | Otto_distance_V9 | 依距離做不同反應，測距示範 |
| follow | Otto_follow_V9 | 跟隨前方物體 |
| run | Otto_run_V9 | 快走／跑步 |
| happydance | Otto_Happydance_V9 | 開心跳舞 |
| jingle | Otto_jingle_V9 | 音樂鈴聲 |
| mario | Otto_MarioBros_V9 | 瑪利歐主題曲＋動作 |
| birthday | Otto_happybirthday_V9 | 生日快樂歌（慶生神器） |
| singleladies | Otto_singleladies_V9 | Single Ladies 舞 |
| smoothcriminal | Otto_smoothcriminal_V9 | Smooth Criminal 舞 |
| sw | Otto_SW_V9 | 星際大戰主題 |
| retrieve | Otto_retrieve_V9 | 撿東西／找回 |
| alarm | Otto_Alarm_V9 | 鬧鐘 |
| footalign | Otto_Footalign_V9 | **腳掌對齊**（組裝歸零，裝腳前先燒這支） |
| calib | Otto_Calibration_V9 | 四馬達校正 |
| calibeasy | Otto_Calibrationeasy_V9 | 簡易校正 |
| calibserial | Otto_Calibrationserial_V9 | 序列埠即時校正（配 CH16 微調） |
| remote | Otto_Mblock_Scratch_Serial_V9 | **序列遙控韌體**，就是 `flash-remote` 燒的那支 |

## PLUS 款（otto-plus/Codes/，⚠️ 需額外模組/函式庫，未必用內建庫編得過）

| 名稱 | 資料夾 | 用途 |
|------|--------|------|
| clapdance | OttoPLUS_clapdance_V9 | 拍手觸發跳舞 |
| clapwalk | OttoPLUS_clapwalk_V9 | 拍手走路 |
| guardian | OttoPLUS_Guardian_V9 | 守衛模式 |
| stopgo | OttoPLUS_stopgo_V9 | 走走停停 |
| touchultra | OttoPLUS_touchultrasound_V9 | 觸碰＋超音波 |
| appsound | OttoAPP_sound_V9 | App 聲音 |

> PLUS 支若 `build-example` 報缺函式庫，屬正常（那些是加購模組）。基本款 OTTO 用不到，別燒。

## AI 改寫建議
這些是「現成積木」。學員要新動作時，AI 可以：
1. 讀某支原廠範例當骨架（例：`allmoves` 學動作 API、`avoid` 學 if/超音波）。
2. 保留原廠 `#include <Otto9.h>` ＋ 9 參數 `Otto.init(2,3,4,5,true,A6,13,8,9)` 不動。
3. 只改 `loop()` 裡的動作組合 → `build` 驗證 → `flash` 上真機。
