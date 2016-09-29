#!/usr/bin/env python3

import os, sys
import http.server
import socketserver

class BatsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        root = os.getcwd()
        
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        if self.path == "/headers":
            self.wfile.write(self.headers.as_string().encode())
        elif self.path == "/port":
            response = "answer from port %s\n" % PORT
            self.wfile.write(response.encode())
        else:
            self.wfile.write("No route for this path!\n".encode())

if __name__ == '__main__':
    PORT = int(sys.argv[1])
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(('0.0.0.0', PORT), BatsHandler)
    httpd.serve_forever()
