import random
import string
import asyncio

# from blockchain import Blockchain
from sharing import ShareManager, SentenceFactory


async def boardcast(chain):
    await ShareManager().broadcast(SentenceFactory.new_block(chain))


def create_block(chain, size=0):
    # chain = [chain for chain in Blockchain.all_chains() if chain.is_owner][0]
    # pre = ''.join(random.choice(['Cool', 'Nice', 'Great', 'Yeah', 'Gorgeous']))
    # suf = ''.join(random.choice('😎🤔😆🎉👍'))
    # block = chain.create_block({
    #     'title': 'Random Payload (' + ''.join(random.choices(string.hexdigits, k=6)) + ')',
    #     'content': pre + ' ' + suf,
    #     'filler': ''.join(random.choices(string.ascii_letters + string.digits, k=size))
    # })
    block = chain.create_block(''.join(random.choices(string.ascii_letters + string.digits, k=size)))
    chain.save_block(block)

    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(boardcast(chain))

    return block
