import redis
from rq import Worker, Queue, Connection

import settings

redis = redis.from_url(settings.redis_url)

if __name__ == '__main__':
    with Connection(redis):
        worker = Worker([Queue('default')])
        worker.work()
