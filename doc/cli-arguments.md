# 命令行参数说明

程序入口为 `run.py`。启动时会通过 `src/arg/arg.py` 中的 `Config` 解析命令行参数。

查看内置帮助：

```bash
python run.py -h
# 或
python run.py --help
```

查看版本：

```bash
python run.py -v
# 或
python run.py --version
```

当前版本字符串来自 `src/metadata/soft_info.py`（例如 `himawari8-observer v1.3.0`）。

---

## 参数一览

| 短选项 | 长选项 | 取值 | 默认值 | 说明 |
|--------|--------|------|--------|------|
| `-dl` | `--download` | `equal` / `complete` | `equal` | 下载方式 |
| `-r` | `--resolution` | `550` / `2200` / `4400` / `8800` / `11000` | `2200` | 目标图像边长（像素） |
| `-a` | `--adjust` | 开关标志 | 关闭 | 是否自动调整图片，避免被任务栏遮挡 |
| `-v` | `--version` | — | — | 打印版本后退出 |
| `-h` | `--help` | — | — | 打印帮助后退出 |

分辨率可选值与默认值由 `src/resolution_grade.py` 定义，经 `src/metadata/soft_config.py` 再导出。

---

## 参数详解

### `-dl` / `--download`

选择卫星图的下载方式。

| 取值 | 含义 |
|------|------|
| `equal` | **碎片下载**：按 550×550 瓦片分块下载，再合成为完整图（默认） |
| `complete` | **完整下载**：通过完整图接口一次拉取整张图 |

可省略参数值（`nargs="?"`）：只写 `-dl` 时等价于 `equal`。

示例：

```bash
python run.py -dl equal
python run.py --download complete
python run.py -dl
```

---

### `-r` / `--resolution`

指定最终图像一侧的像素边长。可选：

| 取值 | 对应碎片划分（约） |
|------|-------------------|
| `550` | 1×1（1d） |
| `2200` | 4×4（4d，默认） |
| `4400` | 8×8（8d） |
| `8800` | 16×16（16d） |
| `11000` | 20×20（20d） |

瓦片基本尺寸为 550×550；边长越大，下载与合成耗时越多。

可省略参数值：只写 `-r` 时等价于默认分辨率 `2200`。

示例：

```bash
python run.py -r 2200
python run.py --resolution 11000
python run.py -r
```

---

### `-a` / `--adjust`

用于控制是否自动裁剪/调整壁纸，减轻被任务栏遮挡的问题。

帮助文案含义：启用自动调整。

> **实现说明**：`action="store_true"`，默认关闭；传入 `-a` / `--adjust` 时启用。启动时冻结进 `build_wallpaper_job`，compose 之后、设壁纸之前调用 `fix_pic`，输出为同目录 `*_adjust.png`。

示例：

```bash
python run.py -a
python run.py --adjust
```

---

### `-v` / `--version`

打印程序名称与版本号后退出，不启动托盘与定时任务。

```bash
python run.py -v
```

---

### `-h` / `--help`

由 `argparse` 自动提供，打印用法与各参数说明后退出。

---

## 组合示例

```bash
# 碎片下载 + 默认 2200 分辨率（4d）
python run.py

# 碎片下载 + 11000 分辨率
python run.py -dl equal -r 11000

# 完整下载 + 2200 分辨率
python run.py --download complete --resolution 2200
```

打包后的可执行文件用法相同，将 `python run.py` 换成对应可执行文件名即可，例如：

```bash
himawari8-observer.exe -r 4400
himawari8-observer.exe -h
```

---

## 相关源码

| 文件 | 作用 |
|------|------|
| `run.py` | 启动入口，构造 `Config()` 解析参数 |
| `src/arg/arg.py` | 参数定义与读取接口 |
| `src/resolution_grade.py` | 分辨率档位映射与默认 |
| `src/metadata/soft_config.py` | 再导出分辨率列表与默认值 |
| `src/metadata/soft_info.py` | 程序名、版本、描述与帮助 epilog |

读取解析结果可使用：

- `Config().get_download_method()`（尚未接入流水线）
- `Config().get_download_resolution()`（`main()` 已接入壁纸更新）
- `Config().is_auto_adjust_picture()` → 启动时冻结为 `auto_adjust`，经 `build_wallpaper_job` 注入

> **接线说明**：`-r` / `-a` 在启动时解析并冻结进 `WallpaperJobRef`；托盘「图片分辨率」可运行中换档（不回写 CLI），并立即触发一次壁纸更新。「打开日志」打开 `LOG_PATH`。`-dl` 仍未驱动业务。
