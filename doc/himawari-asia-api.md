# himawari.asia API 文档

> 来源：`har/himawari.asia.har`（页面 `https://himawari.asia/`，抓取时间约 2026-07-16）  
> 站点配置：`https://himawari.asia/js/env.js`（appVersion `6.4.1k4`）

本文档整理该 HAR 中**实际请求到的接口**，以及 `env.js` 中定义、用于拼装瓦片/缩略图的 URL 模板。静态资源（CSS/JS/图标字体等）仅作分类索引，不逐条展开。

---

## 1. 概述

| 角色 | Base URL | 说明 |
|------|----------|------|
| 前端站点 | `https://himawari.asia` | 页面、配置、台风区域 JSON |
| 影像数据 CDN | `https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/` | `latest.json`、瓦片、缩略图、蓝石底图（由 `env.js` 的 `imgBaseUrl` / `thumbnailBaseUrl` / `movieBaseUrl` 指定） |

产品（`showImage` / path 中的产品 ID）：

| ID | 含义（据 env.js） | 刷新间隔 | 瓦片边长 |
|----|-------------------|----------|----------|
| `D531106` | 全盘真彩色（FD） | 600000 ms（10 分钟） | 550×550 |
| `D531107` | 日本区域等 | 150000 ms（2.5 分钟） | 600×480 |
| `FULL_24h` | 红外波段 + 蓝石底图 | 600000 ms | 550×550 |
| `D531108` | 台风/目标区域坐标（站点 JSON） | — | — |

---

## 2. 核心数据 API

### 2.1 获取最新观测时间

用于轮询最新可用影像时刻（页面约每 60s 检查一次，见 `latestDateCheckInterval`）。

#### D531106（全盘）

```
GET {imgBaseUrl}img/D531106/latest.json?_={timestamp}
```

**示例**

```
GET https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/latest.json?_=1784212009139
```

| 项 | 值 |
|----|-----|
| Method | `GET` |
| Query `_` | 缓存破坏参数（毫秒时间戳），可选但前端会带 |
| Status | `200` |
| Content-Type | `application/json` |

**响应示例**

