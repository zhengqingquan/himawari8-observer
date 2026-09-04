# himawari.asia / NICT 同源 API 文档

> 来源：  
> 1. 历史上对 `https://himawari.asia/` 的浏览器抓包整理（约 2026-07-16）  
> 2. `doc/himawari8.nict.go.jp.har`（`https://himawari8.nict.go.jp/`，约 2026-09-04，含台风区 JSON / `event.js` / GPS 前端逻辑）  
> 站点配置：`/js/env.js`（himawari.asia 曾见 `6.4.1k4`；NICT 抓包为 `6.4.1n`）

本文档整理 HAR 中**实际请求到的接口**、前端拼装用的 URL 模板，以及**明确不是 HTTP API** 的能力（如 GPS）。静态资源（CSS/图标字体等）仅作分类索引。

---

## 1. 概述

| 角色 | Base URL | 说明 |
|------|----------|------|
| NICT 官方站 | `https://himawari8.nict.go.jp/` | 页面、配置、台风区 JSON、影像（`env.js` 中 `imgBaseUrl` 等均指向本域） |
| himawari.asia 前端 | `https://himawari.asia` | 同源页面镜像；影像可能改走京都大学 CDN（以该站 `env.js` 为准） |
| 影像 CDN（asia 配置） | `https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/` | 仅 himawari.asia 的 `imgBaseUrl` / `thumbnailBaseUrl` / `movieBaseUrl` 曾指向此处 |

下文 `{imgBaseUrl}` / `{host}`：NICT 抓包均为 `https://himawari8.nict.go.jp/`；asia 站请读其 `env.js`。

产品（`showImage` / path 中的产品 ID）：

| ID | 含义（据 env.js） | 刷新间隔 | 瓦片边长 |
|----|-------------------|----------|----------|
| `D531106` | 全盘真彩色（FD） | 600000 ms（10 分钟） | 550×550 |
| `D531107` | 日本区域等 | 150000 ms（2.5 分钟） | 600×480 |
| `FULL_24h` | 红外波段 + 蓝石底图 | 600000 ms | 550×550 |
| `D531108` | 台风/目标区域坐标 JSON（站点 `/json/`，非瓦片产品） | 随观测时刻 | — |

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
GET https://himawari8.nict.go.jp/img/D531106/latest.json?_=1788487475411
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

NICT 抓包（2026-09-04）同结构：

