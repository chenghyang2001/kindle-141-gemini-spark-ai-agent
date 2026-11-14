#!/usr/bin/env python3
"""
AI 教學影片生成器 — 環境檢查工具

檢查所有先決條件是否就緒：
- Google Chrome（headless 截圖用）
- ffmpeg（影片合成用）
- edge-tts（TTS 語音合成用）
- Python 版本

用法：
    python env_check.py
    python env_check.py --json

作者：阿亮老師・3A科技研究社
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_version_from_cmd(cmd: list[str], timeout: int = 10) -> str:
    """執行指令並取得輸出。"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
        return ""
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def find_chrome() -> str:
    """跨平台尋找 Chrome。"""
    system = platform.system()

    if system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif system == "Linux":
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
    else:
        candidates = []

    for path in candidates:
        expanded = os.path.expandvars(path)
        if os.path.isfile(expanded):
            return expanded

    for cmd_name in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"]:
        found = shutil.which(cmd_name)
        if found:
            return found

    return ""


def check_chrome() -> dict:
    """檢查 Chrome 是否安裝。"""
    chrome = find_chrome()
    if chrome:
        # 嘗試取得版本
        version = get_version_from_cmd([chrome, "--version"])
        if not version:
            version = chrome
        return {
            "name": "Google Chrome",
            "required": "已安裝",
            "found": version.replace("Google Chrome ", ""),
            "passed": True,
        }
    return {
        "name": "Google Chrome",
        "required": "已安裝",
        "found": "未安裝",
        "passed": False,
    }


def check_ffmpeg() -> dict:
    """檢查 ffmpeg 是否安裝。"""
    output = get_version_from_cmd(["ffmpeg", "-version"])
    if output:
        # 提取版本號
        parts = output.split()
        version = parts[2] if len(parts) >= 3 else output[:50]
        return {
            "name": "ffmpeg",
            "required": "已安裝",
            "found": version,
            "passed": True,
        }
    return {
        "name": "ffmpeg",
        "required": "已安裝",
        "found": "未安裝",
        "passed": False,
    }


def check_edge_tts() -> dict:
    """檢查 edge-tts 是否安裝。"""
    try:
        import importlib.metadata
        version = importlib.metadata.version("edge-tts")
        return {
            "name": "edge-tts",
            "required": "已安裝",
            "found": version,
            "passed": True,
        }
    except Exception:
        return {
            "name": "edge-tts",
            "required": "已安裝",
            "found": "未安裝",
            "passed": False,
        }


def check_python() -> dict:
    """檢查 Python 版本。"""
    version = sys.version.split()[0]
    return {
        "name": "Python",
        "required": "≥ 3.8",
        "found": version,
        "passed": True,  # 如果能跑這個腳本就符合
    }


def check_nodejs() -> dict:
    """檢查 Node.js 版本（專業模式用）。"""
    output = get_version_from_cmd(["node", "--version"])
    if output:
        version = output.strip().lstrip("v")
        try:
            major = int(version.split(".")[0])
            passed = major >= 18
        except ValueError:
            passed = False
        return {
            "name": "Node.js (Pro)",
            "required": "≥ 18（選用）",
            "found": version,
            "passed": passed,
            "optional": True,
        }
    return {
        "name": "Node.js (Pro)",
        "required": "≥ 18（選用）",
        "found": "未安裝",
        "passed": False,
        "optional": True,
    }


def check_remotion() -> dict:
    """檢查 Remotion 安裝狀態（專業模式用）。"""
    config_path = Path(__file__).parent / ".remotion_config.json"
    if config_path.is_file():
        try:
            import json as _json
            with open(config_path, "r", encoding="utf-8") as f:
                config = _json.load(f)
            project_dir = config.get("remotion_project_dir", "")
            if project_dir and Path(project_dir).is_dir():
                node_modules = Path(project_dir) / "node_modules"
                if node_modules.is_dir():
                    return {
                        "name": "Remotion (Pro)",
                        "required": "已設定（選用）",
                        "found": f"已安裝 ({project_dir})",
                        "passed": True,
                        "optional": True,
                    }
                return {
                    "name": "Remotion (Pro)",
                    "required": "已設定（選用）",
                    "found": "專案存在但缺少依賴",
                    "passed": False,
                    "optional": True,
                }
        except Exception:
            pass
    return {
        "name": "Remotion (Pro)",
        "required": "已設定（選用）",
        "found": "未設定",
        "passed": False,
        "optional": True,
    }


