import os

# logging
# -------
logging = {
    'format': '%(asctime)s | [%(levelname)s] %(message)s',
    'level':  'INFO',
}

# redis
# -----
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
