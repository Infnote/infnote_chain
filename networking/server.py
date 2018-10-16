import asyncio
import websockets

from typing import Any
from dataclasses import dataclass
from .peer import Peer

from utils import settings
from utils.logger import default_logger as log


@dataclass
class Server:
    peer_in: Any = None
    peer_out: Any = None

    def start(self):
        log.info(f'Start server {settings.server.address}:{settings.server.port}')
        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(self.handle, '0.0.0.0', settings.server.port)
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    async def handle(self, socket, _):
        peer = Peer.from_client(socket)
        peer.peer_in = self.peer_in
        peer.peer_out = self.peer_out
        await peer.catched()
