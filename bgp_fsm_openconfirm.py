#!/usr/bin/env python3

import asyncio
import bgp_message

import loguru

from bgp_event import BgpEvent


async def fsm_openconfirm(self, event):
    """ Finite State Machine - OpenConfirm state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # Send the NOTIFICATION with a Cease
        await self.send_notification_message(6)

        # Releases all BGP resources
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Stop HoldTimer (not required by RFC4271)
        self.hold_timer = 0

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 10: HoldTimer_Expires":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with the error code Hold Timer Expired
        await self.send_notification_message(HOLD_TIMER_EXPIRED)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Release all BGP resources
        pass

        # Drop the TCP connection
        self.close_connection()

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 11: KeepaliveTimer_Expires":
        self.logger.info(event.name)

        # Send KEEPALIVE message
        await self.send_keepalive_message()

        # Restart the KeepaliveTimer
        self.keepalive_timer = self.keepalive_time

        # Remain in OpenConfirm state
        pass

    if event.name in {"Event 18: TcpConnectionFails", "Event 25: NotifMsg"}:
        self.logger.info(event.name)

        # Set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Release all BGP resouces
        pass
            
        # Drop the TCP connection
        await self.close_connection()

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Stop HoldTimer (not required by RFC4271)
        self.hold_timer = 0

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 19: BGPOpen":
        self.logger.info(event.name)

        ### Colision detection needs to happen here ###

    if event.name in {"Event 21: BGPHeaderErr", "Event 22: BGPOpenMsgErr"}:
        self.logger.info(event.name)

        message = event.message

        # Send a NOTIFICATION message with the appropriate error code
        await self.send_notification_message(message.message_error_code, message.message_error_subcode, message.message_error_data)

        # Set the BGP ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Set HoldTimer to zero (not required by RFC4271)
        self.hold_timer = 0

        # Release all BGP resources
        pass

        # Drop the TCP connection
        await self.close_connection()

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Stop HoldTimer (not required by RFC4271)
        self.hold_timer = 0

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0

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

        # Stop HoldTimer (not required by RFC4271)
        self.hold_timer = 0

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 26: KeepAliveMsg":
        self.logger.info(event.name)

        # Restart the HoldTimer
        self.hold_timer = self.hold_time

        # Change state to Established
        self.change_state("Established")

    if event.name in {"Event 9: ConnectRetryTimer_Expires", "Event 12: DelayOpenTimer_Expires", "Event 13: IdleHoldTimer_Expires",
                      "Event 20: BGPOpen with DelayOpenTimer running", "Event 27: UpdateMsg", "Event 28: UpdateMsgErr"}:
        self.logger.info(event.name)

        # Send the NOTIFICATION with the Error Code Finite State Machine Error
        await self.send_notification_message("FINITE_STATE_MACHINE_ERROR")

        # Set ConnecRetryTimer to zro
        self.connect_retry_timer = 0

        # Set HoldTimer to zero (not required by RFC4271)
        self.hold_timer = 0

        # Release all BGP resources
        pass

        # Drop TCP connection
        self.close_connection()

        # Increment the ConnectRetryCounter by 1
        connect_retry_counter += 1
        
        # Stop HoldTimer (not required by RFC4271)
        self.hold_timer = 0

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0


        # Chhange state to Idle
        self.switch_state("Idle")

