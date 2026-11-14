#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax-H3 地端生影音（ComfyUI）呼叫器
把提示詞 + 參考圖丟給本機 ComfyUI 的 MiniMax-H3 workflow，生出「帶語音的直式影片」。
免 FAL API 費，跑在本機 GPU。

用法:
  python minimax_h3_local.py --prompt "一個女子轉身冷笑" --ref 角色圖.png --out 輸出.mp4
  python minimax_h3_local.py --prompt "..." --ref char.png --audio 語音.wav --workflow r2v_voice_turbo

前置:
  1. ComfyUI 要先啟動（預設 http://127.0.0.1:8000）
  2. MiniMax-H3 模型已放在 ComfyUI/models/（diffusion_models/vae/loras/text_encoders）
  3. workflow JSON 範本在 ComfyUI 根目錄（_api_r2v_voice_turbo.json 等）

短劇用法（角色一致性）：
  同一角色的每顆鏡頭，用「同一張參考圖」當 --ref，角色就不會換臉。
"""
import argparse, json, os, sys, time, uuid, urllib.request, urllib.parse, shutil

COMFY = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8000")
COMFY_DIR = os.environ.get("COMFYUI_DIR", r"C:\Users\user\Documents\ComfyUI")

# 可用的 workflow 範本（放在 ComfyUI 根目錄）
WORKFLOWS = {
    "r2v_voice_turbo": "_api_r2v_voice_turbo.json",  # 參考圖→影片+語音（加速，推薦）
    "r2v_voice":       "_api_r2v_voice.json",         # 參考圖→影片+語音
    "i2v_teacher":     "_api_i2v_teacher.json",       # 圖生影片
}


def http_json(path, data=None):
    url = f"{COMFY}{path}"
    if data is not None:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def check_comfy():
    try:
        http_json("/system_stats")
        return True
    except Exception:
        return False


def load_workflow(name):
    fn = WORKFLOWS.get(name, name)
    path = os.path.join(COMFY_DIR, fn)
    if not os.path.exists(path):
        sys.exit(f"[錯誤] 找不到 workflow: {path}")
    return json.load(open(path, encoding="utf-8"))


def find_node(wf, class_type):
    """回傳第一個符合 class_type 的節點 id"""
    for nid, node in wf.items():
        if node.get("class_type") == class_type:
            return nid
    return None


def patch_workflow(wf, prompt=None, ref_image=None, audio=None, width=None, height=None):
    """把使用者的提示詞/參考圖/語音塞進 workflow"""
    # 1. prompt → MiniMaxH3ReferenceToVideo 的 prompt
    nid = find_node(wf, "MiniMaxH3ReferenceToVideo")
    if nid and prompt is not None:
        wf[nid]["inputs"]["prompt"] = prompt
        if width:  wf[nid]["inputs"]["width"] = int(width)
        if height: wf[nid]["inputs"]["height"] = int(height)
    # 2. 參考圖 → 第一個 LoadImage
    if ref_image:
        img_nid = find_node(wf, "LoadImage")
        if img_nid:
            # ComfyUI LoadImage 吃 input/ 目錄下的檔名，先複製過去
            dst = os.path.join(COMFY_DIR, "input", os.path.basename(ref_image))
            if os.path.abspath(ref_image) != os.path.abspath(dst):
                shutil.copy2(ref_image, dst)
            wf[img_nid]["inputs"]["image"] = os.path.basename(ref_image)
    # 3. 語音 → LoadAudio
    if audio:
        aud_nid = find_node(wf, "LoadAudio")
        if aud_nid:
            dst = os.path.join(COMFY_DIR, "input", os.path.basename(audio))
            if os.path.abspath(audio) != os.path.abspath(dst):
                shutil.copy2(audio, dst)
            wf[aud_nid]["inputs"]["audio"] = os.path.basename(audio)
    return wf


def submit(wf):
    client_id = str(uuid.uuid4())
    res = http_json("/prompt", {"prompt": wf, "client_id": client_id})
    return res["prompt_id"]


def wait(prompt_id, timeout=900):
    """輪詢 /history 直到完成，回傳 output 檔路徑"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            hist = http_json(f"/history/{prompt_id}")
        except Exception:
            time.sleep(3); continue
        if prompt_id in hist:
            outs = hist[prompt_id].get("outputs", {})
            for nid, out in outs.items():
                for key in ("gifs", "videos", "images"):
                    if key in out and out[key]:
                        f = out[key][0]
                        return os.path.join(COMFY_DIR, "output", f.get("subfolder", ""), f["filename"])
            return None  # 完成但沒抓到 output
        time.sleep(3)
    sys.exit(f"[逾時] {timeout}s 未完成")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="影片提示詞（用 ai-media-generator 的 Seedance/H3 提示詞知識寫）")
    ap.add_argument("--ref", help="參考圖路徑（鎖角色一致性，同角色用同張）")
    ap.add_argument("--audio", help="語音檔路徑（選配）")
    ap.add_argument("--out", default="minimax_h3_output.mp4", help="輸出檔名")
    ap.add_argument("--workflow", default="r2v_voice_turbo", choices=list(WORKFLOWS.keys()))
    ap.add_argument("--width", type=int, help="寬（預設沿用workflow，短劇直式576）")
    ap.add_argument("--height", type=int, help="高（短劇直式768）")
    args = ap.parse_args()

    if not check_comfy():
        sys.exit(f"[錯誤] ComfyUI 沒在跑。請先啟動 ComfyUI（{COMFY}），並確認 MiniMax-H3 模型已載入。")

    wf = load_workflow(args.workflow)
    wf = patch_workflow(wf, prompt=args.prompt, ref_image=args.ref, audio=args.audio,
                        width=args.width, height=args.height)
    print(f"[H3] 送出任務（workflow={args.workflow}）...")
    pid = submit(wf)
    print(f"[H3] prompt_id={pid}，本機 GPU 生成中（依長度約數十秒~數分鐘）...")
    result = wait(pid)
    if not result or not os.path.exists(result):
        sys.exit("[錯誤] 生成完成但找不到輸出檔，請到 ComfyUI/output 查看")
    shutil.copy2(result, args.out)
    print(f"[H3] ✅ 完成 → {args.out}")


if __name__ == "__main__":
    main()
