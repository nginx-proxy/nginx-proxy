FROM nginx:1.13
LABEL maintainer="Jason Wilder mail@jasonwilder.com"

# Install `openssl` and clean up the `apt` cache.
RUN apt update \
 && apt install openssl -y --no-install-recommends \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*
