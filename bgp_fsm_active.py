#!/usr/bin/env python3

############################################################################
#                                                                          #
#  PyBGP - Python BGP implementation                                       #
#  Copyright (C) 2020  Sebastian Majewski                                  #
#                                                                          #
#  This program is free software: you can redistribute it and/or modify    #
#  it under the terms of the GNU General Public License as published by    #
#  the Free Software Foundation, either version 3 of the License, or       #
#  (at your option) any later version.                                     #
#                                                                          #
#  This program is distributed in the hope that it will be useful,         #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#  GNU General Public License for more details.                            #
#                                                                          #
#  You should have received a copy of the GNU General Public License       #
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                          #
#  Author's email: ccie18643@gmail.com                                     #
#  Github repository: https://github.com/ccie18643/PyBGP                   #
#                                                                          #
############################################################################


import asyncio

import loguru


async def fsm_active(self, event):
    """ Finite State Machine - Active state """

    if event.name == "Event 2: ManualStop":
        self.logger.info(event.name)

        # Set ConnectRetryCounter to zero
        self.connect_retry_counter = 0

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 8: AutomaticStop":
        self.logger.info(event.name)

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 9: ConnectRetryTimer_Expires":
        self.logger.info(event.name)

        # Restart the ConnectRetryTimer
        self.connect_retry_timer = self.connect_retry_time

        if not self.passive_tcp_establishment:
            # Initiate a TCP connection to the other BGP peer
            self.task_open_connection = asyncio.create_task(self.open_connection())
            await asyncio.sleep(0.001)

            # Stop KeepaliveTimer (not required by RFC4271)
            self.keepalive_timer = 0

            # Change state to  Connect
            self.change_state("Connect")

    if event.name in {"Event 16: Tcp_CR_Acked", "Event 17: TcpConnectionConfirmed"}:

        # Take an ownership of the connection
        self.reader = event.reader
        self.writer = event.writer
        self.peer_ip = event.peer_ip
        self.peer_port = event.peer_port
        self.tcp_connection_established = True

        self.logger = loguru.logger.bind(peer=f"{self.mode} {self.peer_ip}:{self.peer_port}", state=self.state)

        self.logger.info(event.name)

        # Stop the ConnectRetryTimer and set the ConnectRetryTimer to zero
        self.connect_retry_timer = 0

        # Send an open message to the peer
        await self.send_open_message()

        # Set the holdtimer to a large value, holdtimer value of 4 minutes is suggested
        self.hold_timer = 240

        # Changes state to OpenSent
        self.change_state("OpenSent")

    if event.name == "Event 18: TcpConnectionFails":
        self.logger.info(event.name)

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name in {"Event 21: BGPHeaderErr", "Event 22: BGPOpenMsgErr"}:
        self.logger.info(event.name)

        message = event.message

        # If the SendNOTIFICATIONwithoutOPEN attribute is set to TRUE, then the local system
        # sends a NOTIFICATION message with the appropriate error code
        if self.send_notification_without_open:
            await self.send_notification_message(message.message_error_code, message.message_error_subcode, message.message_error_data)

        # Increment ConnectRetryCounter
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name == "Event 24: NotifMsgVerErr":
        self.logger.info(event.name)

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")

    if event.name in {
        "Event 8: AutomaticStop",
        "Event 10: HoldTimer_Expires",
        "Event 11: KeepaliveTimer_Expires",
        "Event 13: IdleHoldTimer_Expires",
        "Event 19: BGPOpen",
        "Event 23: OpenCollisionDump",
        "Event 25: NotifMsg",
        "Event 26: KeepAliveMsg",
        "Event 27: UpdateMsg",
        "Event 28: UpdateMsgErr",
    }:
        self.logger.info(event.name)

        # Increment the ConnectRetryCounter by 1
        self.connect_retry_counter += 1

        # Change state to Idle
        self.change_state("Idle")
