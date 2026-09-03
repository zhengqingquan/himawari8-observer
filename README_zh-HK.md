<!-- markdownlint-disable -->

[简体中文](README.md) | **繁體中文** | [English](README_en-US.md)

<div align="center">

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="120" alt="himawari8-observer">

# himawari8-observer

定時將葵花 8 號（Himawari-8）衛星影像設為 Windows 桌面桌布<br>
輕量系統匣常駐 · Python 本機合成

[回報問題](https://github.com/zhengqingquan/himawari8-observer/issues) · [Releases](https://github.com/zhengqingquan/himawari8-observer/releases)<br>
[功能](#功能) · [使用](#使用) · [打包](#打包) · [參數說明](doc/cli-arguments.md)

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

## 功能

- 依解析度檔位（550～11000）下載 550×550 圖磚並本機合成
- 預設約每 20 分鐘更新；啟動時立即更新一次
- 觀測時間與成圖參數未變時跳過下載（切換解析度／修邊會重新拉取）
- 預設黑邊修邊，減輕工作列遮擋（上／下邊距可調）
- 預設設成桌布後清理圖磚與舊快取（保留目前桌布圖）
- 系統匣：手動更新、暫停定時、切換解析度、修邊、清理開關、開機啟動等

## 環境

- Windows 10 / 11
- Python 依賴見 `requirements.txt`

## 使用

```bash
python run.py
python run.py -r 4400
python run.py --margin-bottom 12
python run.py --no-adjust -r 2200
python run.py --no-cleanup-after-apply
python run.py -h
```

| 選項 | 說明 |
|------|------|
| `-r` / `--resolution` | 合成邊長：`550` / `1100` / `2200`（預設）/ `4400` / `8800` / `11000` |
| `-a` / `--adjust` | 黑邊修邊（**預設開啟**；`--no-adjust` 關閉） |
| `--margin-top` / `--margin-bottom` | 上／下邊黑邊百分比（預設各 `5`） |
| `--cleanup-after-apply` | 設成桌布後清理快取（**預設開啟**；`--no-cleanup-after-apply` 關閉） |
| `-v` / `--version` | 印出版本後結束 |

完整參數說明見 [`doc/cli-arguments.md`](doc/cli-arguments.md)。

## 打包

```cmd
pyinstaller --noconsole --onefile --icon assets/app.ico --add-data "assets/tray_icon.png;assets" --name himawari8-observer run.py
```
