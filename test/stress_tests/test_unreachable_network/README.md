# nginx-proxy template is not considered when a container is not reachable

Having a container with the `VIRTUAL_HOST` environment variable set but on a network not reachable from the nginx-proxy container will result in nginx-proxy serving the default nginx welcome page for all requests.

Furthermore, if the nginx-proxy in such state is restarted, the nginx process will crash and the container stops.

In the generated nginx config file, we can notice the presence of an empty `upstream {}` block.

This can be fixed by merging [PR-585](https://github.com/jwilder/nginx-proxy/pull/585).

## How to reproduce

1. a first web container is created on network `netA`
1. a second web container is created on network `netB`
1. nginx-proxy is created with access to `netA` only


## Erratic behavior

- nginx serves the default welcome page for all requests to `/` and error 404 for any other path
- nginx-container crash on restart

Log shows:

```
webB_1          | starting a web server listening on port 82
webA_1          | starting a web server listening on port 81
reverseproxy    | forego     | starting dockergen.1 on port 5000
reverseproxy    | forego     | starting nginx.1 on port 5100
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Generated '/etc/nginx/conf.d/default.conf' from 3 containers
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Running 'nginx -s reload'
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Error running notify command: nginx -s reload, exit status 1
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Watching docker events
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Contents of /etc/nginx/conf.d/default.conf did not change. Skipping notification 'nginx -s reload'
reverseproxy    | reverseproxy    | forego     | starting dockergen.1 on port 5000  <---- nginx-proxy container restarted
reverseproxy    | forego     | starting nginx.1 on port 5100
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Generated '/etc/nginx/conf.d/default.conf' from 3 containers
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Running 'nginx -s reload'
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Error running notify command: nginx -s reload, exit status 1
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Watching docker events
reverseproxy    | dockergen.1 | 2017/02/20 01:10:24 Contents of /etc/nginx/conf.d/default.conf did not change. Skipping notification 'nginx -s reload'
reverseproxy    | forego     | starting dockergen.1 on port 5000
reverseproxy    | forego     | starting nginx.1 on port 5100
reverseproxy    | nginx.1    | 2017/02/20 01:11:02 [emerg] 17#17: no servers are inside upstream in /etc/nginx/conf.d/default.conf:64
reverseproxy    | forego     | starting nginx.1 on port 5200
reverseproxy    | forego     | sending SIGTERM to nginx.1
reverseproxy    | forego     | sending SIGTERM to dockergen.1
reverseproxy exited with code 0
reverseproxy exited with code 0

```

## Expected behavior

- no default nginx welcome page should be served
- nginx is able to forward requests to containers of `netA`
- nginx respond with error 503 for unknown virtual hosts
- nginx is not able to forward requests to containers of `netB` and responds with an error
- nginx should survive restarts
