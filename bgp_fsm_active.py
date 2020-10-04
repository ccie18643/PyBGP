#!/usr/bin/env python3

import sys
import asyncio
import bgp_message

import loguru

from bgp_event import BgpEvent


async def fsm_active(self, event):
    """ Finite State Machine - Active state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # If the DelayOpenTimer is running and the
        # SendNOTIFICATIONwithoutOPEN session attribute is set, the
        # local system sends a NOTIFICATION with a Cease

        # Releases all BGP resources including stopping the DelayOpenTimer
        pass

        # Drop the TCP connection
        await self.close_connection()
        self.task_open_connection.cancel()

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Stop the ConnectRetryTimer and set ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 9: ConnectRetryTimer_Expires":
        self.logger.info(event.name)

        # Restart the ConnectRetryTimer
        self.connect_retry_timer = self.connect_retry_time

        # Continue to listen for a connection that may be initiated by the remote BGP peer
        pass

        if not self.passive_tcp_establishment:
            # Initiate a TCP connection to the other BGP peer
            self.task_open_connection = asyncio.create_task(self.open_connection())
            await asyncio.sleep(0.001)

            # Change state to  Connect
            self.change_state("Connect")

