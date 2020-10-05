#!/usr/bin/env python3

import asyncio
import bgp_message

import loguru

from bgp_event import BgpEvent


async def fsm_established(self, event):
    """ Finite State Machine - Established state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # Send the NOTIFICATION with a Cease
        await self.send_notification_message(6)

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Set HoldTimer to zero (not required by RFC4271)
        self.hold_timer = 0

        # Delete all routes associated with this connection
        pass

        # Releases all BGP resources
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 10: HoldTimer_Expires":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with the error code Hold Timer Expired
        await self.send_notification_message(4)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Release all BGP resources
        pass

        # Drop the TCP connection
        self.close_connection()

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 11: KeepaliveTimer_Expires":
        self.logger.info(event.name)
            
        # Send KEEPALIVE message
        await self.send_keepalive_message()

        # Restart KeepaliveTimer
        self.keepalive_timer = self.keepalive_time

    if event.name in {"Event 18: TcpConnectionFails", "Event 24: NotifMsgVerErr", "Event 25: NotifMsg"}:
        self.logger.info(event.name)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Delete all routes associated with this connection
        pass

        # Release all BGP resouces
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 26: KeepAliveMsg":
        self.logger.info(event.name)
            
        # Restart the HoldTimer
        self.hold_timer = self.hold_time

        # Remain in Established state
        pass

    if event.name == "Event 27: UpdateMsg":
        self.logger.info(event.name)

        # Process the message,
        pass

        # Restart HoldTimer, if the negotiated HoldTime value is non-zero
        self.hold_timer = self.hold_time

        #Remain in the Established state
        pass

    if event.name == "Event 28: UpdateMsgErr":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with an Update error
        pass

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Delete all routes associated with this connection
        pass

        # Release all BGP resouces
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 28: UpdateMsgErr":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with the Error Code Finite State Machine Error
        self.send_notificaion_message(bgp.message.FINITE_STATE_MACHINE_ERROR)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Delete all routes associated with this connection
        pass

        # Release all BGP resouces
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1


        # Change state to Idle
        self.change_state("Idle")

