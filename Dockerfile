FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN python ./app.py
