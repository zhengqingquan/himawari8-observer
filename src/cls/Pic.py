from time import strftime
from src.dl.dlinit import dl_init
from src.metadata.soft_config import PROGRAM_DIR_ABS_PATH

class Pic(object):
    """
    图片分为两种下载方式，碎片方式和完整方式。
    碎片下载方式（equal way）：图片在下载过程中根据像素被分为多份，分别下载，最后再合成一张图片。
    完整下载方式（complete way）：图片在下载过程中就是一张完整的图片。
    """
    himawari8_base = "https://himawari8.nict.go.jp/img/D531106"  # 碎片下载方式使用的url，后面会合成完整的下载方式，不应该被修改
    sc_nc_web_base = "https://sc-nc-web.nict.go.jp/wsdb_osndisk/fileSearch/download"  # 完整下载方式使用的url
    hash_base = "https://sc-nc-web.nict.go.jp/wsdb_osndisk/shareDirDownload/bDw2maKV"  # 获取Token时使用的url
    suffix = "png"  # 图片类型后缀
    pic_pixel = 550  # 图片基本像素大小
    pic_size = 0  # 图片大小
    dl_finish_equal = False  # 碎片下载方式下，图片是否下载完成的状态位
    dl_finish_cpl = False  # 完整下载方式下，图片是否下载完成的状态位

    def __init__(self, pic_time, equal):
        """
        根据传入的时间和图片碎片数量来构造图片实例。
        :param pic_time:照片的时间。
        :param equal:str类型，从程序参数传入。意为被等分为多少块，例如：20d
        """
        arr_equal = {"1d": 1, "4d": 4, "8d": 8, "16d": 16, "20d": 20}
        self.str_equal = equal  # 被等分为多少块，str类型，例如：20d
        self.int_equal = arr_equal.get(self.str_equal)  # 被等分为多少块，int类型，例如：20

        self.year = strftime("%Y", pic_time)  # 年
        self.month = strftime("%m", pic_time)  # 月
        self.day = strftime("%d", pic_time)  # 日
        self.hour = strftime("%H", pic_time)  # 时
        self.minute = strftime("%M", pic_time)  # 分
        self.seconds = strftime("%S", pic_time)  # 秒

        self.arr_puzzle = []  # 下载时的文件夹路径，数组类型
        self.arr_url = []  # 下载时的url，数组类型
        self.arr_path = []  # 下载时的文件路径，数组类型
        self.dic = {}  # 下载时url与图片路径的映射，字典类型
        self.post_data = {}  # 使用post下载时候的data数据。
        self.pic_chip = self.int_equal ** 2  # 图片有多少张。
        self.pic_side = self.pic_pixel * self.int_equal  # 图片的边为多少像素

        # 存储图片时的顶级路径的文件夹名称，例如：img
        # 用于下载时保存的文件夹名称，可以修改。
        self.folder_top = "img"

        # 存放完整图片的文件夹名称，例如：complete
        # 用于下载时保存的文件夹名称，可以修改。
        self.folder_complete = "complete"

        # 存储文件夹名称，例如：20210515052000
        # 用于下载时保存的文件夹名称，可以修改。
        self.folder_root = f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}"

        # 碎片下载方式下，最终的图片名，例如：20d20210603052000.png
        # 该名称用于构建下载时使用的url，为固定格式，不应该被修改。
        self.pic_name_equal = f"{self.str_equal}" \
                              f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}.{self.suffix}"

        # 完整下载方式下，最终的图片名，例如：hima820210608022000fd.png
        # 该名称用于构建下载时使用的url，为固定格式，不应该被修改。
        self.pic_name_cpl = f"hima8" \
                            f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}fd.{self.suffix}"

        # 存储的当前文件夹目录，用来创建文件夹。例如：..img/20d20210515052000/complete
        # 用于下载时保存的文件夹路径，不建议修改。
        self.folder_path = PROGRAM_DIR_ABS_PATH.joinpath(f"./{self.folder_top}/{self.folder_root}/{self.folder_complete}")

        # 碎片下载方式下，最终的图片相对路径，用来最终合成。例如：..img/20210515052000/complete/20d20210603052000.png
        # 用于下载时保存的文件夹路径，不建议修改。
        self.final_path_equal = PROGRAM_DIR_ABS_PATH.joinpath(f"{self.folder_path}/{self.pic_name_equal}")

        # 完整下载方式下，最终的图片相对路径，用来下载。例如..img/20210515052000/complete/hima820210608022000fd.png
        # 用于下载时保存的文件夹路径，不建议修改。
        self.final_path_cpl = PROGRAM_DIR_ABS_PATH.joinpath(f"{self.folder_path}/{self.pic_name_cpl}")

        # 在碎片下载方式下，构建url和path的映射
        self.build_dic()

        # 在完整下载方式下，构建post请求的data
        self.build_post_data()

    def build_dic(self):
        """
        根据时间获取所有需要下载的url和path
        :return:
        """
        print(f"正在构建url和path的映射字典。")
        location_x = 0
        location_y = 0

        # 构建文件夹时防止当20d的情况下会下载20x20，共四百张图片在一个文件夹中，这里做了写分开的组合。
        while location_y < self.int_equal:
            while location_x < self.int_equal:
                # 下载时url使用的碎片图片的名称，例如：084000_3_0.png
                pic_name = f"{self.hour}{self.minute}{self.seconds}_{location_x}_{location_y}.{self.suffix}"

                # 每张碎片图片的下载url，例如：https://himawari8.nict.go.jp/img/D531106/4d/550/2021/06/04/084000_3_3.png
                url = f"{self.himawari8_base}/{self.str_equal}/{self.pic_pixel}" \
                      f"/{self.year}/{self.month}/{self.day}/{pic_name}"

                # 碎片文件的路径，用来创建文件夹。例如：..img/20210515052000/4d/0
                puzzle_path = PROGRAM_DIR_ABS_PATH.joinpath(f"./{self.folder_top}/{self.folder_root}/{self.str_equal}/{location_y}")

                # 每张碎片图片的存储路径，用来下载。例如：..img/20210515052000/4d/0/084000_3_0.png
                pic_path = PROGRAM_DIR_ABS_PATH.joinpath(f"{puzzle_path}/{pic_name}")

                self.arr_url.append(url)
                self.arr_puzzle.append(puzzle_path)
                self.arr_path.append(pic_path)
                location_x = location_x + 1
            location_x = 0
            location_y = location_y + 1

        # 把url和path组合成字典dic
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

    def build_post_data(self):
        self.post_data = {"_method": "POST",
                          "data[FileSearch][is_compress]": "false",
                          "data[FileSearch][fixedToken]": "",
                          "data[FileSearch][hashUrl]": "bDw2maKV",
                          "action": "dir_download_dl",
                          "filelist[0]":
                              f"/osn-disk/webuser/wsdb/share_directory/bDw2maKV/{self.suffix}/Pifd/"
                              f"{self.year}/{self.month}-{self.day}/{self.hour}/{self.pic_name_cpl}",
                          "dl_path":
                              f"/osn-disk/webuser/wsdb/share_directory/bDw2maKV/{self.suffix}/Pifd/"
                              f"{self.year}/{self.month}-{self.day}/{self.hour}/{self.pic_name_cpl}"
                          }
        print("post请求的data构建完成。")

    def download_finish(self):
        """
        判断是否全部碎片都下载完成。
        :return:全部完成返回Ture，否则返回False
        """
        self.dl_finish_equal = True
        for key, val in self.dic.items():
            if val[1] == 0:
                self.dl_finish_equal = False
        return self.dl_finish_equal


if __name__ == '__main__':
    from tool.tool import *
    from dl.dlinit import *
    from dl.dlpic import *

    requester = dl_init()
    last_time = get_last_time(requester)
    pic = Pic(last_time, "20d")  # 实例化类

    print_dic(pic.dic)  # 打印碎片下载方式的映射
    print_dic(pic.post_data)  # 打印完整下载方式下post请求的data
    print(pic.download_finish())  # 打印看是否下载完整
    pass
