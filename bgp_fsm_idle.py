#!/usr/bin/env python3

import asyncio

import loguru

from bgp_event import BgpEvent


async def fsm_idle(self, event):
    """ Finite State Machine - Idle state """

    if event.name in {"Event 1: ManualStart", "Event 3: AutomaticStart"}:
        self.logger.info(event.name)

        # Initialize all BGP resources for the peer connection
        pass

        # Sets ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Starts the ConnectRetryTimer with the initial value
        self.connect_retry_timer = self.connect_retry_time

        # Initiate a TCP connection to the other BGP peer
        self.task_open_connection = asyncio.create_task(self.open_connection())
        await asyncio.sleep(0.001)

        # Change state to Connect
        self.change_state("Connect")

