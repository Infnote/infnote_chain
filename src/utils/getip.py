import socket
import subprocess

from .logger import default_logger as log
from requests import get
from requests.exceptions import ConnectTimeout, ConnectionError as ConnectError


def get_host_ip():
    try:
        ip = get('https://api.ipify.org', timeout=1).text
        if subprocess.call(['ping', '-c 1', ip], stdout=subprocess.DEVNULL, timeout=0.5) == 0:
            log.info(f'Public IP: {ip}')
            return ip
    except (ConnectTimeout, ConnectError, subprocess.TimeoutExpired):
        log.error('Failed to get public IP.')

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except ConnectionError:
        ip = '127.0.0.1'
    finally:
        s.close()

    log.info(f'Local IP: {ip}')
    return ip
