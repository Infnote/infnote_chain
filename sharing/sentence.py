from enum import Enum
from dataclasses import dataclass, field
from networking import Message
from functools import reduce
from networking import Peer
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

    def answer(self, question):
        return Message(self.dict,
                       Message.Type.ERROR if self.type == Sentence.Type.ERROR else Message.Type.ANSWER,
                       question.message.identifer)

    def __repr__(self):
        max_width = reduce(lambda result, x: result if result > x else x, self.dict.keys(), 0)
        spaces = ' ' * max_width
        return reduce(lambda result, x: f'{result}[{x[0]}{spaces}] {x[1]}', self.dict, '')


@dataclass
class Info(Sentence):

    type: Sentence.Type = Sentence.Type.INFO

    version: str = '0.1'
    peers: int = 0
    chains: dict = field(default_factory=dict)
    platform: str = 'Python 3.7'
    is_full_node: bool = True

    def __post_init__(self):
        chains = Blockchain.all_chains()
        for chain in chains:
            self.chains[chain.id] = chain.height

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


@dataclass
class WantPeers(Sentence):

    type: Sentence.Type = Sentence.Type.WANT_PEERS

    count: int = 0

    @classmethod
    def load(cls, d):
        want_peers = cls()
        try:
            want_peers.count = d['count']
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'count': self.count
        }


@dataclass
class Peers(Sentence):

    type: Sentence.Type = Sentence.Type.PEERS

    peers: list = field(default_factory=list)

    @classmethod
    def load(cls, d):
        peers = cls()
        try:
            peers.peers = [Peer(address=peer['address'], port=peer['port']) for peer in d['peers']]
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'peers': [peer.dict for peer in self.peers]
        }


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


@dataclass
class Blocks(Sentence):

    type: Sentence.Type = Sentence.Type.BLOCKS

    blocks: list = field(default_factory=list)

    @classmethod
    def load(cls, d):
        blocks = cls()
        try:
            blocks.blocks = [Block(data) for data in d['blocks']]
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'blocks': [block.dict for block in self.blocks]
        }


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
        except (KeyError, ValueError):
            return None

    @property
    def dict(self):
        return {
            **super().dict,
            'chain_id': self.chain_id,
            'height': self.height
        }


class SentenceFactory:

    @staticmethod
    def load(d):
        t = d.get('type')
        if t is None:
            return None

        if t == 'info':
            return Info.load(d)
        elif t == 'error':
            return Error.load(d)
        elif t == 'want_peers':
            return WantPeers.load(d)
        elif t == 'peers':
            return Peers.load(d)
        elif t == 'want_blocks':
            return WantBlocks.load(d)
        elif t == 'blocks':
            return Blocks.load(d)
        elif t == 'new_block':
            return NewBlock.load(d)

        return None

    @staticmethod
    def respond_new_block(new_block: NewBlock) -> WantBlocks:
        pass

    @staticmethod
    def respond_want_blocks(want_blocks: WantBlocks):
        chain = Blockchain.load(want_blocks.chain_id)
        if chain is None:
            return None

        blocks = chain.get_blocks(want_blocks.from_height, want_blocks.to_height)
        if blocks is None:
            return None

        answer = Blocks()
        answer.blocks = blocks
        return answer

    @staticmethod
    def respond_want_peers(want_peers: WantPeers) -> Peers:
        pass

    @staticmethod
    def create_new_block(chain: Blockchain) -> NewBlock:
        response = NewBlock()
        response.chain_id = chain.id
        response.height = chain.height
        return response
