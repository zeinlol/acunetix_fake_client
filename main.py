from typing import NoReturn

from api.base import AcunetixAPI
from cli_arguments import CLI_ARGUMENTS


def main() -> NoReturn:
    api = AcunetixAPI(
        username=CLI_ARGUMENTS.username,
        password=CLI_ARGUMENTS.password,
        host=CLI_ARGUMENTS.host,
        port=CLI_ARGUMENTS.port,
        secure=CLI_ARGUMENTS.secure,
    )
    ...


if __name__ == '__main__':
    main()
