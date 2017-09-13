import os

import redis
from rq import Worker, Queue, Connection

try:
    import config
    redis_url = config.redis_url
    print('using local config file')
except:
    print('using environment variable')
    redis_url = os.getenv('REDIS_URL')

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
 with Connection(conn):
 worker = Worker(map(Queue, listen))
 worker.work()
