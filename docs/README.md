# Table of Contents

- [Virtual Hosts and Ports](#virtual-hosts-and-ports)
- [Path-based Routing](#path-based-routing)
- [Docker Networking](#docker-networking)
- [Upstream (Backend) features](#upstream-backend-features)
- [Basic Authentication Support](#basic-authentication-support)
- [mTLS client side certificate authentication](#mtls-client-side-certificate-authentication)
- [Logging](#logging)
- [SSL Support](#ssl-support)
- [IPv6 Support](#ipv6-nat)
- [HTTP/2 and HTTP/3](#http2-and-http3)
- [Headers](#headers)
- [Custom Nginx Configuration](#custom-nginx-configuration)
- [TCP and UDP stream](#tcp-and-udp-stream)
- [Unhashed vs SHA1 upstream names](#unhashed-vs-sha1-upstream-names)
- [Separate Containers](#separate-containers)
- [Docker Compose](#docker-compose)
- [Configuration Summary](#configuration-summary)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Virtual Hosts and Ports

### Multiple Hosts

If you need to support multiple virtual hosts for a container, you can separate each entry with commas. For example, `foo.bar.com,baz.bar.com,bar.com` and each host will be setup the same.

### Wildcard Hosts

You can also use wildcards at the beginning and the end of host name, like `*.bar.com` or `foo.bar.*`. Or even a regular expression, which can be very useful in conjunction with a wildcard DNS service like [nip.io](https://nip.io) or [sslip.io](https://sslip.io), using `~^foo\.bar\..*\.nip\.io` will match `foo.bar.127.0.0.1.nip.io`, `foo.bar.10.0.2.2.nip.io` and all other given IPs. More information about this topic can be found in the nginx documentation about [`server_names`](http://nginx.org/en/docs/http/server_names.html).

### Default Host

To set the default host for nginx use the env var `DEFAULT_HOST=foo.bar.com` for example

```console
docker run --detach \
    --publish 80:80 \
    --env DEFAULT_HOST=foo.bar.com \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

nginx-proxy will then redirect all requests to a container where `VIRTUAL_HOST` is set to `DEFAULT_HOST`, if they don't match any (other) `VIRTUAL_HOST`. Using the example above requests without matching `VIRTUAL_HOST` will be redirected to a plain nginx instance after running the following command:

```console
docker run --detach \
    --env VIRTUAL_HOST=foo.bar.com \
    nginx
```

### Virtual Ports

When your container exposes only one port, nginx-proxy will default to this port, else to port 80.

If you need to specify a different port, you can set a `VIRTUAL_PORT` env var to select a different one. This variable cannot be set to more than one port.

For each host defined into `VIRTUAL_HOST`, the associated virtual port is retrieved by order of precedence:

1. From the `VIRTUAL_PORT` environment variable
1. From the container's exposed port if there is only one
1. From the default port 80 when none of the above methods apply

### Multiple ports

If your container expose more than one service on different ports and those services need to be proxied, you'll need to use the `VIRTUAL_HOST_MULTIPORTS` environment variable. This variable takes virtual host, path, port and dest definition in YAML (or JSON) form, and completely override the `VIRTUAL_HOST`, `VIRTUAL_PORT`, `VIRTUAL_PROTO`, `VIRTUAL_PATH` and `VIRTUAL_DEST` environment variables on this container.

The YAML syntax should be easier to write on Docker compose files, while the JSON syntax can be used for CLI invocation.

The expected format is the following:

```yaml
hostname:
  path:
    port: int
    proto: string
    dest: string
```

For each hostname entry, `path`, `port`, `proto` and `dest` are optional and are assigned default values when missing:

- `path` = "/"
- `port` = default port
- `proto` = "http"
- `dest` = ""

#### Multiple ports routed to different hostnames

The following example use an hypothetical container running services over HTTP on port 80, 8000 and 9000:

```yaml
services:
  multiport-container:
    image: somerepo/somecontainer
    container_name: multiport-container
    environment:
      VIRTUAL_HOST_MULTIPORTS: |-
        www.example.org:
        service1.example.org:
          "/":
            port: 8000
        service2.example.org:
          "/":
            port: 9000

# There is no path dict specified for www.example.org, so it get the default values:
# www.example.org:
#   "/":
#     port: 80 (default port)
#     dest: ""

# JSON equivalent:
#     VIRTUAL_HOST_MULTIPORTS: |-
#       {
#         "www.example.org": {},
#         "service1.example.org": { "/": { "port": 8000, "dest": "" } },
#         "service2.example.org": { "/": { "port": 9000, "dest": "" } }
#       }
```

This would result in the following proxy config:

- `www.example.org` -> `multiport-container:80` over `HTTP`
- `service1.example.org` -> `multiport-container:8000` over `HTTP`
- `service2.example.org` -> `multiport-container:9000` over `HTTP`

#### Multiple ports routed to same hostname and different paths

The following example use an hypothetical container running services over HTTP on port 80 and 8000 and over HTTPS on port 9443:

```yaml
services:
  multiport-container:
    image: somerepo/somecontainer
    container_name: multiport-container
    environment:
      VIRTUAL_HOST_MULTIPORTS: |-
        www.example.org:
          "/":
          "/service1":
            port: 8000
            dest: "/"
          "/service2":
            port: 9443
            proto: "https"
            dest: "/"

# port and dest are not specified on the / path, so this path is routed to the
# default port with the default dest value (empty string) and default proto (http)

# JSON equivalent:
#     VIRTUAL_HOST_MULTIPORTS: |-
#       {
#         "www.example.org": {
#           "/": {},
#           "/service1": { "port": 8000, "dest": "/" },
#           "/service2": { "port": 9443, "proto": "https", "dest": "/" }
#         }
#       }
```

This would result in the following proxy config:

- `www.example.org` -> `multiport-container:80` over `HTTP`
- `www.example.org/service1` -> `multiport-container:8000` over `HTTP`
- `www.example.org/service2` -> `multiport-container:9443` over `HTTPS`

⬆️ [back to table of contents](#table-of-contents)

## Path-based Routing

You can have multiple containers proxied by the same `VIRTUAL_HOST` by adding a `VIRTUAL_PATH` environment variable containing the absolute path to where the container should be mounted. For example with `VIRTUAL_HOST=foo.example.com` and `VIRTUAL_PATH=/api/v2/service`, then requests to http://foo.example.com/api/v2/service will be routed to the container. If you wish to have a container serve the root while other containers serve other paths, give the root container a `VIRTUAL_PATH` of `/`. Unmatched paths will be served by the container at `/` or will return the default nginx error page if no container has been assigned `/`.
It is also possible to specify multiple paths with regex locations like `VIRTUAL_PATH=~^/(app1|alternative1)/`. For further details see the nginx documentation on location blocks. This is not compatible with `VIRTUAL_DEST`.

The full request URI will be forwarded to the serving container in the `X-Original-URI` header.

> [!NOTE]
> Your application needs to be able to generate links starting with `VIRTUAL_PATH`. This can be achieved by it being natively on this path or having an option to prepend this path. The application does not need to expect this path in the request.

### VIRTUAL_DEST

This environment variable can be used to rewrite the `VIRTUAL_PATH` part of the requested URL to proxied application. The default value is empty (off).
Make sure that your settings won't result in the slash missing or being doubled. Both these versions can cause troubles.

If the application runs natively on this sub-path or has a setting to do so, `VIRTUAL_DEST` should not be set or empty.
If the requests are expected to not contain a sub-path and the generated links contain the sub-path, `VIRTUAL_DEST=/` should be used.

```console
docker run --detach \
    --name app1 \
    --env VIRTUAL_HOST=example.tld \
    --env VIRTUAL_PATH=/app1/ \
    --env VIRTUAL_DEST=/ \
    app
```

In this example, the incoming request `http://example.tld/app1/foo` will be proxied as `http://app1/foo` instead of `http://app1/app1/foo`.

### Per-VIRTUAL_PATH location configuration

The same options as from [Per-VIRTUAL_HOST location configuration](#Per-VIRTUAL_HOST-location-configuration) are available on a `VIRTUAL_PATH` basis.
The only difference is that the filename gets an additional block `HASH=$(echo -n $VIRTUAL_PATH | sha1sum | awk '{ print $1 }')`. This is the sha1-hash of the `VIRTUAL_PATH` (no newline). This is done for filename sanitization purposes.

The used filename is `${VIRTUAL_HOST}_${PATH_HASH}_location`, or when `VIRTUAL_HOST` is a regex, `${VIRTUAL_HOST_HASH}_${PATH_HASH}_location`.

The filename of the previous example would be `example.tld_8610f6c344b4096614eab6e09d58885349f42faf_location`.

### DEFAULT_ROOT

This environment variable of the nginx proxy container can be used to customize the return error page if no matching path is found. Furthermore it is possible to use anything which is compatible with the `return` statement of nginx.

Exception: If this is set to the string `none`, no default `location /` directive will be generated. This makes it possible for you to provide your own `location /` directive in your [`/etc/nginx/vhost.d/VIRTUAL_HOST`](#per-virtual_host) or [`/etc/nginx/vhost.d/default`](#per-virtual_host-default-configuration) files.

If unspecified, `DEFAULT_ROOT` defaults to `404`.

Examples (YAML syntax):

- `DEFAULT_ROOT: "none"` prevents `nginx-proxy` from generating a default `location /` directive.
- `DEFAULT_ROOT: "418"` returns a 418 error page instead of the normal 404 one.
- `DEFAULT_ROOT: "301 https://github.com/nginx-proxy/nginx-proxy/blob/main/README.md"` redirects the client to this documentation.

Nginx variables such as `$scheme`, `$host`, and `$request_uri` can be used. However, care must be taken to make sure the `$` signs are escaped properly. For example, if you want to use `301 $scheme://$host/myapp1$request_uri` you should use:

- Bash: `DEFAULT_ROOT='301 $scheme://$host/myapp1$request_uri'`
- Docker Compose yaml: `- DEFAULT_ROOT: 301 $$scheme://$$host/myapp1$$request_uri`

⬆️ [back to table of contents](#table-of-contents)

## Docker Networking

### Custom external HTTP/HTTPS ports

If you want to use `nginx-proxy` with different external ports that the default ones of `80` for `HTTP` traffic and `443` for `HTTPS` traffic, you'll have to use the environment variable(s) `HTTP_PORT` and/or `HTTPS_PORT` in addition to the changes to the Docker port mapping. If you change the `HTTPS` port, the redirect for `HTTPS` traffic will also be configured to redirect to the custom port. Typical usage, here with the custom ports `1080` and `10443`:

```console
docker run --detach \
    --publish 1080:1080 \
    --publish 10443:10443 \
    --env HTTP_PORT=1080 \
    --env HTTPS_PORT=10443 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

### Multiple Networks

With the addition of [overlay networking](https://docs.docker.com/engine/userguide/networking/get-started-overlay/) in Docker 1.9, your `nginx-proxy` container may need to connect to backend containers on multiple networks. By default, if you don't pass the `--net` flag when your `nginx-proxy` container is created, it will only be attached to the default `bridge` network. This means that it will not be able to connect to containers on networks other than `bridge`.

If you want your `nginx-proxy` container to be attached to a different network, you must pass the `--net=my-network` option in your `docker create` or `docker run` command. At the time of this writing, only a single network can be specified at container creation time. To attach to other networks, you can use the `docker network connect` command after your container is created:

```console
docker run --detach \
    --name my-nginx-proxy \
    --publish 80:80 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --net my-network \
    nginxproxy/nginx-proxy
docker network connect my-other-network my-nginx-proxy
```

In this example, the `my-nginx-proxy` container will be connected to `my-network` and `my-other-network` and will be able to proxy to other containers attached to those networks.

### Host networking

`nginx-proxy` is compatible with containers using Docker's [host networking](https://docs.docker.com/network/host/), both with the proxy connected to one or more [bridge network](https://docs.docker.com/network/bridge/) (default or user created) or running in host network mode itself.

Proxyed containers running in host network mode **must** use the [`VIRTUAL_PORT`](#virtual-ports) environment variable, as this is the only way for `nginx-proxy` to get the correct port (or a port at all) for those containers.

### Internet vs. Local Network Access

If you allow traffic from the public internet to access your `nginx-proxy` container, you may want to restrict some containers to the internal network only, so they cannot be accessed from the public internet. On containers that should be restricted to the internal network, you should set the environment variable `NETWORK_ACCESS=internal`. By default, the _internal_ network is defined as `127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16`. To change the list of networks considered internal, mount a file on the `nginx-proxy` at `/etc/nginx/network_internal.conf` with these contents, edited to suit your needs:

```nginx
# These networks are considered "internal"
allow 127.0.0.0/8;
allow 10.0.0.0/8;
allow 192.168.0.0/16;
allow 172.16.0.0/12;

# Traffic from all other networks will be rejected
deny all;
```

When internal-only access is enabled, external clients will be denied with an `HTTP 403 Forbidden`

> [!NOTE]
> If there is a load-balancer / reverse proxy in front of `nginx-proxy` that hides the client IP (example: AWS Application/Elastic Load Balancer), you will need to use the nginx `realip` module (already installed) to extract the client's IP from the HTTP request headers. Please see the [nginx realip module configuration](http://nginx.org/en/docs/http/ngx_http_realip_module.html) for more details. This configuration can be added to a new config file and mounted in `/etc/nginx/conf.d/`.

⬆️ [back to table of contents](#table-of-contents)

## Upstream (Backend) features

### SSL Upstream

If you would like the reverse proxy to connect to your backend using HTTPS instead of HTTP, set `VIRTUAL_PROTO=https` on the backend container.

> [!NOTE]
> If you use `VIRTUAL_PROTO=https` and your backend container exposes port 80 and 443, `nginx-proxy` will use HTTPS on port 80. This is almost certainly not what you want, so you should also include `VIRTUAL_PORT=443`.

### uWSGI Upstream

If you would like to connect to uWSGI backend, set `VIRTUAL_PROTO=uwsgi` on the backend container. Your backend container should then listen on a port rather than a socket and expose that port.

### FastCGI Upstream

If you would like to connect to FastCGI backend, set `VIRTUAL_PROTO=fastcgi` on the backend container. Your backend container should then listen on a port rather than a socket and expose that port.

#### FastCGI File Root Directory

If you use fastcgi,you can set `VIRTUAL_ROOT=xxx` for your root directory

### Upstream Server HTTP Load Balancing Support

If you have multiple containers with the same `VIRTUAL_HOST` and `VIRTUAL_PATH` settings, nginx will spread the load across all of them. To change the load balancing algorithm from nginx's default (round-robin), set the `com.github.nginx-proxy.nginx-proxy.loadbalance` label on one or more of your application containers to the desired load balancing directive. See the [`ngx_http_upstream_module` documentation](https://nginx.org/en/docs/http/ngx_http_upstream_module.html) for available directives.

> [!NOTE]
>
> - Don't forget the terminating semicolon (`;`).
> - If you are using Docker Compose, remember to escape any dollar sign (`$`) characters (`$` becomes `$$`).

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

### Upstream Server HTTP Keep-Alive Support

By default `nginx-proxy` will enable HTTP keep-alive between itself and backend server(s) and set the maximum number of idle connections to twice the number of servers listed in the corresponding `upstream{}` block, [per nginx recommendation](https://www.nginx.com/blog/avoiding-top-10-nginx-configuration-mistakes/#no-keepalives). To manually set the maximum number of idle connections or disable HTTP keep-alive entirely, use the `com.github.nginx-proxy.nginx-proxy.keepalive` label on the server's container (setting it to `disabled` will disable HTTP keep-alive).

See the [nginx keepalive documentation](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#keepalive) and the [Docker label documentation](https://docs.docker.com/config/labels-custom-metadata/) for details.

⬆️ [back to table of contents](#table-of-contents)

## Basic Authentication Support

In order to be able to secure your virtual host, you have to create a file named as its equivalent `VIRTUAL_HOST` variable (or if using a regex `VIRTUAL_HOST`, as the sha1 hash of the regex) in directory
`/etc/nginx/htpasswd/`. Example: `/etc/nginx/htpasswd/app.example.com`.

```console
docker run --detach \
    --publish 80:80 \
    --publish 443:443 \
    --volume /path/to/htpasswd:/etc/nginx/htpasswd \
    --volume /path/to/certs:/etc/nginx/certs \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

If you want to define basic authentication for a `VIRTUAL_PATH`, you have to create a file named as `/etc/nginx/htpasswd/${VIRTUAL_HOST}_${VIRTUAL_PATH_SHA1}`
(where `$VIRTUAL_PATH_SHA1` is the SHA1 hash for the virtual path, you can use any SHA1 online generator to calculate it).

You'll need apache2-utils on the machine where you plan to create the htpasswd file. Follow these [instructions](http://httpd.apache.org/docs/programs/htpasswd.html)

⬆️ [back to table of contents](#table-of-contents)

## mTLS client side certificate authentication
In mTLS, both the client and server have a certificate, and both sides authenticate using their public/private key pair.
A "root" TLS certificate is necessary for mTLS; this enables an organization to be their own certificate authority. The certificates used by authorized clients and servers have to correspond to this root certificate. The root certificate is self-signed, meaning that the organization creates it themselves.
Make sure you have a root certificate (CA) and client public/private key pair. There is a [howto in the wiki](https://github.com/nginx-proxy/nginx-proxy/wiki/mTLS-client-side-certificate-authentication).

### Certificate Authority (CA)
#### Per-VIRTUAL_HOST CA
In order to secure a virtual host, you have to copy your CA certificate file (ca.crt) named as its equivalent `VIRTUAL_HOST` variable or if `VIRTUAL_HOST` is a regex, after the sha1 hash of the regex with the suffix `.ca.crt` in directory
`/etc/nginx/certs/`. Example: `/etc/nginx/certs/app.example.com.ca.crt`.
Or if your `VIRTUAL_HOST` is a regex: `/etc/nginx/certs/9ae5d1b655182b052fed458ec701f9ae1524e1c2.ca.crt`.

#### Global CA
If you want to secure everything globally you can copy your CA certificate file (ca.crt) named as `ca.crt` in directory
`/etc/nginx/certs/`. Example: `/etc/nginx/certs/ca.crt`.

### Certificate Revocation List (CRL)
#### Per-VIRTUAL_HOST CRL
In order to use a certificate revocation list, you have to copy your CRL file named as its equivalent `VIRTUAL_HOST` variable or if `VIRTUAL_HOST` is a regex, after the sha1 hash of the regex with the suffix `.crl.pem` in directory
`/etc/nginx/certs/`. Example: `/etc/nginx/certs/app.example.com.crl.pem`.
Or if your `VIRTUAL_HOST` is a regex: `/etc/nginx/certs/9ae5d1b655182b052fed458ec701f9ae1524e1c2.crl.pem`.

#### Global CRL
If you want to use a global CRL file you have to copy your CRL file named as `ca.crl.pem` in directory
`/etc/nginx/certs/`. Example: `/etc/nginx/certs/ca.crl.pem`.

> [!NOTE]
> Use Per-VIRTUAL_HOST CRL if you configured the [Per-VIRTUAL_HOST CA](#per-virtual_host-ca) or Global CRL if you configured the [Global CA](#global-ca)

> [!IMPORTANT]
> Make sure you rotate the CRL before it's expiration date, even if nothing has changed. An expired CRL will make Nginx unable to validate the certificates that were issued.

### optional ssl_verify_client
Optional [`ssl_verify_client`](https://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_verify_client) can be activated by using the `com.github.nginx-proxy.nginx-proxy.ssl_verify_client: "optional"` label on a proxied container. If this label is set on a proxied container access is not blocked but the result of the mTLS verify is stored in the [$ssl_client_verify](https://nginx.org/en/docs/http/ngx_http_ssl_module.html#var_ssl_client_verify) variable which you can use this in the [Per-VIRTUAL_HOST location](https://github.com/nginx-proxy/nginx-proxy/tree/main/docs#per-virtual_host-location-configuration) and [Per-VIRTUAL_PATH location](https://github.com/nginx-proxy/nginx-proxy/tree/main/docs#per-virtual_path-location-configuration) configurations.

⬆️ [back to table of contents](#table-of-contents)

## Logging

The default nginx access log format is

```
$host $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$upstream_addr"
```

### Custom log format

If you want to use a custom access log format, you can set `LOG_FORMAT=xxx` on the proxy container.

With docker compose take care to escape the `$` character with `$$` to avoid variable interpolation. Example: `$remote_addr` becomes `$$remote_addr`.

### JSON log format

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

### Log format escaping

If you want to manually set nginx `log_format`'s `escape`, set the `LOG_FORMAT_ESCAPE` variable to [a value supported by nginx](https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format).

### Disable access logs

To disable nginx access logs entirely, set the `DISABLE_ACCESS_LOGS` environment variable to any value.

### Disabling colors in the container log output

To remove colors from the container log output, set the [`NO_COLOR` environment variable to any value other than an empty string](https://no-color.org/) on the nginx-proxy container.

```console
docker run --detach \
    --publish 80:80 \
    --env NO_COLOR=1 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

⬆️ [back to table of contents](#table-of-contents)

## SSL Support

SSL is supported using single host, wildcard and SAN certificates using naming conventions for certificates or optionally [specifying a cert name as an environment variable](#san-certificates).

To enable SSL:

```console
docker run --detach \
    --publish 80:80 \
    --publish 443:443 \
    --volume /path/to/certs:/etc/nginx/certs \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

The contents of `/path/to/certs` should contain the certificates and private keys for any virtual hosts in use. The certificate and keys should be named after the virtual host with a `.crt` and `.key` extension. For example, a container with `VIRTUAL_HOST=foo.bar.com` should have a `foo.bar.com.crt` and `foo.bar.com.key` file in the certs directory.

If you are running the container in a virtualized environment (Hyper-V, VirtualBox, etc...), /path/to/certs must exist in that environment or be made accessible to that environment. By default, Docker is not able to mount directories on the host machine to containers running in a virtual machine.

### SSL Support using an ACME CA

[acme-companion](https://github.com/nginx-proxy/acme-companion) is a lightweight companion container for the nginx-proxy. It allows the automated creation/renewal of SSL certificates using the ACME protocol.

By default nginx-proxy generates location blocks to handle ACME HTTP Challenge. This behavior can be changed with environment variable `ACME_HTTP_CHALLENGE_LOCATION`. It accepts these values:

- `true`: default behavior, handle ACME HTTP Challenge in all cases.
- `false`: do not handle ACME HTTP Challenge at all.
- `legacy`: legacy behavior for compatibility with older (<= `2.3`) versions of acme-companion, only handle ACME HTTP challenge when there is a certificate for the domain and `HTTPS_METHOD=redirect`.

By default, nginx-proxy does not handle ACME HTTP Challenges for unknown virtual hosts. This may happen in cases when a container is not running at the time of the renewal. To enable handling of unknown virtual hosts, set `ACME_HTTP_CHALLENGE_ACCEPT_UNKNOWN_HOST` environment variable to `true` on the nginx-proxy container.

### Diffie-Hellman Groups

[RFC7919 groups](https://datatracker.ietf.org/doc/html/rfc7919#appendix-A) with key lengths of 2048, 3072, and 4096 bits are [provided by `nginx-proxy`](https://github.com/nginx-proxy/nginx-proxy/dhparam). The ENV `DHPARAM_BITS` can be set to `2048` or `3072` to change from the default 4096-bit key. The DH key file will be located in the container at `/etc/nginx/dhparam/dhparam.pem`. Mounting a different `dhparam.pem` file at that location will override the RFC7919 key.

To use custom `dhparam.pem` files per-virtual-host, the files should be named after the virtual host with a `dhparam` suffix and `.pem` extension. For example, a container with `VIRTUAL_HOST=foo.bar.com` should have a `foo.bar.com.dhparam.pem` file in the `/etc/nginx/certs` directory.

> [!WARNING]
> The default generated `dhparam.pem` key is 4096 bits for A+ security. Some older clients (like Java 6 and 7) do not support DH keys with over 1024 bits. In order to support these clients, you must provide your own `dhparam.pem`.

In the separate container setup, no pre-generated key will be available and neither the [nginxproxy/docker-gen](https://hub.docker.com/r/nginxproxy/docker-gen) image, nor the offical [nginx](https://registry.hub.docker.com/_/nginx/) image will provide one. If you still want A+ security in a separate container setup, you should mount an RFC7919 DH key file to the nginx container at `/etc/nginx/dhparam/dhparam.pem`.

Set `DHPARAM_SKIP` environment variable to `true` to disable using default Diffie-Hellman parameters. The default value is `false`.

```console
docker run --env DHPARAM_SKIP=true ....
```

### Wildcard Certificates

Wildcard certificates and keys should be named after the parent domain name with a `.crt` and `.key` extension. For example:

- `VIRTUAL_HOST=foo.bar.com` would use cert name `bar.com.crt` and `bar.com.key` if `foo.bar.com.crt` and `foo.bar.com.key` are not available
- `VIRTUAL_HOST=sub.foo.bar.com` use cert name `foo.bar.com.crt` and `foo.bar.com.key` if `sub.foo.bar.com.crt` and `sub.foo.bar.com.key` are not available, but won't use `bar.com.crt` and `bar.com.key`.

### SAN Certificates

If your certificate(s) supports multiple domain names, you can start a container with `CERT_NAME=<name>` to identify the certificate to be used. For example, a certificate for `*.foo.com` and `*.bar.com` could be named `shared.crt` and `shared.key`. A container running with `VIRTUAL_HOST=foo.bar.com` and `CERT_NAME=shared` will then use this shared cert.

### OCSP Stapling

To enable OCSP Stapling for a domain, `nginx-proxy` looks for a PEM certificate containing the trusted CA certificate chain at `/etc/nginx/certs/<domain>.chain.pem`, where `<domain>` is the domain name in the `VIRTUAL_HOST` directive. The format of this file is a concatenation of the public PEM CA certificates starting with the intermediate CA most near the SSL certificate, down to the root CA. This is often referred to as the "SSL Certificate Chain". If found, this filename is passed to the NGINX [`ssl_trusted_certificate` directive](http://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_trusted_certificate) and OCSP Stapling is enabled.

### How SSL Support Works

The default SSL cipher configuration is based on the [Mozilla intermediate profile](https://wiki.mozilla.org/Security/Server_Side_TLS#Intermediate_compatibility_.28recommended.29) version 5.0 which should provide compatibility with clients back to Firefox 27, Android 4.4.2, Chrome 31, Edge, IE 11 on Windows 7, Java 8u31, OpenSSL 1.0.1, Opera 20, and Safari 9. Note that the DES-based TLS ciphers were removed for security. The configuration also enables HSTS, PFS, OCSP stapling and SSL session caches. Currently TLS 1.2 and 1.3 are supported.

If you don't require backward compatibility, you can use the [Mozilla modern profile](https://wiki.mozilla.org/Security/Server_Side_TLS#Modern_compatibility) profile instead by including the environment variable `SSL_POLICY=Mozilla-Modern` to the nginx-proxy container or to your container. This profile is compatible with clients back to Firefox 63, Android 10.0, Chrome 70, Edge 75, Java 11, OpenSSL 1.1.1, Opera 57, and Safari 12.1.

> [!NOTE]
> This profile is **not** compatible with any version of Internet Explorer.

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
      (this policy should use a 1024 bits DH key for compatibility but this container provides a 4096 bits key. The <a href="#diffie-hellman-groups">Diffie-Hellman Groups</a> section details different methods of bypassing this, either globally or per virtual-host.)
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

The default behavior for the proxy when port 80 and 443 are exposed is as follows:

- If a virtual host has a usable cert, port 80 will redirect to 443 for that virtual host so that HTTPS is always preferred when available.
- If the virtual host does not have a usable cert, but `default.crt` and `default.key` exist, those will be used as the virtual host's certificate.
- If the virtual host does not have a usable cert, and `default.crt` and `default.key` do not exist, or if the virtual host is configured not to trust the default certificate, SSL handshake will be rejected (see [Default and Missing Certificate](#default-and-missing-certificate) below).

The redirection from HTTP to HTTPS use by default a [`301`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/301) response for every HTTP methods (except `CONNECT` and `TRACE` which are disabled on nginx). If you wish to use a custom redirection response for the `OPTIONS`, `POST`, `PUT`, `PATCH` and `DELETE` HTTP methods, you can either do it globally with the environment variable `NON_GET_REDIRECT` on the proxy container or per virtual host with the `com.github.nginx-proxy.nginx-proxy.non-get-redirect` label on proxied containers. Valid values are [`307`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/307) and [`308`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/308).

To serve traffic in both SSL and non-SSL modes without redirecting to SSL, you can include the environment variable `HTTPS_METHOD=noredirect` (the default is `HTTPS_METHOD=redirect`). You can also disable the non-SSL site entirely with `HTTPS_METHOD=nohttp`, or disable the HTTPS site with `HTTPS_METHOD=nohttps`. `HTTPS_METHOD` can be specified on each container for which you want to override the default behavior or on the proxy container to set it globally. If `HTTPS_METHOD=noredirect` is used, Strict Transport Security (HSTS) is disabled to prevent HTTPS users from being redirected by the client. If you cannot get to the HTTP site after changing this setting, your browser has probably cached the HSTS policy and is automatically redirecting you back to HTTPS. You will need to clear your browser's HSTS cache or use an incognito window / different browser.

By default, [HTTP Strict Transport Security (HSTS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security) is enabled with `max-age=31536000` for HTTPS sites. You can disable HSTS with the environment variable `HSTS=off` or use a custom HSTS configuration like `HSTS=max-age=31536000; includeSubDomains; preload`.

> [!WARNING]
> HSTS will force your users to visit the HTTPS version of your site for the max-age time - even if they type in http:// manually. The only way to get to an HTTP site after receiving an HSTS response is to clear your browser's HSTS cache.

### Default and Missing Certificate

If no matching certificate is found for a given virtual host, nginx-proxy will configure nginx to use the default certificate (`default.crt` with `default.key`).

If the default certificate is also missing, nginx-proxy will:

- force enable HTTP; i.e. `HTTPS_METHOD` will switch to `noredirect` if it was set to `nohttp` or `redirect`. If this switch to HTTP is not wanted set `ENABLE_HTTP_ON_MISSING_CERT=false` (default is `true`).
- configure nginx to reject the SSL handshake for this vhost. Client browsers will render a TLS error page. As of October 2024, web browsers display the following error messages:

#### Chrome:

> This site can’t be reached
>
> The web page at https://example.test/ might be temporarily down or it may have moved permanently to a new web address.
>
> `ERR_SSL_UNRECOGNIZED_NAME_ALERT`

#### Firefox:

> Secure Connection Failed
>
> An error occurred during a connection to example.test. SSL peer has no certificate for the requested DNS name.
>
> Error code: `SSL_ERROR_UNRECOGNIZED_NAME_ALERT`
>
> - The page you are trying to view cannot be shown because the authenticity of the received data could not be verified.
> - Please contact the website owners to inform them of this problem.

#### Safari:

> Safari Can't Open the Page
>
> Safari can't open the page "https://example.test" because Safari can't establish a secure connection to the server "example.test".

> [!NOTE]
> Prior to version `1.7`, nginx-proxy never trusted the default certificate: when the default certificate was present, virtual hosts that did not have a usable per-virtual-host cert used the default cert but always returned a 500 error over HTTPS. If you want to restore this behaviour, you can do it globally by setting the enviroment variable `TRUST_DEFAULT_CERT` to `false` on the proxy container, or per-virtual-host by setting the label `com.github.nginx-proxy.nginx-proxy.trust-default-cert`to `false` on a proxied container.

### Certificate selection

Summarizing all the above informations, nginx-proxy will select the certificate for a given virtual host using the following sequence:

1. if `CERT_NAME` is used, nginx-proxy will use the corresponding certificate if it exists (eg `foor.bar.com` → `CERT_NAME.crt`), or disable HTTPS for this virtual host if it does not. See [SAN certificates](#san-certificates).
2. if a certificate exactly matching the virtual host hostname exist, nginx-proxy will use it (eg `foo.bar.com` → `foo.bar.com.crt`).
3. if the virtual host hostname is a subdomain (eg `foo.bar.com` but not `bar.com`) and a certificate exactly matching its parent domain exist , nginx-proxy will use it (eg `foor.bar.com` → `bar.com.crt`). See [wildcard certificates](#wildcard-certificates).
4. if the default certificate (`default.crt`) exist and is trusted, nginx-proxy will use it (eg `foor.bar.com` → `default.crt`). See [default and missing certificate](#default-and-missing-certificate).
5. if the default certificate does not exist or isn't trusted, nginx-proxy will disable HTTPS for this virtual host (eg `foor.bar.com` → no HTTPS).

> [!IMPORTANT]
> Using `CERT_NAME` take precedence over the certificate selection process, meaning nginx-proxy will not auto select a correct certificate in step 2 trough 5 if `CERT_NAME` was used with an incorrect value or without corresponding certificate.

> [!NOTE]
> In all the above cases, if a private key file corresponding to the selected certificate (eg `foo.bar.com.key` for the `foor.bar.com.crt` certificate) does not exist, HTTPS will be disabled for this virtual host.

⬆️ [back to table of contents](#table-of-contents)

## IPv6 Support

### IPv6 Docker Networks

nginx-proxy support both IPv4 and IPv6 on Docker networks.

By default nginx-proxy will prefer IPv4: if a container can be reached over both IPv4 and IPv6, only its IPv4 will be used.

This can be changed globally by setting the environment variable `PREFER_IPV6_NETWORK` to `true` on the proxy container: with this setting the proxy will only use IPv6 for containers that can be reached over both IPv4 and IPv6.

IPv4 and IPv6 are never both used at the same time on containers that use both IP stacks to avoid artificially inflating the effective round robin weight of those containers.

### Listening on IPv6

By default the nginx-proxy container will only listen on IPv4. To enable listening on IPv6 too, set the `ENABLE_IPV6` environment variable to `true`:

```console
docker run --detach \
    --publish 80:80 \
    --env ENABLE_IPV6=true \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

### Scoped IPv6 Resolvers

Nginx does not support scoped IPv6 resolvers. In [docker-entrypoint.sh](https://github.com/nginx-proxy/nginx-proxy/blob/main/app/docker-entrypoint.sh) the resolvers are parsed from resolv.conf, but any scoped IPv6 addreses will be removed.

### IPv6 NAT

By default, docker uses IPv6-to-IPv4 NAT. This means all client connections from IPv6 addresses will show docker's internal IPv4 host address. To see true IPv6 client IP addresses, you must [enable IPv6](https://docs.docker.com/config/daemon/ipv6/) and use [ipv6nat](https://github.com/robbertkl/docker-ipv6nat). You must also disable the userland proxy by adding `"userland-proxy": false` to `/etc/docker/daemon.json` and restarting the daemon.

⬆️ [back to table of contents](#table-of-contents)

## HTTP/2 and HTTP/3

### HTTP/2 support

HTTP/2 is enabled by default and can be disabled if necessary either per-proxied container or globally:

To disable HTTP/2 for a single proxied container, set the `com.github.nginx-proxy.nginx-proxy.http2.enable` label to `false` on this container.

To disable HTTP/2 globally set the environment variable `ENABLE_HTTP2` to `false` on the nginx-proxy container.

More reading on the potential TCP head-of-line blocking issue with HTTP/2: [HTTP/2 Issues](https://www.twilio.com/blog/2017/10/http2-issues.html), [Comparing HTTP/3 vs HTTP/2](https://blog.cloudflare.com/http-3-vs-http-2/)

### HTTP/3 support

> [!WARNING]
> HTTP/3 support [is still considered experimental in nginx](https://www.nginx.com/blog/binary-packages-for-preview-nginx-quic-http3-implementation/) and as such is considered experimental in nginx-proxy too and is disabled by default. [Feedbacks for the HTTP/3 support are welcome in #2271.](https://github.com/nginx-proxy/nginx-proxy/discussions/2271)

HTTP/3 use the QUIC protocol over UDP (unlike HTTP/1.1 and HTTP/2 which work over TCP), so if you want to use HTTP/3 you'll have to explicitely publish the 443/udp port of the proxy in addition to the 443/tcp port:

```console
docker run --detach \
    --publish 80:80 \
    --publish 443:443/tcp \
    --publish 443:443/udp \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

HTTP/3 can be enabled either per-proxied container or globally:

To enable HTTP/3 for a single proxied container, set the `com.github.nginx-proxy.nginx-proxy.http3.enable` label to `true` on this container.

To enable HTTP/3 globally set the environment variable `ENABLE_HTTP3` to `true` on the nginx-proxy container.

⬆️ [back to table of contents](#table-of-contents)

## Headers

By default, `nginx-proxy` forwards all incoming request headers from the client to the backend server unmodified, with the following exceptions:

- `Connection`: Set to `upgrade` if the client sets the `Upgrade` header, otherwise set to `close`. (Keep-alive between `nginx-proxy` and the backend server is not supported.)
- `Proxy`: Always removed if present. This prevents attackers from using the so-called [httpoxy attack](http://httpoxy.org). There is no legitimate reason for a client to send this header, and there are many vulnerable languages / platforms (`CVE-2016-5385`, `CVE-2016-5386`, `CVE-2016-5387`, `CVE-2016-5388`, `CVE-2016-1000109`, `CVE-2016-1000110`, `CERT-VU#797896`).
- `X-Real-IP`: Set to the client's IP address.
- `X-Forwarded-For`: The client's IP address is appended to the value provided by the client. (If the client did not provide this header, it is set to the client's IP address.)
- `X-Forwarded-Host`: If the client did not provide this header or if the `TRUST_DOWNSTREAM_PROXY` environment variable is set to `false` (see below), this is set to the value of the `Host` header provided by the client. Otherwise, the header is forwarded to the backend server unmodified.
- `X-Forwarded-Proto`: If the client did not provide this header or if the `TRUST_DOWNSTREAM_PROXY` environment variable is set to `false` (see below), this is set to `http` for plain HTTP connections and `https` for TLS connections. Otherwise, the header is forwarded to the backend server unmodified.
- `X-Forwarded-Ssl`: Set to `on` if the `X-Forwarded-Proto` header sent to the backend server is `https`, otherwise set to `off`.
- `X-Forwarded-Port`: If the client did not provide this header or if the `TRUST_DOWNSTREAM_PROXY` environment variable is set to `false` (see below), this is set to the port of the server that accepted the client's request. Otherwise, the header is forwarded to the backend server unmodified.
- `X-Original-URI`: Set to the original request URI.

### Trusting Downstream Proxy Headers

For legacy compatibility reasons, `nginx-proxy` forwards any client-supplied `X-Forwarded-Proto` (which affects the value of `X-Forwarded-Ssl`), `X-Forwarded-Host`, and `X-Forwarded-Port` headers unchecked and unmodified. To prevent malicious clients from spoofing the protocol, hostname, or port that is perceived by your backend server, you are encouraged to set the `TRUST_DOWNSTREAM_PROXY` value to `false` if:

- you do not operate a second reverse proxy downstream of `nginx-proxy`, or
- you do operate a second reverse proxy downstream of `nginx-proxy` but that proxy forwards those headers unchecked from untrusted clients.

The default for `TRUST_DOWNSTREAM_PROXY` may change to `false` in a future version of `nginx-proxy`. If you require it to be enabled, you are encouraged to explicitly set it to `true` to avoid compatibility problems when upgrading.

### Proxy Protocol Support

`nginx-proxy` has support for the [Proxy Protocol](https://www.haproxy.org/download/1.8/doc/proxy-protocol.txt). This allows a separate proxy to send requests to `nginx-proxy` and encode information about the client connection without relying on HTTP headers. This can be enabled by setting `ENABLE_PROXY_PROTOCOL=true` on the main `nginx-proxy` container. It's important to note that enabling the proxy protocol will require all connections to `nginx-proxy` to use the protocol.

You can use this feature in conjunction with the `realip` module in nginx. This will allow for setting the `$remote_addr` and `$remote_port` nginx variables to the IP and port that are provided from the protocol message. Documentation for this functionality can be found in the [nginx documentation](https://nginx.org/en/docs/http/ngx_http_realip_module.html).

A simple example is as follows:

1. Create a configuration file for nginx, this can be global (in `conf.d`) or host specific (in `vhost.d`)
2. Add your `realip` configuration:

```nginx
# Your proxy server ip address
set_real_ip_from  192.168.1.0/24;

# Where to replace `$remote_addr` and `$remote_port` from
real_ip_header proxy_protocol;
```

⬆️ [back to table of contents](#table-of-contents)

## Custom Nginx Configuration

If you need to configure Nginx beyond what is possible using environment variables, you can provide custom configuration files on either a proxy-wide or per-`VIRTUAL_HOST` basis.

### Replacing default proxy settings

If you want to replace the default proxy settings for the nginx container, add a configuration file at `/etc/nginx/proxy.conf`. A file with the default settings would look like this:

```nginx
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

> [!IMPORTANT]
> If you provide this file it will replace the defaults; you may want to check the [nginx.tmpl](https://github.com/nginx-proxy/nginx-proxy/blob/main/nginx.tmpl) file to make sure you have all of the needed options.

### Proxy-wide

To add settings on a proxy-wide basis, add your configuration file under `/etc/nginx/conf.d` using a name ending in `.conf`.

This can be done in a derived image by creating the file in a `RUN` command or by `COPY`ing the file into `conf.d`:

```Dockerfile
FROM nginxproxy/nginx-proxy
RUN { \
      echo 'server_tokens off;'; \
      echo 'client_max_body_size 100m;'; \
    } > /etc/nginx/conf.d/my_proxy.conf
```

Or it can be done by mounting in your custom configuration in your `docker run` command or your Docker Compose file:

```nginx
# content of the my_proxy.conf file
server_tokens off;
client_max_body_size 100m;
```

<details>
  <summary>Docker CLI</summary>

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --publish 443:443 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume /path/to/my_proxy.conf:/etc/nginx/conf.d/my_proxy.conf:ro \
    nginxproxy/nginx-proxy
```

</details>

<details>
  <summary>Docker Compose file</summary>

```yaml
services:
  proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - /path/to/my_proxy.conf:/etc/nginx/conf.d/my_proxy.conf:ro
```

</details>

> [!NOTE]
> The filenames of extra configuration files affect the order in which configuration is applied.
> nginx reads configuration from `/etc/nginx/conf.d` directory in alphabetical order.
> Note that the configuration managed by nginx-proxy is placed at `/etc/nginx/conf.d/default.conf`.

### Per-VIRTUAL_HOST

To add settings on a per-`VIRTUAL_HOST` basis, add your configuration file under `/etc/nginx/vhost.d`. Unlike in the proxy-wide case, which allows multiple config files with any name ending in `.conf`, the per-`VIRTUAL_HOST` file must be named exactly after the `VIRTUAL_HOST`, or if `VIRTUAL_HOST` is a regex, after the sha1 hash of the regex.

In order to allow virtual hosts to be dynamically configured as backends are added and removed, it makes the most sense to mount an external directory as `/etc/nginx/vhost.d` as opposed to using derived images or mounting individual configuration files.

For example, if you have a virtual host named `app.example.com`, you could provide a custom configuration for that host as follows:

1. create your virtual host config file:

```nginx
# content of the custom-vhost-config.conf file
client_max_body_size 100m;
```

2. mount it to `/etc/nginx/vhost.d/app.example.com`:
<details>
  <summary>Docker CLI</summary>

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --publish 443:443 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume /path/to/custom-vhost-config.conf:/etc/nginx/vhost.d/app.example.com:ro \
    nginxproxy/nginx-proxy
```

</details>

<details>
  <summary>Docker Compose file</summary>

```yaml
services:
  proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - /path/to/custom-vhost-config.conf:/etc/nginx/vhost.d/app.example.com:ro
```

</details>

If you are using multiple hostnames for a single container (e.g. `VIRTUAL_HOST=example.com,www.example.com`), the virtual host configuration file must exist for each hostname:

<details>
  <summary>Docker CLI</summary>

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --publish 443:443 \
    --volume /path/to/custom-vhost-config.conf:/etc/nginx/vhost.d/example.com:ro \
    --volume /path/to/custom-vhost-config.conf:/etc/nginx/vhost.d/www.example.com:ro \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy
```

</details>

<details>
  <summary>Docker Compose file</summary>

```yaml
services:
  proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - /path/to/custom-vhost-config.conf:/etc/nginx/vhost.d/example.com:ro
      - /path/to/custom-vhost-config.conf:/etc/nginx/vhost.d/www.example.com:ro
```

</details>

### Per-VIRTUAL_HOST default configuration

If you want most of your virtual hosts to use a default single configuration and then override on a few specific ones, add those settings to the `/etc/nginx/vhost.d/default` file. This file will be used on any virtual host which does not have a [per-VIRTUAL_HOST file](#per-virtual_host) associated with it.

### Per-VIRTUAL_HOST location configuration

To add settings to the "location" block on a per-`VIRTUAL_HOST` basis, add your configuration file under `/etc/nginx/vhost.d` just like the per-`VIRTUAL_HOST` section except with the suffix `_location` (like this section, if your `VIRTUAl_HOST` is a regex, use the sha1 hash of the regex instead, with the suffix `_location` appended).

For example, if you have a virtual host named `app.example.com` and you have configured a proxy_cache `my-cache` in another custom file, you could tell it to use a proxy cache as follows:

1. create your virtual host location config file:

```nginx
# content of the custom-vhost-location-config.conf file
proxy_cache my-cache;
proxy_cache_valid 200 302 60m;
proxy_cache_valid 404 1m;
```

2. mount it to `/etc/nginx/vhost.d/app.example.com_location`:

<details>
  <summary>Docker CLI</summary>

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --publish 443:443 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume /path/to/custom-vhost-location-config.conf:/etc/nginx/vhost.d/app.example.com_location:ro \
    nginxproxy/nginx-proxy
```

</details>

<details>
  <summary>Docker Compose file</summary>

```yaml
services:
  proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - /path/to/custom-vhost-location-config.conf:/etc/nginx/vhost.d/app.example.com_location:ro
```

</details>

If you are using multiple hostnames for a single container (e.g. `VIRTUAL_HOST=example.com,www.example.com`), the virtual host configuration file must exist for each hostname:

<details>
  <summary>Docker CLI</summary>

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --publish 443:443 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume /path/to/custom-vhost-location-config.conf:/etc/nginx/vhost.d/example.com_location:ro \
    --volume /path/to/custom-vhost-location-config.conf:/etc/nginx/vhost.d/www.example.com_location:ro \
    nginxproxy/nginx-proxy
```

</details>

<details>
  <summary>Docker Compose file</summary>

```yaml
services:
  proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - /path/to/custom-vhost-location-config.conf:/etc/nginx/vhost.d/example.com_location:ro
      - /path/to/custom-vhost-location-config.conf:/etc/nginx/vhost.d/www.example.com_location:ro
```

</details>

### Per-VIRTUAL_HOST location default configuration

If you want most of your virtual hosts to use a default single `location` block configuration and then override on a few specific ones, add those settings to the `/etc/nginx/vhost.d/default_location` file. This file will be used on any virtual host which does not have a [Per-VIRTUAL_HOST location file](#per-virtual_host-location-configuration) associated with it.

### Overriding `location` blocks

The `${VIRTUAL_HOST}_${PATH_HASH}_location`, `${VIRTUAL_HOST}_location`, and `default_location` files documented above make it possible to _augment_ the generated [`location` block(s)](https://nginx.org/en/docs/http/ngx_http_core_module.html#location) in a virtual host. In some circumstances, you may need to _completely override_ the `location` block for a particular combination of virtual host and path. To do this, create a file whose name follows this pattern:

```
/etc/nginx/vhost.d/${VIRTUAL_HOST}_${PATH_HASH}_location_override
```

where `${VIRTUAL_HOST}` is the name of the virtual host (the `VIRTUAL_HOST` environment variable), or the sha1 hash of `VIRTUAL_HOST` when it's a regex, and `${PATH_HASH}` is the SHA-1 hash of the path, as [described above](#per-virtual_path-location-configuration).

For convenience, the `_${PATH_HASH}` part can be omitted if the path is `/`:

```
/etc/nginx/vhost.d/${VIRTUAL_HOST}_location_override
```

When an override file exists, the `location` block that is normally created by `nginx-proxy` is not generated. Instead, the override file is included via the [nginx `include` directive](https://nginx.org/en/docs/ngx_core_module.html#include).

You are responsible for providing a suitable `location` block in your override file as required for your service. By default, `nginx-proxy` uses the `VIRTUAL_HOST` name as the upstream name for your application's Docker container; see [here](#unhashed-vs-sha1-upstream-names) for details. As an example, if your container has a `VIRTUAL_HOST` value of `app.example.com`, then to override the location block for `/` you would create a file named `/etc/nginx/vhost.d/app.example.com_location_override` that contains something like this:

```nginx
location / {
    proxy_pass http://app.example.com;
}
```

### Per-VIRTUAL_HOST `server_tokens` configuration

Per virtual-host `servers_tokens` directive can be configured by passing appropriate value to the `SERVER_TOKENS` environment variable. Please see the [nginx http_core module configuration](https://nginx.org/en/docs/http/ngx_http_core_module.html#server_tokens) for more details.

### Custom error page

To override the default error page displayed on 50x errors, mount your custom HTML error page inside the container at `/usr/share/nginx/html/errors/50x.html`:

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume /path/to/error.html:/usr/share/nginx/html/errors/50x.html:ro \
    nginxproxy/nginx-proxy
```

> [!NOTE]
> This will not replace your own services error pages.

⬆️ [back to table of contents](#table-of-contents)

## TCP and UDP stream

If you want to proxy non-HTTP traffic, you can use nginx's stream module. Write a configuration file and mount it inside `/etc/nginx/toplevel.conf.d`.

```nginx
# stream.conf
stream {
    upstream stream_backend {
        server backend1.example.com:12345;
        server backend2.example.com:12345;
        server backend3.example.com:12346;
        # ...
    }
    server {
        listen     12345;
        #TCP traffic will be forwarded to the "stream_backend" upstream group
        proxy_pass stream_backend;
    }

    server {
        listen     12346;
        #TCP traffic will be forwarded to the specified server
        proxy_pass backend.example.com:12346;
    }

    upstream dns_servers {
        server 192.168.136.130:53;
        server 192.168.136.131:53;
        # ...
    }
    server {
        listen     53 udp;
        #UDP traffic will be forwarded to the "dns_servers" upstream group
        proxy_pass dns_servers;
    }
    # ...
}
```

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --publish 12345:12345 \
    --publish 12346:12346 \
    --publish 53:53:udp \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume ./stream.conf:/etc/nginx/toplevel.conf.d/stream.conf:ro \
    nginxproxy/nginx-proxy
```

> [!NOTE]
> TCP and UDP stream are not core features of nginx-proxy, so the above is provided as an example only, without any guarantee.

⬆️ [back to table of contents](#table-of-contents)

## Unhashed vs SHA1 upstream names

By default the nginx configuration `upstream` blocks will use this block's corresponding hostname as a predictable name. However, this can cause issues in some setups (see [this issue](https://github.com/nginx-proxy/nginx-proxy/issues/1162)). In those cases you might want to switch to SHA1 names for the `upstream` blocks by setting the `SHA1_UPSTREAM_NAME` environment variable to `true` on the nginx-proxy container.

> [!NOTE]
> Using regular expressions in `VIRTUAL_HOST` will always result in a corresponding `upstream` block with an SHA1 name.

⬆️ [back to table of contents](#table-of-contents)

## Separate Containers

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

First start nginx with a volume mounted to `/etc/nginx/conf.d`:

```console
docker run --detach \
    --name nginx \
    --publish 80:80 \
    --volume /tmp/nginx:/etc/nginx/conf.d \
    nginx
```

Then start the docker-gen container with the shared volume and template:

```console
docker run --detach \
    --name docker-gen \
    --volumes-from nginx \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume $(pwd):/etc/docker-gen/templates \
    nginxproxy/docker-gen -notify-sighup nginx -watch /etc/docker-gen/templates/nginx.tmpl /etc/nginx/conf.d/default.conf
```

Finally, start your containers with `VIRTUAL_HOST` environment variables.

```console
docker run --env VIRTUAL_HOST=foo.bar.com  ...
```

### Network segregation

To allow for network segregation of the nginx and docker-gen containers, the label `com.github.nginx-proxy.nginx-proxy.nginx` must be applied to the nginx container, otherwise it is assumed that nginx and docker-gen share the same network:

```console
docker run --detach \
    --name nginx \
    --publish 80:80 \
    --label "com.github.nginx-proxy.nginx-proxy.nginx" \
    --volume /tmp/nginx:/etc/nginx/conf.d \
    nginx
```

Network segregation make it possible to run the docker-gen container in an [internal network](https://docs.docker.com/reference/cli/docker/network/create/#internal), unreachable from the outside.

You can also customise the label being used by docker-gen to find the nginx container with the `NGINX_CONTAINER_LABEL`environment variable (on the docker-gen container):

```console
docker run --detach \
    --name docker-gen \
    --volumes-from nginx \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    --volume $(pwd):/etc/docker-gen/templates \
    --env "NGINX_CONTAINER_LABEL=com.github.foobarbuzz" \
    nginxproxy/docker-gen -notify-sighup nginx -watch /etc/docker-gen/templates/nginx.tmpl /etc/nginx/conf.d/default.conf

docker run --detach \
    --name nginx \
    --publish 80:80 \
    --label "com.github.foobarbuzz" \
    --volume "/tmp/nginx:/etc/nginx/conf.d" \
    nginx
```

⬆️ [back to table of contents](#table-of-contents)

## Docker Compose

```yaml
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

⬆️ [back to table of contents](#table-of-contents)

## Configuration summary

This section summarize the configurations available on the proxy and proxied container.

### Proxy container

Configuration available either on the nginx-proxy container, or the docker-gen container in a [separate containers setup](#separate-containers):

| Environment Variable | Default Value |
|---------------------|---------------|
| [`ACME_HTTP_CHALLENGE_LOCATION`](#ssl-support-using-an-acme-ca) | `true` |
| [`ACME_HTTP_CHALLENGE_ACCEPT_UNKNOWN_HOST`](#ssl-support-using-an-acme-ca) | `false` |
| [`DEBUG_ENDPOINT`](#debug-endpoint) | `false` |
| [`DEFAULT_HOST`](#default-host) | no default value |
| [`DEFAULT_ROOT`](#default_root) | `404` |
| [`DHPARAM_SKIP`](#diffie-hellman-groups) | `false` |
| [`DHPARAM_BITS`](#diffie-hellman-groups) | `4096` |
| [`DISABLE_ACCESS_LOGS`](#disable-access-logs) | `false` |
| [`ENABLE_HTTP_ON_MISSING_CERT`](#default-and-missing-certificate) | `true` |
| [`ENABLE_HTTP2`](#http2-support) | `true` |
| [`ENABLE_HTTP3`](#http3-support) | `false` |
| [`ENABLE_IPV6`](#listening-on-ipv6) | `false` |
| [`ENABLE_PROXY_PROTOCOL`](#proxy-protocol-support) | `false` |
| [`HTTP_PORT`](#custom-external-httphttps-ports) | `80` |
| [`HTTPS_PORT`](#custom-external-httphttps-ports) | `443` |
| [`HTTPS_METHOD`](#how-ssl-support-works) | `redirect` |
| [`HSTS`](#how-ssl-support-works) | `max-age=31536000` |
| [`LOG_FORMAT`](#custom-log-format) | no default value |
| [`LOG_FORMAT_ESCAPE`](#log-format-escaping) | no default value |
| [`LOG_JSON`](#json-log-format) | `false` |
| [`NGINX_CONTAINER_LABEL`](#network-segregation) | `com.github.nginx-proxy.nginx-proxy.nginx` |
| [`NON_GET_REDIRECT`](#how-ssl-support-works) | `301` |
| [`PREFER_IPV6_NETWORK`](#ipv6-docker-networks) | `false` |
| `RESOLVERS` | no default value |
| [`SHA1_UPSTREAM_NAME`](#unhashed-vs-sha1-upstream-names) | `false` |
| [`SSL_POLICY`](#how-ssl-support-works) | `Mozilla-Intermediate` |
| [`TRUST_DEFAULT_CERT`](#default-and-missing-certificate) | `true` |
| [`TRUST_DOWNSTREAM_PROXY`](#trusting-downstream-proxy-headers) | `true` |

### Proxyied container

Configuration available on each proxied container, either by environment variable or by label:

| Environment Variable | Label | Default Value |
|---------------------|---------------|---------------|
| [`ACME_HTTP_CHALLENGE_LOCATION`](#ssl-support-using-an-acme-ca) | n/a | global (proxy) value |
| [`CERT_NAME`](#san-certificates) | n/a | no default value |
| n/a | [`com.github.nginx-proxy.nginx-proxy.debug-endpoint`](#debug-endpoint) | global (proxy) value |
| [`ENABLE_HTTP_ON_MISSING_CERT`](#default-and-missing-certificate) | n/a | global (proxy) value |
| [`HSTS`](#how-ssl-support-works) | n/a | global (proxy) value |
| n/a | [`com.github.nginx-proxy.nginx-proxy.http2.enable`](#http2-support) | global (proxy) value |
| n/a | [`com.github.nginx-proxy.nginx-proxy.http3.enable`](#http3-support) | global (proxy) value |
| [`HTTPS_METHOD`](#how-ssl-support-works) | n/a | global (proxy) value |
| n/a | [`com.github.nginx-proxy.nginx-proxy.keepalive`](#upstream-server-http-keep-alive-support) | `auto` |
| n/a | [`com.github.nginx-proxy.nginx-proxy.loadbalance`](#upstream-server-http-load-balancing-support) | no default value |
| n/a | [`com.github.nginx-proxy.nginx-proxy.non-get-redirect`](#how-ssl-support-works) | global (proxy) value |
| [`SERVER_TOKENS`](#per-virtual_host-server_tokens-configuration) | n/a | no default value |
| [`SSL_POLICY`](#how-ssl-support-works) | n/a | global (proxy) value |
| n/a | [`com.github.nginx-proxy.nginx-proxy.ssl_verify_client`](#optional-ssl_verify_client) | `on` |
| n/a | [`com.github.nginx-proxy.nginx-proxy.trust-default-cert`](#default-and-missing-certificate) | global (proxy) value |
| [`VIRTUAL_DEST`](#virtual_dest) | n/a | `empty string` |
| [`VIRTUAL_HOST`](#virtual-hosts-and-ports) | n/a | no default value |
| [`VIRTUAL_HOST_MULTIPORTS`](#multiple-ports) | n/a | no default value |
| [`VIRTUAL_PATH`](#path-based-routing) | n/a | `/` |
| [`VIRTUAL_PORT`](#virtual-ports) | n/a | no default value |
| [`VIRTUAL_PROTO`](#upstream-backend-features) | n/a | `http` |
| [`VIRTUAL_ROOT`](#fastcgi-file-root-directory) | n/a | `/var/www/public` |

### Configuration by files

Additional configuration and/or features available by mounting files to the nginx-proxy container (or to both the nginx and docker-gen containers in a [separate containers setup](#separate-containers)).

In the following tables, `<VIRTUAL_HOST>` is the value of the `VIRTUAL_HOST` environment variable, or the SHA-1 hash of the regex if `VIRTUAL_HOST` is a regex. `<PATH_HASH>` is the SHA-1 hash of the path, as described in [Per-Virtual Path Location Configuration](#per-virtual_path-location-configuration).

#### Proxy-wide

| File Path | Description |
|-----------|-------------|
| [`/etc/nginx/conf.d/proxy.conf`](#replacing-default-proxy-settings) | Proxy-wide configuration, replacing the default proxy settings. |
| [`/etc/nginx/conf.d/<custom_name>.conf`](#proxy-wide) | Proxy-wide configuration, augmenting the default proxy settings. |
| [`/etc/nginx/toplevel.conf.d/<custom_name>.conf`](#tcp-and-udp-stream) | Custom Nginx configuration, augmenting the default Nginx settings. |
| [`/usr/share/nginx/html/errors/50x.html`](#custom-error-page) | Custom error page for 50x errors, replacing the default error page. |

#### Per-VIRTUAL_HOST configuration

| File Path | Description |
|-----------|-------------|
| [`/etc/nginx/vhost.d/<VIRTUAL_HOST>`](#per-virtual_host) | Per-`VIRTUAL_HOST` additional configuration. |
| [`/etc/nginx/vhost.d/default`](#per-virtual_host-default-configuration) | Per-`VIRTUAL_HOST` default additional configuration. |
| [`/etc/nginx/vhost.d/<VIRTUAL_HOST>_location`](#per-virtual_host-location-configuration) | Per-`VIRTUAL_HOST` additional location configuration. |
| [`/etc/nginx/vhost.d/<VIRTUAL_HOST>_<PATH_HASH>_location`](#per-virtual_path-location-configuration) | Per-`VIRTUAL_PATH` additional location configuration. |
| [`/etc/nginx/vhost.d/default_location`](#per-virtual_host-location-default-configuration) | Per-`VIRTUAL_HOST` default additional location configuration. |
| [`/etc/nginx/vhost.d/<VIRTUAL_HOST>_location_override`](#overriding-location-blocks) | Per-`VIRTUAL_HOST` location configuration override. |
| [`/etc/nginx/vhost.d/<VIRTUAL_HOST>_<PATH_HASH>_location_override`](#overriding-location-blocks) | Per-`VIRTUAL_PATH` location configuration override. |

#### Authentication

| File Path | Description |
|-----------|-------------|
| [`/etc/nginx/htpasswd/<VIRTUAL_HOST>`](#basic-authentication-support) | Basic authentication for a specific `VIRTUAL_HOST`. |
| [`/etc/nginx/htpasswd/<VIRTUAL_HOST>_<PATH_HASH>`](#basic-authentication-support) | Basic authentication for a specific path within a `VIRTUAL_HOST`. |
| [`/etc/nginx/certs/<VIRTUAL_HOST>.ca.crt`](#per-virtual_host-ca) | Per-`VIRTUAL_HOST` Certificate Authority (CA) certificate for mTLS client authentication. |
| [`/etc/nginx/certs/<VIRTUAL_HOST>.crl.pem`](#per-virtual_host-crl) | Per-`VIRTUAL_HOST` Certificate Revocation List (CRL) for mTLS client authentication. |
| [`/etc/nginx/certs/ca.crt`](#global-ca) | Global Certificate Authority (CA) certificate for mTLS client authentication. |
| [`/etc/nginx/certs/ca.crl.pem`](#global-crl) | Global Certificate Revocation List (CRL) for mTLS client authentication. |

#### SSL/TLS

| File Path | Description |
|-----------|-------------|
| [`/etc/nginx/certs/<VIRTUAL_HOST>.crt`](#ssl-support) | Per-`VIRTUAL_HOST` SSL/TLS certificate. |
| [`/etc/nginx/certs/<VIRTUAL_HOST>.key`](#ssl-support) | Per-`VIRTUAL_HOST` SSL/TLS private key. |
| [`/etc/nginx/certs/<VIRTUAL_HOST>.dhparam.pem`](#diffie-hellman-groups) | Per-`VIRTUAL_HOST` Diffie-Hellman parameters. |
| [`/etc/nginx/certs/dhparam.pem`](#diffie-hellman-groups) | Global Diffie-Hellman parameters. |

⬆️ [back to table of contents](#table-of-contents)

## Troubleshooting

If you can't access your `VIRTUAL_HOST`, inspect the generated nginx configuration:

```console
docker exec <nginx-proxy-instance> nginx -T
```

Pay attention to the `upstream` definition blocks, which should look like this:

```nginx
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

### Debug endpoint

The debug endpoint can be enabled:

- globally by setting the `DEBUG_ENDPOINT` environment variable to `true` on the nginx-proxy container.
- per container by setting the `com.github.nginx-proxy.nginx-proxy.debug-endpoint` label to `true` on a proxied container.

Enabling it will expose the endpoint at `<your.domain.tld>/nginx-proxy-debug`.

Querying the debug endpoint will show the global config, along with the virtual host and per path configs in JSON format.

```yaml
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
    environment:
      DEBUG_ENDPOINT: "true"

  test:
    image: nginx
    environment:
      VIRTUAL_HOST: test.nginx-proxy.tld
```

(on the CLI, using [`jq`](https://jqlang.github.io/jq/) to format the output of `curl` is recommended)

```console
curl -s -H "Host: test.nginx-proxy.tld" localhost/nginx-proxy-debug | jq
```

```json
{
  "global": {
    "acme_http_challenge": "true",
    "default_cert_ok": false,
    "default_host": null,
    "default_root_response": "404",
    "enable_access_log": true,
    "enable_debug_endpoint": "true",
    "enable_http2": "true",
    "enable_http3": "false",
    "enable_proxy_protocol": "false",
    "enable_http_on_missing_cert": "true",
    "enable_ipv6": false,
    "enable_json_logs": false,
    "external_http_port": "80",
    "external_https_port": "443",
    "hsts": "max-age=31536000",
    "https_method": "redirect",
    "log_format": null,
    "log_format_escape": null,
    "nginx_proxy_version": "1.8.0",
    "resolvers": "127.0.0.11",
    "sha1_upstream_name": false,
    "ssl_policy": "Mozilla-Intermediate",
    "trust_downstream_proxy": true
  },
  "request": {
    "host": "test.nginx-proxy.tld",
    "http2": "",
    "http3": "",
    "https": "",
    "ssl_cipher": "",
    "ssl_protocol": ""
  },
  "vhost": {
    "acme_http_challenge_enabled": true,
    "acme_http_challenge_legacy": false,
    "cert": "",
    "cert_ok": false,
    "default": false,
    "enable_debug_endpoint": true,
    "hostname": "test.nginx-proxy.tld",
    "hsts": "max-age=31536000",
    "http2_enabled": true,
    "http3_enabled": false,
    "https_method": "noredirect",
    "is_regexp": false,
    "paths": {
      "/": {
        "dest": "",
        "keepalive": "disabled",
        "network_tag": "external",
        "ports": {
          "legacy": [
            {
              "Name": "wip-test-1"
            }
          ]
        },
        "proto": "http",
        "upstream": "test.nginx-proxy.tld"
      }
    },
    "server_tokens": "",
    "ssl_policy": "",
    "upstream_name": "test.nginx-proxy.tld",
    "vhost_root": "/var/www/public"
  }
}
```

> [!WARNING]
> Please be aware that the debug endpoint work by rendering the JSON response straight to the nginx configuration in plaintext. nginx has an upper limit on the size of the configuration files it can parse, so only activate it when needed, and preferably on a per container basis if your setup has a large number of virtual hosts.

⬆️ [back to table of contents](#table-of-contents)

## Contributing

Before submitting pull requests or issues, please check github to make sure an existing issue or pull request is not already open.

### Running Tests Locally

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

⬆️ [back to table of contents](#table-of-contents)
