import json
import os

from collections import namedtuple
from .getip import get_host_ip
from .logger import default_logger as log


__SETTINGS = {
    'database': {
        'host': 'localhost',
        'port': 27017,
        'name': 'infnote_chain',
    },
    'debug': True,
    'server': {
        'address': get_host_ip(),
        'port': 32767,
    },
    'manage': {
        'address': '127.0.0.1',
        'port': 32700
    },
    'peers': {
        'sync': False,
        'retry': 5
    }
}

settings = None
settings_loc = None


def write_to_settings_file():
    __create_settings_file(settings_loc, dict(settings._asdict()))


def __create_settings_file(path, value):
    try:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'w+') as file:
            content = json.JSONEncoder(indent=4).encode(value)
            file.write(content)
        return True
    except OSError as err:
        log.error(f'{err}')
        return False


def __json_object_hook(d):
    values = [__json_object_hook(value) if isinstance(value, dict) else value for value in d.values()]
    return namedtuple('X', d.keys())(*values)


def __read_user_settings(path):
    with open(path, 'r') as file:
        content = file.read()
        user = json.JSONDecoder().decode(content)

        db_settings = user.get('database')
        if db_settings is not None and isinstance(db_settings, dict):
            __SETTINGS['database']['host'] = db_settings.get('host')
            __SETTINGS['database']['port'] = db_settings.get('port')
            __SETTINGS['database']['name'] = db_settings.get('name')

        debug = user.get('debug')
        if debug is not None and isinstance(debug, bool):
            __SETTINGS['debug'] = debug

        server = user.get('server')
        if server is not None and isinstance(server, dict):
            address = server.get('address')
            if address is not None or address != 'auto':
                __SETTINGS['server']['address'] = address
            __SETTINGS['server']['port'] = server.get('port')

        socket = user.get('manage')
        if socket is not None and isinstance(socket, dict):
            address = socket.get('address')
            port = socket.get('port')
            if isinstance(address, str) and address != "auto":
                __SETTINGS['manage']['address'] = address
            if isinstance(port, int):
                __SETTINGS['manage']['port'] = port

        peers = user.get('peers')
        if peers is not None and isinstance(peers, dict):
            sync = peers.get('sync')
            if sync is not None:
                __SETTINGS['peers']['sync'] = sync
            retry = peers.get('retry')
            if retry is not None and isinstance(retry, int):
                __SETTINGS['peers']['retry'] = retry


global_path = '/etc/infnote/settings.json'
optional_path = '/usr/local/etc/infnote/settings.json'
user_path = '~/.infnote/settings.json'
if os.path.isfile(user_path):
    __read_user_settings(user_path)
elif os.path.isfile(global_path):
    __read_user_settings(global_path)
elif os.path.isfile(optional_path):
    __read_user_settings(optional_path)
else:
    if not __create_settings_file(global_path, __SETTINGS):
        if not __create_settings_file(optional_path, __SETTINGS):
            __create_settings_file(user_path, __SETTINGS)

settings = __json_object_hook(__SETTINGS)
