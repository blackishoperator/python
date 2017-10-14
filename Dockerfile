FROM ubuntu:latest

RUN apt-get update
RUN apt-get install -y python3

EXPOSE 80
EXPOSE 8080
EXPOSE 443

ADD /app.py /app.py

RUN echo "print("hello docker")" > app.py
RUN python3 app.py
