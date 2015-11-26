FROM jwilder/nginx-proxy

MAINTAINER [ "Jason Wilder <mail@jasonwilder.com>", "Yves Blusseau <90z7oey02@sneakemail.com>" ]

RUN apt-get update

# Install python packages needed by simp_le
RUN apt-get install -y -q --no-install-recommends python python-requests

# Install python packages needed to build  simp_le
RUN apt-get install -y -q --no-install-recommends git gcc libssl-dev libffi-dev python-dev python-pip

# Get Let's Encrypt simp_le client source
RUN git -C /opt clone https://github.com/kuba/simp_le.git

WORKDIR /opt/simp_le
# Upgrade setuptools
RUN pip install -U setuptools
# Install simp_le in /usr/local/bin
RUN python ./setup.py install

# Make house cleaning
RUN rm -rf /opt/simp_le

RUN -get autoremove -y git gcc libssl-dev libffi-dev python-dev python-pip

RUN apt-get clean all
RUN rm -r /var/lib/apt/lists/*

COPY . /app/
