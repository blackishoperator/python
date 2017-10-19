FROM python:3

#RUN apt-get install git
#RUN git config user.email "blackish.murderer@gmail.com"
#RUN git config user.name "blackish-murderer"
RUN git clone https://blackish-murderer:stgrfrlm!SAAC8@github.com/blackish-murderer/flop.git
RUN git pull https://blackish-murderer:stgrfrlm!SAAC8@github.com/blackish-murderer/flop.git
RUN git remote add origin https://blackish-murderer:stgrfrlm!SAAC8@github.com/blackish-murderer/flop.git
RUN cd flop
RUN echo > empty
RUN git add empty
RUN git commit -m "spawning"
RUN git push origin master
#
#WORKDIR /usr/src/app
#
#COPY . .
