In this scenario, we have a wildcard certificate for `*.web.nginx-proxy.tld` and 3 web containers:
- 1.web.nginx-proxy.tld
- 2.web.nginx-proxy.tld
- 3.web.nginx-proxy.tld

We want web containers 1 and 2 to support SSL, but 3 should not (using `HTTPS_METHOD=nohttps`)