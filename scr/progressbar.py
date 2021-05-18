
from alive_progress import alive_bar
import time

with alive_bar(3) as bar:
    time.sleep(3)
    bar()  # file read, tokenizing
    time.sleep(2)
    bar()  # tokens ok, processing
    time.sleep(5)
    bar()  # we're done! 3 calls with total=3