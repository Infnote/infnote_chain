from .message import Message
from typing import Any
from dataclasses import dataclass, field

from utils.logger import default_logger as log


@dataclass
class Dispatcher:
    handlers: dict = field(default_factory=dict)
    global_handler: Any = None

    def register(self, identifer, handler):
        self.handlers[identifer] = handler

    async def dispatch(self, message: Message, peer):
        handler = self.handlers.get(message.identifer)
        if handler is not None:
            try:
                await handler(message, peer)
            except TypeError:
                handler(message, peer)
            del self.handlers[message.identifer]
        elif self.global_handler is not None:
            await self.global_handler(message, peer)
        else:
            log.warn('Missing gloabel handler for receiving messages.')
