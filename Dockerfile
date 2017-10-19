FROM python:3

RUN git clone https://blackish-murderer:1q2w3e4r@github.com/blackish-murderer/flop.git
RUN cd flop
RUN git push --repo https://blackish-murderer:1q2w3e4r@github.com/blackish-murderer/flop.git
#
#WORKDIR /usr/src/app
#
#COPY . .
