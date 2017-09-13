from apscheduler.schedulers.blocking import BlockingScheduler
from rq import Queue
from worker import conn
from run import run_gather_data, run_trader

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

sched = BlockingScheduler()

hiq = Queue('high', connection=conn)
lowq = Queue('low', connection=conn)

def gather_data():
    hiq.enqueue(run_gather_data)

def trader():
    lowq.enqueue(run_trader)

sched.add_job(trader, 'cron', day_of_week='mon-fri', hour=10, minute=0)
sched.add_job(gather_data, 'cron', day_of_week='mon-fri', hour='9-16', minute='*', second=0)


sched.start()
