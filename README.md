nginx-proxy sets up a container running nginx and [docker-gen][1].  docker-gen generate reverse proxy configs for nginx and reloads nginx when containers they are started and stopped.

See [Automated Nginx Reverse Proxy for Docker][2] for why you might want to use this.

### Usage

To run it:

    $ docker run -d -p 80:80 -v /var/run/docker.sock:/tmp/docker.sock jwilder/nginx-proxy

Then start any containers you want proxied with an env var `VIRTUAL_HOST=subdomain.youdomain.com`

    $ docker run -e VIRTUAL_HOST=foo.bar.com  ...

Provided your DNS is setup to forward foo.bar.com to the a host running nginx-proxy, the request will be routed to a container with the VIRTUAL_HOST env var set.

### Multiple Ports

If your container exposes multiple ports, nginx-proxy will default to the service running on port 80.  If you need to specify a different port, you can set a VIRTUAL_PORT env var to select a different one.  If your container only exposes one port and it has a VIRTUAL_HOST env var set, that port will be selected.

  [1]: https://github.com/jwilder/docker-gen
  [2]: http://jasonwilder.com/blog/2014/03/25/automated-nginx-reverse-proxy-for-docker/

### Multiple Hosts

If you need to support multipe virtual hosts for a container, you can separate each entry with commas.  For example, `foo.bar.com,baz.bar.com,bar.com` and each host will be setup the same.

### Separate Containers

nginx-proxy can also be run as two separate containers using the [jwilder/docker-gen](https://index.docker.io/u/jwilder/docker-gen/)
image and the official [nginx](https://registry.hub.docker.com/_/nginx/) image.

You may want to do this to prevent having the docker socket bound to a publicly exposed container service.

To run nginx proxy as a separate container you'll need to have [nginx.tmpl](https://github.com/jwilder/nginx-proxy/blob/master/nginx.tmpl) on your host system.

First start nginx with a volume:


    $ docker run -d -p 80:80 --name nginx -v /tmp/nginx:/etc/nginx/conf.d -t nginx

Then start the docker-gen container with the shared volume and template:

```
$ docker run --volumes-from nginx \
    -v /var/run/docker.sock:/tmp/docker.sock \
    -v $(pwd):/etc/docker-gen/templates \
    -t docker-gen -notify-sighup nginx -watch --only-published /etc/docker-gen/templates/nginx.tmpl /etc/nginx/conf.d/default.conf
```

Finally, start your containers with `VIRTUAL_HOST` environment variables.

    $ docker run -e VIRTUAL_HOST=foo.bar.com  ...
