import json
import os

from collections import namedtuple
from .getip import get_host_ip


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
    'socket': {
        'address': '127.0.0.1',
        'port': 32700
    },
    'peers': {
        'sync': True,
        'retry': 5
    }
}

settings = None


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

        socket = user.get('socket')
        if socket is not None and isinstance(socket, dict):
            address = socket.get('address')
            port = socket.get('port')
            if isinstance(address, str) and address != "auto":
                __SETTINGS['socket']['address'] = address
            if isinstance(port, int):
                __SETTINGS['socket']['port'] = port

        peers = user.get('peers')
        if peers is not None and isinstance(peers, dict):
            sync = peers.get('sync')
            if sync is not None:
                __SETTINGS['peers']['sync'] = sync
            retry = peers.get('retry')
            if retry is not None and isinstance(retry, int):
                __SETTINGS['peers']['retry'] = retry


current_path = os.path.dirname(__file__) + '/../settings.json'
global_path = '/etc/infnote/settings.json'
if os.path.isfile(current_path):
    __read_user_settings(current_path)
elif os.path.isfile(global_path):
    __read_user_settings(global_path)

settings = __json_object_hook(__SETTINGS)

