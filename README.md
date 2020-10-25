# PyBGP - Python BGP project

Python / Asyncio based BGP implementation. At this time it fully supports Finite State Machine and its able to open and maintain connectivity to BGP peer in either passive or active mode. Connection collision detection is already implemented so it's able to drop less desired connection if two of them form simultaneously. Can support connectivity to multiple peers at the same time.


#### Already implemented:

 - TX/RX Network IO - running as coroutine
 - Finite State Machine - running as coroutine
 - Event system with message queuing
 - Passive and Active connectivity with collision detection mechanism
 - Ability to maintain simultaneous connectivity with multiple peers

#### Work in progress:

 - BGP Updates

#### Next steps:

 - Implementing fully functional Route Reflector


### Comunication with three BGP peers
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_01.png)



### Finite State Machine establishing connectivity by using active TCP connection
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_02.png)



### Finite State Machine establishing connectivity by using passive TCP connection
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_03.png)



### Finite State Machine chosing passive over active connection due to peer's higher BGP ID
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/log_04.png)

