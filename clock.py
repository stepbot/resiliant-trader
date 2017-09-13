from apscheduler.schedulers.blocking import BlockingScheduler
from rq import Queue
from worker import conn
from run import run_trader

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

sched = BlockingScheduler()

q = Queue(connection=conn)


#def gather_data():
    #q.enqueue(run_gather_data)

def trader():
    q.enqueue(run_trader)

sched.add_job(trader, 'cron', day_of_week='mon-fri', hour=10, minute=30)
#sched.add_job(gather_data, 'cron', day_of_week='mon-fri', hour='9-16', minute='*', second=0)


sched.start()
