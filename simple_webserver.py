from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        try:
            print(f'Getting path: {self.path[1:]}')
            print(self.path[1:])
            file_to_open = open('./web_pages/' + self.path[1:]).read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(file_to_open, 'utf-8'))
        except:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404 - Not Found')

    def do_POST(self):
        # Parse the form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     }
        )

        # Get the form values
        request_date = form.getvalue("date")
        last_name = form.getvalue("last_name")

        self.send_response(500)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(f"<html><body><h1>POST!</h1><p>{request_date}</p><p>{last_name}</p></body></html>".encode('utf-8'))


port = 8080
httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
print(f'Listening to port: {port}')
httpd.serve_forever()