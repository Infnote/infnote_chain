import json
import os

from collections import namedtuple
from .getip import get_host_ip
from .logger import default_logger as log


class Settings:
    __settings = {
        'database': {
            'host': 'localhost',
            'port': 27017,
            'name': 'infnote_chain',
        },
        'debug': True,
        'server': {
            'address': 'auto',
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

    def __init__(self):
        self.location = None

    def write_to_settings_file(self):
        if self.location is not None:
            self.__create_settings_file(self.location, self.__settings)

    def __create_settings_file(self, path, value):
        try:
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            with open(path, 'w+') as file:
                content = json.JSONEncoder(indent=4).encode(value)
                file.write(content)
            self.location = path
            return True
        except OSError as err:
            log.error(f'{err}')
            return False

    def __json_object_hook(self, d):
        values = [self.__json_object_hook(value) if isinstance(value, dict) else value for value in d.values()]
        return namedtuple('X', d.keys())(*values)

    def __read_user_settings(self, path):
        with open(path, 'r') as file:
            content = file.read()
            user = json.JSONDecoder().decode(content)

            db_settings = user.get('database')
            if db_settings is not None and isinstance(db_settings, dict):
                self.__settings['database']['host'] = db_settings.get('host')
                self.__settings['database']['port'] = db_settings.get('port')
                self.__settings['database']['name'] = db_settings.get('name')

            debug = user.get('debug')
            if debug is not None and isinstance(debug, bool):
                self.__settings['debug'] = debug

            server = user.get('server')
            if server is not None and isinstance(server, dict):
                address = server.get('address')
                if address is not None and address != 'auto':
                    self.__settings['server']['address'] = address
                else:
                    self.__settings['server']['address'] = get_host_ip()
                self.__settings['server']['port'] = server.get('port')

            socket = user.get('manage')
            if socket is not None and isinstance(socket, dict):
                address = socket.get('address')
                port = socket.get('port')
                if isinstance(address, str) and address != "auto":
                    self.__settings['manage']['address'] = address
                if isinstance(port, int):
                    self.__settings['manage']['port'] = port

            peers = user.get('peers')
            if peers is not None and isinstance(peers, dict):
                sync = peers.get('sync')
                if sync is not None:
                    self.__settings['peers']['sync'] = sync
                retry = peers.get('retry')
                if retry is not None and isinstance(retry, int):
                    self.__settings['peers']['retry'] = retry

            self.location = path

    def loading(self):
        global_path = '/etc/infnote/settings.json'
        optional_path = '/usr/local/etc/infnote/settings.json'
        user_path = '~/.infnote/settings.json'
        if os.path.isfile(user_path):
            self.__read_user_settings(user_path)
        elif os.path.isfile(optional_path):
            self.__read_user_settings(optional_path)
        elif os.path.isfile(global_path):
            self.__read_user_settings(global_path)
        else:
            if not self.__create_settings_file(global_path, self.__settings):
                if not self.__create_settings_file(optional_path, self.__settings):
                    self.__create_settings_file(user_path, self.__settings)

        self.write_to_settings_file()

        log.info(f'Config file at: {self.location}')

        return self.__json_object_hook(self.__settings)


settings = Settings().loading()
