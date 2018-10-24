from pymongo import MongoClient, ASCENDING, DESCENDING
from utils import Singleton, settings, log
from datetime import datetime


class Database(metaclass=Singleton):
    def __init__(self):
        db_settings = settings.database
        self.database = MongoClient(db_settings.host, db_settings.port)[db_settings.name]

    def save_chain(self, chain: dict):
        self.database.chains.insert_one(chain)

    def save_block(self, block: dict):
        start = datetime.utcnow()
        self.database.blocks.insert_one(block)
        end = datetime.utcnow()
        log.info("New block saved in %.03f secs" % (end - start).total_seconds())

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

    def get_blocks(self, chain_id: str, start: int, end: int):
        query = {'chain_id': chain_id, 'height': {'$gte': start, '$lte': end}}
        return self.database.blocks.find(query).sort('height', ASCENDING)

    def get_height(self, chain_id):
        return self.database.blocks.count({'chain_id': chain_id})

    def migrate(self):
        log.info('Create index for "public_key" in "chains".')
        self.database.chains.create_index([('public_key', ASCENDING)], unique=True)
        log.info('Create index for "height" in "blocks".')
        self.database.blocks.create_index([('height', DESCENDING)])
