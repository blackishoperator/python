FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y python3

ADD /app.py /app.py
RUN ls
RUN cat app.py
CMD python3 app.py
