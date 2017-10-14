FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y python3

ADD /app.py /app.py
RUN ls
CMD python3 app.py
