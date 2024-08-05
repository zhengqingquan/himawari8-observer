from apscheduler.schedulers.blocking import BlockingScheduler
from src.main import main
import sys
import datetime
from src.metadata.soft_config import DOWNLOAD_INTERVAL_TIME

def stat_time_tast():

    scheduler = BlockingScheduler()

    # 添加一个每隔20分钟执行一次
    scheduler.add_job(main, 'interval', seconds=DOWNLOAD_INTERVAL_TIME, next_run_time=datetime.datetime.now())

    # 也可以添加其他类型的任务，比如每天在特定时间执行
    # scheduler.add_job(job, 'cron', hour=10, minute=30)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)
        sys.exit(0)
