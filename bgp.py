#!/usr/bin/env python3

import sys
import asyncio
import loguru

import bgp_message
from bgp_event import BgpEvent
from bgp_session import BgpSession


async def bgp_session_coroutine(local_id, local_asn, local_hold_time, peer_ip, peer_asn):
    """ Coroutine for the BGP session """

    session = BgpSession(local_id, local_asn, local_hold_time, peer_ip, peer_asn)
    await session.asyncio_init()
    session.event_queue.append(BgpEvent("Event 1: ManualStart"))

    while True:
        await asyncio.sleep(5)
        if session.state == "Idle":
            session.event_queue.append(BgpEvent("Event 3: AutomaticStart"))

async def run_sessions():
    asyncio.create_task(bgp_session_coroutine("192.168.9.201", 65000, 180, "192.168.9.202", 65000))
    asyncio.create_task(bgp_session_coroutine("192.168.9.201", 65000, 180, "192.168.9.203", 65000))
    asyncio.create_task(bgp_session_coroutine("192.168.9.201", 65000, 180, "192.168.9.204", 65000))

    while True:
        await asyncio.sleep(1)


def main():
    loguru.logger.remove(0)
    loguru.logger.add(sys.stdout, colorize=True, level="DEBUG", format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
            + f"|</level> <level>{{extra[peer_ip]:15}} | <normal><cyan>{{function:33}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>")

    asyncio.run(run_sessions())


if __name__ == "__main__":
    sys.exit(main())

