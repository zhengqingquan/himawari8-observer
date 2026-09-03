<!-- markdownlint-disable -->

[简体中文](README.md) | **繁體中文** | [English](README_en-US.md)

<div align="center">

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="120" alt="himawari8-observer">

# himawari8-observer

定時將葵花 8 號（Himawari-8）衛星影像設為 Windows 桌面桌布<br>
輕量系統匣常駐 · 本機合成 · 目前版本 **v1.4.0**

[回報問題](https://github.com/zhengqingquan/himawari8-observer/issues) · [Releases](https://github.com/zhengqingquan/himawari8-observer/releases) · [更新紀錄](CHANGELOG.md)

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

資料來源：[himawari8.nict.go.jp](https://himawari8.nict.go.jp/) · [himawari8-dl.nict.go.jp](https://himawari8-dl.nict.go.jp/)

</div>

## 簡介

在 Windows 上定時拉取葵花 8 號最新影像，合成為桌面桌布，並以系統匣方式常駐執行。

- 支援多種解析度檔位，可依需求切換
- 預設約每 20 分鐘自動更新，啟動時立即更新一次
- 影像與參數未變時可跳過重複下載
- 可選黑邊修邊，減輕工作列遮擋
- 系統匣可手動更新、暫停定時、切換解析度、開機啟動等
- 系統匣修改的設定會寫入程式目錄 `settings.json`，重啟後自動還原
- 日誌預設關閉，可在系統匣或以 `--logging` 開啟

日常使用可從 [Releases](https://github.com/zhengqingquan/himawari8-observer/releases/latest) 下載預編譯包，解壓後直接執行。

## 開發環境

- Windows 10 / 11
- Python 3.10+
- 安裝依賴：

```bash
pip install -r requirements.txt
```

## 開發命令

常駐系統匣：

```bash
python run.py
python run.py -r 4400
python run.py --margin-bottom 12
python run.py --no-adjust -r 2200
python run.py --no-cleanup-after-apply
python run.py -h
python run.py -v
```

只跑一輪（不掛系統匣／排程）：

```bash
python -m src.main
```

常用選項：

| 選項 | 說明 |
|------|------|
| `-r` / `--resolution` | 合成邊長：`550` / `1100` / `2200`（預設） / `4400` / `8800` / `11000` |
| `-a` / `--adjust` | 黑邊修邊（預設開啟；`--no-adjust` 關閉） |
| `--margin-top` / `--margin-bottom` | 上／下邊黑邊百分比（預設上 `0`、下 `5`） |
| `--cleanup-after-apply` | 設成桌布後清理快取（預設開啟；`--no-cleanup-after-apply` 關閉） |
| `--logging` | 啟用日誌（預設關閉；`--no-logging` 關閉） |
| `-v` / `--version` | 印出版本後結束 |

## 打包

```cmd
pip install pyinstaller
pyinstaller --noconfirm himawari8-observer.spec
```

產物在 `dist/himawari8-observer.exe`（無主控台視窗）。

等價命令列：

```cmd
pyinstaller --noconsole --onefile --icon assets/app.ico --add-data "assets/tray_icon.png;assets" --name himawari8-observer run.py
```
