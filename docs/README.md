### Docker Compose

```yaml
version: '2'

services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro

  whoami:
    image: jwilder/whoami
    expose:
      - "8000"
    environment:
      - VIRTUAL_HOST=whoami.example
      - VIRTUAL_PORT=8000
```

```console
docker compose up
curl -H "Host: whoami.example" localhost
```

Example output:
```console
I'm 5b129ab83266
```

### IPv6 support

You can activate the IPv6 support for the nginx-proxy container by passing the value `true` to the `ENABLE_IPV6` environment variable:

```console
docker run -d -p 80:80 -e ENABLE_IPV6=true -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
```

#### Scoped IPv6 Resolvers

NginX does not support scoped IPv6 resolvers. In [docker-entrypoint.sh](https://github.com/nginx-proxy/nginx-proxy/tree/main/docker-entrypoint.sh) the resolvers are parsed from resolv.conf, but any scoped IPv6 addreses will be removed. 

#### IPv6 NAT

By default, docker uses IPv6-to-IPv4 NAT. This means all client connections from IPv6 addresses will show docker's internal IPv4 host address. To see true IPv6 client IP addresses, you must [enable IPv6](https://docs.docker.com/config/daemon/ipv6/) and use [ipv6nat](https://github.com/robbertkl/docker-ipv6nat). You must also disable the userland proxy by adding `"userland-proxy": false` to `/etc/docker/daemon.json` and restarting the daemon.

### Multiple Hosts

If you need to support multiple virtual hosts for a container, you can separate each entry with commas.  For example, `foo.bar.com,baz.bar.com,bar.com` and each host will be setup the same.

### Virtual Ports

When your container exposes only one port, nginx-proxy will default to this port, else to port 80.

If you need to specify a different port, you can set a `VIRTUAL_PORT` env var to select a different one. This variable cannot be set to more than one port.

For each host defined into `VIRTUAL_HOST`, the associated virtual port is retrieved by order of precedence:
1. From the `VIRTUAL_PORT` environment variable
1. From the container's exposed port if there is only one
1. From the default port 80 when none of the above methods apply

### Wildcard Hosts

You can also use wildcards at the beginning and the end of host name, like `*.bar.com` or `foo.bar.*`. Or even a regular expression, which can be very useful in conjunction with a wildcard DNS service like [nip.io](https://nip.io) or [sslip.io](https://sslip.io), using `~^foo\.bar\..*\.nip\.io` will match `foo.bar.127.0.0.1.nip.io`, `foo.bar.10.0.2.2.nip.io` and all other given IPs. More information about this topic can be found in the nginx documentation about [`server_names`](http://nginx.org/en/docs/http/server_names.html).

### Path-based Routing

You can have multiple containers proxied by the same `VIRTUAL_HOST` by adding a `VIRTUAL_PATH` environment variable containing the absolute path to where the container should be mounted. For example with `VIRTUAL_HOST=foo.example.com` and `VIRTUAL_PATH=/api/v2/service`, then requests to http://foo.example.com/api/v2/service will be routed to the container. If you wish to have a container serve the root while other containers serve other paths, give the root container a `VIRTUAL_PATH` of `/`.  Unmatched paths will be served by the container at `/` or will return the default nginx error page if no container has been assigned `/`.
It is also possible to specify multiple paths with regex locations like `VIRTUAL_PATH=~^/(app1|alternative1)/`. For further details see the nginx documentation on location blocks. This is not compatible with `VIRTUAL_DEST`.

The full request URI will be forwarded to the serving container in the `X-Original-URI` header.

**NOTE**: Your application needs to be able to generate links starting with `VIRTUAL_PATH`. This can be achieved by it being natively on this path or having an option to prepend this path. The application does not need to expect this path in the request.

#### VIRTUAL_DEST

This environment variable can be used to rewrite the `VIRTUAL_PATH` part of the requested URL to proxied application. The default value is empty (off).
Make sure that your settings won't result in the slash missing or being doubled. Both these versions can cause troubles.

If the application runs natively on this sub-path or has a setting to do so, `VIRTUAL_DEST` should not be set or empty.
If the requests are expected to not contain a sub-path and the generated links contain the sub-path, `VIRTUAL_DEST=/` should be used.

```console
$ docker run -d -e VIRTUAL_HOST=example.tld -e VIRTUAL_PATH=/app1/ -e VIRTUAL_DEST=/ --name app1 app
```

In this example, the incoming request `http://example.tld/app1/foo` will be proxied as `http://app1/foo` instead of `http://app1/app1/foo`.

#### Per-VIRTUAL_PATH location configuration

The same options as from [Per-VIRTUAL_HOST location configuration](#Per-VIRTUAL_HOST-location-configuration) are available on a `VIRTUAL_PATH` basis.
The only difference is that the filename gets an additional block `HASH=$(echo -n $VIRTUAL_PATH | sha1sum | awk '{ print $1 }')`. This is the sha1-hash of the `VIRTUAL_PATH` (no newline). This is done filename sanitization purposes.
The used filename is `${VIRTUAL_HOST}_${HASH}_location`

The filename of the previous example would be `example.tld_8610f6c344b4096614eab6e09d58885349f42faf_location`.

#### DEFAULT_ROOT

This environment variable of the nginx proxy container can be used to customize the return error page if no matching path is found. Furthermore it is possible to use anything which is compatible with the `return` statement of nginx.

Exception:  If this is set to the string `none`, no default `location /` directive will be generated.  This makes it possible for you to provide your own `location /` directive in your [`/etc/nginx/vhost.d/VIRTUAL_HOST`](#per-virtual_host) or [`/etc/nginx/vhost.d/default`](#per-virtual_host-default-configuration) files.

If unspecified, `DEFAULT_ROOT` defaults to `404`.

Examples (YAML syntax):

  * `DEFAULT_ROOT: "none"` prevents `nginx-proxy` from generating a default `location /` directive.
  * `DEFAULT_ROOT: "418"` returns a 418 error page instead of the normal 404 one.
  * `DEFAULT_ROOT: "301 https://github.com/nginx-proxy/nginx-proxy/blob/main/README.md"` redirects the client to this documentation.

Nginx variables such as `$scheme`, `$host`, and `$request_uri` can be used.  However, care must be taken to make sure the `$` signs are escaped properly.  For example, if you want to use `301 $scheme://$host/myapp1$request_uri` you should use:

* Bash: `DEFAULT_ROOT='301 $scheme://$host/myapp1$request_uri'`
* Docker Compose yaml: `- DEFAULT_ROOT: 301 $$scheme://$$host/myapp1$$request_uri`


### Multiple Networks

With the addition of [overlay networking](https://docs.docker.com/engine/userguide/networking/get-started-overlay/) in Docker 1.9, your `nginx-proxy` container may need to connect to backend containers on multiple networks. By default, if you don't pass the `--net` flag when your `nginx-proxy` container is created, it will only be attached to the default `bridge` network. This means that it will not be able to connect to containers on networks other than `bridge`.

If you want your `nginx-proxy` container to be attached to a different network, you must pass the `--net=my-network` option in your `docker create` or `docker run` command. At the time of this writing, only a single network can be specified at container creation time. To attach to other networks, you can use the `docker network connect` command after your container is created:

```console
docker run -d -p 80:80 -v /var/run/docker.sock:/tmp/docker.sock:ro \
    --name my-nginx-proxy --net my-network nginxproxy/nginx-proxy
docker network connect my-other-network my-nginx-proxy
```

In this example, the `my-nginx-proxy` container will be connected to `my-network` and `my-other-network` and will be able to proxy to other containers attached to those networks.

### Host networking

`nginx-proxy` is compatible with containers using Docker's [host networking](https://docs.docker.com/network/host/), both with the proxy connected to one or more [bridge network](https://docs.docker.com/network/bridge/) (default or user created) or running in host network mode itself.

Proxyed containers running in host network mode **must** use the [`VIRTUAL_PORT`](#virtual-ports) environment variable, as this is the only way for `nginx-proxy` to get the correct port (or a port at all) for those containers.

### Custom external HTTP/HTTPS ports

If you want to use `nginx-proxy` with different external ports that the default ones of `80` for `HTTP` traffic and `443` for `HTTPS` traffic, you'll have to use the environment variable(s) `HTTP_PORT` and/or `HTTPS_PORT` in addition to the changes to the Docker port mapping. If you change the `HTTPS` port, the redirect for `HTTPS` traffic will also be configured to redirect to the custom port. Typical usage, here with the custom ports `1080` and `10443`:

```console
docker run -d -p 1080:1080 -p 10443:10443 -e HTTP_PORT=1080 -e HTTPS_PORT=10443 -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
```

### Internet vs. Local Network Access

If you allow traffic from the public internet to access your `nginx-proxy` container, you may want to restrict some containers to the internal network only, so they cannot be accessed from the public internet.  On containers that should be restricted to the internal network, you should set the environment variable `NETWORK_ACCESS=internal`.  By default, the *internal* network is defined as `127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16`.  To change the list of networks considered internal, mount a file on the `nginx-proxy` at `/etc/nginx/network_internal.conf` with these contents, edited to suit your needs:

```Nginx
# These networks are considered "internal"
allow 127.0.0.0/8;
allow 10.0.0.0/8;
allow 192.168.0.0/16;
allow 172.16.0.0/12;

# Traffic from all other networks will be rejected
deny all;
```

When internal-only access is enabled, external clients will be denied with an `HTTP 403 Forbidden`

> If there is a load-balancer / reverse proxy in front of `nginx-proxy` that hides the client IP (example: AWS Application/Elastic Load Balancer), you will need to use the nginx `realip` module (already installed) to extract the client's IP from the HTTP request headers.  Please see the [nginx realip module configuration](http://nginx.org/en/docs/http/ngx_http_realip_module.html) for more details.  This configuration can be added to a new config file and mounted in `/etc/nginx/conf.d/`.

### SSL Backends

If you would like the reverse proxy to connect to your backend using HTTPS instead of HTTP, set `VIRTUAL_PROTO=https` on the backend container.

> Note: If you use `VIRTUAL_PROTO=https` and your backend container exposes port 80 and 443, `nginx-proxy` will use HTTPS on port 80.  This is almost certainly not what you want, so you should also include `VIRTUAL_PORT=443`.

### uWSGI Backends

If you would like to connect to uWSGI backend, set `VIRTUAL_PROTO=uwsgi` on the backend container. Your backend container should then listen on a port rather than a socket and expose that port.

### FastCGI Backends
 
If you would like to connect to FastCGI backend, set `VIRTUAL_PROTO=fastcgi` on the backend container. Your backend container should then listen on a port rather than a socket and expose that port.
 
### FastCGI File Root Directory

If you use fastcgi,you can set `VIRTUAL_ROOT=xxx`  for your root directory

### Logging

The default nginx access log format is

```
$host $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$upstream_addr"
```

#### Custom log format

If you want to use a custom access log format, you can set `LOG_FORMAT=xxx` on the proxy container.

With docker compose take care to escape the `$` character with `$$` to avoid variable interpolation. Example: `$remote_addr` becomes `$$remote_addr`.

#### JSON log format

If you want access logs in JSON format, you can set `LOG_JSON=true`. This will correctly set the escape character to `json` and the log format to :

```json
{
  "time_local": "$time_iso8601",
  "client_ip": "$http_x_forwarded_for",
  "remote_addr": "$remote_addr",
  "request": "$request",
  "status": "$status",
  "body_bytes_sent": "$body_bytes_sent",
  "request_time": "$request_time",
  "upstream_response_time": "$upstream_response_time",
  "upstream_addr": "$upstream_addr",
  "http_referrer": "$http_referer",
  "http_user_agent": "$http_user_agent",
  "request_id": "$request_id"
}
```

#### Log format escaping

If you want to manually set nginx `log_format`'s `escape`, set the `LOG_FORMAT_ESCAPE` variable to [a value supported by nginx](https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format).

#### Disable access logs

To disable nginx access logs entirely, set the `DISABLE_ACCESS_LOGS` environment variable to any value.

#### Disabling colors in the container log output

To remove colors from the container log output, set the [`NO_COLOR` environment variable to any value other than an empty string](https://no-color.org/) on the nginx-proxy container.

```console
docker run --detach \
  --publish 80:80 \
  --env NO_COLOR=1 \
  --volume /var/run/docker.sock:/tmp/docker.sock:ro \
  nginxproxy/nginx-proxy
```

### Default Host

To set the default host for nginx use the env var `DEFAULT_HOST=foo.bar.com` for example

```console
docker run -d -p 80:80 -e DEFAULT_HOST=foo.bar.com -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
```

nginx-proxy will then redirect all requests to a container where `VIRTUAL_HOST` is set to `DEFAULT_HOST`, if they don't match any (other) `VIRTUAL_HOST`. Using the example above requests without matching `VIRTUAL_HOST` will be redirected to a plain nginx instance after running the following command:

```console
docker run -d -e VIRTUAL_HOST=foo.bar.com nginx
```

### Separate Containers

nginx-proxy can also be run as two separate containers using the [nginxproxy/docker-gen](https://hub.docker.com/r/nginxproxy/docker-gen) image and the official [nginx](https://registry.hub.docker.com/_/nginx/) image.

You may want to do this to prevent having the docker socket bound to a publicly exposed container service.

You can demo this pattern with docker compose:

```console
docker compose --file docker-compose-separate-containers.yml up
curl -H "Host: whoami.example" localhost
```

Example output:
```console
I'm 5b129ab83266
```

To run nginx proxy as a separate container you'll need to have [nginx.tmpl](https://github.com/nginx-proxy/nginx-proxy/blob/main/nginx.tmpl) on your host system.

First start nginx with a volume:


```console
docker run -d -p 80:80 --name nginx -v /tmp/nginx:/etc/nginx/conf.d -t nginx
```

Then start the docker-gen container with the shared volume and template:

```console
docker run --volumes-from nginx \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    -v $(pwd):/etc/docker-gen/templates \
    -t nginxproxy/docker-gen -notify-sighup nginx -watch /etc/docker-gen/templates/nginx.tmpl /etc/nginx/conf.d/default.conf
```

Finally, start your containers with `VIRTUAL_HOST` environment variables.

```console
docker run -e VIRTUAL_HOST=foo.bar.com  ...
```

### SSL Support using an ACME CA

[acme-companion](https://github.com/nginx-proxy/acme-companion) is a lightweight companion container for the nginx-proxy. It allows the automated creation/renewal of SSL certificates using the ACME protocol.

### SSL Support

SSL is supported using single host, wildcard and SNI certificates using naming conventions for certificates or optionally specifying a cert name (for SNI) as an environment variable.

To enable SSL:

```console
docker run -d -p 80:80 -p 443:443 -v /path/to/certs:/etc/nginx/certs -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
```

The contents of `/path/to/certs` should contain the certificates and private keys for any virtual hosts in use. The certificate and keys should be named after the virtual host with a `.crt` and `.key` extension. For example, a container with `VIRTUAL_HOST=foo.bar.com` should have a `foo.bar.com.crt` and `foo.bar.com.key` file in the certs directory.

If you are running the container in a virtualized environment (Hyper-V, VirtualBox, etc...), /path/to/certs must exist in that environment or be made accessible to that environment. By default, Docker is not able to mount directories on the host machine to containers running in a virtual machine.

#### Diffie-Hellman Groups

[RFC7919 groups](https://datatracker.ietf.org/doc/html/rfc7919#appendix-A) with key lengths of 2048, 3072, and 4096 bits are [provided by `nginx-proxy`](https://github.com/nginx-proxy/nginx-proxy/dhparam). The ENV `DHPARAM_BITS` can be set to `2048` or `3072` to change from the default 4096-bit key. The DH key file will be located in the container at `/etc/nginx/dhparam/dhparam.pem`. Mounting a different `dhparam.pem` file at that location will override the RFC7919 key.

To use custom `dhparam.pem` files per-virtual-host, the files should be named after the virtual host with a `dhparam` suffix and `.pem` extension. For example, a container with `VIRTUAL_HOST=foo.bar.com` should have a `foo.bar.com.dhparam.pem` file in the `/etc/nginx/certs` directory.

> COMPATIBILITY WARNING: The default generated `dhparam.pem` key is 4096 bits for A+ security. Some older clients (like Java 6 and 7) do not support DH keys with over 1024 bits. In order to support these clients, you must provide your own `dhparam.pem`.

In the separate container setup, no pre-generated key will be available and neither the [nginxproxy/docker-gen](https://hub.docker.com/r/nginxproxy/docker-gen) image, nor the offical [nginx](https://registry.hub.docker.com/_/nginx/) image will provide one. If you still want A+ security in a separate container setup, you should mount an RFC7919 DH key file to the nginx container at `/etc/nginx/dhparam/dhparam.pem`.

Set `DHPARAM_SKIP` environment variable to `true` to disable using default Diffie-Hellman parameters. The default value is `false`.

```console
docker run -e DHPARAM_SKIP=true ....
```

#### Wildcard Certificates

Wildcard certificates and keys should be named after the domain name with a `.crt` and `.key` extension. For example `VIRTUAL_HOST=foo.bar.com` would use cert name `bar.com.crt` and `bar.com.key`.

#### SNI

If your certificate(s) supports multiple domain names, you can start a container with `CERT_NAME=<name>` to identify the certificate to be used.  For example, a certificate for `*.foo.com` and `*.bar.com` could be named `shared.crt` and `shared.key`.  A container running with `VIRTUAL_HOST=foo.bar.com` and `CERT_NAME=shared` will then use this shared cert.

#### OCSP Stapling

To enable OCSP Stapling for a domain, `nginx-proxy` looks for a PEM certificate containing the trusted CA certificate chain at `/etc/nginx/certs/<domain>.chain.pem`, where `<domain>` is the domain name in the `VIRTUAL_HOST` directive. The format of this file is a concatenation of the public PEM CA certificates starting with the intermediate CA most near the SSL certificate, down to the root CA. This is often referred to as the "SSL Certificate Chain". If found, this filename is passed to the NGINX [`ssl_trusted_certificate` directive](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_trusted_certificate) and OCSP Stapling is enabled.

#### How SSL Support Works

The default SSL cipher configuration is based on the [Mozilla intermediate profile](https://wiki.mozilla.org/Security/Server_Side_TLS#Intermediate_compatibility_.28recommended.29) version 5.0 which should provide compatibility with clients back to Firefox 27, Android 4.4.2, Chrome 31, Edge, IE 11 on Windows 7, Java 8u31, OpenSSL 1.0.1, Opera 20, and Safari 9. Note that the DES-based TLS ciphers were removed for security. The configuration also enables HSTS, PFS, OCSP stapling and SSL session caches. Currently TLS 1.2 and 1.3 are supported.

If you don't require backward compatibility, you can use the [Mozilla modern profile](https://wiki.mozilla.org/Security/Server_Side_TLS#Modern_compatibility) profile instead by including the environment variable `SSL_POLICY=Mozilla-Modern` to the nginx-proxy container or to your container. This profile is compatible with clients back to Firefox 63, Android 10.0, Chrome 70, Edge 75, Java 11, OpenSSL 1.1.1, Opera 57, and Safari 12.1.  Note that this profile is **not** compatible with any version of Internet Explorer.

Complete list of policies available through the `SSL_POLICY` environment variable, including the [AWS ELB Security Policies](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html#describe-ssl-policies) and [AWS Classic ELB security policies](https://docs.aws.amazon.com/fr_fr/elasticloadbalancing/latest/classic/elb-security-policy-table.html):

<details>
  <summary>Mozilla policies</summary>
  <ul>
    <li>
      <a href="https://wiki.mozilla.org/Security/Server_Side_TLS#Modern_compatibility" target="_blank">
        <code>Mozilla-Modern</code>
      </a>
    </li>
    <li>
      <a href="https://wiki.mozilla.org/Security/Server_Side_TLS#Intermediate_compatibility_.28recommended.29" target="_blank">
        <code>Mozilla-Intermediate</code>
      </a>
    </li>
    <li>
      <a href="https://wiki.mozilla.org/Security/Server_Side_TLS#Old_backward_compatibility" target="_blank">
        <code>Mozilla-Old</code>
      </a>
    </li>
  </ul>
</details>
<details>
  <summary>AWS ELB TLS 1.3 security policies</summary>
  <ul>
    <li>
      <code>AWS-TLS13-1-3-2021-06</code>
    </li>
    <li>
      <code>AWS-TLS13-1-2-2021-06</code>
    </li>
    <li>
      <code>AWS-TLS13-1-2-Res-2021-06</code>
    </li>
    <li>
      <code>AWS-TLS13-1-2-Ext1-2021-06</code>
    </li>
    <li>
      <code>AWS-TLS13-1-2-Ext2-2021-06</code>
    </li>
    <li>
      <code>AWS-TLS13-1-1-2021-06</code>
    </li>
    <li>
      <code>AWS-TLS13-1-0-2021-06</code>
    </li>
  </ul>
</details>
<details>
  <summary>AWS ELB FS supported policies</summary>
  <ul>
    <li>
      <code>AWS-FS-1-2-Res-2020-10</code>
    </li>
    <li>
      <code>AWS-FS-1-2-Res-2019-08</code>
    </li>
    <li>
      <code>AWS-FS-1-2-2019-08</code>
    </li>
    <li>
      <code>AWS-FS-1-1-2019-08</code>
    </li>
    <li>
      <code>AWS-FS-2018-06</code>
    </li>
  </ul>
</details>
<details>
  <summary>AWS ELB TLS 1.0 - 1.2 security policies</summary>
  <ul>
    <li>
      <code>AWS-TLS-1-2-Ext-2018-06</code>
    </li>
    <li>
      <code>AWS-TLS-1-2-2017-01</code>
    </li>
    <li>
      <code>AWS-TLS-1-1-2017-01</code>
    </li>
    <li>
      <code>AWS-2016-08</code>
    </li>
  </ul>
</details>
<details>
  <summary>AWS Classic ELB security policies</summary>
  <ul>
     <li>
      <code>AWS-2015-05</code>
    </li>
    <li>
      <code>AWS-2015-03</code>
    </li>
    <li>
      <code>AWS-2015-02</code>
    </li>
  </ul>
</details>
</br>

Note that the `Mozilla-Old` policy should use a 1024 bits DH key for compatibility but this container provides a 4096 bits key. The [Diffie-Hellman Groups](#diffie-hellman-groups) section details different methods of bypassing this, either globally or per virtual-host.

The default behavior for the proxy when port 80 and 443 are exposed is as follows:

* If a virtual host has a usable cert, port 80 will redirect to 443 for that virtual host so that HTTPS is always preferred when available.
* If the virtual host does not have a usable cert, but `default.crt` and `default.key` exist, those will be used as the virtual host's certificate and the client browser will receive a 500 error.
* If the virtual host does not have a usable cert, and `default.crt` and `default.key` do not exist, TLS negotiation will fail (see [Missing Certificate](#missing-certificate) below).

To serve traffic in both SSL and non-SSL modes without redirecting to SSL, you can include the environment variable `HTTPS_METHOD=noredirect` (the default is `HTTPS_METHOD=redirect`). You can also disable the non-SSL site entirely with `HTTPS_METHOD=nohttp`, or disable the HTTPS site with `HTTPS_METHOD=nohttps`. `HTTPS_METHOD` can be specified on each container for which you want to override the default behavior or on the proxy container to set it globally. If `HTTPS_METHOD=noredirect` is used, Strict Transport Security (HSTS) is disabled to prevent HTTPS users from being redirected by the client. If you cannot get to the HTTP site after changing this setting, your browser has probably cached the HSTS policy and is automatically redirecting you back to HTTPS. You will need to clear your browser's HSTS cache or use an incognito window / different browser.

By default, [HTTP Strict Transport Security (HSTS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)  is enabled with `max-age=31536000` for HTTPS sites. You can disable HSTS with the environment variable `HSTS=off` or use a custom HSTS configuration like `HSTS=max-age=31536000; includeSubDomains; preload`. 

*WARNING*: HSTS will force your users to visit the HTTPS version of your site for the `max-age` time - even if they type in `http://` manually.  The only way to get to an HTTP site after receiving an HSTS response is to clear your browser's HSTS cache.

#### Missing Certificate

If HTTPS is enabled for a virtual host but its certificate is missing, nginx-proxy will configure nginx to use the default certificate (`default.crt` with `default.key`) and return a 500 error.

If the default certificate is also missing, nginx-proxy will configure nginx to accept HTTPS connections but fail the TLS negotiation.  Client browsers will render a TLS error page.  As of March 2023, web browsers display the following error messages:

  * Chrome:

    > This site can't provide a secure connection
    >
    > example.test sent an invalid response.
    >
    > Try running Connectivity Diagnostics.
    >
    > `ERR_SSL_PROTOCOL_ERROR`

  * Firefox:

    > Secure Connection Failed
    >
    > An error occurred during a connection to example.test.
    > Peer reports it experienced an internal error.
    >
    > Error code: `SSL_ERROR_INTERNAL_ERROR_ALERT` "TLS error".

### HTTP/2 support

HTTP/2 is enabled by default and can be disabled if necessary either per-proxied container or globally:

To disable HTTP/2 for a single proxied container, set the `com.github.nginx-proxy.nginx-proxy.http2.enable` label to `false` on this container.

To disable HTTP/2 globally set the environment variable `ENABLE_HTTP2` to `false` on the nginx-proxy container.

More reading on the potential TCP head-of-line blocking issue with HTTP/2: [HTTP/2 Issues](https://www.twilio.com/blog/2017/10/http2-issues.html), [Comparing HTTP/3 vs HTTP/2](https://blog.cloudflare.com/http-3-vs-http-2/)

### HTTP/3 support

> **Warning**
> HTTP/3 support [is still considered experimental in nginx](https://www.nginx.com/blog/binary-packages-for-preview-nginx-quic-http3-implementation/) and as such is considered experimental in nginx-proxy too and is disabled by default. [Feedbacks for the HTTP/3 support are welcome in #2271.](https://github.com/nginx-proxy/nginx-proxy/discussions/2271)

HTTP/3 use the QUIC protocol over UDP (unlike HTTP/1.1 and HTTP/2 which work over TCP), so if you want to use HTTP/3 you'll have to explicitely publish the 443/udp port of the proxy in addition to the 443/tcp port:

```console
docker run -d -p 80:80 -p 443:443/tcp -p 443:443/udp \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

HTTP/3 can be enabled either per-proxied container or globally:

To enable HTTP/3 for a single proxied container, set the `com.github.nginx-proxy.nginx-proxy.http3.enable` label to `true` on this container.

To enable HTTP/3 globally set the environment variable `ENABLE_HTTP3` to `true` on the nginx-proxy container.

### Basic Authentication Support

In order to be able to secure your virtual host, you have to create a file named as its equivalent VIRTUAL_HOST variable on directory
/etc/nginx/htpasswd/$VIRTUAL_HOST

```console
docker run -d -p 80:80 -p 443:443 \
    -v /path/to/htpasswd:/etc/nginx/htpasswd \
    -v /path/to/certs:/etc/nginx/certs \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

You'll need apache2-utils on the machine where you plan to create the htpasswd file. Follow these [instructions](http://httpd.apache.org/docs/2.2/programs/htpasswd.html)

If you want to define basic authentication for a `VIRTUAL_PATH`, you have to create a file named as /etc/nginx/htpasswd/${VIRTUAL_HOST}_${VIRTUAL_PATH_SHA1}
(where $VIRTUAL_PATH_SHA1 is the SHA1 hash for the virtual path, you can use any SHA1 online generator to calculate it).

### Upstream (Backend) Server HTTP Load Balancing Support

> **Warning**
> This feature is experimental.  The behavior may change (or the feature may be removed entirely) without warning in a future release, even if the release is not a new major version.  If you use this feature, or if you would like to use this feature but you require changes to it first, please [provide feedback in #2195](https://github.com/nginx-proxy/nginx-proxy/discussions/2195).  Once we have collected enough feedback we will promote this feature to officially supported.

If you have multiple containers with the same `VIRTUAL_HOST` and `VIRTUAL_PATH` settings, nginx will spread the load across all of them.  To change the load balancing algorithm from nginx's default (round-robin), set the `com.github.nginx-proxy.nginx-proxy.loadbalance` label on one or more of your application containers to the desired load balancing directive.  See the [`ngx_http_upstream_module` documentation](https://nginx.org/en/docs/http/ngx_http_upstream_module.html) for available directives.

> **Note**
> * Don't forget the terminating semicolon (`;`).
> * If you are using Docker Compose, remember to escape any dollar sign (`$`) characters (`$` becomes `$$`).

Docker Compose example:

```yaml
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
    environment:
      HTTPS_METHOD: nohttps
  myapp:
    image: jwilder/whoami
    expose:
      - "8000"
    environment:
      VIRTUAL_HOST: myapp.example
      VIRTUAL_PORT: "8000"
    labels:
      com.github.nginx-proxy.nginx-proxy.loadbalance: "hash $$remote_addr;"
    deploy:
      replicas: 4
```

### Upstream (Backend) Server HTTP Keep-Alive Support

> **Warning**
> This feature is experimental.  The behavior may change (or the feature may be removed entirely) without warning in a future release, even if the release is not a new major version.  If you use this feature, or if you would like to use this feature but you require changes to it first, please [provide feedback in #2194](https://github.com/nginx-proxy/nginx-proxy/discussions/2194).  Once we have collected enough feedback we will promote this feature to officially supported.

To enable HTTP keep-alive between `nginx-proxy` and backend server(s), set the `com.github.nginx-proxy.nginx-proxy.keepalive` label on the server's container either to `auto` or to the desired maximum number of idle connections. The `auto` setting will dynamically set the maximum number of idle connections to twice the number of servers listed in the corresponding `upstream{}` block, [per nginx recommendation](https://www.nginx.com/blog/avoiding-top-10-nginx-configuration-mistakes/#no-keepalives).

See the [nginx keepalive documentation](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#keepalive) and the [Docker label documentation](https://docs.docker.com/config/labels-custom-metadata/) for details.

### Headers

By default, `nginx-proxy` forwards all incoming request headers from the client to the backend server unmodified, with the following exceptions:

  * `Connection`: Set to `upgrade` if the client sets the `Upgrade` header, otherwise set to `close`. (Keep-alive between `nginx-proxy` and the backend server is not supported.)
  * `Proxy`: Always removed if present. This prevents attackers from using the so-called [httpoxy attack](http://httpoxy.org). There is no legitimate reason for a client to send this header, and there are many vulnerable languages / platforms (`CVE-2016-5385`, `CVE-2016-5386`, `CVE-2016-5387`, `CVE-2016-5388`, `CVE-2016-1000109`, `CVE-2016-1000110`, `CERT-VU#797896`).
  * `X-Real-IP`: Set to the client's IP address.
  * `X-Forwarded-For`: The client's IP address is appended to the value provided by the client. (If the client did not provide this header, it is set to the client's IP address.)
  * `X-Forwarded-Host`: If the client did not provide this header or if the `TRUST_DOWNSTREAM_PROXY` environment variable is set to `false` (see below), this is set to the value of the `Host` header provided by the client. Otherwise, the header is forwarded to the backend server unmodified.
  * `X-Forwarded-Proto`: If the client did not provide this header or if the `TRUST_DOWNSTREAM_PROXY` environment variable is set to `false` (see below), this is set to `http` for plain HTTP connections and `https` for TLS connections. Otherwise, the header is forwarded to the backend server unmodified.
  * `X-Forwarded-Ssl`: Set to `on` if the `X-Forwarded-Proto` header sent to the backend server is `https`, otherwise set to `off`.
  * `X-Forwarded-Port`: If the client did not provide this header or if the `TRUST_DOWNSTREAM_PROXY` environment variable is set to `false` (see below), this is set to the port of the server that accepted the client's request. Otherwise, the header is forwarded to the backend server unmodified.
  * `X-Original-URI`: Set to the original request URI.

#### Trusting Downstream Proxy Headers

For legacy compatibility reasons, `nginx-proxy` forwards any client-supplied `X-Forwarded-Proto` (which affects the value of `X-Forwarded-Ssl`), `X-Forwarded-Host`, and `X-Forwarded-Port` headers unchecked and unmodified. To prevent malicious clients from spoofing the protocol, hostname, or port that is perceived by your backend server, you are encouraged to set the `TRUST_DOWNSTREAM_PROXY` value to `false` if:

  * you do not operate a second reverse proxy downstream of `nginx-proxy`, or
  * you do operate a second reverse proxy downstream of `nginx-proxy` but that proxy forwards those headers unchecked from untrusted clients.

The default for `TRUST_DOWNSTREAM_PROXY` may change to `false` in a future version of `nginx-proxy`. If you require it to be enabled, you are encouraged to explicitly set it to `true` to avoid compatibility problems when upgrading.

### Custom Nginx Configuration

If you need to configure Nginx beyond what is possible using environment variables, you can provide custom configuration files on either a proxy-wide or per-`VIRTUAL_HOST` basis.

#### Replacing default proxy settings

If you want to replace the default proxy settings for the nginx container, add a configuration file at `/etc/nginx/proxy.conf`. A file with the default settings would look like this:

```Nginx
# HTTP 1.1 support
proxy_http_version 1.1;
proxy_set_header Host $http_host;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $proxy_connection;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Host $proxy_x_forwarded_host;
proxy_set_header X-Forwarded-Proto $proxy_x_forwarded_proto;
proxy_set_header X-Forwarded-Ssl $proxy_x_forwarded_ssl;
proxy_set_header X-Forwarded-Port $proxy_x_forwarded_port;
proxy_set_header X-Original-URI $request_uri;

# Mitigate httpoxy attack (see README for details)
proxy_set_header Proxy "";
```

***NOTE***: If you provide this file it will replace the defaults; you may want to check the .tmpl file to make sure you have all of the needed options.

#### Proxy-wide

To add settings on a proxy-wide basis, add your configuration file under `/etc/nginx/conf.d` using a name ending in `.conf`.

This can be done in a derived image by creating the file in a `RUN` command or by `COPY`ing the file into `conf.d`:

```Dockerfile
FROM nginxproxy/nginx-proxy
RUN { \
      echo 'server_tokens off;'; \
      echo 'client_max_body_size 100m;'; \
    } > /etc/nginx/conf.d/my_proxy.conf
```

Or it can be done by mounting in your custom configuration in your `docker run` command:

```console
docker run -d -p 80:80 -p 443:443 -v /path/to/my_proxy.conf:/etc/nginx/conf.d/my_proxy.conf:ro -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
```

#### Per-VIRTUAL_HOST

To add settings on a per-`VIRTUAL_HOST` basis, add your configuration file under `/etc/nginx/vhost.d`. Unlike in the proxy-wide case, which allows multiple config files with any name ending in `.conf`, the per-`VIRTUAL_HOST` file must be named exactly after the `VIRTUAL_HOST`.

In order to allow virtual hosts to be dynamically configured as backends are added and removed, it makes the most sense to mount an external directory as `/etc/nginx/vhost.d` as opposed to using derived images or mounting individual configuration files.

For example, if you have a virtual host named `app.example.com`, you could provide a custom configuration for that host as follows:

```console
docker run -d -p 80:80 -p 443:443 -v /path/to/vhost.d:/etc/nginx/vhost.d:ro -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
{ echo 'server_tokens off;'; echo 'client_max_body_size 100m;'; } > /path/to/vhost.d/app.example.com
```

If you are using multiple hostnames for a single container (e.g. `VIRTUAL_HOST=example.com,www.example.com`), the virtual host configuration file must exist for each hostname. If you would like to use the same configuration for multiple virtual host names, you can use a symlink:

```console
{ echo 'server_tokens off;'; echo 'client_max_body_size 100m;'; } > /path/to/vhost.d/www.example.com
ln -s /path/to/vhost.d/www.example.com /path/to/vhost.d/example.com
```

#### Per-VIRTUAL_HOST default configuration

If you want most of your virtual hosts to use a default single configuration and then override on a few specific ones, add those settings to the `/etc/nginx/vhost.d/default` file. This file will be used on any virtual host which does not have a `/etc/nginx/vhost.d/{VIRTUAL_HOST}` file associated with it.

#### Per-VIRTUAL_HOST location configuration

To add settings to the "location" block on a per-`VIRTUAL_HOST` basis, add your configuration file under `/etc/nginx/vhost.d` just like the previous section except with the suffix `_location`.

For example, if you have a virtual host named `app.example.com` and you have configured a proxy_cache `my-cache` in another custom file, you could tell it to use a proxy cache as follows:

```console
docker run -d -p 80:80 -p 443:443 -v /path/to/vhost.d:/etc/nginx/vhost.d:ro -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
{ echo 'proxy_cache my-cache;'; echo 'proxy_cache_valid  200 302  60m;'; echo 'proxy_cache_valid  404 1m;' } > /path/to/vhost.d/app.example.com_location
```

If you are using multiple hostnames for a single container (e.g. `VIRTUAL_HOST=example.com,www.example.com`), the virtual host configuration file must exist for each hostname. If you would like to use the same configuration for multiple virtual host names, you can use a symlink:

```console
{ echo 'proxy_cache my-cache;'; echo 'proxy_cache_valid  200 302  60m;'; echo 'proxy_cache_valid  404 1m;' } > /path/to/vhost.d/app.example.com_location
ln -s /path/to/vhost.d/www.example.com /path/to/vhost.d/example.com
```

#### Per-VIRTUAL_HOST location default configuration

If you want most of your virtual hosts to use a default single `location` block configuration and then override on a few specific ones, add those settings to the `/etc/nginx/vhost.d/default_location` file. This file will be used on any virtual host which does not have a `/etc/nginx/vhost.d/{VIRTUAL_HOST}_location` file associated with it.

#### Overriding `location` blocks

The `${VIRTUAL_HOST}_${PATH_HASH}_location`, `${VIRTUAL_HOST}_location`, and `default_location` files documented above make it possible to *augment* the generated [`location` block(s)](https://nginx.org/en/docs/http/ngx_http_core_module.html#location) in a virtual host.  In some circumstances, you may need to *completely override* the `location` block for a particular combination of virtual host and path.  To do this, create a file whose name follows this pattern:

```
/etc/nginx/vhost.d/${VIRTUAL_HOST}_${PATH_HASH}_location_override
```

where `${VIRTUAL_HOST}` is the name of the virtual host (the `VIRTUAL_HOST` environment variable) and `${PATH_HASH}` is the SHA-1 hash of the path, as [described above](#per-virtual_path-location-configuration).

For convenience, the `_${PATH_HASH}` part can be omitted if the path is `/`:

```
/etc/nginx/vhost.d/${VIRTUAL_HOST}_location_override
```

When an override file exists, the `location` block that is normally created by `nginx-proxy` is not generated.  Instead, the override file is included via the [nginx `include` directive](https://nginx.org/en/docs/ngx_core_module.html#include).

You are responsible for providing a suitable `location` block in your override file as required for your service.  By default, `nginx-proxy` uses the `VIRTUAL_HOST` name as the upstream name for your application's Docker container; see [here](#unhashed-vs-sha1-upstream-names) for details.  As an example, if your container has a `VIRTUAL_HOST` value of `app.example.com`, then to override the location block for `/` you would create a file named `/etc/nginx/vhost.d/app.example.com_location_override` that contains something like this:

```
location / {
    proxy_pass http://app.example.com;
}
```

#### Per-VIRTUAL_HOST `server_tokens` configuration
Per virtual-host `servers_tokens` directive can be configured by passing appropriate value to the `SERVER_TOKENS` environment variable. Please see the [nginx http_core module configuration](https://nginx.org/en/docs/http/ngx_http_core_module.html#server_tokens) for more details.

### Unhashed vs SHA1 upstream names

By default the nginx configuration `upstream` blocks will use this block's corresponding hostname as a predictable name. However, this can cause issues in some setups (see [this issue](https://github.com/nginx-proxy/nginx-proxy/issues/1162)). In those cases you might want to switch to SHA1 names for the `upstream` blocks by setting the `SHA1_UPSTREAM_NAME` environment variable to `true` on the nginx-proxy container.

Please note that using regular expressions in `VIRTUAL_HOST` will always result in a corresponding `upstream` block with an SHA1 name.

### Troubleshooting

If you can't access your `VIRTUAL_HOST`, inspect the generated nginx configuration:

```console
docker exec <nginx-proxy-instance> nginx -T
```

Pay attention to the `upstream` definition blocks, which should look like this:

```Nginx
# foo.example.com
upstream foo.example.com {
	## Can be connected with "my_network" network
	# Exposed ports: [{   <exposed_port1>  tcp } {   <exposed_port2>  tcp } ...]
	# Default virtual port: <exposed_port|80>
	# VIRTUAL_PORT: <VIRTUAL_PORT>
	# foo
	server 172.18.0.9:<Port>;
	# Fallback entry
	server 127.0.0.1 down;
}
```

The effective `Port` is retrieved by order of precedence:
1. From the `VIRTUAL_PORT` environment variable
1. From the container's exposed port if there is only one
1. From the default port 80 when none of the above methods apply

### Contributing

Before submitting pull requests or issues, please check github to make sure an existing issue or pull request is not already open.

#### Running Tests Locally

To run tests, you just need to run the command below:

```console
make test
```

This commands run tests on two variants of the nginx-proxy docker image: Debian and Alpine.

You can run the tests for each of these images with their respective commands:

```console
make test-debian
make test-alpine
```

You can learn more about how the test suite works and how to write new tests in the [test/README.md](https://github.com/nginx-proxy/nginx-proxy/tree/main/test/README.md) file.
