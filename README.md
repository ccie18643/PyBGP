# PyBGP - Python BGP project

Basic BGP implementation in Python for educational purposes. At this time it fully supports Finite State Machine and its able to open and maintain connectivity to BGP peer in either passive or active mode. Connection collision detection is already implemented so its able to drop less desired connection if two of them form simultaneously. Project written in Python using Asyncio. Can support connectivity to multiple peers at the same time. Next to do is implementation of BGP updates.

### Log output showing comunication with three BGP peers
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/ss01.png)


### Log output showing BGP Finite State Machine establishing connectivity to peer router by using active TCP connection
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/ss02.png)


### Log output showing BGP Finite State Machine establishing connectivity to peer router by using passive TCP connection
![Sample PyBGP log output](https://github.com/ccie18643/PyBGP/blob/master/pictures/ss02.png)

