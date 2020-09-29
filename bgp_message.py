import struct
import socket

OPEN = 1
UPDATE = 2
NOTIFICATION = 3
KEEPALIVE = 4

HEADER_SIZE = 19

class Header:
    def read(self, data):
        self.size, self.type = struct.unpack("!xxxxxxxxxxxxxxxxHB", data[:19])


class Open:
    def read(self, data):
        self.version, self.asn, self.hold_time, self.bgp_id, self.opt_len = struct.unpack("!BHHIB", data[:10])
        if self.opt_len:
            self.opt = data[10:10 + self.opt_len]

    def write(self, asn, bgp_id, hold_time=180, opt=b"", version=4):
        self.version = version
        self.asn = asn
        self.hold_time = hold_time
        self.bgp_id = struct.unpack("!L", socket.inet_aton(bgp_id))[0]
        self.opt_len = len(opt)
        self.opt = opt
        return b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff" + struct.pack("!HB",
                19 + 10 + self.opt_len, OPEN) + struct.pack("!BHHIB",
                self.version, self.asn, self.hold_time, self.bgp_id, self.opt_len) + self.opt

class Notification:
    def read(self, data):
        self.error_code, self.error_subcode = struct.unpack("!BB", data[:2])

    def write(self, error_code, error_subcode=0, data=b""):
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.data = data
        return b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff" + struct.pack("!HB",
                19 + 2 + len(self.data), NOTIFICATION) + struct.pack("!BB",
                self.error_code, self.error_subcode) + data



class Update:
    def read(self, data):
        pass
    

class Keepalive:
    def write(self):
        return b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff" + struct.pack("!HB", 19, 4)

