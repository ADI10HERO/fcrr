# f.c.r.r
## Flask Celery RabbitMQ Redis


Uses flask with celery as the worker, rabbitmq as broker and redis for backend.
Scales well, really fast :)

To run the application: 

#### Prerequisite:
If you don't have docker and docker compose please install it with the following code:
```sh
chmod +x install_docker_compose.sh
./install_docker_compose.sh
```

## How to use
#### Method 1: 
```sh
docker pull adi10hero/fcrr:latest
docker-compose up
```

#### Method 2:
```sh
docker-compose up --build  #this builds the application (recommended)
```

## Results

1. When your app runs successfully 
<image src='images/task_1.png'>

2. When you click submit as new task
<image src='images/task_2.png'>

3. When you check for status of a newly created (long) task
<image src='images/task_3.png'>

4. When status is checked after completion of task
<image src='images/task_5.png'>

### Note:
- Minimal application built under 4-5 hrs with no prior knowledge of any component except flask.
- Contributions highly appreciated.
