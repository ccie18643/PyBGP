# PyBGP

### An attempt to write the BGP router
<br>

PyBGP is Python / Asyncio-based BGP implementation. It fully supports the Finite State Machine and can open and maintain connectivity to BGP peers in either passive or active mode. Connection collision detection is already implemented, so it can drop the less desired connection if two form simultaneously. It can support connectivity to multiple peers at the same time.

---

### Features

#### Already implemented:

 - Finite State Machine - running as a coroutine
 - Event system with message queuing
 - TX/RX Network IO - running as a coroutine
 - Timers - connect_retry, hold, keepalive
 - Support for parsing and creating BGP messages
 - Passive and Active connectivity with a collision detection mechanism
 - Ability to maintain simultaneous connectivity with multiple peers

#### Work in progress:

 - BGP Updates

#### Next steps:

 - Implementing fully functional Route Reflector

---

### Examples

#### Communication with three BGP peers
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_01.png)



#### Finite State Machine establishing connectivity by using an active TCP connection
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_02.png)



#### Finite State Machine establishing connectivity by using a passive TCP connection
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_03.png)



#### Finite State Machine choosing passive over active connection due to peer's higher BGP ID
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_04.png)

