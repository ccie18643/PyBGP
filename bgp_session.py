#!/usr/bin/env python3

import sys
import asyncio
import bgp_message

import loguru

from bgp_event import BgpEvent


class BgpSession():

    from bgp_timers import decrease_connect_retry_timer
    from bgp_timers import decrease_hold_timer
    from bgp_timers import decrease_keepalive_timer

    from bgp_network_io import open_connection
    from bgp_network_io import close_connection
    from bgp_network_io import send_keepalive_message
    from bgp_network_io import send_notification_message
    from bgp_network_io import send_open_message
    from bgp_network_io import send_update_message
    from bgp_network_io import message_input_loop

    from bgp_fsm_idle import fsm_idle
    from bgp_fsm_connect import fsm_connect
    from bgp_fsm_active import fsm_active
    from bgp_fsm_opensent import fsm_opensent
    from bgp_fsm_openconfirm import fsm_openconfirm
    from bgp_fsm_established import fsm_established

    def __init__(self, local_id, local_asn, local_hold_time, peer_ip, peer_asn):
        """ Class constructor """

        self.local_id = local_id
        self.local_asn = local_asn
        self.local_hold_time = local_hold_time
        self.peer_ip = peer_ip
        self.peer_asn = peer_asn

        self.event_queue = []

        self.reader = None
        self.writer = None

        self.state = "Idle"

        self.logger = loguru.logger.bind(peer_ip=self.peer_ip, state=self.state)

        self.connect_retry_time = 5

    async def asyncio_init(self):
        """ Start all coroutines and make sure they run before returning """

        asyncio.create_task(self.fsm())
        asyncio.create_task(self.decrease_hold_timer())
        asyncio.create_task(self.decrease_connect_retry_timer())
        asyncio.create_task(self.decrease_keepalive_timer())
        asyncio.create_task(self.message_input_loop())
        await asyncio.sleep(1)

    def enqueue_event(self, event):
        self.logger.opt(ansi=True, depth=1).debug(f"<cyan>[ENQ]</cyan> {event.name}")
        self.event_queue.append(event)

    def dequeue_event(self):
        event = self.event_queue.pop(0)
        self.logger.opt(ansi=True, depth=1).debug(f"<cyan>[DEQ]</cyan> {event.name}")
        return event

    def change_state(self, state):
        assert state in {"Idle", "Connect", "Active", "OpenSent", "OpenConfirm", "Established"}
        self.logger.info(f"State: {self.state} -> {state}")
        self.state = state
        self.logger = loguru.logger.bind(peer_ip=self.peer_ip, state=self.state)

    async def fsm(self):
        """ Finite State Machine loop """

        while True:
            if self.event_queue:
                event = self.dequeue_event()

                if self.state == "Idle":
                    await self.fsm_idle(event)
                
                if self.state == "Connect":
                    await self.fsm_connect(event)

                if self.state == "Active":
                    await self.fsm_active(event)

                if self.state == "OpenSent":
                    await self.fsm_opensent(event)

                if self.state == "OpenConfirm":
                    await self.fsm_openconfirm(event)

                if self.state == "Established":
                    await self.fsm_established(event)

            await asyncio.sleep(1)

