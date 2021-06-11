FROM python:3.9.5

LABEL maintainer="tinhhn.uit@gmail.com"

RUN apt-get update && apt-get -y install cron memcached  \
    && rm -rf /var/lib/apt/lists/*  \
    && ln -snf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime  \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone

ENV PYTHONUNBUFFERED=1
WORKDIR /app


COPY requirements.txt /app/
RUN pip install -r requirements.txt
#COPY . /app/


CMD service memcached start && cron && python manage.py makemigrations && python manage.py migrate && python manage.py installtasks && python manage.py runserver 0.0.0.0:8000 --insecure
