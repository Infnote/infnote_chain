import asyncio

from threading import Thread
from dataclasses import dataclass, field
from networking import Peer, Message, Server
from .sentence import Sentence, Info, SentenceFactory


@dataclass
class ShareManager:
    peers: list = field(default_factory=list)

    def start(self):
        for peer in self.peers:
            peer.peer_in = self.peer_in
            peer.peer_out = self.peer_out
            Thread(target=peer.open).start()

        server = Server()
        server.peer_in = self.peer_in
        server.peer_out = self.peer_out
        Thread(target=server.start).start()

    async def peer_in(self, peer):
        print(f'Peer in : {peer}')
        peer.dispatcher.global_handler = self.handle
        if not peer.is_server:
            self.peers.append(peer)
        else:
            await peer.send(Info().question)

    async def peer_out(self, peer):
        print(f'Peer out: {peer}')
        self.peers.remove(peer)

    async def handle(self, message: Message, peer: Peer):
        if message.type == Message.Type.QUESTION:
            sentence = SentenceFactory.load(message.content)
            if sentence is not None:
                sentence.message = message
                await self.answer(sentence, peer)

    @staticmethod
    async def answer(sentence, peer):
        if sentence.type == Sentence.Type.NEW_BLOCK:
            await peer.send(SentenceFactory.respond_new_block(sentence).question)
        elif sentence.type == Sentence.Type.WANT_BLOCKS:
            answer = SentenceFactory.respond_want_blocks(sentence)
            if answer is not None:
                await peer.send(answer.answer(sentence))
        elif sentence.type == Sentence.Type.WANT_PEERS:
            await peer.send(SentenceFactory.respond_want_peers(sentence).answer(sentence))
        elif sentence.type == Sentence.Type.INFO:
            await peer.send(Info().answer(sentence))

    def boardcast(self, sentence):
        for peer in self.peers:
            asyncio.get_event_loop().run_until_complete(peer.send(sentence.question))
