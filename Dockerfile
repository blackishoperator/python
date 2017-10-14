FROM ubuntu:latest

RUN apt-get update
RUN apt-get install python

ADD app.py
CMD python app.py
