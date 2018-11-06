import json

from dataclasses import dataclass
from calendar import timegm
from typing import Optional
from datetime import datetime
from hashlib import sha256
from base58 import b58encode
from .key import Key
from .storage import Database
from utils.reprutil import flat_dict_for_repr
from utils import log

from .codegen.objects_pb2 import BlockData

@dataclass
class Block:
    time: datetime
    block_hash: str = ''
    prev_hash: str = ''
    signature: str = ''
    chain_id: str = ''
    height: int = 0
    payload: bytes = b''

    def __init__(self, data: dict = None):
        self.time = timegm(datetime.utcnow().utctimetuple())
        if data is not None:
            self.block_hash = data.get('hash')
            self.prev_hash = data.get('prev_hash')
            self.time = data.get('time')
            self.signature = data.get('signature')
            self.chain_id = data.get('chain_id')
            self.height = data.get('height')
            self.payload = data.get('payload')

    @classmethod
    def from_bytes(cls, data: bytes):
        obj = BlockData()
        obj.ParseFromString(data)
        block = Block()
        block.time = obj.time,
        block.block_hash = obj.hash,
        block.prev_hash = obj.prev_hash,
        block.signature = obj.signature,
        block.chain_id = obj.chain_id,
        block.height = obj.height,
        block.payload = obj.payload
        return block

    @property
    def is_genesis(self):
        return self.height == 0

    @property
    def dict(self) -> dict:
        data = {
            'hash': self.block_hash,
            'time': self.time,
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
        return BlockData(
            time=self.time,
            chain_id=self.chain_id,
            height=self.height,
            payload=self.payload,
            prev_hash=self.prev_hash
        ).SerializeToString()

    @property
    def data(self) -> bytes:
        return BlockData(
            time=self.time,
            chain_id=self.chain_id,
            height=self.height,
            payload=self.payload,
            prev_hash=self.prev_hash,
            hash=self.block_hash,
            signature=self.signature
        ).SerializeToString()

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def is_valid(self) -> bool:
        start = datetime.utcnow()

        key = Key(self.chain_id)
        valid = (self.height == 0 or (self.prev_hash is not None and len(self.prev_hash) > 0)) and \
            b58encode(sha256(self.data_for_hashing).digest()).decode('ascii') == self.block_hash and \
            key.verify(self.signature, self.data_for_hashing)

        end = datetime.utcnow()
        log.info("Block validated in %.03f secs" % (end - start).total_seconds())

        return valid

    def __repr__(self):
        return flat_dict_for_repr({**self.dict, 'size': f'{len(self.data)} bytes'})


class Blockchain:
    @classmethod
    def all_chains(cls):
        objects = Database().all_chains()
        return [cls(Key(obj['public_key'], obj['private_key'])) for obj in objects]

    @classmethod
    def remote_chain(cls, public_key):
        chain = cls.load(public_key)
        if chain is None:
            remote = cls(Key(public_key))
            remote.save()
            return remote
        return chain

    @classmethod
    def load(cls, chain_id: str):
        """
        Load a exist chain from database

        :param chain_id: chain id = public key
        :return:
        """
        info = Database().get_chain(chain_id)
        if info is not None:
            if info.get('private_key') is not None and len(info['private_key']) > 0:
                return cls(Key(chain_id, info['private_key']))
            return cls(Key(chain_id))
        return None

    # TODO: validate information
    @classmethod
    def create(cls, **kwargs):
        """
        Create a new chain with a genesis block for chain information

        There should be 6 fields:
        name, version, author, website, email, desc

        :param kwargs: chain info
        :return: Blockchain
        """
        chain = cls(Key())
        block = chain.create_block(json.JSONEncoder(
            separators=(',', ':'),
            sort_keys=True,
            ensure_ascii=False
        ).encode(kwargs))
        chain.save()
        chain.save_block(block)
        return chain

    def __init__(self, key: Key):
        self.key = key
        self.database = Database()
        self.__info = None

    @property
    def info(self):
        if self.__info is not None:
            return self.__info
        else:
            genesis = self.get_block(0)
            if genesis is not None:
                self.__info = json.JSONDecoder().decode(genesis.payload.decode('utf8'))
            return {**self.__info, 'chain_id': self.id}

    @property
    def id(self):
        return self.key.public_key

    @property
    def is_owner(self) -> bool:
        return self.key.can_sign

    @property
    def height(self) -> int:
        return self.database.get_height(self.id)

    def get_block(self, height: int = None, block_hash: str = None) -> Optional[Block]:
        info = self.database.get_block(self.id, height, block_hash)
        return Block(info) if info is not None else None

    def get_blocks(self, start: int, end: int):
        blocks = self.database.get_blocks(self.id, start, end)
        if blocks is not None:
            return [Block(info) for info in blocks]
        return None

    def create_block(self, payload: bytes) -> Block:
        if isinstance(payload, dict) or isinstance(payload, list):
            payload = json.JSONEncoder(separators=(',', ':'), ensure_ascii=False).encode(payload).encode('utf8')
        if isinstance(payload, str):
            payload = payload.encode('utf8')
        if len(payload) > 2**20:
            raise ValueError('Block payload size should less than 1MB.')
        block = Block()
        block.payload = payload
        block.chain_id = self.id
        block.height = self.height
        if block.height > 0:
            block.prev_hash = self.database.get_block(self.id, block.height - 1)['hash']
        block.block_hash = b58encode(sha256(block.data_for_hashing).digest()).decode('utf8')
        block.signature = b58encode(self.key.sign(block.data_for_hashing)).decode('utf8')
        return block

    def save_block(self, block: Block) -> bool:
        if block.is_valid and self.get_block(block.height) is None:
            if self.height == 0:
                self.database.save_block(block.dict)
                return True
            elif self.height > 0:
                prev = self.get_block(block.height - 1)
                if prev is not None and prev.block_hash == block.prev_hash:
                    self.database.save_block(block.dict)
                    return True
        return False

    def save(self) -> bool:
        if Blockchain.load(self.id) is None:
            self.database.save_chain({
                'public_key': self.key.public_key,
                'private_key': self.key.private_key
            })
            return True
        return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return Block(self.database.get_block(self.id, height=key))
        elif isinstance(key, str):
            return Block(self.database.get_block(self.id, block_hash=key))
        return None
