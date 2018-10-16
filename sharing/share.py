import asyncio

from threading import Thread
from networking import Peer, Message, Server
from .sentence import Sentence, Info, SentenceFactory

from utils.logger import default_logger as log


class ShareManager:
    def __init__(self):
        self.servers = []
        self.clients = []

    def start(self):
        for peer in self.servers:
            peer.peer_in = self.peer_in
            peer.peer_out = self.peer_out
            Thread(target=peer.open).start()

        server = Server()
        server.peer_in = self.peer_in
        server.peer_out = self.peer_out
        Thread(target=server.start).start()

    async def peer_in(self, peer):
        log.info(f'Peer in : {peer}')
        peer.dispatcher.global_handler = self.handle
        if peer.is_server:
            await peer.send(Info().question)
        else:
            self.clients.append(peer)

    async def peer_out(self, peer):
        log.info(f'Peer out: {peer}')
        if peer.is_server:
            self.servers.remove(peer)
        else:
            self.clients.remove(peer)

    async def handle(self, message: Message, peer: Peer):
        if message.type == Message.Type.QUESTION:
            sentence = SentenceFactory.load(message.content)
            if sentence is not None:
                sentence.message = message
                await self.answer(sentence, peer)

    @staticmethod
    async def answer(sentence, peer):
        log.debug(f'Legal Sentence:\n{sentence}')

        answer = None
        msg = None
        if sentence.type == Sentence.Type.NEW_BLOCK:
            answer = SentenceFactory.respond_new_block(sentence)
            msg = answer.question
        elif sentence.type == Sentence.Type.WANT_BLOCKS:
            answer = SentenceFactory.respond_want_blocks(sentence)
            msg = answer.answer(sentence)
        elif sentence.type == Sentence.Type.WANT_PEERS:
            answer = SentenceFactory.respond_want_peers(sentence)
            msg = answer.answer(sentence)
        elif sentence.type == Sentence.Type.INFO:
            answer = Info()
            msg = answer.answer(sentence)

        if answer is not None and msg is not None:
            log.debug(f'Answering to {peer}:\n{answer}')
            await peer.send(msg)

    def boardcast(self, sentence):
        log.debug(f'Boardcasting: {sentence}')
        for peer in self.servers:
            asyncio.get_event_loop().run_until_complete(peer.send(sentence.question))
