from flask import Flask, flash, render_template, request, redirect, url_for
from celery import Celery
from time import sleep


app = Flask(__name__)
app.secret_key = 'secret_key'

app.config['CELERY_BROKER_URL'] = 'amqp://admin:pass@rabbit:5672'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'


client = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
client.conf.update(app.config)


@client.task(bind=True)
def long_task(self):
    print("Long task called")
    sleep(45)
    self.update_state(state='PROGRESS', meta={'current': 0, 'total': 1, 'status': "task is in progress"})
    return {"Status": "Completed"}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    elif request.method == 'POST':
        task = long_task.apply_async()
        return render_template('index.html', message = task.id)

@app.route('/status/<id>', methods=['GET'])
def check_status(id):
    task = long_task.AsyncResult(id)
    status = task.status
    info = task.info
    return render_template('status.html', status = status, info = info)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

