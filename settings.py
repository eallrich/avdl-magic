"""avdl-magic: A perhaps not-so-magical audio/video download assistant.
Copyright (C) 2015  Evan Allrich

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
jobkey = lambda id: 'job:%s' % id
joblist = 'alljobs'
