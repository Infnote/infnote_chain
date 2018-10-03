from pymongo import MongoClient, ASCENDING, DESCENDING
from .settings import SETTINGS


class Singleton(type):
    instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.instances:
            cls.instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instances[cls]


class Database(metaclass=Singleton):
    def __init__(self):
        db_settings = SETTINGS['database']
        self.database = MongoClient(db_settings['host'], db_settings['port'])[db_settings['name']]

    def save_chain(self, chain: dict):
        self.database.chains.insert_one(chain)

    def save_block(self, block: dict):
        self.database.blocks.insert_one(block)

    def get_chain(self, public_key: str):
        return self.database.chains.find_one({'public_key': public_key})

    def all_chains(self):
        return self.database.chains.find()

    def get_block(self, chain_id: str, height: int = None, block_hash: str = None):
        query = {'chain_id': chain_id}
        if height is not None:
            query['height'] = height
        if block_hash is not None and len(block_hash) > 0:
            query['hash'] = block_hash
        return self.database.blocks.find_one(query)

    def get_height(self, chain_id):
        return self.database.blocks.count({'chain_id': chain_id})

    def migrate(self):
        self.database.chains.create_index([('public_key', ASCENDING)], unique=True)
        self.database.blocks.create_index([('height', DESCENDING)])
