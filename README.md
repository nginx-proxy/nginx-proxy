# nginx-proxy

This repository is a fork of the very well known [jwilder/nginx-proxy](https://github.com/nginx-proxy/nginx-proxy)

I customised it to my needs. Which are:
 - Provide an override for location /
 - While using fastcgi, nginx serves static files directly instead of passing them along
 - Multi node, Multi container swarm config

## How did I solve the swarm situation

 - Every node generate their config as usual, except they do it in a different folder (/etc/nginx/node.conf.d/)
 - the nginx.tmpl is using service_name instead of IP
 - The proxy is deployed globally (one instance per node)
 - Everytime a new file is added to the node.conf.d or everytime any file in this directory is updated, (entr)[http://eradman.com/entrproject/] will run a python script
 - That python script combines all configs into one that is /etc/nginx/conf.d/default.conf using (crossplane)[https://github.com/nginxinc/crossplane]

For this to work, all you need is a way to share data between node. It could be a volume driver or anything. I'm using
azure, so I have a shared directory on all nodes (which also contains my static files) so I bind /etc/nginx/node.conf.d/
in the shared directory, all nodes add their files, all proxy will regenerate their config including all other nodes.
When a new node joins, entr will trigger in each node and the new configuration is generated. If you rebalance your swarm,
docker-gen will trigger, that node's config will be updated which in turns triggers entr and so on.

## Override root location

You can set `LOCATION_PATH=xxx` (eg: "~ \.php$") and use the vhost.d/default or vhost.d/{VIRTUAL_HOST} to add:
```
location / {
    try_files $uri /index.php?$query_string;
    limit_rate_after 1000k;
    limit_rate 50k;
}

location {LOCATION_PATH} {
  ...
}
```

## Bind static files

You can bind your files in "/etc/nginx/static_files/{VIRTUAL_HOST}" and nginx will set the root of the server block to
that folder as follows:

```
server {
  ...

  root /etc/nginx/static_files/my.domain.com;

  '''
}
```

In combination with LOCATION_PATH override you can skip sending queries to the container and serve files directly.

Be aware that if using FastCGI you will also have to explicitly set your VIRTUAL_ROOT.

