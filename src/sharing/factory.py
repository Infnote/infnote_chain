import requests

from .sentence import *
from typing import Optional
from networking import PeerManager
from utils.settings import settings


class SentenceFactory:

    @staticmethod
    def load(message: Message):
        d = message.content
        t = d.get('type')
        if t is None:
            return None

        result = None
        if t == Sentence.Type.INFO.value:
            result = Info.load(d)
        elif t == Sentence.Type.ERROR.value:
            result = Error.load(d)
        elif t == Sentence.Type.WANT_PEERS.value:
            result = WantPeers.load(d)
        elif t == Sentence.Type.PEERS.value:
            result = Peers.load(d)
        elif t == Sentence.Type.WANT_BLOCKS.value:
            result = WantBlocks.load(d)
        elif t == Sentence.Type.BLOCKS.value:
            result = Blocks.load(d)
        elif t == Sentence.Type.NEW_BLOCK.value:
            result = NewBlock.load(d)
        elif t == Sentence.Type.TRANSACTION.value:
            result = Transaction.load(d)

        if result is not None:
            result.message = message
            return result
        return None

    @staticmethod
    def want_blocks(chain_id, start, end) -> WantBlocks:
        r = WantBlocks()
        r.chain_id = chain_id
        r.from_height = start
        r.to_height = end
        return r

    @classmethod
    def want_blocks_for_new_block(cls, new_block: NewBlock) -> Optional[WantBlocks]:
        chain = Blockchain.load(new_block.chain_id)
        if chain is not None:
            if chain.height < new_block.height:
                return cls.want_blocks(new_block.chain_id, chain.height, new_block.height - 1)
        elif new_block.height > 0:
            return cls.want_blocks(new_block.chain_id, 0, new_block.height - 1)
        return None

    @classmethod
    def want_blocks_for_info(cls, info: Info) -> list:
        result = []
        for chain_id, height in info.chains.items():
            chain = Blockchain.load(chain_id)
            if chain is None:
                if height > 0:
                    result.append(cls.want_blocks(chain_id, 0, height - 1))
            elif chain.height < height:
                result.append(cls.want_blocks(chain_id, chain.height, height - 1))
        return result

    @classmethod
    def want_peers_for_info(cls, info: Info) -> Optional[WantPeers]:
        if info.peers > 0:
            return WantPeers(count=info.peers)
        return None

    @staticmethod
    def send_blocks(want_blocks: WantBlocks):
        chain = Blockchain.load(want_blocks.chain_id)
        if chain is None:
            return None

        blocks = chain.get_blocks(want_blocks.from_height, want_blocks.to_height)
        if blocks is None:
            return None

        # make every sentence size as large as possible but less than 1.5MB
        answer = []
        size = 0
        tmp = []
        for block in blocks:
            if block.size + size > 2**20 * 1.5:
                answer.append(Blocks(blocks=list(tmp), end=False))
                tmp = [block]
                size = 0
            else:
                size += block.size
                tmp.append(block)
        if len(tmp) > 0:
            answer.append(Blocks(blocks=list(tmp), end=True))
        answer[-1].end = True
        return answer

    @staticmethod
    def send_peers(want_peers: WantPeers) -> Optional[Peers]:
        peers = []
        for peer in PeerManager().peers(want_peers.count):
            peers.append(peer)
        if len(peers) <= 0:
            return None

        response = Peers()
        response.peers = peers
        return response

    @staticmethod
    def new_block(chain: Blockchain) -> NewBlock:
        response = NewBlock()
        response.chain_id = chain.id
        response.height = chain.height
        return response

    @staticmethod
    def handle_peers(peers: Peers):
        if peers is None:
            return

        # TODO: need a better peers updating strategy
        for peer in peers.peers:
            PeerManager().add_peer(peer)

    @staticmethod
    def handle_blocks(blocks: Blocks):
        if blocks is None:
            return

        # TODO: need to mark bad chain (when there is two blocks which have same height)
        for block in blocks.blocks:
            Blockchain.remote_chain(block.chain_id).save_block(block)

        try:
            requests.get(settings.hooks.new_block)
        except Exception:
            pass

    @staticmethod
    def transaction(payload):
        transaction = Transaction()
        transaction.chain_id = payload.chain_id
        transaction.payload = payload.content
        return transaction
