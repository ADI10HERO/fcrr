# Scalable flask server to handle async long tasks
# using Flask, celery, rabitmq and redis.
#
# (C) 2020 Aditya Srivastava, Mumbai, India
# GNU General Public License v3 (GPLv3)
# email adityasrivastava301199@gmail.com

from flask import Flask, flash, render_template, request, redirect, url_for
from celery import Celery
from time import sleep, time

import redis
import hashlib
import requests
import os


app = Flask(__name__)
app.secret_key = 'secret_key'

app.config['CELERY_BROKER_URL'] = 'amqp://admin:pass@rabbit:5672'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

client = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
client.conf.update(app.config)

r = redis.Redis(host='redis')


def generate_ts():
    """Generate timestamp string."""
    return ''.join(str(time()).split('.'))


@client.task(bind=True)
def long_task(self, task_id, url):
    """
    Simulate a long task.

    Inputs:
    task_id: string, unique hash of each task
    url: string, the url of audio file to download

    Return:
    json serializable object, status of the task after completion
    """
    db_contents = {
        'state': 'progress',
        'url': url,
        'message': 'your file is being processed now'
    }
    r.hmset(task_id, db_contents)
    self.update_state(state='PROGRESS',
                      meta={
                          'current': 0,
                          'total': 1,
                          'status': "task is in progress"
                      })

    try:
        rq = requests.get(url)
        fpath = '{}.wav'.format(generate_ts())
        img_name = fpath.split('.')[0]+'.png'
        with open(fpath, "wb") as f:
            f.write(rq.content)
        sleep(40)
        os.remove(fpath)  # deleting the temp file
        db_contents = {
            'state': 'success',
            'url': url,
            'message': 'processing completed'
        }
        r.hmset(task_id, db_contents)
        r.expire(task_id, 60*60*24)

    except Exception as e:
        db_contents = {
            'state': 'Failed',
            'url': url,
            'message': e,
        }
        # print(e)
        r.hmset(task_id, db_contents)
        r.expire(task_id, 60*60*24)
        # return {"task-status": "exception"}

    return {"Task-Status": "Completed"}


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Route to root/home page.

    Accepts get and post requests
    """
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':
        url = request.form.get("url")
        task_id = hashlib.md5(url.encode()).hexdigest()
        result = r.hgetall(task_id)

        if result:
            # result exists, i.e previously queried
            msg = str(task_id) + " " + r.hget(task_id, "state").decode('utf-8')
            info = "Previous request found, skipped download,\
                    returning result"
            if msg != "Failed":
                return render_template('index.html', message=msg, info=info)

        # create task with task_id as id
        db_contents = {
            'state': 'accepted',
            'url': url,
            'message': 'your file is accepted, will be processed soon'
        }
        r.hmset(task_id, db_contents)

        # finally call the long task
        longtask = long_task.delay(task_id, url)
        return render_template('index.html', message=task_id)


@app.route('/status/<id>', methods=['GET'])
def check_status(id):
    """Route to check the status of the long async task."""
    result = r.hgetall(id)
    if result is None:
        # result does not exist
        return render_template('status.html',
                               status="Not Found",
                               info="No such task found"
                               )

    task_id = id
    status = r.hget(task_id, "state").decode('utf-8')
    info = r.hget(task_id, "message").decode('utf-8')

    return render_template('status.html', status=str(status), info=str(info))


@app.route('/clear', methods=['GET'])
def clear():
    """Helper function to clear the redis-db."""
    r.flushdb()
    return "db cleared"


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