```json
{
  "date": "2026-09-04 00:50:00",
  "file": "PI_H09_20260904_0050_TRC_FLDK_R10_PGPFD.png"
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

### 2.4 台风 / 目标区域坐标（D531108）

前端在切换观测时刻时请求（`himawari8-image.js`）：

```
GET {host}/json/D531108/{YYYY}/{MM}/{DD}/{HHMMSS}.json
```

| 项 | 值 |
|----|-----|
| Method | `GET` |
| Status | `200`（有台风目标区时）；无数据时前端显示 `No Typhoon Now`（`no_typhoon`） |
| Content-Type | `application/json` |
| `env.js` | `targetArea: { visible: true, visibleType: "TY" }` |

**NICT HAR 示例（2026-09-04）**

```
GET https://himawari8.nict.go.jp/json/D531108/2026/09/04/005000.json
```

**himawari.asia 历史示例**

```
GET https://himawari.asia/json/D531108/2026/07/16/141000.json
```

**响应示例（NICT）**

```json
{
  "northwest": [35.119, 120.753],
  "north": [34.890, 127.489],
  "northeast": [34.776, 132.645],
  "west": [29.189, 122.248],
  "center": [29.024, 128.437],
  "east": [28.941, 133.211],
  "southeast": [23.759, 123.264],
  "south": [23.637, 129.088],
  "southwest": [23.576, 133.602],
  "type": "TY"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `northwest` … `southwest` | `[lat, lon]` | 九宫格方位点经纬度（画目标框） |
| `center` | `[lat, lon]` | 中心点（台风场景下即台风中心附近） |
| `type` | string | `"TY"` = 台风目标区；与 `visibleType: "TY"`、UI `[type="TY"]` 对应 |

> 时刻 `{HHMMSS}` 通常与当前展示的 `D531106`（或所选产品）观测时间对齐（示例中全盘 `latest` 为 `00:50:00` → `005000.json`）。

#### 相关媒体模板（前端拼装；本 NICT HAR 未逐条请求）

点击目标区后可能播放快照/动画（`himawari8-image.js`）：

```
{imgBaseUrl}img/D531108/SnapShot/{YYYY}/{MM}/{DD}/{480|720}/hima8{YYYY}{MM}{DD}{HHMMSS}r3.png
{movieBaseUrl}{YYYY}{MM}{DD}_pir3.mp4
```

---

### 2.5 事件列表

```
GET {host}/json/event.js?_={timestamp}
```

| 站点 | Status | 说明 |
|------|--------|------|
| `himawari8.nict.go.jp`（2026-09-04 HAR） | `200` | 返回 JSON 数组（历史问答/事件条目：`status`、`category`、`view_url`、`st`/`et` 等） |
| `himawari.asia`（历史 HAR） | `404` | 当时资源不存在；前端 `showEvent: true` 仍会尝试加载 |

**NICT 条目字段（摘录）**

| 字段 | 说明 |
|------|------|
| `status` | 如 `"1"` |
| `category` | 如 `"qa"` |
| `view_url` / `url` | 站点内深链 |
| `st` / `et` | 事件起止时间文案 |
| `organization` / `user` | 发布方信息 |

---

### 2.6 用户当前位置（非 HTTP API）

页面「GPS」按钮**不请求** NICT 位置接口，而是浏览器本地定位：

```
navigator.geolocation.getCurrentPosition → 地图移到 (longitude, latitude) → 叠加 #gps_pin
```

| 项 | 说明 |
|----|------|
| HAR 可见 | 仅 `gps_button*.svg`、`gps_pin.png` 等静态图 |
| 无服务端响应 | 抓包中不会出现「当前用户 lat/lon」的 JSON |
| 不支持时 | `!navigator.geolocation` 则移除 GPS 按钮；失败弹 `gps_error` 对话框 |

若程序需要「当前位置」，应使用本机 OS / Geolocation，**不能**从 Himawari HTTP API 获取。

---

## 3. 站点配置

### 3.1 环境配置

```
GET {host}/js/env.js
```

| 项 | himawari.asia（历史） | himawari8.nict.go.jp（2026-09-04） |
|----|----------------------|-----------------------------------|
| Status | `200` | `200` |
| Content-Type | `application/javascript` | 同左 |
| `appVersion` | `6.4.1k4` | `6.4.1n` |

以全局变量 `$Env` 暴露配置，与本项目相关的关键字段：

| 字段 | NICT 抓包示例 | 说明 |
|------|---------------|------|
| `host` | `https://himawari8.nict.go.jp` | 站点根 |
| `imgBaseUrl` | `https://himawari8.nict.go.jp/` | 影像根路径（asia 站可能为京都 CDN） |
| `thumbnailBaseUrl` | 同上 | 缩略图根路径 |
| `movieBaseUrl` | 同上 | 动画根路径 |
| `oldestDate` | `2015-07-07T01:50:00Z` | 可回溯最早时间 |
| `latestDateCheckInterval` | `60000` | 最新时间轮询间隔（ms） |
| `showImage` | `D531106` | 默认产品 |
| `showEvent` | `true` | 是否拉 `json/event.js` |
| `targetArea.visibleType` | `"TY"` | 目标区类型（台风） |
| `navigateBand13` | `{ latitude: 36, longitude: 140, altitude: 10 }` | 红外导航用参考点（非用户 GPS） |
| `image.download.url` | `https://sc-web.nict.go.jp/himawari/`（NICT）；asia 历史曾为 `sc-nc-web.../shareDirDownload/...` | 官方完整图下载页 |
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

### 5.1 站点静态资源（himawari.asia / himawari8.nict.go.jp 同源结构）

| 类型 | 路径前缀 | 说明 |
|------|----------|------|
| 文档 | `/` | 首页 HTML |
| JS | `/js/*.js` | `env.js`、`himawari8-image.js` 等 |
| CSS | `/css/*.css` | 含 `no_typhoon` / GPS 按钮文案样式 |
| 字体 | `/font/pe-icon-7-*` | 图标字体 |
| 图片 | `/img/*` | UI；含 `gps_button*.svg`、`gps_pin.png`、`target_area_button*.svg`（**不是**位置 API） |
| 组件 | `/tileViewer/`、`/timeline/`、`/picker/`、`/eventViewer/` | 前端组件 |

### 5.2 第三方

| URL | 用途 |
|-----|------|
| `fonts.googleapis.com/css?family=Oswald` | 字体 |
| `connect.facebook.net/.../sdk.js` | Facebook SDK |
| `www.googletagmanager.com/gtag/js` | GA |
| `www.google-analytics.com/analytics.js` | GA |

---

## 6. 与旧 NICT 下载域对照

本项目运行时使用（下载瓦片）：

```
https://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json
https://himawari8.nict.go.jp/img/D531106/...
```

官方实时网页（`himawari8.nict.go.jp`）的 `env.js` 将影像也放在**同域**：

```
https://himawari8.nict.go.jp/img/D531106/latest.json
https://himawari8.nict.go.jp/img/D531106/{scale}/550/...
https://himawari8.nict.go.jp/json/D531108/{YYYY}/{MM}/{DD}/{HHMMSS}.json
```

himawari.asia 前端曾改用京都大学镜像：

```
https://jh190005-4.kudpc.kyoto-u.ac.jp/himawari/img/D531106/...
```

路径结构（`img/{product}/latest.json`、`img/{product}/{scale}/{size}/...`、`json/D531108/...`）一致，**按 `env.js` 的 Base URL 替换即可**。

---

## 7. HAR 请求清单（数据相关）

### 7.1 himawari.asia / 京都 CDN（历史）

| # | Method | URL 模式 | Status |
|---|--------|----------|--------|
| 1 | GET | `.../img/D531106/latest.json` | 200 |
| 2 | GET | `.../img/D531107/latest.json` | 200 |
| 3 | GET | `.../img/FULL_24h/latest.json` | 200 |
| 4–9 | GET | `.../img/D531106/{1d…20d}/550/{date}/..._{x}_{y}.png` | 200 / 304 |
| 10 | GET | `.../img/D531106/thumbnail/550/{date}/..._0_0.png` | 200 / 304 |
| 11 | GET | `.../img/FULL_24h/B13/1d/550/{date}/..._0_0.png` | 200 / 304 |
| 12 | GET | `.../img/FULL_24h/BlueMarble/1d/275/BlueMarble_0_0.png` | 200 |
| 13 | GET | `https://himawari.asia/json/D531108/{date}.json` | 200 |
| 14 | GET | `…/json/event.js` | 404 |
| 15 | GET | `…/js/env.js` | 200 |

### 7.2 himawari8.nict.go.jp（`doc/himawari8.nict.go.jp.har`，2026-09-04）

| # | Method | URL 模式 | Status |
|---|--------|----------|--------|
| 1 | GET | `/img/D531106/latest.json` | 200 |
| 2 | GET | `/img/D531107/latest.json` | 200 |
| 3 | GET | `/img/FULL_24h/latest.json` | 200 |
| 4 | GET | `/json/D531108/2026/09/04/005000.json` | 200（`type: TY`） |
| 5 | GET | `/json/event.js` | 200 |
| 6 | GET | `/js/env.js` | 200（`appVersion` `6.4.1n`） |
| 7 | GET | `/img/D531106/thumbnail/550/2026/09/04/005000_0_0.png` | 200 |
| 8 | GET | `/img/D531106/2d/550/2026/09/04/005000_{x}_{y}.png` | 200（视口局部） |
| — | — | 用户 GPS 坐标 | **无 HTTP 请求**（仅 `navigator.geolocation`） |

> 高档位（`8d` / `16d` / `20d`）在浏览器 HAR 中多为**视口局部瓦片**，不一定请求满 N×N 网格；壁纸程序若要整图合成，仍应按档位拉齐全部瓦片。

---

*文档根据 himawari.asia 与 `himawari8.nict.go.jp` 抓包整理；镜像主机名可能随站点配置变更，以对应站 `env.js` 中 `imgBaseUrl` 为准。*
