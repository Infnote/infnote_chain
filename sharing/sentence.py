from platform import uname
from enum import Enum
from dataclasses import dataclass, field
from networking import Message
from functools import reduce
from networking import Peer, PeerManager
from blockchain import Block, Blockchain


@dataclass
class Sentence:
    class Type(Enum):
        EMPTY = ''
        INFO = 'info'
        ERROR = 'error'
        WANT_PEERS = 'want_peers'
        PEERS = 'peers'
        WANT_BLOCKS = 'want_blocks'
        BLOCKS = 'blocks'
        NEW_BLOCK = 'new_block'

    message: Message = None
    type: Type = Type.EMPTY

    @classmethod
    def load(cls, d):
        pass

    @property
    def dict(self) -> dict:
        return {
            'type': self.type.value
        }

    @property
    def question(self):
        return Message(self.dict)

    def to(self, question):
        return Message(self.dict,
                       Message.Type.ERROR if self.type == Sentence.Type.ERROR else Message.Type.ANSWER,
                       question.message.identifer)

    def __repr__(self):
        max_width = reduce(lambda r, x: r if r > len(x) else len(x), self.dict.keys(), 0)
        result = ''
        for key, value in self.dict.items():
            if isinstance(value, dict):
                value = len(value.keys())
            result += f'[{key}{" " * (max_width - len(key))}] {value}\n'
        return (f'{self.message}\n' if self.message is not None else '') + result


@dataclass
class Info(Sentence):

    type: Sentence.Type = Sentence.Type.INFO

    version: str = '0.1'
    peers: int = 0
    chains: dict = field(default_factory=dict)
    platform: dict = field(default_factory=dict)
    is_full_node: bool = True

    def __post_init__(self):
        info = uname()
        self.platform = {
            'system': info.system,
            'version': info.release,
            'node': info.node
        }

        chains = Blockchain.all_chains()
        for chain in chains:
            self.chains[chain.id] = chain.height

        self.peers = PeerManager().count

    @classmethod
    def load(cls, d):
        info = cls()
        try:
            info.version = d['version']
            info.peers = d['peers']
            info.chains = d['chains']
            info.platform = d['platform']
            info.is_full_node = d['full_node']
            return info
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'version': self.version,
            'peers': self.peers,
            'chains': self.chains,
            'platform': self.platform,
            'full_node': self.is_full_node
        }

    def __repr__(self):
        return super().__repr__()


@dataclass
class Error(Sentence):

    type: Sentence.Type = Sentence.Type.ERROR

    code: int = 0
    desc: str = ''

    @classmethod
    def load(cls, d):
        error = cls()
        try:
            error.code = d['code']
            error.desc = d['desc']
            return error
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'code': self.code,
            'desc': self.desc
        }

    def __repr__(self):
        return super().__repr__()


@dataclass
class WantPeers(Sentence):

    type: Sentence.Type = Sentence.Type.WANT_PEERS

    count: int = 0

    @classmethod
    def load(cls, d):
        want_peers = cls()
        try:
            want_peers.count = d['count']
            return want_peers
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'count': self.count
        }

    def __repr__(self):
        return super().__repr__()


@dataclass
class Peers(Sentence):

    type: Sentence.Type = Sentence.Type.PEERS

    peers: list = field(default_factory=list)

    @classmethod
    def load(cls, d):
        peers = cls()
        try:
            peers.peers = [Peer(address=peer['address'], port=peer['port']) for peer in d['peers']]
            return peers
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'peers': [peer.dict for peer in self.peers]
        }

    def __repr__(self):
        return super().__repr__()


@dataclass
class WantBlocks(Sentence):

    type: Sentence.Type = Sentence.Type.WANT_BLOCKS

    chain_id: str = ''
    from_height: int = 0
    to_height: int = 0

    @classmethod
    def load(cls, d):
        want_blocks = cls()
        try:
            want_blocks.chain_id = d['chain_id']
            want_blocks.from_height = d['from']
            want_blocks.to_height = d['to']
            return want_blocks
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'chain_id': self.chain_id,
            'from': self.from_height,
            'to': self.to_height
        }

    def __repr__(self):
        return super().__repr__()


@dataclass
class Blocks(Sentence):

    type: Sentence.Type = Sentence.Type.BLOCKS

    blocks: list = field(default_factory=list)

    @classmethod
    def load(cls, d):
        blocks = cls()
        try:
            blocks.blocks = [Block(data) for data in d['blocks']]
            blocks.blocks.sort(key=lambda e: e.height)
            return blocks
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'blocks': [block.dict for block in self.blocks]
        }

    def __repr__(self):
        return super().__repr__()


@dataclass
class NewBlock(Sentence):

    type: Sentence.Type = Sentence.Type.NEW_BLOCK

    chain_id: str = ''
    height: int = 0

    @classmethod
    def load(cls, d):
        new_block = cls()
        try:
            new_block.chain_id = d['chain_id']
            new_block.height = d['height']
            return new_block
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'chain_id': self.chain_id,
            'height': self.height
        }

    @property
    def boardcast(self):
        if self.message is None:
            self.message = Message(self.dict, Message.Type.BROADCAST)
        return self.message

    def __repr__(self):
        return super().__repr__()
