import base64
import datetime
import logging
import os
from subprocess import call
import time

# Flask imports
from flask import Flask, flash, render_template, request, send_from_directory, url_for

# Redis and RQ imports
import redis
from rq import Queue
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
    logger.info("Running with options:\n    %s" % ' '.join(options))
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
        flash("I'm sorry, that doesn't really look like a youtube URL... :-(", 'error')
        flash("I can download anything that starts with https://www.youtube.com/...", 'info')
        return None


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        logger.info("Received request to download %s" % request.form['yturl'])
        clean_url = validate_url(request.form['yturl'])
        if clean_url is not None:
            logger.info("Queuing task to get %s" % clean_url)
            job = rqueue.enqueue_call(
                func=download,
                args=(clean_url,),
                result_ttl=900 # 15 minutes
            )
            job_id  = job.get_id()
            job_url = url_for('results', job_id=job_id)
            flash("Queued Job ID: <a href=\"%s\">%s</a>" % (job_url, job_id), 'info')
            redis.lpush('alljobs', job_id)
            # Keep only the ten latest
            redis.ltrim('alljobs', 0, 9)
            job_details = {
                'job_id':      job_id,
                'results_url': job_url,
                'request_url': clean_url,
                'submitted':   time.time(),
            }
            redis.hmset('job:%s' % job_id, job_details)
            redis.expire('job:%s' % job_id, 86400) # 24 hours

    # Populate data for queued jobs
    makedatetime = lambda ts: datetime.datetime.fromtimestamp(float(ts))
    nicedate = lambda ts: makedatetime(ts).strftime("%Y-%m-%dT%H:%M:%S")
    jobs = []
    # Show the ten most recent jobs
    for job_id in redis.lrange('alljobs', 0, 9):
        job_details = redis.hgetall('job:%s' % job_id)
        job_details['submitted'] = nicedate(job_details['submitted'])
        job = rqueue.fetch_job(job_id)
        if job is None:
            logger.info("Job already deleted. Details: %r" % job_details)
            job_details['status'] = 'deleted'
        else:
            job_details['status'] = job.get_status()
        jobs.append(job_details)
    jobs.sort(key=lambda x: x['submitted'], reverse=True)

    # Populate data for files available for download
    files = get_files_available()
    url = lambda x: url_for('download_file', filename=x)
    files_with_urls = [[name, modified, size, url(name)] for name, modified, size in files]

    return render_template('index.html', available=files_with_urls, jobs=jobs)


@app.route('/download/<path:filename>')
def download_file(filename):
    """Simple and sufficient. Lets a user download a file we've pulled in."""
    return send_from_directory('downloads', filename, as_attachment=True)


@app.route('/results/<job_id>')
def results(job_id):
    try:
        job = Job.fetch(job_id, connection=redis)
        return job.get_status()
    except:
        return "No info. Probably deleted?"


@app.route('/ping')
def ping():
    return str(int(time.time()))

