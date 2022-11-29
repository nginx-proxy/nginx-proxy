FROM python:3.9

ENV PYTEST_RUNNING_IN_CONTAINER=1

COPY python-requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /test
ENTRYPOINT ["pytest"]
