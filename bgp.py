#!/usr/bin/env python3

import sys
import asyncio
import bgp_message

import loguru

BGP_ID = "192.168.9.201"
BGP_ASN = 65000

HOLD_TIME = 30


class BgpEvent():

    def __init__(self, name, message=None):
        self.name = name
        self.message = message


class BgpSession():

    def __init__ (self, peer_ip):
        self.peer_ip = peer_ip

        self.event_queue = []

        self.reader = None
        self.writer = None

        self.state = "Idle"

        self.logger = loguru.logger.bind(peer_ip=self.peer_ip, state=self.state)

        self.connect_retry_time = 5
        self.keepalive_time = None
        self.hold_time = None

        self.connect_retry_timer = 0
        self.keepalive_timer = 0
        self.hold_timer = 0

        self.task_fsm = asyncio.create_task(self.fsm())
        self.task_decrease_hold_timer = asyncio.create_task(self.decrease_hold_timer())
        self.task_decrease_connect_retry_timer = asyncio.create_task(self.decrease_connect_retry_timer())
        self.task_decrease_keepalive_timer = asyncio.create_task(self.decrease_keepalive_timer())
        self.task_message_input_loop = asyncio.create_task(self.message_input_loop())

    def change_state(self, state):
        assert state in {"Idle", "Connect", "Active", "OpenSent", "OpenConfirm", "Established"}
        self.logger.info(f"State: {self.state} -> {state}")
        self.state = state
        self.logger = loguru.logger.bind(peer_ip=self.peer_ip, state=self.state)

    async def decrease_connect_retry_timer(self):
        """ Decrease connect_retry_timer every second if its value is greater than zero """

        self.logger.debug(f"Starting decrease_connect_retry_timer() coroutine")

        while True:
            await asyncio.sleep(1)
            if self.connect_retry_timer:
                self.logger.debug(f"connect_retry_timer = {self.connect_retry_timer}")
                self.connect_retry_timer -= 1
                if not self.connect_retry_timer:
                    self.event_queue.append(BgpEvent("Event 9: ConnectRetryTimer_Expires"))

    async def decrease_hold_timer(self):
        """ Decrease hold_timer every second if its value is greater than zero """

        self.logger.debug(f"Starting decrease_hold_timer() coroutine")

        while True:
            await asyncio.sleep(1)
            if self.hold_timer:
                self.logger.debug(f"hold_timer = {self.hold_timer}")
                self.hold_timer -= 1
                if not self.hold_timer:
                    self.event_queue.append(BgpEvent("Event 10: HoldTimer_Expires"))

    async def decrease_keepalive_timer(self):
        """ Decrease keepalive_timer every second if its value is greater than zero """

        self.logger.debug(f"Starting decrease_keepalive_timer() coroutine")

        while True:
            await asyncio.sleep(1)
            if self.keepalive_timer:
                self.logger.debug(f"keepalive_timer = {self.keepalive_timer}")
                self.keepalive_timer -= 1
                if not self.keepalive_timer:
                    self.event_queue.append(BgpEvent("Event 11: KeepaliveTimer_Expires"))

    async def open_connection(self):
        """ Open TCP connection to the BGP peer """

        self.logger.debug(f"Opening connection to peer")
        try:
            self.reader, self.writer = await asyncio.open_connection(self.peer_ip, 179)
            self.event_queue.append(BgpEvent("Event 16: Tcp_CR_Acked"))

        except OSError:
            self.logger.debug(f"TCP connection failed")
            self.event_queue.append(BgpEvent("Event 18: TcpConnectionFails"))

    async def close_connection(self):
        """ Close TCP connection to the BGP peer """

        self.logger.debug(f"Closing connection to peer")

        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.reader = None
            self.writer = None

    #@connection_exception_handler
    async def send_keepalive_message(self):
        """ Send Keepalive message """

        self.logger.opt(ansi=True).info("<magenta>[>>>]</magenta> Sending keepalive message")
        message = bgp_message.Keepalive()
        self.writer.write(message.write())
        await self.writer.drain()

    #@connection_exception_handler
    async def send_notification_message(self, error_code, error_subcode=0, data=b""):
        """ Send Notification message """

        self.logger.opt(ansi=True).info(f"<magenta>[>>>]</magenta> Sending Notification message [{error_code}, {error_subcode}, {data}]")
        message = bgp_message.Notification(error_code, error_subcode, data)
        self.writer.write(message.write())
        await self.writer.drain()

    #@connection_exception_handler
    async def send_open_message(self, asn, bgp_id, hold_time):
        """ Send Open message """

        self.logger.opt(ansi=True).info("<magenta>[>>>]</magenta> Sending Open message")
        message = bgp_message.Open(asn, bgp_id, hold_time)
        self.writer.write(message.write())
        await self.writer.drain()

    async def message_input_loop(self):
        """ Receive messages from the peer and add them to the input queue """

        self.logger.debug("Starting message input loop")

        while True:

            if self.reader is None:
                await asyncio.sleep(1)
                continue

            data = await self.reader.read(4096)
            self.logger.debug(f"Received {len(data)} bytes of data")

            if len(data) == 0:
                self.logger.error(f"Connection failed")
                self.event_queue.append(BgpEvent("Event 18: TcpConnectionFails"))
                await asyncio.sleep(1)
                continue
            
            while len(data) >= 19:
                message = bgp_message.DecodeMessage(data, asn=BGP_ASN, bgp_id=BGP_ID)

                if message.data_length_error:
                    self.logger.warning(f"Received {message_data_length_received} bytes of data, expected at least {message.data_length_expected}")
                    self.logger.error(f"Connection failed")
                    self.event_queue.append(BgpEvent("Event 18: TcpConnectionFails"))
                    await asyncio.sleep(1)
                    break

                data = data[message.length:]

                if message.message_error_code == bgp_message.MESSAGE_HEADER_ERROR:
                    self.event_queue.append(BgpEvent("Event 21: BGPHeaderErr", message))
                    break

                if message.message_error_code == bgp_message.OPEN_MESSAGE_ERROR:
                    self.event_queue.append(BgpEvent("Event 22: BGPOpenMsgErr", message))
                    break

                if message.type == bgp_message.OPEN:
                    self.logger.opt(ansi=True).info("<green>[<<<]</green> Received Open message")
                    self.event_queue.append(BgpEvent("Event 19: BGPOpen", message))

                if message.type == bgp_message.UPDATE:
                    self.logger.opt(ansi=True).info("<green>[<<<]</green> Received Update message")
                    ### Requires proper handler here

                if message.type == bgp_message.NOTIFICATION:
                    self.logger.opt(ansi=True).info("<green>[<<<]</green> Received Notification message")

                    ### Need to add handler for notifcations about bad header

                    if message.error_code == bgp_mesage.OPEN_MESSAGE_ERROR and messsage.error_subcode == bgp_message.UNSUPPORTED_VERSION_NUMBER:
                        self.event_queue.append(BgpEvent("Event 24: NotifMsgVerErr"))

                    if message.error_code == bgp.message.OPEN_MESSAGE_ERROR and messsage.error_subcode != bgp_message.UNSUPPORTED_VERSION_NUMBER:
                        self.event_queue.append(BgpEvent("Event 25: NotifMsg"))

                if message.type == bgp_message.KEEPALIVE:
                    self.logger.opt(ansi=True).info("<green>[<<<]</green> Received Keepalive message")
                    self.event_queue.append(BgpEvent("Event 26: KeepAliveMsg"))

            else:
                await asyncio.sleep(1)

    async def fsm_idle(self, event):
        """ Finite State Machine - Idle state """

        if event.name in {"Event 1: ManualStart", "Event 3: AutomaticStart"}:
            self.logger.info(event.name)

            # Initialize all BGP resources for the peer connection
            pass

            # Sets ConnectRetryCounter to zero
            self.connect_retry_counter = 0

            # Starts the ConnectRetryTimer with the initial value
            self.connect_retry_timer = self.connect_retry_time

            # Initiate a TCP connection to the other BGP peer
            self.task_open_connection = asyncio.create_task(self.open_connection())
            await asyncio.sleep(0.001)

            # Change state to Connect
            self.change_state("Connect")

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

            # Stop the ConnectRetryTimer and set the ConnectRetryTimer to zero
            self.connect_retry_timer = 0

            # Complete BGP initialization
            pass

            # Send an open message to the peer
            await self.send_open_message(BGP_ASN, BGP_ID, HOLD_TIME)

            # Set the holdtimer to a large value, holdtimer value of 4 minutes is suggested
            self.hold_timer = 240

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

            # Change state to Idle
            self.change_state("Idle")

    async def fsm_active(self, event):
        """ Finite State Machine - Active state """

        pass

    async def fsm_opensent(self, event):
        """ Finite State Machine - OpenSent state """

        if event.name == "Event 2: ManualStop":
            self.logger.info(event.name)

            # Send the NOTIFICATION with a Cease
            await self.send_notification_message(6)

            # Set the ConnectRetryTimer to zero
            self.connect_retry_timer = 0

            # Releases all BGP resources
            pass

            # Drop the TCP connection
            await self.close_connection()

            # Set ConnectRetryCounter to zero
            self.connect_retry_counter = 0

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

        if event.name == "Event 18: TcpConnectionFails":
            self.logger.info(event.name)

            # Close the TCP connection
            await self.close_connection()

            # Restart the ConnectRetryTimer
            self.connect_retry_timer = self.connect_retry_time

            # Continue to listen for a connection that may be initialized by the remote BGP peer
            pass

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
            self.hold_time = min(HOLD_TIME, message.hold_time)
            self.hold_timer = self.hold_time
            
            # Set a KeepAliveTimer
            self.keepalive_time = self.hold_time // 3
            self.keepalive_timer = self.keepalive_time

            # Change state to OpenConfirm
            self.change_state("OpenConfirm")

        if event.name in {"Event 21: BGPHeaderErr", "Event 22: BGPOpenMsgErr"}:
            self.logger.info(event.name)

            message = event.message

            # Send a NOTIFICATION message with the appropriate error code
            await self.send_notification_message(message.message_error_code, message.message_error_subcode, message.message_error_data)

            # Set the BGP ConnectRetryTimer to zero
            self.connect_retry_timer = 0

            # Release all BGP resources
            pass

            # Drop the TCP connection
            await self.close_connection()

            # Increment ConnectRetryCounter
            self.connect_retry_counter += 1

            # Change state to Idle
            self.change_state("Idle")

        if event.name == "Event 24: NotifMsgVerErr":
            self.logger.info(event.name)

            # Set the ConnectRetryTimer to zero
            self.connect_retry_timer = 0

            # Release all bgp resources
            pass

            # Drop the TCP connection
            await self.close_connection()

            # Change state to Idle
            self.change_state("Idle")

        if event.name == "Event 25: NotifMsg":
            self.logger.info(event.name)

            # Set the ConnectRetryTimer to zero
            self.connect_retry_timer = 0

            # Release all bgp resources
            pass

            # Drop the TCP connection
            self.close_connection()

            # Increment ConnectRetryCounter
            self.connect_retry_counter += 1

            # Change state to Idle
            self.change_state("Idle")


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

            # Restart the KeepaliveTimer
            self.keepalive_timer = self.keepalive_time

            # Remain in OpenConfirm state
            pass

        if event.name == "Event 18: TcpConnectionFails":
            self.logger.info(event.name)

            # Set the ConnectRetryTimer to zero
            self.connect_retry_timer = 0

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

            # Change state to Established
            self.change_state("Established")

    async def fsm_established(self, event):
        """ Finite State Machine - Established state """

        if event.name == "Event 2: ManualStop":
            self.logger.info(event.name)

            # Send the NOTIFICATION with a Cease
            await self.send_notification_message(6)

            # Set ConnectRetryCounter to zero
            self.connect_retry_counter = 0

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

        if event.name == "Event 26: KeepAliveMsg":
            self.logger.info(event.name)
            
            # Restart the HoldTimer
            self.hold_timer = self.hold_time

            # Remain in Established state
            pass



    async def fsm(self):
        """ Finite State Machine loop """

        while True:
            if self.event_queue:
                event = self.event_queue.pop(0)

                if self.state == "Idle":
                    await self.fsm_idle(event)
                
                if self.state == "Connect":
                    await self.fsm_connect(event)

                if self.state == "Active":
                    await self.fsm_active(event)

                if self.state == "OpenSent":
                    await self.fsm_opensent(event)

                if self.state == "OpenConfirm":
                    await self.fsm_openconfirm(event)

                if self.state == "Established":
                    await self.fsm_established(event)

            await asyncio.sleep(1)



async def main():
    loguru.logger.remove(0)
    loguru.logger.add(sys.stdout, colorize=True, level="DEBUG", format=f"<green>{{time:YY-MM-DD HH:mm:ss}}</green> <level>| {{level:7}} "
            + f"|</level> <level>{{extra[peer_ip]:15}} | <normal><cyan>{{function:33}}</cyan></normal> | {{extra[state]:11}} | {{message}}</level>")

    session = BgpSession("192.168.9.202")
    #session = BgpSession("192.168.9.201")
    #session = BgpSession("222.222.222.222")

    session.event_queue.append(BgpEvent("Event 1: ManualStart"))
    #await asyncio.sleep(2)
    #session.event_queue.append("Event 2: ManualStop")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":

    asyncio.run(main())


