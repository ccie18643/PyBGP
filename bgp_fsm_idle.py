#!/usr/bin/env python3

"""

PyBGP, Python BGP implmentation version 0.1 - 2020, Sebastian Majewski
bgp_fsm_idle.py - module containing FSM class mthods responsible for handling Idle state

"""

import asyncio


async def fsm_idle(self, event):
    """ Finite State Machine - Idle state """

    if event.name == "Event 1: ManualStart" or (event.name == "Event 3: AutomaticStart" and self.allow_automatic_start):
        self.logger.info(event.name)

        # Sets ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Starts the ConnectRetryTimer with the initial value
        self.connect_retry_timer = self.connect_retry_time

        # Initiate a TCP connection to the other BGP peer
        self.task_open_connection = asyncio.create_task(self.open_connection())

        # Listen for a connection that may be initiated by the remote BGP peer
        pass

        # Change state to Connect
        self.change_state("Connect")

    if event.name == "Event 4: ManualStart_with_PassiveTcpEstablishment" or (
        event.name == "Event 5: AutomaticStart_with_PassiveTcpEstablishment" and self.allow_automatic_start
    ):
        self.logger.info(event.name)

        # Set the PassiveTcpEstablishment attribute to True
        self.passive_tcp_establishment = True

        # Sets ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Starts the ConnectRetryTimer with the initial value
        self.connect_retry_timer = self.connect_retry_time

        # Listen for a connection that may be initiated by the remote BGP peer
        pass

        # Change state to Active
        self.change_state("Active")
