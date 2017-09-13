from apscheduler.schedulers.blocking import BlockingScheduler
from rq import Queue
from worker import conn
from run import run_gather_threads, run_gather_comments

import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

sched = BlockingScheduler()

q = Queue(connection=conn)

def gather_comments():
 q.enqueue(run_gather_comments)

sched.add_job(gather_comments) #enqueue right away once
sched.add_job(gather_comments, 'interval', minutes=1)

sched.start()
