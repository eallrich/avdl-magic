import base64
import datetime
import json
import logging
import os
from subprocess import call
import time

from flask import Flask, render_template, request, send_from_directory, url_for
import lxml.html
import redis
import requests
from rq import get_current_job, Queue
from rq.job import Job

import settings

logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = base64.b64encode(os.urandom(40))

redis = redis.from_url(settings.redis_url)
rqueue = Queue(connection=redis)

# Make sure the destination directory exists
try:
    os.mkdir('downloads')
except OSError:
    # Already exists
    pass

def download(yturl):
    """Our workhorse function. Calls youtube-dl to do our dirty work."""
    # Start with getting the title
    r = requests.get(yturl)
    tree = lxml.html.fromstring(r.content)
    title = tree.findtext('.//title')[:-10] # Removing suffix: " - YouTube"
    job_id = get_current_job()
    redis.hset('job:%s' % job_id, 'page_title', title)
    # Then get the video
    options = [
        'youtube-dl',
        '--default-search=ytsearch:',
        '--restrict-filenames',
        '--format=bestaudio',
        '--extract-audio',
        '--audio-format=mp3',
        '--audio-quality=1',
        '--output=downloads/%(title)s-%(id)s.%(ext)s',
        '--no-mtime',
        yturl,
    ]
    #logger.info("Running with options:\n    %s" % ' '.join(options))
    call(options, shell=False)
    return "Done"


def get_files_available(where='downloads', extension='.mp3'):
    """Provides metadata for any files available for download.

    Returns a list of three-element lists:
        [ [ filename, ISO 8601 mtime, size ],
            ...
        ]"""
    files = [f for f in os.listdir(where) if f.endswith(extension)]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(where, x)), reverse=True)
    path = lambda x: os.path.join(where, x)
    makedatetime = lambda ts: datetime.datetime.fromtimestamp(ts)
    nicedate = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S")
    files = [
        [
            f,
            nicedate(makedatetime(os.path.getmtime(path(f)))),
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
    makedatetime = lambda ts: datetime.datetime.fromtimestamp(float(ts))
    nicedate = lambda ts: makedatetime(ts).strftime("%Y-%m-%dT%H:%M:%S")
    jobs = []
    # Show the ten most recent jobs
    for job_id in redis.lrange('alljobs', 0, 9):
        job_details = redis.hgetall('job:%s' % job_id)
        job_details['submitted'] = nicedate(job_details['submitted'])
        job = rqueue.fetch_job(job_id)
        if job is None:
            job_details['status'] = 'deleted'
        else:
            job_details['status'] = job.get_status()
        jobs.append(job_details)
    jobs.sort(key=lambda x: x['submitted'], reverse=True)
    return jobs


def sizeof_fmt(num, suffix='B'):
    """Happily used from http://stackoverflow.com/a/1094933"""
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def downloaded_files_info():
    files = get_files_available()
    url = lambda x: url_for('download_file', filename=x)
    files_with_urls = [{
        'name': name,
        'modified': modified,
        'size': sizeof_fmt(size),
        'url': url(name),
    } for name, modified, size in files]
    return files_with_urls


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/enqueue', methods=['POST',])
def enqueue():
    data = json.loads(request.data.decode())
    if 'yturl' not in data:
        response = {
            'error': "The Youtube URL to download must be provided as 'yturl'",
        }
        logger.warn("Rejecting /api/enqueue request missing 'yturl'")
        return json.dumps(response), 400 # bad request

    clean_url = validate_url(data['yturl'])
    if clean_url is None:
        response = {
            'error': "I'm sorry, that doesn't really look like a Youtube URL. :-(",
            'info': "I can download anything that starts with https://www.youtube.com/...",
        }
        logger.warn("Rejecting /api/enqueue request for %s" % data['yturl'])
        return json.dumps(response), 403 # forbidden

    logger.info("Accepting /api/enqueue request for %s" % clean_url)
    job = rqueue.enqueue_call(
        func=download,
        args=(clean_url,),
        result_ttl=900 # 15 minutes
    )
    job_id  = job.get_id()
    redis.lpush('alljobs', job_id)
    redis.ltrim('alljobs', 0, 9)
    job_details = {
        'job_id':      job_id,
        'request_url': clean_url,
        'submitted':   time.time(),
    }
    redis.hmset('job:%s' % job_id, job_details)
    redis.expire('job:%s' % job_id, 86400) # 24 hours
    response = {
        'job_id': job_id,
    }
    return json.dumps(response), 201 # created


@app.route('/api/status')
def status():
    response = {
        'jobs': queued_job_info(),
        'files': downloaded_files_info(),
    }
    return json.dumps(response)


@app.route('/download/<path:filename>')
def download_file(filename):
    """Simple and sufficient. Lets a user download a file we've pulled in."""
    return send_from_directory('downloads', filename, as_attachment=True)


@app.route('/api/jobs/<job_id>')
def job_details(job_id):
    try:
        job = Job.fetch(job_id, connection=redis)
        return json.dumps({'status': job.get_status()})
    except:
        response = {
            'error': "No info. Probably deleted?",
        }
        return json.dumps(response), 404 # not found

