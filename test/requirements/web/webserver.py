#!/usr/bin/env python3

import os, sys, re
import http.server
import socketserver

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):

        response_body = ""
        response_code = 200

        if self.path == "/headers":
            response_body += self.headers.as_string()
        elif self.path == "/port":
            response_body += f"answer from port {PORT}\n"
        elif re.match(r"/status/(\d+)", self.path):
            result = re.match(r"/status/(\d+)", self.path)
            response_code = int(result.group(1))
            response_body += f"answer with response code {response_code}\n"
        elif self.path == "/":
            response_body += f"I'm {os.environ['HOSTNAME']}\n"
        else:
            response_body += "No route for this path!\n"
            response_code = 404

        self.send_response(response_code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        if (len(response_body)):
            self.wfile.write(response_body.encode())

if __name__ == '__main__':
    PORT = int(sys.argv[1])
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(('0.0.0.0', PORT), Handler)
    httpd.serve_forever()
