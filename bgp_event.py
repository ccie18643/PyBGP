#!/usr/bin/env python3

"""

PyBGP, Python BGP implmentation version 0.1 - 2020, Sebastian Majewski
bgp_event.py - module containin class supporting FSM events

"""

class BgpEvent:
    def __init__(self, name, message=None, reader=None, writer=None, peer_ip=None, peer_port=None):
        self.name = name
        self.message = message
        self.reader = reader
        self.writer = writer
        self.peer_ip = peer_ip
        self.peer_port = peer_port
