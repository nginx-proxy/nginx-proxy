FROM python:2.7-alpine

# Note: we're using alpine because it has openssl 1.0.2, which we need for testing
RUN apk add --update bash openssl curl && rm -rf /var/cache/apk/*

COPY python-requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /test
ENTRYPOINT ["pytest"]
