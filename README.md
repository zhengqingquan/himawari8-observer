# himawari8-observer

这是一个每隔一段时间把himawari8卫星对地球的图像设为桌面背景的程序。图像的分辨率可以达到11000x11000！

<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/235000_0_0.png?raw=true" width="300" >
<img src="https://github.com/zhengqingquan/gallery/blob/main/himawari8-observer/1/154000_0_0.png?raw=true" width="300">

取名 himawari8-observer 意思就是观察者。把自己当为卫星观察地球。

https://github.com/zhengqingquan/himawari8-observer

https://himawari8.nict.go.jp/

https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV

## 说明

2024 年 7 月 1 日以后停止了对 Himawari 卫星的数据服务。

但 https://himawari8.nict.go.jp/ 仍然可以访问。

## 使用

## 目前支持：
* win10


**必须要做的事：**
- [x] 获得400张550×550的图片
- [x] 合成11000x11000的图片
- [x] 根据路径更换桌面
- [ ] 命令行参数
- [ ] 程序运行提示
- [ ] 下载进度条
- [x] 将png文件变成jpg文件（为了可以在win7上使用）
- [ ] 程序的运行和停止
- [ ] 开机自启动

**后面需要尝试的事：**
- [ ] 提升下载速度的优化
- [ ] 图片可以自行适配不同大小的桌面
- [ ] UI
- [ ] 系统桌面提醒
- [ ] 流量计数
- [x] 提供其他分辨率的下载
- [ ] 其他系统桌面更换
- [ ] 程序的安装和卸载


## 配置

请查看 `requirements.txt`

## 版本
1.1.0 新增：可以直接下载11000x110000的图片
1.0.0 初版：可以合成11000x11000的图片。

## 程序的运行与停止

## 打包

打包使用的python pyinstaller包

```cmd
pyinstaller --noconsole --onefile --name himawari8-observer run.py
```

## 安装


## 卸载


## 鸣谢
很感谢其它同类型的项目给我的一些启发帮助。
很高兴日本气象厅能公开这些照片。