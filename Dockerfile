FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y python3

ADD app.py
CMD python app.py
