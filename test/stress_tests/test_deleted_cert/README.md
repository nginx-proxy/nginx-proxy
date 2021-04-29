Test the behavior of nginx-proxy when restarted after deleting a certificate file is was using.

1. nginx-proxy is created with a virtual host having a certificate
1. while nginx-proxy is running, the certificate file is deleted
1. nginx-proxy is then restarted (without removing the container)
