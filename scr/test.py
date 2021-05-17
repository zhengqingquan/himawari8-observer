"""

给出一个时间点，需要能得到这个时间点的全部图片
"""
import time

# 例如现在给出时间点
# 20210515052000 14：20：00
# https://himawari8.nict.go.jp/img/D531106/20d/550/2021/05/15/052000_7_19.png

# 如果下载的是空的，则会创建一个空的文件。

# 如果是空文件，加入图片的时候会抛出一个错误。PIL.UnidentifiedImageError: cannot identify image file 'try4.png'
from scr.dlpic import *
from scr.folder import *
import time

equal = "20d"
year = "2021"
month = "05"
day = "15"
hour = "05"
minute = "20"
seconds = "00"
# locationX = 7
# locationY = 18
locationX = 0
locationY = 0
pic_name = f"{hour}{minute}{seconds}_{locationX}_{locationY}.png"

# url = f"https://himawari8.nict.go.jp/img/D531106/{equal}/550/{year}/{month}/{day}/{hour}{minute}{seconds}_{locationX}_{locationY}.png"
# print("下载的url为：" + url)

# 是Y轴优先的，也就是说图片是从上到下，从左到右下载的。
# 文件夹1-20代表Y轴1-20。
# folder_path = f"../img/{year}{month}{day}{hour}{minute}{seconds}/puzzle/{locationY}"
# print("文件夹的相对路径为：" + folder_path)

# path = f"{folder_path}/{pic_name}"
# print("图片的相对路径为：" + path)

# create_folder(folder_path)
# dl_pic(url, path)
global time_create_pic
global time_close_pic
global dl_time
while locationY < 20:
    while locationX < 20:
        time_create_pic = time.process_time()
        pic_name = f"{hour}{minute}{seconds}_{locationX}_{locationY}.png"
        print("当前下载文件为：" + pic_name)

        url = f"https://himawari8.nict.go.jp/img/D531106/{equal}/550/{year}/{month}/{day}/{hour}{minute}{seconds}_{locationX}_{locationY}.png"
        print("下载的url为：" + url)

        folder_path = f"../img/{year}{month}{day}{hour}{minute}{seconds}/puzzle/{locationY}"
        print("文件夹的相对路径为：" + folder_path)

        path = f"{folder_path}/{pic_name}"
        print("图片的相对路径为：" + path)

        create_folder(folder_path)
        dl_pic(url, path)

        locationX = locationX + 1
        time_close_pic = time.process_time()
        print("整体运行时间为：" + str(time_close_pic - time_create_pic))
        print("================================================================")

    locationX = 0
    locationY = locationY + 1
