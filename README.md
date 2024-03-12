[![Test](https://github.com/nginx-proxy/nginx-proxy/actions/workflows/test.yml/badge.svg)](https://github.com/nginx-proxy/nginx-proxy/actions/workflows/test.yml)
[![GitHub release](https://img.shields.io/github/v/release/nginx-proxy/nginx-proxy)](https://github.com/nginx-proxy/nginx-proxy/releases)
![nginx 1.25.4](https://img.shields.io/badge/nginx-1.25.4-brightgreen.svg)
[![Docker Image Size](https://img.shields.io/docker/image-size/nginxproxy/nginx-proxy?sort=semver)](https://hub.docker.com/r/nginxproxy/nginx-proxy "Click to view the image on Docker Hub")
[![Docker stars](https://img.shields.io/docker/stars/nginxproxy/nginx-proxy.svg)](https://hub.docker.com/r/nginxproxy/nginx-proxy "DockerHub")
[![Docker pulls](https://img.shields.io/docker/pulls/nginxproxy/nginx-proxy.svg)](https://hub.docker.com/r/nginxproxy/nginx-proxy "DockerHub")

nginx-proxy sets up a container running nginx and [docker-gen](https://github.com/nginx-proxy/docker-gen). docker-gen generates reverse proxy configs for nginx and reloads nginx when containers are started and stopped.

See [Automated Nginx Reverse Proxy for Docker](http://jasonwilder.com/blog/2014/03/25/automated-nginx-reverse-proxy-for-docker/) for why you might want to use this.

### Usage

To run it:

```console
docker run --detach \
    --name nginx-proxy \
    --publish 80:80 \
    --volume /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy:1.5
```

Then start any containers (here an nginx container) you want proxied with an env var `VIRTUAL_HOST=subdomain.yourdomain.com`

```console
docker run --detach \
    --name your-proxied-app \
    --env VIRTUAL_HOST=foo.bar.com \
    nginx
```

Provided your DNS is setup to resolve `foo.bar.com` to the host running nginx-proxy, a request to `http://foo.bar.com` will then be routed to a container with the `VIRTUAL_HOST` env var set to `foo.bar.com` (in this case, the **your-proxied-app** container).

The containers being proxied must :

- [expose](https://docs.docker.com/engine/reference/run/#expose-incoming-ports) the port to be proxied, either by using the `EXPOSE` directive in their `Dockerfile` or by using the `--expose` flag to `docker run` or `docker create`.
- share at least one Docker network with the nginx-proxy container: by default, if you don't pass the `--net` flag when your nginx-proxy container is created, it will only be attached to the default bridge network. This means that it will not be able to connect to containers on networks other than bridge.

Note: providing a port number in `VIRTUAL_HOST` isn't suported, please see [virtual ports](https://github.com/nginx-proxy/nginx-proxy/tree/main/docs#virtual-ports) or [custom external HTTP/HTTPS ports](https://github.com/nginx-proxy/nginx-proxy/tree/main/docs#custom-external-httphttps-ports) depending on what you want to achieve.

### Image variants

The nginx-proxy images are available in two flavors.

#### Debian based version

This image is based on the nginx:mainline image, itself based on the debian slim image.

```console
docker pull nginxproxy/nginx-proxy:1.5
```

#### Alpine based version (`-alpine` suffix)

This image is based on the nginx:alpine image.

```console
docker pull nginxproxy/nginx-proxy:1.5-alpine
```

#### :warning: a note on `latest` and `alpine`:

It is not recommended to use the `latest` (`nginxproxy/nginx-proxy`, `nginxproxy/nginx-proxy:latest`) or `alpine` (`nginxproxy/nginx-proxy:alpine`) tag for production setups.

[Those tags point](https://hub.docker.com/r/nginxproxy/nginx-proxy/tags) to the latest commit in the `main` branch. They do not carry any promise of stability, and using them will probably put your nginx-proxy setup at risk of experiencing uncontrolled updates to non backward compatible versions (or versions with breaking changes). You should always specify the version you want to use explicitly to ensure your setup doesn't break when the image is updated.

### Additional documentation

Please check the [docs section](https://github.com/nginx-proxy/nginx-proxy/tree/main/docs).
