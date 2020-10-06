#!/usr/bin/env python3

import asyncio

from bgp_event import BgpEvent
from bgp_fsm import BgpFsm


class BgpSession:
    def __init__(self, local_id, local_asn, local_hold_time, peer_ip, peer_asn, bgp_listeners=None, active=True, passive=True):
        """ Class constructor """

        self.local_id = local_id
        self.local_asn = local_asn
        self.local_hold_time = local_hold_time
        self.peer_ip = peer_ip
        self.peer_asn = peer_asn
        self.bgp_listeners = bgp_listeners

        self.active_fsm = None
        self.passive_fsm = None

        if active:
            asyncio.create_task(self.start_active_fsm())

        if passive:
            asyncio.create_task(self.start_passive_fsm())

    async def start_active_fsm(self):
        """ Active FSM coroutine """

        self.active_fsm = BgpFsm(self.local_id, self.local_asn, self.local_hold_time, self.peer_ip, self.peer_asn)
        await self.active_fsm.asyncio_init()
        self.active_fsm.enqueue_event(BgpEvent("Event 1: ManualStart"))

        while True:
            await asyncio.sleep(5)
            if self.active_fsm.state == "Idle":
                self.active_fsm.enqueue_event(BgpEvent("Event 3: AutomaticStart"))

    async def start_passive_fsm(self):
        """ Passive FSM coroutine """

        self.passive_fsm = BgpFsm(self.local_id, self.local_asn, self.local_hold_time, self.peer_ip, self.peer_asn)
        await self.passive_fsm.asyncio_init()
        self.passive_fsm.enqueue_event(BgpEvent("Event 4: ManualStart_with_PassiveTcpEstablishment"))
        self.bgp_listeners[self.peer_ip] = self.passive_fsm

        while True:
            await asyncio.sleep(5)
            if self.passive_fsm.state == "Idle":
                self.passive_fsm.enqueue_event(BgpEvent("Event 5: AutomaticStart_with_PassiveTcpEstablishment"))
                self.bgp_listeners[self.peer_ip] = self.passive_fsm
