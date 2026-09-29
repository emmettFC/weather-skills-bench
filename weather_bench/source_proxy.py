"""HTTPS CONNECT proxy for the end-to-end sandbox's public source hosts only."""
import json
import select
import socket
import socketserver
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

ALLOWED={'storage.googleapis.com','naturalearth.s3.amazonaws.com'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_CONNECT(self):
        started=time.monotonic();sent=received=0
        host,sep,port=self.path.rpartition(':')
        if not sep or host not in ALLOWED or port!='443':
            self.send_error(403,'Only benchmark source hosts on HTTPS are available');return
        try:
            with socket.create_connection((host,443),timeout=30) as upstream:
                self.send_response(200,'Connection Established');self.end_headers()
                peers=[self.connection,upstream]
                while True:
                    readable,_,_=select.select(peers,[],[],90)
                    if not readable:break
                    for peer in readable:
                        data=peer.recv(65536)
                        if not data:return
                        target=upstream if peer is self.connection else self.connection
                        target.sendall(data)
                        if peer is upstream:received+=len(data)
                        else:sent+=len(data)
        except OSError:pass
        finally:
            print(json.dumps({'host':host,'sent_bytes':sent,'received_bytes':received,'connection_seconds':time.monotonic()-started}),flush=True)

class Server(socketserver.ThreadingMixIn,HTTPServer):daemon_threads=True

if __name__=='__main__':Server(('0.0.0.0',8080),Handler).serve_forever()
