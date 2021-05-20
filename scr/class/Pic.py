class Pic:
    base = "https://himawari8.nict.go.jp/img/D531106"
    pic_pixel = 550
    suffix = ".png"
    pic_size = 0  # 图片大小
    pic_chip = 0  # 图片有多少张。
    dl_state = 0  # 下载状态，0：下载。1下载完成。2下载中断

    def __init__(self, dic_info):
        self.equal = dic_info.equal  # 被等分为多少块
        self.year = dic_info.equal.year
        self.month = dic_info.equal.month
        self.day = dic_info.day
        self.hour = dic_info.hour
        self.minute = dic_info.minute
        self.seconds = dic_info.seconds
        self.locationX = dic_info.locationX  # X
        self.locationY = dic_info.locationY  # Y

        # 文件名，例如：052000_2_0.png
        self.pic_name = f"{self.hour}{self.minute}{self.seconds}_{self.locationX}_{self.locationY}{self.suffix}"

        # 下载url，例如：https://himawari8.nict.go.jp/img/D531106/20d/550/2021/05/15/052000_20_0.png
        self.dl_url = f"{self.base}/{self.equal}/{self.pic_pixel}/{self.year}/{self.month}/{self.day}/{self.pic_name}"

        # 存储目录，例如：20210515052000
        self.root_folder = f"{self.year}{self.month}{self.day}{self.hour}{self.minute}{self.seconds}"

        # 存储的当前文件夹目录，例如：..img/20210515052000/puzzle/0
        if self.equal is "1d":
            self.folder_path = f"../img/{self.root_folder}/complete/{self.locationY}"
        else:
            self.folder_path = f"../img/{self.root_folder}/puzzle/{self.locationY}"

        # 图片的相对路径，例如：..img/20210515052000/puzzle/0/052000_2_0.png
        self.path = f"{self.folder_path}/{self.pic_name}"
