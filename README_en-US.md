<!-- markdownlint-disable -->

[简体中文](README.md) | [繁體中文](README_zh-HK.md) | **English**

<div align="center">

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="120" alt="himawari8-observer">

# himawari8-observer

Set Himawari-8 satellite imagery as your Windows desktop wallpaper on a schedule<br>
Lightweight system-tray app · Local Python compositing

[Issues](https://github.com/zhengqingquan/himawari8-observer/issues) · [Releases](https://github.com/zhengqingquan/himawari8-observer/releases)<br>
[Features](#features) · [Usage](#usage) · [Packaging](#packaging) · [CLI docs](doc/cli-arguments.md)

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

Data sources: [himawari8.nict.go.jp](https://himawari8.nict.go.jp/) · [himawari8-dl.nict.go.jp](https://himawari8-dl.nict.go.jp/)

</div>

## Features

- Download 550×550 tiles at resolution grades from 550 to 11000 and composite locally
- Updates about every 20 minutes by default; runs once immediately on startup
- Black-border padding on by default to reduce taskbar occlusion (top/bottom margins adjustable)
- After applying wallpaper, cleans tiles and old caches by default (keeps the current wallpaper file)
- Tray menu: manual update, pause schedule, change resolution, padding, cleanup toggle, start on boot, and more

## Requirements

- Windows 10 / 11
- See `requirements.txt` for Python dependencies

## Usage

```bash
python run.py
python run.py -r 4400
python run.py --margin-bottom 12
python run.py --no-adjust -r 2200
python run.py --no-cleanup-after-apply
python run.py -h
```

| Option | Description |
|------|------|
| `-r` / `--resolution` | Composite side length: `550` / `1100` / `2200` (default) / `4400` / `8800` / `11000` |
| `-a` / `--adjust` | Black-border padding (**on** by default; `--no-adjust` to disable) |
| `--margin-top` / `--margin-bottom` | Top/bottom black-border percent (default `5` each) |
| `--cleanup-after-apply` | Clean caches after applying wallpaper (**on** by default; `--no-cleanup-after-apply` to disable) |
| `-v` / `--version` | Print version and exit |

Full CLI reference: [`doc/cli-arguments.md`](doc/cli-arguments.md).

## Packaging

```cmd
pyinstaller --noconsole --onefile --icon assets/app.ico --add-data "assets/tray_icon.png;assets" --name himawari8-observer run.py
```
