import json
import uuid
from http import server
from typing import Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
    def _init_request_data(self) -> (str, dict | list, Any):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        watcher = None
        if client_uuid := query_params.get('watcher_uuid', None):
            watcher = targets_queue.get_watcher(client_uuid=str(client_uuid))
            watcher.update_last_request_time()
            del query_params['watcher_uuid']

        # Reconstruct the modified path
        modified_query = urlencode(query_params, doseq=True)
        self.path = urlunparse(parsed_path._replace(query=modified_query))
        return self.path.removeprefix('/api/v1/'), modified_query, watcher

    def do_GET(self):
        path, query_params, watcher = self._init_request_data()
        response = api.get_request(path=path)
        self._send_api_response(response=response)

    def do_POST(self):
        path, query_params, watcher = self._init_request_data()
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        match path:
            case 'me/login':
                self._handle_log_in(post_data=json.loads(post_data))
            case 'targets':
                if not watcher:
                    self.through_not_authorised()
                else:
                    self._handle_target_creating(path=path, post_data=post_data, watcher=watcher)
            case 'scans':
                new_scan_data = json.loads(post_data)
                target_id = new_scan_data.get('target_id', None)
                if not target_id:
                    self.through_not_found_error()
                if target_scan := next(filter(lambda scan: scan.target_id == target_id, api.get_scans()), None):
                    response = api.get_request(f'scans/{target_scan.scan_id}')
                else:
                    response = api.post_request(path=path, data=post_data)
                self._send_api_response(response=response)
            case _:
                response = api.post_request(path=path, data=post_data)
                self._send_api_response(response=response)
        

    def do_PATCH(self):
        path, query_params, watcher = self._init_request_data()
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        match path:
            case 'me':
                self._handle_log_in(post_data=json.loads(post_data))
            case _:
                response = api.patch_request(path=path, data=post_data)
                self._send_api_response(response=response)

    def do_DELETE(self):
        path, query_params, watcher = self._init_request_data()
        match path:
            case path if path.startswith('targets/'):
                response = api.get_request(path=path)
                if watcher:
                    if targets_queue.delete_target(target=response.json(), watcher=watcher):
                        response = api.delete_request(path=path)
                        self._send_api_response(response=response)
                    else:
                        self._send_response(data_to_send=b'{"response": "Ok"}')
                else:
                    self._send_response(data_to_send=b'{"response": "Ok"}')
            case _:
                response = api.delete_request(path=path)
                self._send_api_response(response=response)


    def through_not_found_error(self):
        self.send_response(404)

    def through_not_authorised(self):
        self.send_response(401)

    def _handle_log_in(self, post_data: dict):
        if post_data.get('email') != CLI_ARGUMENTS.username or post_data.get('password') != api.hash_password:
            self.through_not_authorised()
        else:
            response = {
                "response": "Ok",
                "is_fake_client": True,
                'watcher_uuid': str(uuid.uuid4())
            }
            self._send_response(data_to_send=json.dumps(response).encode())

    def _handle_target_creating(self, path: str, post_data: bytes, watcher):
        client_target = targets_queue.check_target(target=json.loads(post_data), watcher=watcher)
        if not client_target.target_id:
            response = api.post_request(path=path, data=post_data)
            if response.status_code == 409:
                timed_print('Problems with license. Can not add second target. Check if existed target can be removed')
                api_target, is_allowed_to_remove = self._check_if_current_target_can_be_removed()
                if api_target.address == client_target.address:
                    timed_print('Trying to add same target. continue scan')
                    client_target.target_id = api_target.target_id
                    response = {'order': client_target.order, 'target_id': client_target.target_id}
                else:
                    timed_print(f'Allowance for removing data: {is_allowed_to_remove}')
                    if is_allowed_to_remove:
                        api.delete_target(target=api_target)
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
    def _send_api_response(self, response):
        """ Send acunetix API response """
        self.send_response(response.status_code)
        for header in response.headers.items():
            # remove this header because it broke response to real client
            if header[0].lower() != "transfer-encoding":
                self.send_header(header[0], header[1])
        self.end_headers()
        self.wfile.write(response.content)

    def _send_response(self, data_to_send: bytes | None, status_code: int = 200, ):
        """ Send direct response """
        self.send_response(status_code)
        self._fill_default_headers()
        if data_to_send:
            self.wfile.write(data_to_send)

    @staticmethod
    def _check_if_current_target_can_be_removed() -> (Any, bool):
        """ check clients targets and acunetix targets """
        api_targets = api.get_targets()
        if len(api_targets) < 1:
            return None, False
        is_allowed_to_remove = True
        target = api_targets[0]
        client_targets = list(filter(lambda item: item.address == target.address, targets_queue.targets))
        for _client_target in client_targets:
            for watcher in _client_target.watchers:
                if watcher.is_no_requests:
                    _client_target.remove_watcher(watcher=watcher)
            if _client_target.watchers_amount > 0:
                is_allowed_to_remove = False
        return target, is_allowed_to_remove
