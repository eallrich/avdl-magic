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

import datetime
import logging
import os
from subprocess import call

from flask import url_for
import lxml.html
import redis
import requests
from rq import get_current_job, Queue

import settings


logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)

redis = redis.from_url(settings.redis_url)
rqueue = Queue(connection=redis)
# Convenience
jobkey = settings.jobkey
joblist = settings.joblist


def set_title(job_id, url):
    """Sets the job's page_title field using the url's <title>."""
    r = requests.get(url)
    tree = lxml.html.fromstring(r.content)
    title = tree.findtext('.//title')[:-10] # Removing suffix: " - YouTube"
    redis.hset(jobkey(job_id), 'page_title', title)


def download(url):
    """Our workhorse function. Calls youtube-dl to do our dirty work."""
    job_id = get_current_job().get_id()
    destination = os.path.join(settings.download_dir, "%(title)s.%(ext)s")
    # Start with getting the page title
    set_title(job_id, url)
    # Then get the video
    options = [
        'youtube-dl',
        '--ffmpeg-location=/app/ffmpeg/',
        '--default-search=ytsearch:',
        '--restrict-filenames',
        '--format=bestaudio',
        '--extract-audio',
        '--audio-format=mp3',
        '--audio-quality=1',
        '--output=%s' % destination,
        '--no-mtime',
        url,
    ]
    print("Running: %s" % ' '.join(options))
    call(options, shell=False)
    return "Done"


def nicetimedelta(ts):
    """Return human-friendly timedelta strings for 'now() - ts'"""
    old_datetime = datetime.datetime.fromtimestamp(float(ts))
    now = datetime.datetime.now()
    difference = now - old_datetime
    if difference.seconds < 60: # don't show '0 minutes ago'
        return "just now"
    elif difference.seconds < 120: # use singular 'minute'
        return "1 minute ago"
    else:
        return "%d minutes ago" % int(difference.seconds / 60)


def get_files_available(where=settings.download_dir, extension='.mp3'):
    """Provides metadata for any files available for download.

    Returns a list of three-element lists:
        [ [ filename, human-friend mtime, size ],
            ...
        ]"""
    files = [f for f in os.listdir(where) if f.endswith(extension)]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(where, x)), reverse=True)
    path = lambda x: os.path.join(where, x)
    files = [
        [
            f,
            nicetimedelta(os.path.getmtime(path(f))),
            os.path.getsize(path(f))
        ] for f in files]
    return files


def validate_url(url):
    """Confirm the input URL is reasonably safe to feed to youtube-dl."""
    if url.startswith('http://'):
        # Standardize on https
        url = url.replace('http://', 'https://')
    if url.startswith('https://www.youtube.com/'):
        # We're good
        return url
    else:
        return None


def queued_job_info():
    """Provides metadata for all known jobs.

    Returns a list of dictionaries:
        [ {job_id, request_url, submitted, page_title, status},
          ...,
        ]"""
    jobs = []
    # Show the ten most recent jobs
    for job_id in redis.lrange(joblist, 0, 9):
        job = rqueue.fetch_job(job_id)
        if job is None:
            continue # don't bother showing the 'deleted' jobs
        job_details = redis.hgetall(jobkey(job_id))
        job_details['submitted'] = nicetimedelta(job_details['submitted'])
        job_details['status'] = job.get_status()
        jobs.append(job_details)
    return jobs


def sizeof_fmt(num, suffix='B'):
    """Graciously provided by http://stackoverflow.com/a/1094933

    Minor modification: Use base 10 sizes instead of SI units."""
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1000.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1000.0
    return "%.1f%s%s" % (num, 'Y', suffix)


def downloaded_files_info():
    """Provides metadata for all known downloads.

    Returns a list of dictionaries:
        [ {name, modified, size, url},
          ...,
        ]"""
    files = get_files_available()
    url = lambda x: url_for('download_file', filename=x)
    files_with_urls = [{
        'name': name,
        'modified': modified,
        'size': sizeof_fmt(size),
        'url': url(name),
    } for name, modified, size in files]
    return files_with_urls

