#!/usr/bin/env python3

import asyncio
import loguru

import bgp_message

class BgpFsm:

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

        self.peer_port = 0

        self.peer_id = None

        self.event_queue = []
        self.event_serial_number = 0

        self.reader = None
        self.writer = None
        self.tcp_connection_established = False

        self.state = "Idle"
        self.connect_retry_counter = 0
        self.connect_retry_timer = 0
        self.connect_retry_time = 5
        self.hold_timer = 0
        self.hold_time = 0
        self.keepalive_timer = 0
        self.keepalive_time = 0

        self.accept_connections_unconfigured_peers = False
        self.allow_automatic_start = True
        self.allow_automatic_stop = True
        self.collision_detect_established_state = False
        self.damp_peer_oscillations = False
        self.delay_open = False
        self.delay_open_time = 0
        self.delay_open_timer = 0
        self.idle_hold_time = 0
        self.idle_hold_timer = 0
        self.passive_tcp_establishment = False
        self.send_notification_without_open = False
        self.track_tcp_state = False

        self.logger = loguru.logger.bind(peer=f"{self.peer_ip}:{self.peer_port}", state=self.state)

        self.connect_retry_time = 5

        self.task_fsm = asyncio.create_task(self.fsm())
        self.task_decrease_hold_timer = asyncio.create_task(self.decrease_hold_timer())
        self.task_decrease_connect_retry_timer = asyncio.create_task(self.decrease_connect_retry_timer())
        self.task_decrease_keepalive_timer = asyncio.create_task(self.decrease_keepalive_timer())
        self.task_message_input_loop = asyncio.create_task(self.message_input_loop())

    def __del__(self):
        """ Class destructor """

        self.close_connection()
        self.task_fsm.cancel()
        self.task_decrease_hold_timer.cancel()
        self.task_decrease_connect_retry_timer.cancel()
        self.task_decrease_keepalive_timer.cancel()
        self.task_message_input_loop.cancel()

    def enqueue_event(self, event):
        """ Add new event to the event queue """

        # Add serial number to event for ease of debuging
        self.event_serial_number += 1

        if self.event_serial_number > 65535:
            event_serial_number = 1

        event.serial_number = self.event_serial_number

        # In case Stop event is being enqueued flush the queue to expedite it
        if event.name in {"Event 2: ManualStop", "Event 8: AutomaticStop"}:
            self.event_queue.clear()
        self.event_queue.append(event)

        self.logger.opt(ansi=True, depth=1).debug(f"<cyan>[ENQ]</cyan> {event.name} [#{event.serial_number}]")

    def dequeue_event(self):
        """ Pick an event from the event queue """

        event = self.event_queue.pop(0)
        self.logger.opt(ansi=True, depth=1).debug(f"<cyan>[DEQ]</cyan> {event.name} [#{event.serial_number}]")
        return event

    def change_state(self, state):
        """ Change FSM state """

        assert state in {"Idle", "Connect", "Active", "OpenSent", "OpenConfirm", "Established"}

        self.logger.opt(depth=1).info(f"State: {self.state} -> {state}")
        self.state = state

        self.logger = loguru.logger.bind(peer=f"{self.peer_ip}:{self.peer_port}", state=self.state)

        if self.state == "Idle":
            self.connect_retry_timer = 0
            self.keepalive_timer = 0
            self.hold_timer = 0
            self.peer_port = 0
            self.close_connection()

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