```json
{
  "date": "2026-07-16 14:10:00",
  "file": "PI_H09_20260716_1410_TRC_FLDK_R10_PGPFD.png"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 最新观测时间，格式 `YYYY-MM-DD HH:MM:SS`（UTC） |
| `file` | string | 对应完整文件名（参考用） |

#### D531107（区域）

```
GET {imgBaseUrl}img/D531107/latest.json?_={timestamp}
```

**响应示例**

```json
{
  "date": "2026-07-16 14:17:30",
  "file": "PI_H09_20260716_1410_TRC_JP04_R10_PLLJP.png"
}
```

#### FULL_24h（红外 24h）

```
GET {imgBaseUrl}img/FULL_24h/latest.json?_={timestamp}
```

**响应示例**

```json
{
  "date": "2026-07-16 14:00:00"
}
```

> 注意：该产品的 `latest.json` 在 HAR 中**仅返回 `date`**，无 `file` 字段。

---

### 2.2 影像瓦片（Tile）

#### 全盘真彩色 D531106

```
GET {imgBaseUrl}img/D531106/{scale}/{tileSize}/{YYYY}/{MM}/{DD}/{HHMMSS}_{x}_{y}.png
```

| 路径参数 | 说明 |
|----------|------|
| `scale` | 缩放档：`1d` / `2d` / `4d` / `8d` / `16d` / `20d`（一边分成 N 块，`Nd` 表示 N） |
| `tileSize` | 单瓦片像素，全盘一般为 `550` |
| `YYYY/MM/DD` | 观测日期 |
| `HHMMSS` | 观测时刻（时分秒，无分隔符） |
| `x`, `y` | 瓦片坐标，范围 `[0, N)`，`N` 与 `scale` 中数字一致 |

**HAR 中示例**

```
GET https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/1d/550/2026/07/16/141000_0_0.png
```

| 项 | 值 |
|----|-----|
| Status | `200` / `304` |
| Content-Type | `image/png` |

**分辨率对照（一边像素 ≈ `N × 550`）**

| scale | 瓦片数 N×N | 合成边长 |
|-------|------------|----------|
| `1d` | 1×1 | 550 |
| `2d` | 2×2 | 1100 |
| `4d` | 4×4 | 2200 |
| `8d` | 8×8 | 4400 |
| `16d` | 16×16 | 8800 |
| `20d` | 20×20 | 11000 |

`env.js` 中 D531106 的 `foregroundImages` 模板：

```
img/D531106/%cd/%w/%date_%x_%y.png
img/D531106/%cd/%ws/coastline/%rgb_%x_%y.png
```

（`%cd`≈scale，`%w`≈tile 边长，`%date`≈`HHMMSS`，`%x`/`%y` 为坐标；海岸线为可选叠加层，本 HAR 未实际请求。）

#### FULL_24h 红外波段

```
GET {imgBaseUrl}img/FULL_24h/{band}/{scale}/{tileSize}/{YYYY}/{MM}/{DD}/{HHMMSS}_{x}_{y}.png
```

| 参数 | 说明 |
|------|------|
| `band` | `B01` … `B16`（HAR 示例为 `B13`） |

**HAR 中示例**

```
GET https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/FULL_24h/B13/1d/550/2015/07/07/015000_0_0.png
```

#### FULL_24h 蓝石底图（BlueMarble）

```
GET {imgBaseUrl}img/FULL_24h/BlueMarble/{scale}/{tileSize}/BlueMarble_{x}_{y}.png
```

**HAR 中示例**

```
GET https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/FULL_24h/BlueMarble/1d/275/BlueMarble_0_0.png
```

> 底图与时间无关；示例中 `tileSize` 为 `275`。

#### D531107（区域产品）

模板（env.js，本 HAR 未请求瓦片，仅请求了 `latest.json`）：

```
img/D531107/%cd/%w/%date_%x_%y.png
```

瓦片尺寸为 `600×480`，scale 档位与全盘不同（见 env.js `scales`）。

---

### 2.3 缩略图（Thumbnail）

#### D531106

```
GET {imgBaseUrl}img/D531106/thumbnail/{tileSize}/{YYYY}/{MM}/{DD}/{HHMMSS}_{x}_{y}.png
```

**HAR 中示例**

```
GET https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/thumbnail/550/2026/07/16/141000_0_0.png
```

| 项 | 值 |
|----|-----|
| Status | `200` / `304` |
| Content-Type | `image/png` |

env.js：`backgroundImage: "img/D531106/thumbnail/550/%date_0_0.png"`

#### D531107

```
img/D531107/thumbnail/600/%date_0_0.png
```

#### FULL_24h

```
img/FULL_24h/thumbnail/BlueMarble/550/BlueMarble_0_0.png
```

---

### 2.4 台风 / 目标区域坐标

```
GET https://himawari.asia/json/D531108/{YYYY}/{MM}/{DD}/{HHMMSS}.json
```

**HAR 中示例**

```
GET https://himawari.asia/json/D531108/2026/07/16/141000.json
```

| 项 | 值 |
|----|-----|
| Method | `GET` |
| Status | `200` |
| Content-Type | `application/json` |

**响应示例**

```json
{
  "northwest": [9.765, 148.040],
  "north": [9.797, 153.238],
  "northeast": [9.835, 157.518],
  "west": [5.177, 147.949],
  "center": [5.193, 153.081],
  "east": [5.213, 157.302],
  "southeast": [0.641, 147.915],
  "south": [0.643, 153.021],
  "southwest": [0.645, 157.220],
  "type": "TY"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `northwest` … `southwest` | `[lat, lon]` | 九宫格方位点经纬度 |
| `center` | `[lat, lon]` | 中心点 |
| `type` | string | 如 `"TY"`（台风），与 `env.js` 中 `targetArea.visibleType` 对应 |

---

### 2.5 事件列表（本 HAR 中失败）

```
GET https://himawari.asia/json/event.js?_={timestamp}
```

| 项 | 值 |
|----|-----|
| Status | `404` |
| 说明 | 请求时资源不存在；前端 `showEvent: true` 仍会尝试加载 |

---

## 3. 站点配置

### 3.1 环境配置

```
GET https://himawari.asia/js/env.js
```

| 项 | 值 |
|----|-----|
| Status | `200` |
| Content-Type | `application/javascript` |

以全局变量 `$Env` 暴露配置，与本项目相关的关键字段：

| 字段 | 示例值 | 说明 |
|------|--------|------|
| `host` | `https://himawari.asia` | 站点根 |
| `imgBaseUrl` | `https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/` | 影像根路径 |
| `thumbnailBaseUrl` | 同上 | 缩略图根路径 |
| `movieBaseUrl` | 同上 | 动画根路径 |
| `oldestDate` | `2015-07-07T01:50:00Z` | 可回溯最早时间 |
| `latestDateCheckInterval` | `60000` | 最新时间轮询间隔（ms） |
| `showImage` | `D531106` | 默认产品 |
| `image.download.url` | `https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV` | 官方完整图下载页（HAR 未请求） |

---

## 4. 推荐调用流程（壁纸类程序）

与本仓库「下载碎片图 → 合成 → 设壁纸」对应的最小链路：

```
1. GET {imgBaseUrl}img/D531106/latest.json
      → 取得 date（如 2026-07-16 14:10:00）

2. 将 date 解析为 YYYY, MM, DD, HHMMSS
      → 2026 / 07 / 16 / 141000

3. 按目标分辨率选择 scale（如 4d → 2200px）
   for y in 0..N-1:
     for x in 0..N-1:
       GET {imgBaseUrl}img/D531106/{Nd}/550/{YYYY}/{MM}/{DD}/{HHMMSS}_{x}_{y}.png

4. 按 (x,y) 拼接为完整 PNG，再设为桌面壁纸
```

示例（4d，最新时刻 `141000`）：

```
https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/4d/550/2026/07/16/141000_0_0.png
…
https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/4d/550/2026/07/16/141000_3_3.png
```

共 16 张。

---

## 5. HAR 中其它请求（非核心 API）

以下为页面静态/第三方资源，实现数据下载时一般**无需**对接。

### 5.1 himawari.asia 静态资源

| 类型 | 路径前缀 | 说明 |
|------|----------|------|
| 文档 | `/` | 首页 HTML |
| JS | `/js/*.js` | 业务脚本、jQuery 等 |
| CSS | `/css/*.css` | 样式 |
| 字体 | `/font/pe-icon-7-*` | 图标字体 |
| 图片 | `/img/*` | UI 按钮 SVG/PNG、Logo |
| 组件 | `/tileViewer/`、`/timeline/`、`/picker/`、`/eventViewer/` | 前端组件 |

### 5.2 第三方

| URL | 用途 |
|-----|------|
| `fonts.googleapis.com/css?family=Oswald` | 字体 |
| `connect.facebook.net/.../sdk.js` | Facebook SDK |
| `www.googletagmanager.com/gtag/js` | GA |
| `www.google-analytics.com/analytics.js` | GA |

---

## 6. 与旧 NICT 域名对照

本项目历史代码曾使用：

```
https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json
https://himawari8.nict.go.jp/img/D531106/...
```

当前 himawari.asia 前端已改用京都大学镜像：

```
https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/...
```

路径结构（`img/{product}/latest.json`、`img/{product}/{scale}/{size}/...`）与旧站一致，**仅需替换 Base URL**。

---

## 7. HAR 请求清单（数据相关）

| # | Method | URL 模式 | Status |
|---|--------|----------|--------|
| 1 | GET | `.../img/D531106/latest.json` | 200 |
| 2 | GET | `.../img/D531107/latest.json` | 200 |
| 3 | GET | `.../img/FULL_24h/latest.json` | 200 |
| 4 | GET | `.../img/D531106/1d/550/{date}/..._0_0.png` | 304 |
| 5 | GET | `.../img/D531106/thumbnail/550/{date}/..._0_0.png` | 304 |
| 6 | GET | `.../img/FULL_24h/B13/1d/550/{date}/..._0_0.png` | 200 |
| 7 | GET | `.../img/FULL_24h/BlueMarble/1d/275/BlueMarble_0_0.png` | 200 |
| 8 | GET | `https://himawari.asia/json/D531108/{date}.json` | 200 |
| 9 | GET | `https://himawari.asia/json/event.js` | 404 |
| 10 | GET | `https://himawari.asia/js/env.js` | 200 |

---

*文档根据 `har/himawari.asia.har` 自动整理，镜像主机名可能随站点配置变更，以 `env.js` 中 `imgBaseUrl` 为准。*
