while true;
do
    ls -d /etc/nginx/node.conf.d/*.conf | entr -d python3 /app/mergeswarm.py;
done