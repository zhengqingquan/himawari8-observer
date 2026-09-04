<!-- markdownlint-disable -->

**简体中文** | [繁體中文](README_zh-HK.md) | [English](README_en-US.md)

<div align="center">

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="120" alt="himawari8-observer">

# himawari8-observer

定时将葵花 8 号（Himawari-8）卫星影像设为 Windows 桌面壁纸<br>
轻量托盘常驻 · 本地合成 · 当前版本 **v1.5.0**

[反馈问题](https://github.com/zhengqingquan/himawari8-observer/issues) · [Releases](https://github.com/zhengqingquan/himawari8-observer/releases) · [更新记录](CHANGELOG.md)

[![Version](https://img.shields.io/github/v/release/zhengqingquan/himawari8-observer)](https://github.com/zhengqingquan/himawari8-observer/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Stars](https://img.shields.io/github/stars/zhengqingquan/himawari8-observer?color=ffcb47&labelColor=black)<br>
![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%20%2F%2011-0078D6?logo=windows&logoColor=white)
![PyInstaller](https://img.shields.io/badge/Packaging-PyInstaller-blueviolet)

<p>
  <img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="300" alt="Himawari sample 1" />
  <img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/154000_0_0.png?raw=true" width="300" alt="Himawari sample 2" />
</p>

数据源：[himawari8.nict.go.jp](https://himawari8.nict.go.jp/) · [himawari8-dl.nict.go.jp](https://himawari8-dl.nict.go.jp/)

</div>

## 简介

在 Windows 上定时拉取葵花 8 号最新影像，合成为桌面壁纸，并以系统托盘方式常驻运行。

- 支持多种分辨率档位，可按需切换
- 默认约每 10 分钟自动更新，启动时立刻更新一次
- 影像与参数未变时可跳过重复下载
- 可选黑边修边，减轻任务栏遮挡
- 可选减轻色带、台风/位置标注、昨日影像等
- 托盘可手动更新、暂停定时、换分辨率、开机启动等
- 托盘修改的设置保存在程序目录 `settings.json`，重启后自动恢复
- 日志默认关闭，可在托盘或用 `--logging` 开启

日常使用可从 [Releases](https://github.com/zhengqingquan/himawari8-observer/releases/latest) 下载预编译包，解压后直接运行。

更完整的 CLI 说明见 [doc/cli-arguments.md](doc/cli-arguments.md)；更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## 开发环境

- Windows 10 / 11
- Python 3.10+
- 安装依赖：

```bash
pip install -r requirements.txt
```

## 开发命令

常驻托盘：

```bash
python run.py
python run.py -r 4400
python run.py --margin-bottom 12
python run.py --no-adjust -r 2200
python run.py --no-cleanup-after-apply
python run.py --download-interval-minutes 20
python run.py --show-typhoon-marker --show-my-location
python run.py -h
python run.py -v
```

只跑一轮（不挂托盘 / 调度）：

```bash
python -m src.oneshot
```

常用选项：

| 选项 | 说明 |
|------|------|
| `-r` / `--resolution` | 合成边长：`550` / `1100` / `2200`（默认） / `4400` / `8800` / `11000` |
| `-a` / `--adjust` | 黑边修边（默认开启；`--no-adjust` 关闭） |
| `--margin-top` / `--margin-bottom` | 顶 / 底边黑边百分比（默认顶 `0`、底 `5`） |
| `--cleanup-after-apply` | 设壁纸后清理缓存（默认开启；`--no-cleanup-after-apply` 关闭） |
| `--use-yesterday-local-time` | 按本机钟点取昨日影像（默认关闭） |
| `--reduce-banding` | 减轻色带（默认关闭） |
| `--show-typhoon-marker` | 标注台风中心（默认关闭） |
| `--show-my-location` | 标注我的位置（IP 粗定位，默认关闭） |
| `--download-interval-minutes` | 定时间隔：`5` / `10`（默认） / `15` / `20` / `30` |
| `--logging` | 启用日志（默认关闭；`--no-logging` 关闭） |
| `-v` / `--version` | 打印版本后退出 |

## 打包

```cmd
pip install pyinstaller
pyinstaller --noconfirm himawari8-observer.spec
```

产物在 `dist/himawari8-observer.exe`（无控制台窗口）。

等价命令行：

```cmd
pyinstaller --noconsole --onefile --icon assets/app.ico --add-data "assets/tray_icon.png;assets" --name himawari8-observer run.py
```
