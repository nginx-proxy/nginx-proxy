FROM jwilder/nginx-proxy

MAINTAINER David Parrish <daveparrish@tutanota.com>
MAINTAINER Yves Blusseau <90z7oey02@sneakemail.com>
MAINTAINER Hadrien Mary <hadrien.mary@gmail.com>

# Install simp_le program
COPY /install_simp_le.sh /app/install_simp_le.sh
RUN chmod +rx /app/install_simp_le.sh && sync && /app/install_simp_le.sh && rm -f /app/install_simp_le.sh

COPY letsencrypt_service letsencrypt_service_data.tmpl nginx.tmpl Procfile update_certs update_nginx /app/
