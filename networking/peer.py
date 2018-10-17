import asyncio
import websockets
import websockets.client

from .message import Message
from .dispatcher import Dispatcher
from dataclasses import dataclass
from typing import Any
from utils import Singleton, settings
from pymongo import MongoClient, ASCENDING, DESCENDING

from utils.logger import default_logger as log


@dataclass
class Peer:
    address: str
    port: int = 80
    rank: int = 100
    socket: Any = None
    dispatcher: Dispatcher = Dispatcher()
    is_server: bool = True
    peer_in: Any = None
    peer_out: Any = None

    @property
    def dict(self):
        return {
            'address': self.address,
            'port': self.port
        }

    @classmethod
    def from_client(cls, socket):
        address, port = socket.remote_address
        peer = cls(address, port)
        peer.socket = socket
        peer.is_server = False
        return peer

    def open(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self.catched())

    async def catched(self):
        try:
            await self.__open()
        except OSError:
            log.debug(f'Failed to connect {self}')
        except websockets.ConnectionClosed:
            log.debug(f'Disconnected from {self}')
        finally:
            if self.peer_out is not None:
                await self.peer_out(self)

    async def __open(self):
        if not self.is_server:
            if self.peer_in is not None:
                await self.peer_in(self)
            await self.recv()
            return
        host = f'ws://{self.address}:{self.port}'
        async with websockets.connect(host) as socket:
            self.socket = socket
            if self.peer_in is not None:
                await self.peer_in(self)
            await self.recv()

    async def send(self, message: Message, callback=None):
        if callback is not None:
            self.dispatcher.register(message.identifer, callback)
        log.debug(f'Sending: {message} to {self}')
        await self.socket.send(message.dump())

    async def recv(self):
        async for data in self.socket:
            msg = Message.load(data)
            if msg is not None:
                log.debug(f'Received: {msg} from {self}')
                await self.dispatcher.dispatch(msg, self)
            else:
                log.warn(f'Bad message:\n{data}')
                self.rank -= 1

    def __repr__(self):
        return f'<Peer{"(Server)" if self.is_server else ""}: {self.address}:{self.port} (rank: {self.rank})>'


class PeerManager(metaclass=Singleton):

    def __init__(self):
        db_settings = settings.database
        self.database = MongoClient(db_settings.host, db_settings.port)[db_settings.name]

    @property
    def count(self) -> int:
        return len(self.all_peers())

    def all_peers(self) -> [Peer]:
        return [Peer(peer['address'], peer['port'], peer['rank']) for peer in self.database.peers.find()]

    def peers(self, count=10, without_self=False) -> [Peer]:
        query = {}
        if without_self:
            query['address'] = {
                '$nin': [settings.server.address, '0.0.0.0', 'localhost', '127.0.0.1']
            }
        result = self.database.peers.find(query).sort('rank', DESCENDING).limit(count)
        return [Peer(peer['address'], peer['port'], peer['rank']) for peer in result]

    def add_peer(self, peer: Peer):
        return self.database.peers.update_one(
            {'address': peer.address},
            {'$set': {'address': peer.address, 'port': peer.port, 'rank': peer.rank}},
            upsert=True
        )

    def migrate(self):
        log.info('Create index for "address" in "peers".')
        self.database.peers.create_index([('address', ASCENDING)], unique=True)
        log.info(f'Add this host as a peer to "peers" ({settings.server.address}:{settings.server.port}).')
        self.database.peers.update_one(
            {'address': settings.server.address},
            {'$set': {'address': settings.server.address, 'port': settings.server.port, 'rank': 100}},
            upsert=True
        )

    def __repr__(self):
        result = self.database.peers.aggregate(
            [{
                '$group': {
                    '_id': '$by_user',
                    'rank': {
                        '$avg': '$rank'
                    }
                }
            }]
        )
        arrange_rank = list(result)[0]['rank']
        return "<PeerManager: %d peers, rank %.02f(avg.)>" % (self.count, arrange_rank)
