#!/usr/bin/env sh

_SCRIPT_="$0"

ACME_BIN="/acme.sh/acme.sh --home /acme.sh --config-home /acmecerts"

DEFAULT_CONF="/etc/nginx/conf.d/default.conf"


CERTS="/etc/nginx/certs"


updatessl() {
  nginx -t && nginx -s reload
  if grep ACME_DOMAINS $DEFAULT_CONF ; then
    for d_list in $(grep ACME_DOMAINS $DEFAULT_CONF | cut -d ' ' -f 2);
    do
      d=$(echo "$d_list" | cut -d , -f 1)
      $ACME_BIN --issue \
      -d $d_list \
      --nginx \
      --fullchain-file "$CERTS/$d.crt" \
      --key-file "$CERTS/$d.key" \
      --reloadcmd "nginx -t && nginx -s reload"
    done

    #generate nginx conf again.
    docker-gen /app/nginx.tmpl /etc/nginx/conf.d/default.conf
  else
    echo "skip updatessl"
  fi
  nginx -t && nginx -s reload
}



"$@"



