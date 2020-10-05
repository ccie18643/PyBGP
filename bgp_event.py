#!/usr/bin/env python3

class BgpEvent():

    def __init__(self, name, message=None, reader=None, writer=None):
        self.name = name
        self.message = message
        self.reader = reader
        self.writer = writer
