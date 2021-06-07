"""
进度条
"""
from dl.dlpic import dl_pic_2

url = "https://himawari8.nict.go.jp/img/D531106/1d/550/2021/05/21/012000_0_0.png"
path = "../test/temp2.png"

# print("第一句话")
# print("第二句话",end="\r")
# print("第四句话",end="\r")
#
# print("\n第三句话")


dl_pic_2(url, path)


def progressbar():
    print('\r', '🍅' * filled + '--' * (duration - filled), '[{:.0%}]'.format(frac), extra, end='')
    pass


# with alive_bar(3) as bar:
#     time.sleep(3)
#     bar()  # file read, tokenizing
#     time.sleep(2)
#     bar()  # tokens ok, processing
#     time.sleep(5)
#     bar()  # we're done! 3 calls with total=3

if __name__ == '__main__':
    pass
