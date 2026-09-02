# himawari8-observer

每隔一段时间将葵花 8 号（Himawari）卫星影像设为 Windows 桌面壁纸的本地常驻程序。合成图边长最高可达约 11000×11000。

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="300" >
<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/154000_0_0.png?raw=true" width="300">

取名 himawari8-observer：把自己当为卫星观察地球。

- 仓库：https://github.com/zhengqingquan/himawari8-observer
- 瓦片与观测时间：https://himawari8.nict.go.jp/ · https://himawari8-dl.nict.go.jp/

## 说明

影像来自 NICT 的 Himawari 瓦片服务（按 550×550 分块下载后本地合成）。旧的 sc-nc-web「完整图」接口已不可用，本程序也不再提供该选项。

## 环境

- Windows 10 / 11
- Python 依赖见 `requirements.txt`

## 使用

```bash
python run.py
python run.py -r 4400
python run.py -a -r 2200
python run.py -h
```

常用参数：

| 选项 | 说明 |
|------|------|
| `-r` / `--resolution` | 合成边长：`550` / `1100` / `2200`（默认）/ `4400` / `8800` / `11000` |
| `-a` / `--adjust` | 启用修边，减轻任务栏遮挡 |
| `-v` / `--version` | 打印版本后退出 |

更完整说明见 [`doc/cli-arguments.md`](doc/cli-arguments.md)。

启动后托盘常驻，可：

- 更新壁纸 / 暂停或恢复定时更新
- 切换图片分辨率（立即触发一次更新）
- 开机启动、打开日志、访问官网、关于与退出

定时间隔默认约 20 分钟；进程启动时会立刻更新一次。需要马上换图时可用托盘「更新壁纸」。

## 打包

```cmd
pyinstaller --noconsole --onefile --name himawari8-observer run.py
```
