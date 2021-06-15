FROM python:3.9.5

LABEL maintainer="tinhhn.uit@gmail.com"

RUN apt-get update && apt-get -y install cron memcached unzip xvfb libxi6 libgconf-2-4 default-jdk vim \
    && ln -snf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime  \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone  \
    && curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add    \
    && echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list    \
    && apt-get -y update    \
    && apt-get -y install google-chrome-stable  \
    && wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip   \
    && unzip chromedriver_linux64.zip   \
    && mv chromedriver /usr/bin/chromedriver    \
    && chmod +x /usr/bin/chromedriver   \
    && rm -f chromedriver_linux64.zip   \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
WORKDIR /app


COPY requirements.txt /app/
RUN pip install -r requirements.txt
#COPY . /app/


CMD service memcached start && cron && python manage.py installtasks && python manage.py runserver 0.0.0.0:8000 --insecure
