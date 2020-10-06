#!/usr/bin/env python3

import bgp_message


async def fsm_established(self, event):
    """ Finite State Machine - Established state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # Send the NOTIFICATION with a Cease
        await self.send_notification_message(bgp_message.CEASE)

        # Delete all routes associated with this connection
        pass

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 10: HoldTimer_Expires":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with the error code Hold Timer Expired
        await self.send_notification_message(bgp_message.HOLD_TIMER_EXPIRED)

        # Delete all routes associated with this connection
        pass

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

        # Delete all routes associated with this connection
        pass

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 26: KeepAliveMsg":
        self.logger.info(event.name)

        # Restart the HoldTimer
        self.hold_timer = self.hold_time

    if event.name == "Event 27: UpdateMsg":
        self.logger.info(event.name)

        # Process the message,
        pass

        # Restart HoldTimer
        self.hold_timer = self.hold_time

    if event.name == "Event 28: UpdateMsgErr":
        self.logger.info(event.name)

        # Send a NOTIFICATION message with an Update error
        pass

        # Delete all routes associated with this connection
        pass

        # Release all BGP resouces
        pass

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name in {
        "Event 9: ConnectRetryTimer_Expires",
        "Event 12: DelayOpenTimer_Expires",
        "Event 13: IdleHoldTimer_Expires",
        "Event 20: BGPOpen with DelayOpenTimer running",
        "Event 21: BGPHeaderErr",
        "Event 22: BGPOpenMsgErr",
    }:
        self.logger.info(event.name)

        # Send a NOTIFICATION message with the Error Code Finite State Machine Error
        self.send_notificaion_message(bgp_message.FINITE_STATE_MACHINE_ERROR)

        # Delete all routes associated with this connection
        pass

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")
