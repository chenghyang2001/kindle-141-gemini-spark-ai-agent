# -*- coding: utf-8 -*-
"""
otto_ctl.py — 用 arduino-cli 控管 OTTO 機器人（Arduino Nano + Otto9）
一支搞定：偵測連接埠 / 編譯 / 燒錄真機 / 燒常駐遙控韌體 / 即時送序列指令。

用法：
  python otto_ctl.py detect
  python otto_ctl.py build   <sketch.ino 或資料夾>
  python otto_ctl.py flash   <sketch.ino> [-p COM3] [--new-bootloader]
  python otto_ctl.py flash-remote [-p COM3] [--new-bootloader]
  python otto_ctl.py remote  "walk 4 1000 1" [-p COM3] [-b 9600]
  python otto_ctl.py console [-p COM3] [-b 9600]

備註：
  - arduino-cli 會自動往上層目錄找專案的 _tools/arduino-cli.exe；找不到就用 PATH 的 arduino-cli。
  - 可用 --project <OTTO 專案根> 明確指定專案位置。
  - remote / console 需要 pyserial：pip install pyserial
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

FQBN_OLD = "arduino:avr:nano:cpu=atmega328old"   # 舊 bootloader，57600（OTTO V9 預設）
FQBN_NEW = "arduino:avr:nano:cpu=atmega328"       # 新 bootloader，115200
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
REMOTE_FW = os.path.join(SKILL_ROOT, "firmware", "OttoRemote")


def find_project(start, explicit=None):
    """往上層找含 _tools/arduino-cli.exe 的 OTTO 專案根。"""
    if explicit:
        return os.path.abspath(explicit)
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, "_tools", "arduino-cli.exe")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def resolve_cli(project):
    if project:
        exe = os.path.join(project, "_tools", "arduino-cli.exe")
        if os.path.exists(exe):
            return exe
    found = shutil.which("arduino-cli") or shutil.which("arduino-cli.exe")
    if found:
        return found
    sys.exit("✗ 找不到 arduino-cli：專案 _tools/ 內沒有，PATH 也沒有。請用 --project 指定 OTTO 專案根。")


def resolve_libs(project):
    if project:
        libs = os.path.join(project, "_tools", "libraries")
        if os.path.isdir(libs):
            return libs
    return None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def cmd_detect(cli):
    r = run([cli, "board", "list", "--format", "json"])
    ports = []
    try:
        data = json.loads(r.stdout)
        entries = data.get("detected_ports", data if isinstance(data, list) else [])
        for e in entries:
            port = e.get("port", e)
            if port.get("protocol") == "serial" or str(port.get("address", "")).upper().startswith("COM"):
                ports.append(port.get("address"))
    except Exception:
        print(r.stdout or r.stderr)
    if ports:
        print("偵測到序列埠：")
        for p in ports:
            print("  •", p)
        print("\n（CH340 不回報板型，全部顯示未知是正常的；OTTO 通常是其中新出現的那個 COM 號）")
    else:
        print("✗ 沒偵測到任何序列埠。檢查：OTTO 是否插上、CH340 驅動是否安裝（見 troubleshooting.md）。")
    return ports


def auto_port(cli, given):
    if given:
        return given
    ports = cmd_detect(cli)
    if len(ports) == 1:
        print(f"→ 自動選用唯一連接埠 {ports[0]}")
        return ports[0]
    sys.exit("✗ 偵測到 0 或多個連接埠，請用 -p COMx 明確指定要燒哪一個。")


def prepare_sketch(path):
    """arduino-cli 需要 sketch 資料夾且內含同名 .ino。
    傳單一 .ino 檔時，自動複製到正確命名的暫存資料夾。回傳 (sketch_dir, cleanup_or_None)。"""
    path = os.path.abspath(path)
    if os.path.isdir(path):
        return path, None
    if path.lower().endswith(".ino"):
        stem = os.path.splitext(os.path.basename(path))[0]
        parent = os.path.dirname(path)
        if os.path.basename(parent) == stem:
            return parent, None
        tmp = tempfile.mkdtemp(prefix="otto_")
        sk = os.path.join(tmp, stem)
        os.makedirs(sk, exist_ok=True)
        shutil.copy(path, os.path.join(sk, stem + ".ino"))
        return sk, tmp
    sys.exit(f"✗ 不是 .ino 檔也不是 sketch 資料夾：{path}")


def do_compile(cli, libs, fqbn, sketch_dir):
    cmd = [cli, "compile", "--fqbn", fqbn]
    if libs:
        cmd += ["--libraries", libs]
    cmd += [sketch_dir]
    print(f"⚙  編譯（{fqbn}）…")
    r = run(cmd)
    if r.returncode != 0:
        print("✗ 編譯失敗：\n" + (r.stderr or r.stdout)[-2000:])
        return False
    for line in r.stdout.splitlines():
        if "bytes" in line.lower() or "Sketch uses" in line:
            print("  " + line.strip())
    print("✓ 編譯成功")
    return True


def do_upload(cli, fqbn, port, sketch_dir):
    print(f"🔌 燒錄到 {port} …")
    r = run([cli, "upload", "-p", port, "--fqbn", fqbn, sketch_dir])
    if r.returncode != 0:
        print("✗ 燒錄失敗：\n" + (r.stderr or r.stdout)[-2000:])
        print("  排查順序：序列埠被占用（關掉監看/Arduino IDE）→ 驅動 → 換 --new-bootloader 試 115200。")
        return False
    print("✓ 燒錄完成，OTTO 會重開機並執行新程式")
    return True


def cmd_build(cli, libs, fqbn, sketch):
    sk, tmp = prepare_sketch(sketch)
    try:
        ok = do_compile(cli, libs, fqbn, sk)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


def cmd_flash(cli, libs, fqbn, sketch, port):
    sk, tmp = prepare_sketch(sketch)
    try:
        if not do_compile(cli, libs, fqbn, sk):
            return 1
        if not do_upload(cli, fqbn, port, sk):
            return 1
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    return 0


# ============================================================
# 即時遙控（需要 pyserial；對應 firmware/OttoRemote = 原廠 mBlock 序列協定）
# 原廠協定：M 動作 時間 幅度 / H 手勢 / K 唱歌 / D 測距 / N 噪音 / B 電量 / S 停
# 回覆包在 &&…%%（&&A%%=收到、&&F%%=完成、&&D 25%%=距離 25cm）
# ============================================================

# 白話別名 → 動作編號（id, 預設時間 T, 預設幅度 size 或 None）
_MOVE = {
    "forward": (1, 1000, 15), "walk": (1, 1000, 15),
    "back": (2, 1000, 15), "backward": (2, 1000, 15),
    "left": (3, 1000, 15), "turnleft": (3, 1000, 15),
    "right": (4, 1000, 15), "turnright": (4, 1000, 15),
    "updown": (5, 1000, 30), "moonwalk": (6, 1000, 30), "moonwalkr": (7, 1000, 30),
    "swing": (8, 1000, 30), "crusaito": (9, 1000, 30),
    "jump": (11, 1000, None), "flapping": (12, 1000, 30),
    "tiptoe": (14, 1000, 30), "bend": (15, 500, None),
    "shakeleg": (17, 500, None), "jitter": (19, 500, 30), "ascturn": (20, 500, 15),
}


def translate(line):
    """把白話指令翻成原廠序列協定。已是協定格式（單字母開頭）就原樣送出。"""
    t = line.split()
    if not t:
        return None
    head = t[0]
    if len(head) == 1 and head.upper() in "SMHKTDGLCERNBI":
        return line.strip()                     # 原生協定直接放行
    k = head.lower()
    if k in ("stop", "home"):
        return "S"
    if k in ("dist", "distance"):
        return "D"
    if k == "noise":
        return "N"
    if k == "battery":
        return "B"
    if k == "sing":
        return "K " + (t[1] if len(t) > 1 else "8")
    if k == "gesture":
        return "H " + (t[1] if len(t) > 1 else "1")
    if k in _MOVE:
        mid, dT, dS = _MOVE[k]
        T = t[1] if len(t) > 1 else dT
        parts = ["M", str(mid), str(T)]
        if dS is not None:
            parts.append(str(t[2] if len(t) > 2 else dS))
        return " ".join(parts)
    return line.strip()                         # 不認得就照原樣送（讓韌體判斷）


def _serial(port, baud):
    try:
        import serial  # pyserial
    except ImportError:
        sys.exit("✗ 即時遙控需要 pyserial：請先執行  pip install pyserial")
    import time
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2.0)   # 等 Nano 重開機（DTR 觸發 reset）
    ser.reset_input_buffer()
    return ser


def _read_replies(ser, timeout=1.2):
    """讀取一段時間，抽出所有 &&…%% 內容，回傳有意義的酬載清單。"""
    import re
    import time
    buf, t0 = "", time.time()
    while time.time() - t0 < timeout:
        chunk = ser.read_all().decode("utf-8", "replace")
        if chunk:
            buf += chunk
            t0 = time.time() - (timeout - 0.35)   # 收到東西就縮短等待
        time.sleep(0.05)
    out = []
    for m in re.findall(r"&&(.*?)%%", buf, re.S):
        s = m.strip()
        if s in ("A", "F", ""):
            continue                              # 略過純 ack/finish
        out.append(s)
    return out


def cmd_remote(port, baud, line):
    proto = translate(line)
    ser = _serial(port, baud)
    print(f"→ {line.strip()}   （協定：{proto}）")
    ser.write((proto + "\r\n").encode("ascii", "ignore"))
    for payload in _read_replies(ser):
        print("  ⟵", payload)
    ser.close()
    return 0


def cmd_console(port, baud):
    ser = _serial(port, baud)
    print(f"OTTO 主控台（{port} @ {baud}）　輸入指令按 Enter，quit 離開")
    print("白話：forward / back / left / right / jump / swing / dist / sing 8 / gesture 1 / stop")
    print("原生協定也可：M 1 1000 15 ｜ K 8 ｜ D")
    try:
        while True:
            line = input("otto> ").strip()
            if line.lower() in ("quit", "exit", "q"):
                break
            if not line:
                continue
            proto = translate(line)
            ser.write((proto + "\r\n").encode("ascii", "ignore"))
            for payload in _read_replies(ser, timeout=0.8):
                print("  ⟵", payload)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        ser.close()
    print("\n再見")
    return 0


# ============================================================
# 原廠範例庫：一句話把 參考資料/ 內的 25 支原廠 .ino 編譯／燒進真機
# ============================================================
_CODE = "參考資料/OTTO機器人/原廠資料/Code"
_PLUS = "參考資料/OTTO機器人/原廠資料/otto-plus/Codes"
EXAMPLES = [
    ("allmoves", _CODE, "Otto_allmoves_V9", "依序展示全部內建動作（動作總覽）"),
    ("avoid", _CODE, "Otto_avoid_V9", "超音波自動避障"),
    ("distance", _CODE, "Otto_distance_V9", "依距離做反應（測距示範）"),
    ("follow", _CODE, "Otto_follow_V9", "跟隨前方物體"),
    ("run", _CODE, "Otto_run_V9", "快走／跑步"),
    ("happydance", _CODE, "Otto_Happydance_V9", "開心跳舞"),
    ("jingle", _CODE, "Otto_jingle_V9", "音樂鈴聲"),
    ("mario", _CODE, "Otto_MarioBros_V9", "瑪利歐主題曲＋動作"),
    ("birthday", _CODE, "Otto_happybirthday_V9", "生日快樂歌"),
    ("singleladies", _CODE, "Otto_singleladies_V9", "Single Ladies 舞"),
    ("smoothcriminal", _CODE, "Otto_smoothcriminal_V9", "Smooth Criminal 舞"),
    ("sw", _CODE, "Otto_SW_V9", "星際大戰主題"),
    ("retrieve", _CODE, "Otto_retrieve_V9", "撿東西／找回"),
    ("alarm", _CODE, "Otto_Alarm_V9", "鬧鐘"),
    ("footalign", _CODE, "Otto_Footalign_V9", "腳掌對齊（組裝歸零，裝腳前用）"),
    ("calib", _CODE, "Otto_Calibration_V9", "四馬達校正"),
    ("calibeasy", _CODE, "Otto_Calibrationeasy_V9", "簡易校正"),
    ("calibserial", _CODE, "Otto_Calibrationserial_V9", "序列埠校正"),
    ("remote", _CODE, "Otto_Mblock_Scratch_Serial_V9", "序列遙控韌體（＝OttoRemote 來源）"),
    ("clapdance", _PLUS, "OttoPLUS_clapdance_V9", "PLUS：拍手觸發跳舞（需額外模組）"),
    ("clapwalk", _PLUS, "OttoPLUS_clapwalk_V9", "PLUS：拍手走路（需額外模組）"),
    ("guardian", _PLUS, "OttoPLUS_Guardian_V9", "PLUS：守衛模式（需額外模組）"),
    ("stopgo", _PLUS, "OttoPLUS_stopgo_V9", "PLUS：走走停停（需額外模組）"),
    ("touchultra", _PLUS, "OttoPLUS_touchultrasound_V9", "PLUS：觸碰＋超音波（需額外模組）"),
    ("appsound", _PLUS, "OttoAPP_sound_V9", "PLUS：App 聲音（需額外模組）"),
]


def cmd_examples():
    print("原廠範例（用 flash-example <名稱> 燒進真機、build-example <名稱> 只編譯）：\n")
    for short, _, _, desc in EXAMPLES:
        print(f"  {short:<16} {desc}")
    return 0


def _example_dir(project, short):
    if not project:
        sys.exit("✗ 找不到 OTTO 專案根，無法定位原廠範例。請用 --project 指定。")
    for s, base, folder, _ in EXAMPLES:
        if s == short:
            d = os.path.join(project, base.replace("/", os.sep), folder)
            if not os.path.isdir(d):
                sys.exit(f"✗ 範例資料夾不存在：{d}")
            return d
    sys.exit(f"✗ 沒有這支範例：{short}（用 examples 看清單）")


def main():
    ap = argparse.ArgumentParser(description="用 arduino-cli 控管 OTTO 機器人")
    ap.add_argument("--project", help="OTTO 專案根（含 _tools/arduino-cli.exe）")
    ap.add_argument("--new-bootloader", action="store_true", help="用新版 bootloader（115200）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("detect", help="列出序列埠")
    p = sub.add_parser("build", help="只編譯"); p.add_argument("sketch")
    p = sub.add_parser("flash", help="編譯＋燒錄"); p.add_argument("sketch"); p.add_argument("-p", "--port")
    p = sub.add_parser("flash-remote", help="燒常駐遙控韌體"); p.add_argument("-p", "--port")
    p = sub.add_parser("remote", help="送一條序列指令"); p.add_argument("line"); p.add_argument("-p", "--port", required=True); p.add_argument("-b", "--baud", type=int, default=115200)
    p = sub.add_parser("console", help="互動主控台"); p.add_argument("-p", "--port", required=True); p.add_argument("-b", "--baud", type=int, default=115200)
    sub.add_parser("examples", help="列出原廠 25 支範例")
    p = sub.add_parser("build-example", help="只編譯原廠範例"); p.add_argument("name")
    p = sub.add_parser("flash-example", help="把原廠範例燒進真機"); p.add_argument("name"); p.add_argument("-p", "--port")

    args = ap.parse_args()
    project = find_project(os.getcwd(), args.project)
    cli = resolve_cli(project)
    libs = resolve_libs(project)
    fqbn = FQBN_NEW if args.new_bootloader else FQBN_OLD

    if args.cmd == "detect":
        cmd_detect(cli); return 0
    if args.cmd == "build":
        return cmd_build(cli, libs, fqbn, args.sketch)
    if args.cmd == "flash":
        port = auto_port(cli, args.port)
        return cmd_flash(cli, libs, fqbn, args.sketch, port)
    if args.cmd == "flash-remote":
        if not os.path.isdir(REMOTE_FW):
            sys.exit(f"✗ 找不到遙控韌體：{REMOTE_FW}")
        port = auto_port(cli, args.port)
        return cmd_flash(cli, libs, fqbn, REMOTE_FW, port)
    if args.cmd == "remote":
        return cmd_remote(args.port, args.baud, args.line)
    if args.cmd == "console":
        return cmd_console(args.port, args.baud)
    if args.cmd == "examples":
        return cmd_examples()
    if args.cmd == "build-example":
        return cmd_build(cli, libs, fqbn, _example_dir(project, args.name))
    if args.cmd == "flash-example":
        port = auto_port(cli, args.port)
        return cmd_flash(cli, libs, fqbn, _example_dir(project, args.name), port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
