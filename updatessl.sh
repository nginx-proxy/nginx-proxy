#!/usr/bin/env sh

_SCRIPT_="$0"

ACME_BIN="/acme.sh/acme.sh --home /acme.sh --config-home /acmecerts"

DEFAULT_CONF="/etc/nginx/conf.d/default.conf"

NGINX_HOME="/etc/nginx"

CERTS="/etc/nginx/certs"


updatessl() {

  for d_list in $(grep ACMD_DOMAINS $DEFAULT_CONF | cut -d ' ' -f 2);
  do
    d=$(echo "$d_list" | cut -d , -f 1)
    $ACME_BIN --issue \
    -d $d_list \
    -w $NGINX_HOME/html \
    --pre-hook "$_SCRIPT_ pre_hook $DEFAULT_CONF" \
    --post-hook "$_SCRIPT_ post_hook $DEFAULT_CONF" \
    --fullchain-file "$CERTS\$d.crt" \
    --key-file "$CERTS\$d.crt" \
    --reloadcmd "service nginx configtest && service force-reload"
  done

  #generate nginx conf again.
  docker-gen /app/nginx.tmpl /etc/nginx/conf.d/default.conf
  service nginx configtest && service force-reload
}



pre_hook() {
  _d_conf="$1"
  sed -i "s|#\(location.*#acme\)|\\1|" $_d_conf && service nginx configtest && service force-reload
}

post_hook() {
  _d_conf="$1"
  sed -i "s|\(location.*#acme\)|#\\1|"  $_d_conf 
}


"$@"



