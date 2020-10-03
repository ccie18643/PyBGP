#!/usr/bin/env python3

import sys
import asyncio
import bgp_message

import loguru

from bgp_event import BgpEvent
from bgp_session import BgpSession


async def main():
    loguru.logger.remove(0)
    loguru.logger.add(sys.stdout, colorize=True, level="DEBUG", format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
            + f"|</level> <level>{{extra[peer_ip]:15}} | <normal><cyan>{{function:33}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>")

    session = BgpSession(local_id="192.168.9.201", local_asn=65000, local_hold_time=180, peer_ip="192.168.9.202", peer_asn=65000)

    session.event_queue.append(BgpEvent("Event 1: ManualStart"))

    while True:
        await asyncio.sleep(2)
        if session.state == "Idle":
            session.event_queue.append(BgpEvent("Event 2: AutomaticStart"))


if __name__ == "__main__":

    asyncio.run(main())


