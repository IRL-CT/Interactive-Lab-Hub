"""Optional loopback-only test broker: pip install -r requirements-test.txt."""
import argparse
import asyncio
import logging
from amqtt.broker import Broker

async def run(port):
    broker = Broker({'listeners': {'default': {'type':'tcp','bind':f'127.0.0.1:{port}'}},
                     'plugins': {'amqtt.plugins.authentication.AnonymousAuthPlugin': {'allow_anonymous':True}}})
    await broker.start()
    try:
        await asyncio.Event().wait()
    finally:
        await broker.shutdown()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=18883)
    a = p.parse_args()
    logging.basicConfig(level=logging.ERROR)
    try: asyncio.run(run(a.port))
    except KeyboardInterrupt: pass
