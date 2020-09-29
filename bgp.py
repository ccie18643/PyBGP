#!/usr/bin/env python3

import sys
import asyncio
import bgp_message

import loguru

BGP_ID = "192.168.9.201"
BGP_ASN = 65000

HOLD_TIME = 30

class BgpSession():

    def __init__ (self, peer_ip):
        self.peer_ip = peer_ip

        self.connect_retry_time = 5
        self.hold_time = None
        self.keepalive_time = None
        self.state = "Idle"
        self.logger = loguru.logger.bind(peer_ip=peer_ip, state=self.state)

        self.reader = None
        self.writer = None

        self.connect_retry_timer = None
        self.hold_timer = None
        self.keepalive_timer = None

    def change_state(self, state):
        assert state in {"Idle", "Connect", "Active", "OpenSent", "OpenConfirm", "Established"}
        self.logger.debug(f"State: {self.state} -> {state}")
        self.state = state
        self.logger = loguru.logger.bind(peer_ip=self.peer_ip, state=self.state)
        
    async def event_manual_start(self, reset_connect_retry_counter = True):
        """ Event 1:  ManualStart """

        self.logger.info("Event 1: ManualStart")

        if self.state == "Idle":
            # Initialize all BGP resources for the peer connection
            pass

            # Set ConnectRetryCounter to zero
            self.connect_retry_counter = 0

            # Change state to Connect
            self.change_state("Connect")

            # Initiate a TCP connection to the other BGP peer
            self.task_open_connection = asyncio.create_task(self.open_connection())

            # Starts the ConnectRetryTimer with the initial value
            self.task_start_connect_retry_timer = asyncio.create_task(self.start_connect_retry_timer())

    async def event_manual_stop(self):
        """ Event 2: ManualStop """

        self.logger.info("Event 2: ManualStop")

        if self.state in {"Connect", "OpenSent", "OpenConfirm", "Established"}:

            if self.state in {"OpenSent", "OpenConfirm", "Established"}:

                # Send the NOTIFICATION with a Cease
                self.logger.debug("Sending Notification message with a Cease")
                message = bgp_message.Notification()
                self.writer.write(message.write(error_code = 6))
                await self.writer.drain()

            if self.state == "Established":
                # Delete all routes associated with this connection
                pass

            # Sets the ConnectRetryTimer to zero
            self.connect_retry_timer = 0

            # Sets the ConnectRetryCounter to zero
            self.connect_retry_counter = 0

            # Release all BGP resources
            pass

            # Drop the TCP connection
            self.writer.close()
            await self.writer.wait_closed()

            # Changes  state to Idle
            self.change_state("Idle")

    async def event_connect_retry_timer_expires(self):
        """ Event 9: ConnectRetryTimer_Expires """

        self.logger.info("Event 9: ConnectRetryTimer_Expires")

        if self.state == "Connect":

            self.task_open_connection.cancel()

            self.connect_retry_counter += 1
            self.logger.debug(f"connect_retry_counter = {self.connect_retry_counter}")

            # Initiate a TCP connection to the other BGP peer
            self.task_open_connection = asyncio.create_task(self.open_connection())

            # Starts the ConnectRetryTimer with the initial value
            self.task_start_connect_retry_timer = asyncio.create_task(self.start_connect_retry_timer())

    async def event_hold_timer_expires(self):
        """ Event 10: HoldTimer_Expires """

        self.logger.info("Event 10: HoldTimer_Expires")

        if self.state == "OpenSent":
            self.task_event_tcp_cr_acked.cancel()

            # Restarting FSM
            asyncio.create_task(self.event_manual_stop())
            while self.state != "Idle":
                await asyncio.sleep(1)
            await asyncio.sleep(5)
            asyncio.create_task(self.event_manual_start())

        if self.state == "OpenConfirm":
            #self.task_event_tcp_cr_acked.cancel()

            # Restarting FSM
            asyncio.create_task(self.event_manual_stop())
            while self.state != "Idle":
                await asyncio.sleep(1)
            await asyncio.sleep(5)
            asyncio.create_task(self.event_manual_start())

        if self.state == "Established":
            self.change_state("Idle")
            await asyncio.sleep(1)
            # nedd to complete this

    async def event_keepalive_timer_expires(self):
        """ Event 11: KeepaliveTimer_Expires """

        self.logger.info("Event 11: KeepaliveTimer_Expires")

        asyncio.create_task(self.send_keepalive())
        asyncio.create_task(self.start_keepalive_timer())

    async def event_tcp_cr_acked(self):
        """ Event 16: TCP_CR_Acked """

        self.logger.info("Event 16: TCP_CR_Acked")
        
        if self.state == "Connect":

            # Stops the connectretrytimer and set the connectretrytimer to zero 
            self.task_start_connect_retry_timer.cancel()
            self.connect_retry_timer = 0

            # Completes bgp initialization
            pass

            # Sends an open message
            self.logger.debug("Sending open message to peer")
            message = bgp_message.Open()
            self.writer.write(message.write(bgp_id=BGP_ID, asn=BGP_ASN, hold_time=HOLD_TIME))
            await self.writer.drain()

            # Change state to OpenSent
            self.change_state("OpenSent")

            # Set the holdtimer to a large value, holdtimer value of 4 minutes is suggested
            #self.task_hold_timer = asyncio.create_task(self.start_hold_timer(240))
            self.task_hold_timer = asyncio.create_task(self.start_hold_timer(10))

            self.logger.debug("Waiting for open message from peer")

            try:
                header = bgp_message.Header()
                header.read(await self.reader.readexactly(bgp_message.HEADER_SIZE))
            
            except asyncio.exceptions.IncompleteReadError:
                # Need to handle this properly
                self.logger.critical("IncompleteReadError received")
                sys.exit()

            if header.type == bgp_message.OPEN:
                self.logger.debug("Open message from peer received")
                message = bgp_message.Open()
                message.read(await self.reader.readexactly(header.size - bgp_message.HEADER_SIZE))
                self.change_state("OpenConfirm")
                self.task_event_bgp_open = asyncio.create_task(self.event_bgp_open(message))

            if header.type == bgp_message.NOTIFICATION:
                message = bgp_message.Notification()
                message.read(await self.reader.readexactly(header.size - bgp_message.HEADER_SIZE))
                # Need to make this adhere to standard
                self.writer.close()
                await self.writer.wait_closed()
                self.logger.critical("Notification message received")
                sys.exit()

    async def event_tcp_connection_confirmed(self):
        """ Event 17: TcpConnectionConfirmed """

        self.logger.info("Event 17: TcpConnectionConfirmed")

    async def event_tcp_connection_fails(self):
        """ Event 18: TcpConnectionFails """

        self.logger.info("Event 18: TcpConnectionFails")

        if self.state == "Connect":

            self.task_start_connect_retry_timer.cancel()

            self.connect_retry_counter += 1
            self.logger.debug(f"connect_retry_counter = {self.connect_retry_counter}")

            await asyncio.sleep(1)

            # Initiate a TCP connection to the other BGP peer
            self.task_open_connection = asyncio.create_task(self.open_connection())

            # Starts the ConnectRetryTimer with the initial value
            self.connect_retry_timer = self.connect_retry_time
            self.task_start_connect_retry_timer = asyncio.create_task(self.start_connect_retry_timer())

    async def event_bgp_open(self, open_message):
        """ Event 19: BGPOpen """

        self.logger.info("Event 19: BGPOpen")

        if self.state == "OpenConfirm":
            self.logger.debug("Sending keepalive to ack open")

            message = bgp_message.Keepalive()
            self.writer.write(message.write())
            await self.writer.drain()

            self.hold_time = min(HOLD_TIME, open_message.hold_time)
            self.keepalive_time = self.hold_time // 3

            self.connect_retry_timer = 0
            
            self.logger.debug("Waiting for OpenConfirm keepalive")

            try:
                header = bgp_message.Header()
                header.read(await self.reader.readexactly(bgp_message.HEADER_SIZE))
            
            except asyncio.exceptions.IncompleteReadError:
                # Need to handle this properly
                self.logger.critical("IncompleteReadError received")
                sys.exit()

            if header.type == bgp_message.KEEPALIVE:
                self.logger.debug("Received OpenConfirm keepalive")
                self.change_state("Established")
                self.task_hold_timer.cancel()
                self.task_hold_timer = asyncio.create_task(self.start_hold_timer())
                asyncio.create_task(self.start_keepalive_timer())
                asyncio.create_task(self.maintain_session())

            if header.type == bgp_message.NOTIFICATION:
                messaage = bgp_message.Notification()
                messaage.read(await self.reader.readexactly(header.size - bgp_message.HEADER_SIZE))
                # Need to make this adhere to standard
                self.writer.close()
                await self.writer.wait_closed()
                self.logger.critical("Notification message received")
                sys.exit()



    async def event_bgp_header_err(self):
        """ Event 21: BGPHeaderErr """

        self.logger.info("Event 21: BGPHeaderErr")

    async def event_bgp_open_msg_err(self):
        """ Event 22: BGPOpenMsgErr """

        self.logger.info("Event 22: BGPOpenMsgErr")

    async def event_notif_msg_ver_err(self):
        """ Event 24: NotifMsgVerErr """

        self.logger.info("Event 24: NotifMsgVerErr")

    async def event_notif_msg(self):
        """ Event 25: NotifMsg """

        self.logger.info("Event 25: NotifMs")

    async def event_keep_alive_msg(self):
        """ Event 26: KeepAliveMsg """

        self.logger.info("Event 26: KeepAliveMsg")

    async def event_update_msg(self):
        """ Event 27: UpdateMsg """

        self.logger.info("Event 27: UpdateMsg")

    async def event_update_msg_err(self):
        """ Event 28: UpdateMsgErr """

        self.logger.info("Event 28: UpdateMsgErr")

    async def open_connection(self):
        """ Open TCP connection to the BGP peer """

        self.logger.debug(f"Opening connection to peer")
        try:
            self.reader, self.writer = await asyncio.open_connection(self.peer_ip, 179)
            self.task_event_tcp_cr_acked = asyncio.create_task(self.event_tcp_cr_acked())

        except OSError:
            self.logger.debug(f"TCP connection failed")
            asyncio.create_task(self.event_tcp_connection_fails())

    async def send_keepalive(self):
        """ Send Keepalive message """
        self.logger.debug("Sending keepalive")
        message = bgp_message.Keepalive()
        self.writer.write(message.write())
        await self.writer.drain()


    async def start_keepalive_timer(self):
        """ Initialize keepalive timer and then decrease it every second """

        self.keepalive_timer = self.keepalive_time
        
        self.logger.debug(f"Starting keepalive_timer at {self.keepalive_time}")

        while self.state in {"OpenConfirm", "Established"}: # Not sure if i need OpenConfirm here
            self.logger.debug(f"keepalive_timer = {self.keepalive_timer}")
            await asyncio.sleep(1)
            if self.keepalive_timer:
                self.keepalive_timer -= 1
                if not self.keepalive_timer:
                    asyncio.create_task(self.event_keepalive_timer_expires())
                    break

    async def start_hold_timer(self, hold_time=None):
        """ Initialize hold timer and then decrease it every second """

        if hold_time is None:
            self.hold_timer = self.hold_time
        else:
            self.hold_timer = hold_time

        self.logger.debug(f"Starting hold_timer at {hold_time}")

        while self.state in {"OpenSent", "OpenConfirm", "Established"}:
            self.logger.debug(f"hold_timer = {self.hold_timer}")
            await asyncio.sleep(1)
            if self.hold_timer:
                self.hold_timer -= 1
                if not self.hold_timer:
                    asyncio.create_task(self.event_hold_timer_expires())
                    break
    
    async def start_connect_retry_timer(self):
        """ Decrease connect retry timer every second """

        self.connect_retry_timer = self.connect_retry_time

        self.logger.debug(f"Starting connect_retry_timer at {self.connect_retry_time}")

        while self.state == "Connect":
            self.logger.debug(f"connect_retry_timer = {self.connect_retry_timer}")
            await asyncio.sleep(1)
            if self.connect_retry_timer:
                self.connect_retry_timer -= 1
                if not self.connect_retry_timer:
                    asyncio.create_task(self.event_connect_retry_timer_expires())
                    break

    async def maintain_session(self):
        """ Receive communication from BGP peer and react to it approprietely """

        while self.state == "Established":
            header = bgp_message.Header()

            try:
                header.read(await self.reader.readexactly(bgp_message.HEADER_SIZE))

                if header.type == bgp_message.UPDATE:
                    self.logger.debug("Received update")
                    messaage = bgp_message.Update()
                    messaage.read(await self.reader.readexactly(header.size - bgp_message.HEADER_SIZE))

                if header.type == bgp_message.NOTIFICATION:
                    self.logger.debug("Received notification")
                    messaage = bgp_message.Notification()
                    messaage.read(await self.reader.readexactly(header.size - bgp_message.HEADER_SIZE))

                if header.type == bgp_message.KEEPALIVE:
                    self.logger.debug("Received keepalive")
                    self.hold_timer = self.hold_time

            except asyncio.exceptions.IncompleteReadError:
                # Need to handle this properly
                self.logger.critical("IncompleteReadError received")
                sys.exit()


async def main():
    loguru.logger.remove(0)
    loguru.logger.add(sys.stdout, colorize=True, level="DEBUG", format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
            + f"|</level> <level>{{extra[peer_ip]:15}} | <normal><cyan>{{function:30}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>")

    session = BgpSession("192.168.9.202")
    #session = BgpSession("192.168.9.201")
    #session = BgpSession("222.222.222.222")
    asyncio.create_task(session.event_manual_start())
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":

    asyncio.run(main())


