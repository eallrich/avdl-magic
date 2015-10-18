import base64
import logging
import os
from subprocess import call
import time

from flask import Flask, flash, render_template, request, send_from_directory, url_for
from flask_bootstrap import Bootstrap
from rq import Queue
from rq.job import Job
from worker import conn

import settings

logging.basicConfig(**settings.logging)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = base64.b64encode(os.urandom(40))
Bootstrap(app)

# RQ Queue
q = Queue(connection=conn)

def download(yturl):
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
    files = [f for f in os.listdir(where) if f.endswith(extension)]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(where, x)), reverse=True)
    return files


def validate_url(url):
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
    logger.info("%s %s" % (request.method, request.base_url))
    if request.method == 'POST':
        logger.info("Received request to download %s" % request.form['yturl'])
        clean_url = validate_url(request.form['yturl'])
        if clean_url is not None:
            logger.info("Queuing task to get %s" % clean_url)
            job = q.enqueue_call(
                func=download,
                args=(clean_url,),
                result_ttl=900 # 15 minutes
            )
            flash("Queued Job ID: <a href=\"%s\">%s</a>" % (url_for('results', job_id=job.get_id()), job.get_id()), 'warning')

    files = get_files_available()
    file_urls = [(f, url_for('download_file', filename=f)) for f in files]
    return render_template('index.html', available=file_urls)


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('downloads', filename, as_attachment=True)


@app.route('/results/<job_id>')
def results(job_id):
    logger.info("%s %s" % (request.method, request.base_url))
    job = Job.fetch(job_id, connection=conn)
    if job.is_finished:
        return "Finished!", 200
    else:
        return "Still working...", 202


@app.route('/status')
def status():
    logger.info("%s %s" % (request.method, request.base_url))
    jobs_data = [{
        'id': j.get_id(), 
        'status': j.get_status(),
        'url': j.args[0]}
        for j in q.jobs]
    return render_template('status.html', jobs=jobs_data)


@app.route('/ping')
def ping():
    logger.info("%s %s" % (request.method, request.base_url))
    return str(int(time.time()))

