#!/usr/bin/env python3

import sys
import asyncio
import bgp_message

import loguru

from bgp_event import BgpEvent


async def fsm_connect(self, event):
    """ Finite State Machine - Connect state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # Drop the TCP connection
        await self.close_connection()
        self.task_open_connection.cancel()

        # Releases all BGP resources
        pass

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Stop the ConnectRetryTimer and set ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Stop to listen for a connection that may be initiated by the remote BGP peer
        self.stop_server()

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 9: ConnectRetryTimer_Expires":
        self.logger.info(event.name)

        # Drop the TCP connection
        self.task_open_connection.cancel()

        # Restart the ConnectRetryTimer
        self.connect_retry_timer = self.connect_retry_time

        # Stop the DelayOpenTimer
        pass

        # Initiate a TCP connection to the other BGP peer
        self.task_open_connection = asyncio.create_task(self.open_connection())
        await asyncio.sleep(0.001)

        # Continue to listen for a connection that may be initiated by the remote BGP peer
        pass

        # Stay in the Connect state
        pass

    if event.name in {"Event 16: Tcp_CR_Acked", "Event 17: TcpConnectionConfirmed"}:
        self.logger.info(event.name)

        # Take an ownership of the connection
        self.reader = event.reader
        self.writer = event.writer
        self.connection_active = True

        # Stop the ConnectRetryTimer and set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Complete BGP initialization
        pass

        # Send an open message to the peer
        await self.send_open_message()

        # Set the holdtimer to a large value, holdtimer value of 4 minutes is suggested
        self.hold_timer = 240

        ##### ??? #####
        # Stop to listen for a connection that may be initiated by the remote BGP peer
        self.stop_server()

        # Changes state to OpenSent
        self.change_state("OpenSent")

    if event.name == "Event 18: TcpConnectionFails":
        self.logger.info(event.name)

        # Stop the ConnectRetryTimer
        self.connect_retry_timer = 0

        # Drop the TCP connection
        await self.close_connection()

        # Release all BGP resouces
        pass

        # Stop to listen for a connection that may be initiated by the remote BGP peer
        self.stop_server()

        # Change state to Idle
        self.change_state("Idle")

    if event.name in {"Event 21: BGPHeaderErr", "Event 22: BGPOpenMsgErr"}:
        self.logger.info(event.name)

        message = event.message

        # If the SendNOTIFICATIONwithoutOPEN attribute is set to TRUE, then the local system
        # sends a NOTIFICATION message with the appropriate error code
        if self.send_notification_without_open:
            await self.send_notification_message(message.message_error_code, message.message_error_subcode, message.message_error_data)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Release all BGP resources
        pass

        # Set HoldTimer to zero (not required by RFC4271)
        self.hold_timer = 0

        # Drop the TCP connection
        await self.close_connection()

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Stop to listen for a connection that may be initiated by the remote BGP peer
        self.stop_server()

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 24: NotifMsgVerErr":
        self.logger.info(event.name)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Set HoldTimer to zero (not required by RFC4271)
        self.hold_timer = 0

        # Release all bgp resources
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Stop to listen for a connection that may be initiated by the remote BGP peer
        self.stop_server()

        # Change state to Idle
        self.change_state("Idle")

    if event.name in {"Event 8: AutomaticStop", "Event 10: HoldTimer_Expires", "Event 11: KeepaliveTimer_Expires",
                      "Event 13: IdleHoldTimer_Expires", "Event 19: BGPOpen", "Event 23: OpenCollisionDump",
                      "Event 25: NotifMsg", "Event 26: KeepAliveMsg", "Event 27: UpdateMsg", "Event 28: UpdateMsgErr"}:
            
        # If the ConnectRetryTimer is running, stop and reset the ConnectRetryTimer (set to zero)
        self.connect_retry_timer = 0

        # If the DelayOpenTimer is running, stop and reset the DelayOpenTimer (set to zero)
        pass

        # Release all BGP resources
        pass

        # Drop the TCP connection
        await self.close_connection()
        self.task_open_connection.cancel()

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Stop to listen for a connection that may be initiated by the remote BGP peer
        self.stop_server()

        # Change state to Idle
        self.change_state("Idle")

