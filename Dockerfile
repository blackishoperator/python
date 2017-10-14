FROM dockerfile/ubuntu

RUN \
  apt-get update && \
  apt-get install -y python python-dev python-pip python-virtualenv && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /data
CMD ["bash"]
