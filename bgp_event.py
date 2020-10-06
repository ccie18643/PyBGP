#!/usr/bin/env python3


class BgpEvent:
    def __init__(self, name, message=None, reader=None, writer=None, peer_ip=None, peer_port=None):
        self.name = name
        self.message = message
        self.reader = reader
        self.writer = writer
        self.peer_ip = peer_ip
        self.peer_port = peer_port
