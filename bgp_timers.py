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

from bgp_event import BgpEvent


async def decrease_connect_retry_timer(self):
    """ Decrease connect_retry_timer every second if its value is greater than zero """

    self.logger.debug("Starting decrease_connect_retry_timer() coroutine")

    if not hasattr(self, "connect_retry_timer"):
        self.connect_retry_timer = 0

    while True:
        await asyncio.sleep(1)
        if self.connect_retry_timer:
            self.logger.debug(f"connect_retry_timer = {self.connect_retry_timer}")
            self.connect_retry_timer -= 1
            if not self.connect_retry_timer:
                self.enqueue_event(BgpEvent("Event 9: ConnectRetryTimer_Expires"))


async def decrease_hold_timer(self):
    """ Decrease hold_timer every second if its value is greater than zero """

    self.logger.debug("Starting decrease_hold_timer() coroutine")

    if not hasattr(self, "hold_timer"):
        self.hold_timer = 0

    while True:
        await asyncio.sleep(1)
        if self.hold_timer:
            self.logger.debug(f"hold_timer = {self.hold_timer}")
            self.hold_timer -= 1
            if not self.hold_timer:
                self.enqueue_event(BgpEvent("Event 10: HoldTimer_Expires"))


async def decrease_keepalive_timer(self):
    """ Decrease keepalive_timer every second if its value is greater than zero """

    self.logger.debug("Starting decrease_keepalive_timer() coroutine")

    if not hasattr(self, "keepalive_timer"):
        self.keepalive_timer = 0

    while True:
        await asyncio.sleep(1)
        if self.keepalive_timer:
            self.logger.debug(f"keepalive_timer = {self.keepalive_timer}")
            self.keepalive_timer -= 1
            if not self.keepalive_timer:
                self.enqueue_event(BgpEvent("Event 11: KeepaliveTimer_Expires"))
