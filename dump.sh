#!/bin/bash
echo
echo "-------------------------------------------------------------------------------"
find /etc/nginx/ -type f -name '*.conf' -o -path '/etc/nginx/vhost.d/*'
echo
echo "-------------------------------------------------------------------------------"
find /etc/nginx/ -type f -name '*.conf' | while read config_file; do
    echo "> $config_file"
    awk '{printf "%3d %s\n", NR, $0}' "$config_file"
done