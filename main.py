import urllib.parse
import mimetypes
import socket
import json

from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from threading import Thread

class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == '/':
            self.send_html_file('index.html')

        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')

        else:
            if Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
    
    def do_POST(self): 

        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = '127.0.0.1', 5000
        data_to_log = json.dumps([data_dict.get('username'), data_dict.get('message')])
        sock.sendto(data_to_log.encode(), server)
        sock.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)

        if mt:
            self.send_header('Content-type', mt[0])

        else:
            self.send_header('Content-type', 'text/plain')

        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = '', 3000
    http = server_class(server_address, handler_class)

    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print('Close server')
    finally:
        http.server_close()

def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = '127.0.0.1', 5000
    sock.bind(server)

    try:
        while True:

            data, address = sock.recvfrom(1024)
            data = json.loads(data.decode())
            log_time = str(datetime.now())
            log = {log_time: {'username': data[0], 'message': data[1]}}

            with open('storage/data.json', 'r+') as file:
                file_data: dict = json.load(file)
                file.seek(0)
                file_data.update(log)
                json.dump(file_data, file)

    except KeyboardInterrupt:
        print('Destroy server')
    finally:
        sock.close()

if __name__ == '__main__':

    http_server = Thread(target=run_http_server)
    sock_server = Thread(target=socket_server)

    http_server.start()
    sock_server.start()
