from client.client_base import Client
from core.tools import timed_print
from http import server


async def socket_listener(listen_host: str, listen_port: int):
    timed_print(f"Socket is listening on {listen_host}:{listen_port}")
    http_server = server.HTTPServer((listen_host, listen_port), Client)
    http_server.serve_forever()
