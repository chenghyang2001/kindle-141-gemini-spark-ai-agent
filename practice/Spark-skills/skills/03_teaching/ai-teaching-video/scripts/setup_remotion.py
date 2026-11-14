#!/usr/bin/env python3
"""
Remotion 專業模式環境設定腳本

檢查 Node.js >= 18，初始化 Remotion 專案，安裝依賴套件。
設定完成後將專案路徑記錄供後續渲染使用。

使用方式：
    python setup_remotion.py
    python setup_remotion.py --project-dir D:/my-remotion-project

作者：阿亮老師・3A科技研究社
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# 預設 Remotion 專案目錄
DEFAULT_PROJECT_DIR = Path.home() / "remotion-teaching-video"

# 設定檔路徑（記錄 Remotion 專案位置）
CONFIG_PATH = Path(__file__).parent / ".remotion_config.json"

# Remotion 相關套件
REMOTION_PACKAGES = [
    "remotion@^4.0.438",
    "@remotion/cli@^4.0.438",
    "@remotion/player@^4.0.438",
    "@remotion/media-utils@^4.0.438",
    "@remotion/transitions@^4.0.438",
    "@remotion/shapes@^4.0.438",
    "zod@^3.22.0",
    "react@^18.2.0",
    "react-dom@^18.2.0",
]

DEV_PACKAGES = [
    "@types/react@^18.2.0",
    "typescript@^5.3.0",
]


def check_node_version() -> tuple[bool, str]:
    """檢查 Node.js 版本是否 >= 18。"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return False, "Node.js 未安裝"

        version_str = result.stdout.strip().lstrip("v")
        major = int(version_str.split(".")[0])

        if major < 18:
            return False, f"Node.js 版本 {version_str} 太舊，需要 >= 18"

        return True, version_str
    except FileNotFoundError:
        return False, "Node.js 未安裝"
    except (subprocess.TimeoutExpired, ValueError, IndexError) as e:
        return False, f"無法偵測 Node.js 版本: {e}"


def check_npm() -> bool:
    """檢查 npm 是否可用。"""
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def init_remotion_project(project_dir: Path) -> bool:
    """初始化 Remotion 專案目錄。"""
    project_dir.mkdir(parents=True, exist_ok=True)

    # 初始化 package.json（如果不存在）
    package_json = project_dir / "package.json"
    if not package_json.is_file():
        print("[設定] 初始化 package.json...")
        pkg = {
            "name": "teaching-video-remotion",
            "version": "1.0.0",
            "description": "AI 教學影片 Remotion 專案 — 阿亮老師・3A科技研究社",
            "engines": {"node": ">=18"},
            "scripts": {
                "studio": "remotion studio src/index.ts",
                "render": "remotion render src/index.ts",
                "build": "remotion bundle src/index.ts",
            },
        }
        with open(package_json, "w", encoding="utf-8") as f:
            json.dump(pkg, f, ensure_ascii=False, indent=2)
        print(f"  建立: {package_json}")
    else:
        print(f"[設定] package.json 已存在: {package_json}")

    return True


