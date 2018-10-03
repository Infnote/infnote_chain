import json

from typing import Optional
from datetime import datetime
from hashlib import sha256
from base58 import b58encode
from .key import Key
from .storage import Database


class Block:
    def __init__(self, data: dict = None):
        self.block_hash = ''
        self.prev_hash = ''
        self.time = datetime.utcnow()
        self.signature = ''
        self.chain_id = '',
        self.height = 0,
        self.payload = ''
        if data is not None:
            self.block_hash = data.get('hash')
            self.prev_hash = data.get('prev_hash')
            self.time = datetime.utcfromtimestamp(data.get('time'))
            self.signature = data.get('signature')
            self.chain_id = data.get('chain_id')
            self.height = data.get('height')
            self.payload = data.get('payload')

    @property
    def is_genesis(self):
        return self.height == 0

    @property
    def dict(self) -> dict:
        data = {
            'hash': self.block_hash,
            'time': int(self.time.timestamp()),
            'signature': self.signature,
            'chain_id': self.chain_id,
            'height': self.height,
            'payload': self.payload
        }
        if self.prev_hash is not None and len(self.prev_hash) > 0:
            data['prev_hash'] = self.prev_hash
        return data

    @property
    def data_for_hashing(self) -> bytes:
        data = self.dict
        del data['hash']
        del data['signature']
        return json.JSONEncoder(
            separators=(',', ':'),
            sort_keys=True,
            ensure_ascii=False
        ).encode(data).encode('utf8')

    @property
    def data(self) -> bytes:
        return json.JSONEncoder(
            separators=(',', ':'),
            sort_keys=True,
            ensure_ascii=False
        ).encode(self.dict).encode('utf8')

    @property
    def is_valid(self) -> bool:
        key = Key(self.chain_id)
        return (self.height == 0 or (self.prev_hash is not None and len(self.prev_hash) > 0)) and \
            b58encode(sha256(self.data_for_hashing).digest()).decode('ascii') == self.block_hash and \
            key.verify(self.signature, self.data_for_hashing)

    def __str__(self):
        return json.JSONEncoder(
            sort_keys=True,
            ensure_ascii=False,
            indent=4
        ).encode(self.dict)


class Blockchain:
    @classmethod
    def all_chains(cls):
        objects = Database().all_chains()
        return [cls(Key(obj['public_key'], obj['private_key'])) for obj in objects]

    @classmethod
    def load(cls, chain_id: str):
        """
        Load a exist chain from database

        :param chain_id: chain id = public key
        :return:
        """
        info = Database().get_chain(chain_id)
        if info['private_key'] is not None and len(info['private_key']) > 0:
            return cls(Key(chain_id, info['private_key']))
        return cls(Key(chain_id))

    # TODO: validate information
    @classmethod
    def create(cls, **kwargs):
        """
        Create a new chain with a genesis block for chain information

        There should be 5 fields:
        name, version, author, website, email

        :param kwargs: chain info
        :return: Blockchain
        """
        chain = cls(Key())
        block = chain.create_block(json.JSONEncoder(
            separators=(',', ':'),
            sort_keys=True,
            ensure_ascii=False
        ).encode(kwargs).encode('utf8'))
        chain.save()
        chain.save_block(block)
        return chain

    def __init__(self, key: Key):
        self.key = key
        self.id = self.key.public_key
        self.database = Database()

        genesis = self.get_block(0)
        if genesis is not None:
            self.info = json.JSONDecoder().decode(genesis.payload)

    @property
    def is_owner(self) -> bool:
        return self.key.can_sign

    @property
    def height(self) -> int:
        return self.database.get_height(self.id)

    def get_block(self, height: int = None, block_hash: str = None) -> Optional[Block]:
        info = self.database.get_block(self.id, height, block_hash)
        return Block(info) if info is not None else None

    def create_block(self, payload: str) -> Block:
        block = Block()
        block.payload = payload
        block.chain_id = self.id
        block.height = self.height
        if block.height > 0:
            block.prev_hash = self.database.get_block(self.id, block.height - 1).block_hash
        block.block_hash = b58encode(sha256(block.data_for_hashing).digest()).decode('ascii')
        block.signature = b58encode(self.key.sign(block.data_for_hashing)).decode('ascii')
        return block

    def save_block(self, block: Block) -> bool:
        if block.is_valid and self.get_block(block.height) is None:
            if self.height == 0:
                self.database.save_block(block.dict)
                return True
            elif self.height > 0:
                prev = self.get_block(block.height - 1)
                if prev.block_hash == block.prev_hash:
                    self.database.save_block(block.dict)
                    return True
        return False

    def save(self):
        self.database.save_chain({
            'public_key': self.key.public_key,
            'private_key': self.key.private_key
        })

    def __getitem__(self, key):
        if isinstance(key, int):
            return Block(self.database.get_block(self.id, height=key))
        elif isinstance(key, str):
            return Block(self.database.get_block(self.id, block_hash=key))
        return None
