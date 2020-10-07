#!/usr/bin/env python3

import bgp_message


async def fsm_opensent(self, event):
    """ Finite State Machine - OpenSent state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # Send the NOTIFICATION with a Cease
        await self.send_notification_message(bgp_message.CEASE)

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 8: AutomaticStop":
        self.logger.info(event.name)

        # Send the NOTIFICATION with a Cease
        await self.send_notification_message(bgp_message.CEASE)

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 10: HoldTimer_Expires":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with the error code Hold Timer Expired
        await self.send_notification_message(bgp_message.HOLD_TIMER_EXPIRED)

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 18: TcpConnectionFails":
        self.logger.info(event.name)

        # Close the TCP connection
        self.close_connection()

        # Restart the ConnectRetryTimer
        self.connect_retry_timer = self.connect_retry_time

        # Set the HoldTimer to zero (not required by RFC4271)0
        self.hold_timer = 0

        # Stop HoldTimer (not required by RFC4271)
        self.hold_timer = 0

        # Stop KeepaliveTimer (not required by RFC4271)
        self.keepalive_timer = 0

        # Change state to Active
        self.change_state("Active")

    if event.name == "Event 19: BGPOpen":
        self.logger.info(event.name)

        message = event.message

        # Set the BGP ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Send a KeepAlive message
        await self.send_keepalive_message()

        # Set the HoldTimer according to the negotiated value
        self.hold_time = min(self.local_hold_time, message.hold_time)
        self.hold_timer = self.hold_time

        # Set a KeepAliveTimer
        self.keepalive_time = self.hold_time // 3
        self.keepalive_timer = self.keepalive_time

        # Save the peer BGP ID to be used for collision detection
        self.peer_id = message.id

        # Change state to OpenConfirm
        self.change_state("OpenConfirm")

    if event.name in {"Event 21: BGPHeaderErr", "Event 22: BGPOpenMsgErr"}:
        self.logger.info(event.name)

        message = event.message

        # Send a NOTIFICATION message with the appropriate error code
        await self.send_notification_message(message.message_error_code, message.message_error_subcode, message.message_error_data)

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 24: NotifMsgVerErr":
        self.logger.info(event.name)

        # Change state to Idle
        self.change_state("Idle")

    if event.name in {
        "Event 9: ConnectRetryTimer_Expires",
        "Event 11: KeepaliveTimer_Expires",
        "Event 12: DelayOpenTimer_Expires",
        "Event 13: IdleHoldTimer_Expires",
        "Event 20: BGPOpen with DelayOpenTimer running",
        "Event 25: NotifMsg",
        "Event 26: KeepAliveMsg",
        "Event 27: UpdateMsg",
        "Event 28: UpdateMsgErr",
    }:
        self.logger.info(event.name)

        # Send the NOTIFICATION with the Error Code Finite State Machine Error
        await self.send_notification_message(bgp_message.FINITE_STATE_MACHINE_ERROR)

        # Set ConnecRetryTimer to zro
        self.connect_retry_timer = 0

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Chhange state to Idle
        self.change_state("Idle")