def install_dependencies(project_dir: Path) -> bool:
    """安裝 Remotion 相關 npm 套件。"""
    print(f"\n[安裝] 安裝 Remotion 依賴套件（需要幾分鐘）...")

    # 安裝主要套件
    cmd_main = ["npm", "install", "--save"] + REMOTION_PACKAGES
    print(f"  安裝主要套件: {len(REMOTION_PACKAGES)} 個...")
    result = subprocess.run(
        cmd_main, cwd=str(project_dir),
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        print(f"  [錯誤] 主要套件安裝失敗: {result.stderr[:500]}", file=sys.stderr)
        return False

    # 安裝開發套件
    cmd_dev = ["npm", "install", "--save-dev"] + DEV_PACKAGES
    print(f"  安裝開發套件: {len(DEV_PACKAGES)} 個...")
    result = subprocess.run(
        cmd_dev, cwd=str(project_dir),
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"  [警告] 開發套件安裝失敗: {result.stderr[:300]}", file=sys.stderr)
        # 非致命錯誤，繼續

    print("  套件安裝完成！")
    return True


def create_project_structure(project_dir: Path) -> None:
    """建立 Remotion 專案基本結構。"""
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # tsconfig.json
    tsconfig_path = project_dir / "tsconfig.json"
    if not tsconfig_path.is_file():
        tsconfig = {
            "compilerOptions": {
                "target": "ES2022",
                "module": "ES2022",
                "moduleResolution": "bundler",
                "jsx": "react-jsx",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "outDir": "./dist",
                "declaration": True,
            },
            "include": ["src/**/*"],
        }
        with open(tsconfig_path, "w", encoding="utf-8") as f:
            json.dump(tsconfig, f, ensure_ascii=False, indent=2)
        print(f"  建立: {tsconfig_path}")

    # remotion.config.ts
    remotion_config = project_dir / "remotion.config.ts"
    if not remotion_config.is_file():
        config_content = """// Remotion 設定檔 — AI 教學影片生成器
// 作者：阿亮老師・3A科技研究社
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("png");
Config.setOverwriteOutput(true);
"""
        with open(remotion_config, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"  建立: {remotion_config}")

    # src/index.ts（Remotion 入口）
    index_ts = src_dir / "index.ts"
    if not index_ts.is_file():
        index_content = """// Remotion 入口檔 — AI 教學影片生成器
// 作者：阿亮老師・3A科技研究社
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
"""
        with open(index_ts, "w", encoding="utf-8") as f:
            f.write(index_content)
        print(f"  建立: {index_ts}")

    # src/Root.tsx（根組件）
    root_tsx = src_dir / "Root.tsx"
    if not root_tsx.is_file():
        root_content = """// Remotion Root — AI 教學影片生成器
// 作者：阿亮老師・3A科技研究社
import React from "react";
import { Composition } from "remotion";
import { TeachingVideo } from "./compositions/TeachingVideo";

// 預設合成設定
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TeachingVideo"
        component={TeachingVideo}
        durationInFrames={900}   // 30秒 x 30fps，實際由 timing.json 決定
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          timingFile: "timing.json",
          audioFile: "audio.wav",
        }}
      />
      <Composition
        id="TeachingVideo4K"
        component={TeachingVideo}
        durationInFrames={900}
        fps={30}
        width={3840}
        height={2160}
        defaultProps={{
          timingFile: "timing.json",
          audioFile: "audio.wav",
        }}
      />
    </>
  );
};
"""
        with open(root_tsx, "w", encoding="utf-8") as f:
            f.write(root_content)
        print(f"  建立: {root_tsx}")

    # src/compositions/TeachingVideo.tsx（教學影片合成模板）
    comp_dir = src_dir / "compositions"
    comp_dir.mkdir(parents=True, exist_ok=True)

    teaching_tsx = comp_dir / "TeachingVideo.tsx"
    if not teaching_tsx.is_file():
        teaching_content = """// 教學影片合成組件 — AI 教學影片生成器
// 作者：阿亮老師・3A科技研究社
import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Audio,
  Sequence,
} from "remotion";

// 教學影片 Props 型別
interface TeachingVideoProps {
  timingFile: string;
  audioFile: string;
}

// 單張投影片組件
const Slide: React.FC<{
  title: string;
  content: string;
  slideNumber: number;
  totalSlides: number;
}> = ({ title, content, slideNumber, totalSlides }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 進場動畫：標題滑入 + 淡入
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = spring({ frame, fps, from: -30, to: 0, durationInFrames: 20 });

  // 內容延遲出現
  const contentOpacity = interpolate(frame, [10, 25], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0d0d0d 100%)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 120px",
        fontFamily: "'Noto Sans TC', 'PingFang SC', sans-serif",
      }}
    >
      {/* 裝飾光暈 */}
      <div
        style={{
          position: "absolute",
          top: -200,
          right: -100,
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: "rgba(255,180,50,0.12)",
          filter: "blur(80px)",
        }}
      />

      {/* 標題 */}
      <div
        style={{
          fontSize: 78,
          fontWeight: 900,
          color: "#ffd700",
          textShadow: "0 2px 20px rgba(255,215,0,0.4)",
          letterSpacing: 6,
          opacity: titleOpacity,
          transform: \`translateY(\${titleY}px)\`,
          textAlign: "center",
          maxWidth: "1400px",
        }}
      >
        {title}
      </div>

      {/* 內容 */}
      <div
        style={{
          fontSize: 40,
          fontWeight: 300,
          color: "#e8e8e8",
          lineHeight: 2.0,
          letterSpacing: 2,
          opacity: contentOpacity,
          textAlign: "center",
          maxWidth: "1100px",
          marginTop: 30,
        }}
      >
        {content}
      </div>

      {/* 頁碼 */}
      <div
        style={{
          position: "absolute",
          bottom: 30,
          right: 50,
          fontSize: 16,
          color: "rgba(255,255,255,0.25)",
        }}
      >
        {slideNumber}/{totalSlides}
      </div>

      {/* 底部裝飾條 */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: 5,
          background: "linear-gradient(90deg, #ffd700, #ff8c00, #ffd700)",
        }}
      />
    </AbsoluteFill>
  );
};

// 主要合成組件
export const TeachingVideo: React.FC<TeachingVideoProps> = ({
  timingFile,
  audioFile,
}) => {
  // 注意：實際使用時由 render_remotion.py 動態生成帶有 timing 資料的組件
  // 此為基本模板，展示結構
  return (
    <AbsoluteFill>
      <Sequence from={0} durationInFrames={150}>
        <Slide
          title="AI 教學影片"
          content="由 Remotion 渲染的教學影片範例"
          slideNumber={1}
          totalSlides={1}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
"""
        with open(teaching_tsx, "w", encoding="utf-8") as f:
            f.write(teaching_content)
        print(f"  建立: {teaching_tsx}")


def save_config(project_dir: Path) -> None:
    """儲存 Remotion 專案路徑到設定檔。"""
    config = {
        "remotion_project_dir": str(project_dir.resolve()),
        "version": "2.0.0",
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\n[設定] 專案路徑已儲存: {CONFIG_PATH}")


def load_config() -> dict:
    """讀取 Remotion 設定檔。"""
    if CONFIG_PATH.is_file():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="Remotion 專業模式環境設定 — AI 教學影片生成器"
    )
    parser.add_argument(
        "--project-dir",
        default=str(DEFAULT_PROJECT_DIR),
        help=f"Remotion 專案目錄（預設: {DEFAULT_PROJECT_DIR}）",
    )
    parser.add_argument(
        "--check-only", action="store_true",
        help="僅檢查環境，不安裝",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    print("=" * 60)
    print("  Remotion 專業模式環境設定")
    print("  AI 教學影片生成器 — 阿亮老師・3A科技研究社")
    print("=" * 60)

    # 步驟 1：檢查 Node.js
    print("\n[步驟 1] 檢查 Node.js 版本...")
    node_ok, node_info = check_node_version()
    if node_ok:
        print(f"  Node.js v{node_info} — OK")
    else:
        print(f"  [錯誤] {node_info}")
        print("  請安裝 Node.js >= 18：")
        print("    Windows: winget install OpenJS.NodeJS.LTS")
        print("    macOS:   brew install node@18")
        print("    Linux:   https://nodejs.org/")
        sys.exit(1)

    # 步驟 2：檢查 npm
    print("\n[步驟 2] 檢查 npm...")
    if check_npm():
        print("  npm — OK")
    else:
        print("  [錯誤] npm 不可用，請確認 Node.js 安裝完整")
        sys.exit(1)

    if args.check_only:
        print("\n[完成] 環境檢查通過，可以初始化 Remotion 專案。")
        return

    # 步驟 3：初始化專案
    print(f"\n[步驟 3] 初始化 Remotion 專案: {project_dir}")
    if not init_remotion_project(project_dir):
        sys.exit(1)

    # 步驟 4：安裝依賴
    print("\n[步驟 4] 安裝 Remotion 依賴套件...")
    if not install_dependencies(project_dir):
        print("[錯誤] 套件安裝失敗，請手動執行:")
        print(f"  cd {project_dir}")
        print(f"  npm install {' '.join(REMOTION_PACKAGES)}")
        sys.exit(1)

    # 步驟 5：建立專案結構
    print("\n[步驟 5] 建立專案結構...")
    create_project_structure(project_dir)

    # 步驟 6：儲存設定
    save_config(project_dir)

    # 完成
    print("\n" + "=" * 60)
    print("  Remotion 設定完成！")
    print("=" * 60)
    print(f"\n  專案目錄: {project_dir}")
    print(f"  預覽模式: cd {project_dir} && npx remotion studio")
    print(f"  渲染影片: 使用 render_remotion.py 腳本")
    print("\n  現在可以使用 --mode pro 執行專業模式流水線。")


if __name__ == "__main__":
    main()
