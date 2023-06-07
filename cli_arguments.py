import argparse


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True, type=str, help='Acunetix user name')
    parser.add_argument('-p', '--password', required=True, type=str, help='Acunetix user password')
    parser.add_argument('-ah', '--acunetix-host', required=True, type=str, help='Acunetix API host')
    parser.add_argument('-ap', '--acunetix-port', required=True, type=int, help='Acunetix API port')
    parser.add_argument('-s', '--secure', type=bool, default=False, help='Session is secure')
    parser.add_argument('-px', '--proxy', required=False, type=str, help='Proxy settings')
    parser.add_argument('-sh', '--listen-host', type=str, default='0.0.0.0', help='Listening hosts')
    parser.add_argument('-sp', '--listen-port', type=int, default=3444, help='Listening ports')
    parser.add_argument('-d', '--demo-mode', type=bool, default=False,
                        help='Handle no licence limitations. Wait for other scans finished')
    return parser.parse_args()


CLI_ARGUMENTS = init_args()
