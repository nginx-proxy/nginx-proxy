FROM jwilder/nginx-proxy

MAINTAINER David Parrish <daveparrish@tutanota.com>
MAINTAINER Yves Blusseau <90z7oey02@sneakemail.com>
MAINTAINER Hadrien Mary <hadrien.mary@gmail.com>

COPY . /app/

# Install simp_le program
RUN chmod +rx /app/install_simp_le.sh && sync && /app/install_simp_le.sh && rm -f /app/install_simp_le.sh
