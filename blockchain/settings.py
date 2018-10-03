import json


SETTINGS = {
    'database': {
        'host': 'localhost',
        'port': 27017,
        'name': 'infnote_chain'
    }
}


with open('../settings.json', 'r') as file:
    content = file.read()
    settings = json.JSONDecoder().decode(content)
    db_settings = settings.get('database')
    if db_settings is not None:
        SETTINGS['database']['host'] = db_settings.get('host')
        SETTINGS['database']['port'] = db_settings.get('port')
        SETTINGS['database']['name'] = db_settings.get('name')
