FROM jwilder/nginx-proxy

MAINTAINER [ "Jason Wilder <mail@jasonwilder.com>", "Yves Blusseau <90z7oey02@sneakemail.com>" ]

COPY . /app/

RUN chmod +rx /app/build.sh && /app/build.sh && rm -f /app/build.sh
