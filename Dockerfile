FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y dialog net-tools build-essential
RUN apt-get install -y python3

ADD /app.py /app.py
CMD python3 app.py
