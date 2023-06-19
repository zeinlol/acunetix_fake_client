import json
from http import server

from api.base import AcunetixAPI
from cli_arguments import CLI_ARGUMENTS
from core.tools import timed_print
from scanner.scanner_base import TargetsQueue

api = AcunetixAPI(
    username=CLI_ARGUMENTS.username,
    password=CLI_ARGUMENTS.password,
    host=CLI_ARGUMENTS.acunetix_host,
    port=CLI_ARGUMENTS.acunetix_port,
    secure=CLI_ARGUMENTS.secure,
)

targets_queue = TargetsQueue()
targets_queue.fill_current_targets(targets=api.get_targets())

# noinspection PyPep8Naming
class Client(server.BaseHTTPRequestHandler):
    """
    Socket Client base functions and logic
    """
    def _init_path(self) -> str:
        return self.path.removeprefix('/api/v1/')

    def do_GET(self):
        path = self._init_path()
        response = api.get_request(path=path)
        self._send_api_response(response=response)

    def do_POST(self):
        path = self._init_path()
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        match path:
            case 'me/login':
                self._handle_log_in()
            case 'targets':
                self._handle_target_creating(path=path, post_data=post_data)
            case 'scans':
                new_scan_data = json.loads(post_data)
                target_id = new_scan_data.get('target_id', None)
                if not target_id:
                    self._through_not_found_error()
                if target_scan := next(filter(lambda scan: scan.target_id == target_id, api.get_scans()), None):
                    response = api.get_request(f'scans/{target_scan.scan_id}')
                else:
                    response = api.post_request(path=path, data=post_data)
                self._send_api_response(response=response)
            case _:
                response = api.post_request(path=path, data=post_data)
                self._send_api_response(response=response)
        

    def do_PATCH(self):
        path = self._init_path()
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        match path:
            case 'me':
                self._handle_log_in()
            case _:
                response = api.patch_request(path=path, data=post_data)
                self._send_api_response(response=response)

    def do_DELETE(self):
        path = self._init_path()
        match path:
            case path if path.startswith('targets/'):
                response = api.get_request(path=path)
                if targets_queue.delete_target(target=response.json()):
                    response = api.delete_request(path=path)
                    self._send_api_response(response=response)
                else:
                    self._send_response(data_to_send=b'{"response": "Ok"}')
            case _:
                response = api.delete_request(path=path)
                self._send_api_response(response=response)

    def _handle_log_in(self):
        # TODO: add more clever logic for handle requests. add uuid for each log in attempt?
        # TODO: for logged client check when last time was request from them.
        #  if more than XX time - remove it from system
        # TODO: Check credentials
        self._send_response(data_to_send=b'{"response": "Ok", "is_fake_client": true}')

    def _handle_target_creating(self, path: str, post_data):
        client_target = targets_queue.check_target(target=json.loads(post_data))
        if not client_target.target_id:
            response = api.post_request(path=path, data=post_data)
            if response.status_code == 409:
                timed_print('Problems with license. Can not add second target. Check if existed target can be removed')
                self._check_if_current_target_can_be_removed()
                response = {'order': client_target.order}
                self._send_response(data_to_send=json.dumps(response).encode())
            else:
                client_target.target_id = response.json().get('target_id')
                self._send_api_response(response=response)
        else:
            response = {'order': client_target.order, 'target_id': client_target.target_id}
            self._send_response(data_to_send=json.dumps(response).encode())

    def _fill_default_headers(self):
        headers = {'Content-type': 'application/json; charset=utf8', 'Pragma': 'no-cache', 'Expires': '-1',
                   'Cache-Control': 'no-cache, must-revalidate', }
        for header in headers.items():
            self.send_header(header[0], header[1])
        self.end_headers()

    def _through_not_found_error(self):
        self.send_response(404)

    def _send_api_response(self, response):
        self.send_response(response.status_code)
        for header in response.headers.items():
            # remove this header because it broke response to real client
            if header[0].lower() != "transfer-encoding":
                self.send_header(header[0], header[1])
        self.end_headers()
        self.wfile.write(response.content)

    def _send_response(self, data_to_send: bytes | None, status_code: int = 200, ):
        self.send_response(status_code)
        self._fill_default_headers()
        if data_to_send:
            self.wfile.write(data_to_send)

    def _check_if_current_target_can_be_removed(self):
        # TODO: test targets and remove them if they exist too long
        pass