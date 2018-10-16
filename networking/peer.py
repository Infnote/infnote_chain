import asyncio
import websockets
import websockets.client

from .message import Message
from .dispatcher import Dispatcher
from dataclasses import dataclass
from typing import Any


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
            print(f'Failed to connect {self}')
        except websockets.ConnectionClosed:
            print(f'Disconnected from {self}')
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
        await self.socket.send(message.dump())

    async def recv(self):
        async for data in self.socket:
            msg = Message.load(data)
            if msg is not None:
                await self.dispatcher.dispatch(msg, self)
            else:
                self.rank -= 1

    def __repr__(self):
        return f'<Peer: ws://{self.address}:{self.port} (rank: {self.rank})>'
