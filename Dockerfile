#FROM ubuntu:latest
#
#RUN apt-get update
#RUN apt-get install -y python3
#
#EXPOSE 80
#EXPOSE 8080
#EXPOSE 443
#
#ADD /app.py /app.py
#CMD ["python3" "app.py"]

FROM python:3

WORKDIR /usr/src/app

COPY . .

#CMD [ "python", "./app.py" ]
RUN python ./app.py
