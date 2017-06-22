#!/usr/bin/env python3
import os

import sys
from flask import Flask, Response, request
app = Flask(__name__)


@app.route("/")
def root():
    return Response("I'm %s\n" % os.environ['HOSTNAME'], mimetype="text/plain")


@app.route("/headers")
def headers():
    return Response("".join(["%s: %s\n" % (header, value) for header, value in request.headers.items()]), mimetype="text/plain")


@app.route("/port")
def port():
    return Response("answer from port %s\n" % PORT, mimetype="text/plain")


if __name__ == '__main__':
    PORT = int(sys.argv[1])
    app.run(host="0.0.0.0", port=PORT)
