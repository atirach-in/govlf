from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from controllers import scraping

async def my_job():
    print(f"ทำงานตอน: {datetime.now()}")
    await scraping.sync_data()
    

scheduler = BackgroundScheduler()
# ทำงานทุกวันตอน 3:30 AM
scheduler.add_job(my_job, 'cron', minute=0)
# scheduler.add_job(my_job, 'cron', hour=3, minute=30)

scheduler.start()

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()