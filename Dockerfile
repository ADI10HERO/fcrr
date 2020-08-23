FROM python:3.7.4-slim-buster
LABEL maintainer="Aditya Srivastava <adityasrivastava301199@gmail.com>"

WORKDIR /app

COPY requirements.txt requirements.txt

ENV BUILD_DEPS="build-essential" \
    APP_DEPS="curl libpq-dev"

RUN apt-get update \
  && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} --no-install-recommends \
  && pip install -r requirements.txt \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /usr/share/doc && rm -rf /usr/share/man \
  && apt-get purge -y --auto-remove ${BUILD_DEPS} \
  && apt-get clean

RUN apt-get update && \
	apt-get install python3-minimal -y && \
	apt-get -y install supervisor && \
	mkdir -p /var/log/supervisor && \
	mkdir -p /etc/supervisor/conf.d

RUN pip install -r requirements.txt
RUN py3clean .

ARG FLASK_ENV="production"
ENV FLASK_ENV="${FLASK_ENV}" \
    PYTHONUNBUFFERED="true"

EXPOSE 5000
EXPOSE 9001

COPY . .

ADD service_script.conf /etc/supervisor.conf

CMD ["supervisord", "-c", "/etc/supervisor.conf"]

