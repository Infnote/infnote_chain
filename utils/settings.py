import json


SETTINGS = {
    'database': {
        'host': 'localhost',
        'port': 27017,
        'name': 'infnote_chain'
    },
    'debug': True
}


with open('../settings.json', 'r') as file:
    content = file.read()
    settings = json.JSONDecoder().decode(content)

    db_settings = settings.get('database')
    if db_settings is not None and isinstance(db_settings, dict):
        SETTINGS['database']['host'] = db_settings.get('host')
        SETTINGS['database']['port'] = db_settings.get('port')
        SETTINGS['database']['name'] = db_settings.get('name')

    debug = settings.get('debug')
    if debug is not None and isinstance(debug, bool):
        SETTINGS['debug'] = debug
