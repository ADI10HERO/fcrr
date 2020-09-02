from flask import Flask, flash, render_template, request, redirect, url_for
from celery import Celery
from time import sleep, time

import redis
import hashlib


app = Flask(__name__)
app.secret_key = 'secret_key'

app.config['CELERY_BROKER_URL'] = 'amqp://admin:pass@rabbit:5672'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

client = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
client.conf.update(app.config)

r = redis.Redis(host='redis')

def generate_ts():
    return ''.join(str(time.time()).split('.'))

@client.task(bind=True)
def long_task(self, url):
    print("Long task called")
    db_contents = {
                    'state' : 'progress', 
                    'url': url, 
                    'message': 'your file is being processed now'
                }
    r.hmset(task_id, db_contents)
    r.bgsave()

    try:
        rq = requests.get(url)
        fpath = '{}.wav'.format(generate_ts())
        img_name = fpath.split('.')[0]+'.png'
        with open('uploads/'+fpath, "wb") as f:
            f.write(rq.content)
        time.sleep(40)
        os.remove('uploads/'+fpath)
        db_contents = {
                    'state' : 'success', 
                    'url': url, 
                    'message': 'your file is being processed now'
                }
        r.hmset(task_id, db_contents)
        r.bgsave()
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 1, 'status': "task is in progress"})

    except Exception as e:
        db_contents = {
                        'state' : 'Failed', 
                        'url': url, 
                        'message': e,
                    }
        r.hmset(task_id, db_contents)

    return {"Task-Status": "Completed"}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':
        url = request.form.get("url")
        task_id = hashlib.md5(url).hexdigest()
        result = r.hgetall(task_id)

        if result is not None:
            # result exists, i.e previously queried 
            print(result)
            msg = str(r.hget(task_id, "state"))
            return render_template('index.html', message = msg)

        # create task with task_id as id
        db_contents = {
                        'state' : 'accepted', 
                        'url': url, 
                        'message': 'your file is accepted, will be processed soon'
                    }
        r.hmset(task_id, db_contents)
        r.bgsave()

        # finally call the long task 
        task = long_task.apply_async(url)
        return render_template('index.html', message = task_id)

@app.route('/status/<id>', methods=['GET'])
def check_status(id):
    
    result = r.hgetall(id)
    if result is None:
        # result does not exist 
        return render_template('status.html', status = "Not Found", info = "No such task found")

    print(result)
    status = str(r.hget(task_id, "state"))
    info = str(r.hget(task_id, "message"))

    return render_template('status.html', status = status, info = info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