def check_azure_key() -> dict:
    """檢查 Azure Speech Key（選用）。"""
    key = os.environ.get("AZURE_SPEECH_KEY", "")
    if key:
        return {
            "name": "Azure Speech",
            "required": "AZURE_SPEECH_KEY（選用）",
            "found": f"已設定（{key[:4]}...）",
            "passed": True,
            "optional": True,
        }
    return {
        "name": "Azure Speech",
        "required": "AZURE_SPEECH_KEY（選用）",
        "found": "未設定",
        "passed": False,
        "optional": True,
    }


def check_openai_key() -> dict:
    """檢查 OpenAI API Key（選用）。"""
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        return {
            "name": "OpenAI TTS",
            "required": "OPENAI_API_KEY（選用）",
            "found": f"已設定（{key[:4]}...）",
            "passed": True,
            "optional": True,
        }
    return {
        "name": "OpenAI TTS",
        "required": "OPENAI_API_KEY（選用）",
        "found": "未設定",
        "passed": False,
        "optional": True,
    }


def run_all_checks() -> list[dict]:
    """執行所有檢查。"""
    return [
        check_python(),
        check_chrome(),
        check_ffmpeg(),
        check_edge_tts(),
        check_nodejs(),
        check_remotion(),
        check_azure_key(),
        check_openai_key(),
    ]


def print_table(checks: list[dict]) -> None:
    """以表格格式印出檢查結果。"""
    print()
    print("=" * 65)
    print("  AI 教學影片生成器 v2 — 環境檢查")
    print("  阿亮老師・3A科技研究社")
    print("=" * 65)
    print()

    print(f"  {'檢查項目':<20} {'需求':<12} {'結果':<20} {'狀態'}")
    print("  " + "-" * 58)

    pass_count = 0
    fail_count = 0
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        marker = "[v]" if c["passed"] else "[X]"
        print(f"  {c['name']:<20} {c['required']:<12} {c['found']:<20} {marker} {status}")
        if c["passed"]:
            pass_count += 1
        else:
            fail_count += 1

    print()
    print("  " + "-" * 58)
    total = pass_count + fail_count
    print(f"  總計：{pass_count}/{total} 通過，{fail_count}/{total} 未通過")

    if fail_count == 0:
        print("\n  所有檢查皆通過！可以開始生成教學影片。")
    else:
        print(f"\n  有 {fail_count} 個項目未通過，請安裝缺少的工具：")
        for c in checks:
            if not c["passed"]:
                name = c["name"]
                if "Chrome" in name:
                    print(f"    - {name}：請至 https://www.google.com/chrome/ 下載安裝")
                elif "ffmpeg" in name:
                    print(f"    - {name}：winget install ffmpeg 或至 https://ffmpeg.org/")
                elif "edge-tts" in name:
                    print(f"    - {name}：pip install edge-tts")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="AI 教學影片生成器 — 環境檢查工具"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="以 JSON 格式輸出結果",
    )
    args = parser.parse_args()

    checks = run_all_checks()

    if args.json:
        output = {
            "checks": checks,
            "passed": sum(1 for c in checks if c["passed"]),
            "failed": sum(1 for c in checks if not c["passed"]),
            "total": len(checks),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_table(checks)

    # 只有必要項目（非 optional）未通過時才回傳錯誤碼
    required_failed = any(
        not c["passed"] and not c.get("optional", False)
        for c in checks
    )
    if required_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
