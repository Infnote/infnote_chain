import asyncio

from threading import Thread
from networking import Peer, Message, Server, PeerManager
from .sentence import Sentence, Info
from .factory import SentenceFactory as Factory

from utils.logger import default_logger as log


class ShareManager:
    def __init__(self):
        self.servers = [peer for peer in PeerManager().peers(without_self=True) if peer.address]
        self.clients = []
        self.boardcast_cache = {}

    def start(self):
        for peer in self.servers:
            peer.peer_in = self.peer_in
            peer.peer_out = self.peer_out
            Thread(target=peer.open).start()

        server = Server()
        server.peer_in = self.peer_in
        server.peer_out = self.peer_out
        Thread(target=server.start).start()

    def refresh(self):
        # TODO: need a connection strategy (when current connections is less then specific number)
        pass

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
        self.refresh()

    async def handle(self, message: Message, peer: Peer):
        if message.type == Message.Type.QUESTION:
            sentence = Factory.load(message.content)
            if sentence is not None:
                await self.answer(sentence, peer)

    async def answer(self, question, peer: Peer):
        log.debug(f'Legal Sentence:\n{question}')

        answer = None
        if question.type == Sentence.Type.NEW_BLOCK:
            wb = Factory.want_blocks_for_new_block(question)
            if wb is not None:
                await peer.send(wb.question)
            if self.boardcast_cache.get(question.message.identifer) is None:
                self.boardcast_cache[question.message.identifer] = question
                self.boardcast(question, peer)
            return
        elif question.type == Sentence.Type.INFO:
            answer = Info()
            if answer is not None:
                await peer.send(Info().to(question))
                for want_blocks in Factory.want_blocks_for_info(question):
                    await peer.send(want_blocks.question, lambda m: Factory.handle_blocks(Factory.load(m)))
                want_peers = Factory.want_peers_for_info(question)
                if want_peers is not None:
                    await peer.send(want_peers.question, lambda m: Factory.handle_peers(Factory.load(m)))
            return
        elif question.type == Sentence.Type.WANT_BLOCKS:
            answer = Factory.send_blocks(question)
        elif question.type == Sentence.Type.WANT_PEERS:
            answer = Factory.send_peers(question)

        if answer is not None:
            await peer.send(answer.to(question))

    def boardcast(self, sentence, without=None):
        log.debug(f'Boardcasting: {sentence}')
        for peer in self.servers:
            if peer is without:
                continue
            asyncio.get_event_loop().run_until_complete(peer.send(sentence.question))
