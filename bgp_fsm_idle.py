#!/usr/bin/env python3

import asyncio

import loguru

from bgp_event import BgpEvent


async def fsm_idle(self, event):
    """ Finite State Machine - Idle state """

    if (event.name == "Event 1: ManualStart"
            or (event.name == "Event 3: AutomaticStart" and self.allow_automatic_start)
    ):
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

        # Listen for a connection that may be initiated by the remote BGP peer
        self.start_server()

        # Change state to Connect
        self.change_state("Connect")

    if (event.name == "Event 4: ManualStart_with_PassiveTcpEstablishment"
            or (event.name == "Event 5: AutomaticStart_with_PassiveTcpEstablishment" and self.allow_automatic_start)
    ):
        self.logger.info(event.name)

        # Set the PassiveTcpEstablishment attribute to True
        self.passive_tcp_establishment = True

        # Initialize all BGP resources for the peer connection
        pass

        # Sets ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Starts the ConnectRetryTimer with the initial value
        self.connect_retry_timer = self.connect_retry_time

        # Listen for a connection that may be initiated by the remote BGP peer
        self.start_server()

        # Change state to Active
        self.change_state("Active")
