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
        'address': '0.0.0.0',
        'port': '8080',
    },
}

settings = None


def __json_object_hook(d):
    values = [__json_object_hook(value) if isinstance(value, dict) else value for value in d.values()]
    return namedtuple('X', d.keys())(*values)


with open(os.path.dirname(__file__) + '/../settings.json', 'r') as file:
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
        if address is None:
            address = get_host_ip()
        __SETTINGS['server']['address'] = address
        __SETTINGS['server']['port'] = server.get('port')

    settings = __json_object_hook(__SETTINGS)

