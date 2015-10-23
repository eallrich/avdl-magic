import base64
import os

# appliction
# ----------
secret_key = base64.b64encode(os.urandom(40))
download_dir = 'downloads'
try:
    os.mkdir(download_dir)
except:
    pass # Already exists

# logging
# -------
logging = {
    'format': '[%(levelname)s] %(message)s',
    'level':  'INFO',
}

# redis
# -----
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
jobkey = lamda id: 'job:%s' % id
joblist = 'alljobs'
