from threading import Thread, Timer
from networking import Peer, Message, Server, PeerManager
from .sentence import Sentence, Info
from .factory import SentenceFactory as Factory

from utils import settings, Singleton
from utils.logger import default_logger as log


class ShareManager(metaclass=Singleton):
    def __init__(self):
        self.servers = [peer for peer in PeerManager().peers(without_self=True) if peer.address]
        self.clients = []
        self.broadcast_cache = {}

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

    def retry(self, peer):
        if peer.retry_count >= settings.peers.retry:
            self.servers.remove(peer)
            self.refresh()
        elif peer not in self.clients:
            secs = (peer.retry_count + 1) ** 4
            log.warning(f'Retry after {secs} secs.')
            Timer(secs, peer.open).start()

    async def peer_in(self, peer):
        log.info(f'Peer in : {peer}')
        peer.dispatcher.global_handler = self.handle
        if peer.is_server:
            await peer.send(Info().question)
        else:
            self.clients.append(peer)

    async def peer_out(self, peer):
        if peer.is_server:
            log.warning(f'Peer out: {peer}')
            peer.rank -= 1
            peer.retry_count += 1
            peer.save()
            self.retry(peer)
        else:
            log.info(f'Peer out: {peer}')
            self.clients.remove(peer)

    async def handle(self, message: Message, peer: Peer):
        sentence = Factory.load(message)
        if sentence is None:
            log.warning(f'Bad sentence:\n{message.content}')

        log.debug(f'{peer} said:\n{sentence}')
        if message.type == Message.Type.QUESTION:
            await self.handle_question(sentence, peer)
        elif message.type == Message.Type.ANSWER:
            await self.handle_anwser(sentence, peer)
        elif message.type == Message.Type.BROADCAST:
            await self.handle_broadcast(sentence, peer)

    async def handle_question(self, question, peer: Peer):
        answer = None
        if question.type == Sentence.Type.INFO:
            answer = Info()
            await self.info_actions(question, peer)
        elif question.type == Sentence.Type.WANT_BLOCKS:
            answer = Factory.send_blocks(question)
            for block in answer:
                await self.send_answer(block, question, peer)
            return
        elif question.type == Sentence.Type.WANT_PEERS:
            answer = Factory.send_peers(question)

        if answer is not None:
            await self.send_answer(answer, question, peer)

    async def handle_anwser(self, answer, peer: Peer):
        if answer.type == Sentence.Type.INFO:
            await self.info_actions(answer, peer)
        elif answer.type == Sentence.Type.BLOCKS:
            Factory.handle_blocks(answer)
        elif answer.type == Sentence.Type.PEERS:
            Factory.handle_peers(answer)

    async def handle_broadcast(self, sentence, peer):
        last = self.broadcast_cache.get(sentence.message.identifier)
        if sentence.type == Sentence.Type.NEW_BLOCK and last is None:
            self.broadcast_cache[sentence.message.identifier] = sentence

            wb = Factory.want_blocks_for_new_block(sentence)
            if wb is not None:
                async def handle_blocks(msg, p):
                    await self.handle(msg, p)
                    sen = Factory.load(msg)
                    if sen.type == Sentence.Type.BLOCKS and sen.end:
                        await self.broadcast(sentence, peer)
                        return True
                await self.send_question(wb, peer, handle_blocks)

    async def broadcast(self, sentence, without=None):
        self.broadcast_cache[sentence.boardcast.identifier] = sentence

        log.debug(f'Broadcasting:\n{sentence}')
        for peer in self.servers + self.clients:
            if without is not None and peer.address == without.address and peer.port == without.port:
                continue
            await peer.send(sentence.boardcast)
            log.debug(f'Broadcast sent to {peer}')

    async def info_actions(self, info: Info, peer: Peer):
        if isinstance(info, Message):
            info = Factory.load(info)
        if info is None:
            return

        for want_blocks in Factory.want_blocks_for_info(info):
            await self.send_question(want_blocks, peer)

        if settings.peers.sync:
            want_peers = Factory.want_peers_for_info(info)
            if want_peers is not None:
                await self.send_question(want_peers, peer)

    @staticmethod
    async def send_question(question: Sentence, to: Peer, callback=None):
        log.debug(f'Ask to {to}:\n{question}')
        await to.send(question.question, callback)

    @staticmethod
    async def send_answer(answer: Sentence, question: Sentence, to: Peer):
        log.debug(f'Reply to {to}:\n{answer}')
        await to.send(answer.to(question))
