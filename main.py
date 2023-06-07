import asyncio
from typing import NoReturn

from cli_arguments import CLI_ARGUMENTS
from core import server


def main() -> NoReturn:
    loop = asyncio.new_event_loop()
    loop.run_until_complete(server.socket_listener(listen_host=CLI_ARGUMENTS.listen_host,
                                                   listen_port=CLI_ARGUMENTS.listen_port))


if __name__ == '__main__':
    main()
