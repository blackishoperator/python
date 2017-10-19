FROM python:3

COPY /.netrc ~/.
RUN git clone https://github.com/blackish-murderer/flop.git
RUN cd flop
RUN echo > empty
RUN git config user.name "blackish-murderer"
RUN git config user.email "blackish.murderer@gmail.com"
RUN git add empty
RUN git commit -m "empty"
RUN git push origin master
#
#WORKDIR /usr/src/app
#
#COPY . .
