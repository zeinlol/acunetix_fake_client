from http import server

from api.base import AcunetixAPI
from cli_arguments import CLI_ARGUMENTS

api = AcunetixAPI(
    username=CLI_ARGUMENTS.username,
    password=CLI_ARGUMENTS.password,
    host=CLI_ARGUMENTS.acunetix_host,
    port=CLI_ARGUMENTS.acunetix_port,
    secure=CLI_ARGUMENTS.secure,
)


# noinspection PyPep8Naming
class Client(server.BaseHTTPRequestHandler):
    """
    Socket Client base functions and logic
    """

    def do_GET(self):
        path = self.path.removeprefix('/api/v1/')
        response = api._get_request(path=path)
        self._send_api_response(response=response)

    def do_POST(self):
        path = self.path.removeprefix('/api/v1/')
        if path == 'me/login':
            self.send_response(204)
            headers = {'Content-type': 'application/json; charset=utf8', 'Pragma': 'no-cache', 'Expires': '-1', 'Cache-Control': 'no-cache, must-revalidate',}
            for header in headers.items():
                    self.send_header(header[0], header[1])
            self.end_headers()
            self.wfile.write(b'{response: Ok}')
        else:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            response = api._post_request(path=path, data=post_data)
            self._send_api_response(response=response)

    def do_PATCH(self):
        path = self.path.removeprefix('/api/v1/')
        if path == 'me':
            self.send_response(204)
            headers = {'Content-type': 'application/json; charset=utf8', 'Pragma': 'no-cache', 'Expires': '-1', 'Cache-Control': 'no-cache, must-revalidate',}
            for header in headers.items():
                    self.send_header(header[0], header[1])
            self.end_headers()
            self.wfile.write(b'{response: Ok}')
        else:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            response = api._patch_request(path=path, data=post_data)
            self._send_api_response(response=response)

    def do_DELETE(self):
        path = self.path.removeprefix('/api/v1/')
        response = api._delete_request(path=path)
        self._send_api_response(response=response)

    def _send_api_response(self, response):
        self.send_response(response.status_code)
        for header in response.headers.items():
            # remove this header because it broke response to real client
            if header[0].lower() != "transfer-encoding":
                self.send_header(header[0], header[1])
        self.end_headers()
        self.wfile.write(response.content)
