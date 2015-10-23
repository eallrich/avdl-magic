import json
import logging
import time

from flask import Flask, render_template, request, send_from_directory
import redis
from rq import Queue
from rq.job import Job

import settings
import util

logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = settings.secret_key

redis = redis.from_url(settings.redis_url)
rqueue = Queue(connection=redis)
# Convenience
jobkey = settings.jobkey
joblist = settings.joblist


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

    clean_url = util.validate_url(data['yturl'])
    if clean_url is None:
        response = {
            'error': "I'm sorry, that doesn't really look like a Youtube URL. :-(",
            'info': "Please try again using a link starting with 'https://www.youtube.com'.",
        }
        logger.warn("Rejecting /api/enqueue request for %s" % data['yturl'])
        return json.dumps(response), 403 # forbidden

    logger.info("Accepting /api/enqueue request for %s" % clean_url)
    job = rqueue.enqueue_call(
        func=util.download,
        args=(clean_url,),
        result_ttl=900 # 15 minutes
    )
    job_id  = job.get_id()
    redis.lpush(joblist, job_id)
    redis.ltrim(joblist, 0, 9)
    job_details = {
        'job_id':      job_id,
        'request_url': clean_url,
        'submitted':   time.time(),
        'page_title':  '...', # just a placeholder to keep it pretty
    }
    redis.hmset(jobkey(job_id), job_details)
    redis.expire(jobkey(job_id), 86400) # 24 hours
    response = {
        'job_id': job_id,
    }
    return json.dumps(response), 201 # created


@app.route('/api/status')
def status():
    response = {
        'jobs': util.queued_job_info(),
        'files': util.downloaded_files_info(),
    }
    #return json.dumps(response)
    return 'Internal Server Error', 500


@app.route('/download/<path:filename>')
def download_file(filename):
    """Simple and sufficient. Lets a user download a file we've pulled in."""
    return send_from_directory(
                settings.download_dir,
                filename,
                as_attachment=True
            )


@app.route('/api/jobs/<job_id>')
def job_details(job_id):
    try:
        job = Job.fetch(job_id, connection=redis)
        return json.dumps({'status': job.get_status()})
    except:
        response = {
            'error': "No info, probably deleted.",
        }
        return json.dumps(response), 404 # not found


@app.route('/admin/flushredis')
def flushredis():
    logger.info("Received request to flush redis")
    redis.flushall()
    return "Done"

