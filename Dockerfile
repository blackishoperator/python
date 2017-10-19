FROM python:3

apt-get install git

WORKDIR /usr/src/app

COPY . .

RUN python ./app.py
