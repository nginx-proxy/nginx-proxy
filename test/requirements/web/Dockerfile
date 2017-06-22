# Docker Image running one (or multiple) webservers listening on all given ports from WEB_PORTS environment variable

FROM python:3
RUN pip install flask==0.12
COPY ./webserver.py /
COPY ./entrypoint.sh /
WORKDIR /opt
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

