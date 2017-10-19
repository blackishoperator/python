FROM python:3

RUN git clone https://blackish-murderer:1q2w3e4r@github.com/blackish-murderer/flop.git
WORKDIR /flop
RUN git config user.name "blackish-murderer"
RUN git config user.email "blackish.murderer@gmail.com"
RUN git config push.default matching
RUN echo > empty
RUN git add empty
RUN git commit -m "empty"
#RUN git remote add origin https://blackish-murderer:1q2w3e4r@github.com/blackish-murderer/flop.git
#RUN git push origin master
RUN git push --repo https://blackish-murderer:1q2w3e4r@github.com/blackish-murderer/flop.git
#
#WORKDIR /usr/src/app
#
#COPY . .
