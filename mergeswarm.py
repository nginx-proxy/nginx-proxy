# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from crossplane import parse, build

SWARM_CONFIG_FILE = '/etc/nginx/node.conf.d/swarm.conf'
NGINX_OUTPUT = '/etc/nginx/conf.d/default.conf'
NGINX_RELOAD = 'nginx -s reload'

if not os.path.isfile(SWARM_CONFIG_FILE):
    with open(SWARM_CONFIG_FILE, 'w') as f:
        f.write("http { include ./*.conf; }")

nginx_config = []
swarm_config = parse(SWARM_CONFIG_FILE)['config']
nodes = [f['parsed'] for f in swarm_config[1:-1]]

for node in nodes:
    for statement in node:
        if statement in nginx_config:
            continue
        if statement['directive'] == 'upstream':
            all_upstream = [
                s['args'][0]
                for s in nginx_config if s['directive'] == 'upstream'
            ]
            if statement['args'][0] in all_upstream:
                continue
        if statement['directive'] == 'server':
            server_name = [
                s['args'][0]
                for s in statement['block'] if s['directive'] == 'server_name'
            ][0]
            all_server_names = [
                sl['args'][0]
                for s in nginx_config if s['directive'] == 'server'
                for sl in s['block'] if sl['directive'] == 'server_name'
            ]
            if server_name in all_server_names:
                continue
        nginx_config.append(statement)

with open(NGINX_OUTPUT, 'w') as f:
    f.write(build(nginx_config))

process = subprocess.Popen(NGINX_RELOAD.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
if output:
    sys.stdout.write(output)
if error:
    sys.stderr.write(error)
