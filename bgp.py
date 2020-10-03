#!/usr/bin/env python3

import sys
import asyncio
import loguru
import threading

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

def bgp_session_thread(local_id, local_asn, local_hold_time, peer_ip, peer_asn):
    """ Thread for the BGP session """

    asyncio.run(bgp_session_coroutine(local_id, local_asn, local_hold_time, peer_ip, peer_asn))


def main():
    loguru.logger.remove(0)
    loguru.logger.add(sys.stdout, colorize=True, level="DEBUG", format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
            + f"|</level> <level>{{extra[peer_ip]:15}} | <normal><cyan>{{function:33}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>")

    #threading.Thread(target=bgp_session_thread, args=("192.168.9.201", 65000, 180, "192.168.9.202", 65000)).start()
    #threading.Thread(target=bgp_session_thread, args=("192.168.9.201", 65000, 180, "192.168.9.20", 65000)).start()
    threading.Thread(target=bgp_session_thread, args=("192.168.9.201", 65000, 180, "222.222.222.222", 65000)).start()
    #threading.Thread(target=bgp_session_thread, args=("192.168.9.201", 65000, 180, "192.168.9.203", 65000)).start()
    #threading.Thread(target=bgp_session_thread, args=("192.168.9.201", 65000, 180, "192.168.9.204", 65000)).start()


if __name__ == "__main__":
    sys.exit(main())

