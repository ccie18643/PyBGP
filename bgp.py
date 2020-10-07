#!/usr/bin/env python3

import sys
import asyncio
import loguru

from bgp_event import BgpEvent
from bgp_session import BgpSession


BGP_LISTENERS = {}


async def bgp_broker(reader, writer):
    """ Evaluate incoming connection and send to BGP session if valid peer """

    peer = writer.get_extra_info("peername")
    passive_fsm = BGP_LISTENERS.pop(peer[0], None)

    if passive_fsm:
        passive_fsm.enqueue_event(BgpEvent("Event 17: TcpConnectionConfirmed", reader=reader, writer=writer, peer_ip=peer[0], peer_port=peer[1]))

    else:
        writer.close()
        await writer.wait_closed()


async def start_bgp_broker():
    """ Start listening for incomming BGP connections on port 179"""

    await asyncio.start_server(bgp_broker, "0.0.0.0", 179)


async def main():
    loguru.logger.remove(0)
    loguru.logger.add(
        sys.stdout,
        colorize=True,
        level="DEBUG",
        format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
        + f"|</level> <level>{{extra[peer]:21}} | <normal><cyan>{{function:33}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>",
    )

    await start_bgp_broker()

    BgpSession("1.1.1.1", 65000, 180, "192.168.9.202", 65000, bgp_listeners=BGP_LISTENERS, active_mode=True, passive_mode=True)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
