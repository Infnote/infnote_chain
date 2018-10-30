# import random
# import string
import asyncio

from threading import Thread
from datetime import datetime
# from blockchain import Blockchain
from sharing import ShareManager, SentenceFactory
from utils import log


async def boardcast(chain):
    await ShareManager().broadcast(SentenceFactory.new_block(chain))


def create_block(chain, payload):
    # chain = [chain for chain in Blockchain.all_chains() if chain.is_owner][0]
    # pre = ''.join(random.choice(['Cool', 'Nice', 'Great', 'Yeah', 'Gorgeous']))
    # suf = ''.join(random.choice('😎🤔😆🎉👍'))
    # block = chain.create_block({
    #     'title': 'Random Payload (' + ''.join(random.choices(string.hexdigits, k=6)) + ')',
    #     'content': pre + ' ' + suf,
    #     'filler': ''.join(random.choices(string.ascii_letters + string.digits, k=size))
    # })

    # start = datetime.utcnow()
    # payload = ''.join(random.choices(string.ascii_letters + string.digits, k=size))
    # end = datetime.utcnow()
    # log.info("Generate %d bytes random payload in %.03f secs" % (size, (end - start).total_seconds()))

    start = datetime.utcnow()
    block = chain.create_block(payload)
    end = datetime.utcnow()
    log.info("Create a random content block in %.03f secs" % (end - start).total_seconds())

    start = datetime.utcnow()
    if not chain.save_block(block):
        return None
    end = datetime.utcnow()
    log.info("Validate & Save a random content block in %.03f secs" % (end - start).total_seconds())

    def __b():
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(boardcast(chain))
    Thread(target=__b).start()

    return block
