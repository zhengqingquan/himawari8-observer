<!-- markdownlint-disable -->

**简体中文** | [繁體中文](README_zh-HK.md) | [English](README_en-US.md)

<div align="center">

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="120" alt="himawari8-observer">

# himawari8-observer

定时将葵花 8 号（Himawari-8）卫星影像设为 Windows 桌面壁纸<br>
轻量托盘常驻 · Python 本地合成

[反馈问题](https://github.com/zhengqingquan/himawari8-observer/issues) · [Releases](https://github.com/zhengqingquan/himawari8-observer/releases)<br>
[功能](#功能) · [使用](#使用) · [打包](#打包) · [参数说明](doc/cli-arguments.md)

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

## 功能

- 按分辨率档位（550～11000）下载 550×550 瓦片并本地合成
- 默认约每 20 分钟更新；启动时立刻更新一次
- 默认黑边修边，减轻任务栏遮挡（顶/底边距可调）
- 默认设壁纸后清理瓦片与旧缓存（保留当前壁纸图）
- 托盘：手动更新、暂停定时、换分辨率、修边、清理开关、开机启动等

## 环境

- Windows 10 / 11
- Python 依赖见 `requirements.txt`

## 使用

```bash
python run.py
python run.py -r 4400
python run.py --margin-bottom 12
python run.py --no-adjust -r 2200
python run.py --no-cleanup-after-apply
python run.py -h
```

| 选项 | 说明 |
|------|------|
| `-r` / `--resolution` | 合成边长：`550` / `1100` / `2200`（默认）/ `4400` / `8800` / `11000` |
| `-a` / `--adjust` | 黑边修边（**默认开启**；`--no-adjust` 关闭） |
| `--margin-top` / `--margin-bottom` | 顶/底边黑边百分比（默认各 `5`） |
| `--cleanup-after-apply` | 设壁纸后清理缓存（**默认开启**；`--no-cleanup-after-apply` 关闭） |
| `-v` / `--version` | 打印版本后退出 |

完整参数说明见 [`doc/cli-arguments.md`](doc/cli-arguments.md)。

## 打包

```cmd
pyinstaller --noconsole --onefile --icon assets/app.ico --add-data "assets/tray_icon.png;assets" --name himawari8-observer run.py
```
