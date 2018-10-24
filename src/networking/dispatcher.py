from .message import Message
from typing import Any
from dataclasses import dataclass, field

from utils import log


@dataclass
class Dispatcher:
    handlers: dict = field(default_factory=dict)
    global_handler: Any = None

    def register(self, identifier, handler):
        self.handlers[identifier] = handler

    # TODO: May need a timeout to clean the handlers list
    async def dispatch(self, message: Message, peer):
        handler = self.handlers.get(message.identifier)
        if handler is not None:
            try:
                result = await handler(message, peer)
            except TypeError:
                result = handler(message, peer)
            if result:
                del self.handlers[message.identifier]
        elif self.global_handler is not None:
            await self.global_handler(message, peer)
        else:
            log.warning('Missing gloabel handler for receiving messages.')
