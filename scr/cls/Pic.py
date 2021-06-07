from time import strftime


class Pic:
    base = "https://himawari8.nict.go.jp/img/D531106"
    pic_pixel = 550
    suffix = ".png"
    pic_size = 0  # 图片大小
    dl_finish = False

    def __init__(self, pic_time, equal):
        """
        根据字典信息构造类pic
        :param pic_time:字典类型，里面是构造pic类的信息。
        :param equal:str类型，从程序参数传入。意为被等分为多少块，例如：20d
        """
        arr_equal = {"1d": 1, "4d": 4, "8d": 8, "16d": 16, "20d": 20}
        self.equal_str = equal  # 被等分为多少块，例如：20d
        self.equal_int = arr_equal.get(self.equal_str)  # 被等分为多少块，例如：20

        self.year = strftime("%Y", pic_time)  # 年
        self.month = strftime("%m", pic_time)  # 月
        self.day = strftime("%d", pic_time)  # 日
        self.hour = strftime("%H", pic_time)  # 时
        self.minute = strftime("%M", pic_time)  # 分
        self.seconds = strftime("%S", pic_time)  # 秒

        self.arr_puzzle = []  # 下载时的文件夹路径，数组类型
        self.arr_url = []  # 下载时的url，数组类型
        self.arr_path = []  # 下载时的路径，数组类型
        self.dic = {}  # 下载时url与图片路径的映射，字典类型
        self.pic_chip = self.equal_int ** 2  # 图片有多少张。
        self.pic_side = self.pic_pixel * self.equal_int  # 图片的边为多少像素
        # self.arr_dl_state = [0 for x in range(0, self.pic_chip)]  # 下载状态，0：下载。1下载完成。2下载中断

        # 最终的图片名，例如：20d20210603052000.png
        self.pic_name = f"{self.equal_str}" \
                        f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}{self.suffix}"

        # 存储文件夹名称，例如：20d20210515052000
        self.root_folder = f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}"

        # 存储的当前文件夹目录，例如：..img/20d20210515052000/complete
        self.folder_path = f"../img/{self.root_folder}/complete"

        # 最终的图片相对路径，例如：..img/20210515052000/complete/20d20210603052000.png
        self.final_path = f"{self.folder_path}/{self.pic_name}"

        # 构建url和path的映射
        self.build_dic()

    def build_dic(self):
        # 根据时间获取所有需要下载的url和path
        print(f"正在构建url和path的映射字典。")
        location_x = 0
        location_y = 0
        while location_y < self.equal_int:
            while location_x < self.equal_int:
                # 碎片图片的名称，例如：084000_3_0.png
                pic_name = f"{self.hour}{self.minute}{self.seconds}_{location_x}_{location_y}{self.suffix}"

                # 碎片图片的下载url，例如：https://himawari8.nict.go.jp/img/D531106/4d/550/2021/06/04/084000_3_3.png
                url = f"{self.base}/{self.equal_str}/{self.pic_pixel}/{self.year}/{self.month}/{self.day}/{pic_name}"

                # 碎片图片的路径，例如：..img/20210515052000/4d/0/084000_3_0.png
                pic_path = f"../img/{self.root_folder}/{self.equal_str}/{location_y}/{pic_name}"

                # 碎片文件的路径，例如：..img/20210515052000/4d/0/
                puzzle_path = f"../img/{self.root_folder}/{self.equal_str}/{location_y}"
                self.arr_puzzle.append(puzzle_path)
                self.arr_url.append(url)
                self.arr_path.append(pic_path)
                location_x = location_x + 1
            location_x = 0
            location_y = location_y + 1

        # 把url和path组合成dic
        # 例如self.dic = {
        #     "url1": "..img/20210515052000/complete/20210603052000.png",
        #     "url2": "..img/20210515052000/complete/20210603052000.png",
        # }
        self.dic = dict(zip(self.arr_url, self.arr_path))

        # 在dic中添加了每张图片的下载状态。
        # 例如self.dic = {
        #     "url1": ["..img/20210515052000/complete/20210603052000.png",0],
        #     "url2": ["..img/20210515052000/complete/20210603052000.png",0]
        # }
        for key, val in self.dic.items():
            val = [val, 0]
            self.dic[key] = val
        if self.pic_chip == len(self.dic):
            print("url和path的映射字典构建完成。")

    def download_finish(self):
        """
        判断是否全部碎片都下载完成。
        :return:全部完成返回Ture，否则返回False
        """
        for key, val in self.dic.items():
            if val[1] == 0:
                self.dl_finish = False
            else:
                self.dl_finish = True
        return self.dl_finish


if __name__ == '__main__':
    from tool.tool import *
    from dl.dlinit import *
    from dl.dlpic import *

    requester = dl_init()
    last_time = get_last_time(requester)
    pic = Pic(last_time, "20d")

    print_dic(pic.dic)  # 实例化类
    pass
