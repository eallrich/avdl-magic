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

import redis
from rq import Worker, Queue, Connection

import settings

redis = redis.from_url(settings.redis_url)

if __name__ == '__main__':
    with Connection(redis):
        worker = Worker([Queue('default')])
        worker.work()
