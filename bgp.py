#!/usr/bin/env python3

import sys
import asyncio
import loguru

import bgp_message
from bgp_event import BgpEvent
from bgp_session import BgpSession


INBOUND_LISTENER_REGISTER = {}

async def connection_broker(reader, writer):
    """ Evaluate incoming connection and send to BGP session if valid peer """

    peer = writer.get_extra_info("peername")
    session = INBOUND_LISTENER_REGISTER.get(peer[0], None)

    if session:
        session.enqueue_event(BgpEvent("Event 17: TcpConnectionConfirmed", reader=reader, writer=writer))

    else:
        writer.close()
        await writer.wait_closed()


async def start_server():
    """ Start listening for incomming connections """

    #loguru.logger.opt(depth=0).debug(f"Starting to listen on port 179/TCP")

    server = await asyncio.start_server(connection_broker, "0.0.0.0", 179)


async def bgp_session_coroutine(local_id, local_asn, local_hold_time, peer_ip, peer_asn):
    """ Coroutine for the BGP session """

    session = BgpSession(local_id, local_asn, local_hold_time, peer_ip, peer_asn, INBOUND_LISTENER_REGISTER)
    await session.asyncio_init()
    session.enqueue_event(BgpEvent("Event 1: ManualStart"))
    #session.enqueue_event(BgpEvent("Event 4: ManualStart_with_PassiveTcpEstablishment"))

    while True:
        await asyncio.sleep(5)
        if session.state == "Idle":
            session.enqueue_event(BgpEvent("Event 3: AutomaticStart"))
            #session.enqueue_event(BgpEvent("Event 5: AutomaticStart_with_PassiveTcpEstablishment"))


async def main():
    loguru.logger.remove(0)
    loguru.logger.add(sys.stdout, colorize=True, level="DEBUG", format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
            + f"|</level> <level>{{extra[peer_ip]:15}} | <normal><cyan>{{function:33}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>")

    await start_server()

    asyncio.create_task(bgp_session_coroutine("192.168.9.201", 65000, 180, "192.168.9.202", 65000))
    
    #asyncio.create_task(bgp_session_coroutine("192.168.9.201", 65000, 180, "192.168.9.203", 65000))
    #asyncio.create_task(bgp_session_coroutine("192.168.9.201", 65000, 180, "192.168.9.204", 65000))


    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())

