#!/usr/bin/env python3

############################################################################
#                                                                          #
#  PyBGP - Python BGP implementation                                       #
#  Copyright (C) 2020  Sebastian Majewski                                  #
#                                                                          #
#  This program is free software: you can redistribute it and/or modify    #
#  it under the terms of the GNU General Public License as published by    #
#  the Free Software Foundation, either version 3 of the License, or       #
#  (at your option) any later version.                                     #
#                                                                          #
#  This program is distributed in the hope that it will be useful,         #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#  GNU General Public License for more details.                            #
#                                                                          #
#  You should have received a copy of the GNU General Public License       #
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                          #
#  Author's email: ccie18643@gmail.com                                     #
#  Github repository: https://github.com/ccie18643/PyBGP                   #
#                                                                          #
############################################################################


import asyncio
import sys

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
    """ Start listening for incoming BGP connections on port 179"""

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

    BgpSession(
        local_id="1.1.1.1",
        local_asn=65101,
        local_hold_time=180,
        peer_ip="192.168.9.201",
        peer_asn=65201,
        bgp_listeners=BGP_LISTENERS,
        active_mode=True,
        passive_mode=True,
    )

    """
    BgpSession(
        local_id="1.1.1.1",
        local_asn=65000,
        local_hold_time=180,
        peer_ip="192.168.9.203",
        peer_asn=65000,
        bgp_listeners=BGP_LISTENERS,
        active_mode=True,
        passive_mode=True,
    )

    BgpSession(
        local_id="1.1.1.1",
        local_asn=65000,
        local_hold_time=180,
        peer_ip="192.168.9.204",
        peer_asn=65000,
        bgp_listeners=BGP_LISTENERS,
        active_mode=True,
        passive_mode=True,
    )
    """

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
