import asyncio
import websockets

from typing import Any
from dataclasses import dataclass
from .peer import Peer


@dataclass
class Server:
    peer_in: Any = None
    peer_out: Any = None

    def start(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(self.handle, '0.0.0.0', '8080')
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    async def handle(self, socket, _):
        peer = Peer.from_client(socket)
        peer.peer_in = self.peer_in
        peer.peer_out = self.peer_out
        await peer.catched()
