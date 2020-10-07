#!/usr/bin/env python3

import asyncio
import struct
import socket
import loguru

from bgp_event import BgpEvent
from bgp_fsm import BgpFsm


class BgpSession:
    def __init__(self, local_id, local_asn, local_hold_time, peer_ip, peer_asn, bgp_listeners=None, active_mode=True, passive_mode=True):
        """ Class constructor """

        self.local_id = local_id
        self.local_asn = local_asn
        self.local_hold_time = local_hold_time
        self.peer_ip = peer_ip
        self.peer_asn = peer_asn
        self.bgp_listeners = bgp_listeners
        self.active_mode = active_mode
        self.passive_mode = passive_mode

        self.active_fsm = None
        self.passive_fsm = None

        self.active_fsm = BgpFsm(self.local_id, self.local_asn, self.local_hold_time, self.peer_ip, self.peer_asn)
        self.passive_fsm = BgpFsm(self.local_id, self.local_asn, self.local_hold_time, self.peer_ip, self.peer_asn)

        asyncio.create_task(self.connection_state_tracking())
        asyncio.create_task(self.connection_collision_detection())

    async def connection_state_tracking(self):
        """ Restart both connections if both of them are in Idle state """

        await asyncio.sleep(1)

        while True:
            if self.active_mode and self.active_fsm.state == "Idle" and self.passive_fsm.state != "Established":
                self.active_fsm.enqueue_event(BgpEvent("Event 3: AutomaticStart"))

            if self.passive_mode and self.passive_fsm.state == "Idle" and self.active_fsm.state != "Established":
                self.passive_fsm.enqueue_event(BgpEvent("Event 5: AutomaticStart_with_PassiveTcpEstablishment"))
                self.bgp_listeners[self.peer_ip] = self.passive_fsm

            await asyncio.sleep(10)

    async def connection_collision_detection(self):
        """ Perform collision detection and shutdown non preffered connection """

        self.logger = loguru.logger.bind(peer=self.peer_ip, state="")

        await asyncio.sleep(1)

        while True:

            if self.active_fsm.state != "Idle" and self.passive_fsm.state != "Idle":

                if self.active_fsm.state == "Established" and self.passive_fsm.state != "Established":
                    self.logger.debug("Collision detection E/!E - Closing passive connection")
                    self.passive_fsm.enqueue_event(BgpEvent("Event 8: AutomaticStop"))

                if self.passive_fsm.state == "Established" and self.active_fsm.state != "Established":
                    self.logger.debug("Collision detection !E/E - Closing active connection")
                    self.active_fsm.enqueue_event(BgpEvent("Event 8: AutomaticStop"))

                if self.active_fsm.state == "OpenConfirm" and self.passive_fsm.state == "OpenConfirm":
                    if struct.unpack("!L", socket.inet_aton(self.local_id))[0] > struct.unpack("!L", socket.inet_aton(self.active_fsm.peer_id))[0]:
                        self.logger.debug("Collision detection OC/OC LID > PID - Closing passive connection")
                        self.passive_fsm.enqueue_event(BgpEvent("Event 8: AutomaticStop"))
                    else:
                        self.logger.debug("Collision detection OC/OC LID < PID - Closing active connection")
                        self.active_fsm.enqueue_event(BgpEvent("Event 8: AutomaticStop"))

            await asyncio.sleep(1)

