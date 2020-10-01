import struct
import socket

OPEN = 1
UPDATE = 2
NOTIFICATION = 3
KEEPALIVE = 4

HEADER_SIZE = 19


class DecodeMessage():
    def __init__(self, data):
      
        self.data_length_error = False
        self.data_length_expected = 19
        self.data_length_received = len(data)

        self.message_error_code = 0
        self.message_error_subcode = 0
        self.message_error_data = b""

        # Validate if there is enough data to decode header
        if len(data) < 19:
            self.data_length_error = True
            return

        # Validate Marker field
        for m in struct.iter_unpack("!B", data[:16]):
            if m[0] != 0xff:
                self.message_error_code = 1
                self.message_error_subcode = 1
                return

        self.length, self.type = struct.unpack("!HB", data[16:19])

        # Validate Length field
        if self.length < 19 or self.length > 4096:
            self.message_error_code = 1
            self.message_error_subcode = 2
            self.message_error_data = struct.pack("!H", self.length)
            return

        # Validate Type field
        if self.type not in {OPEN, UPDATE, NOTIFICATION, KEEPALIVE}:
            self.message_error_code = 1
            self.message_error_subcode = 3
            self.message_error_data = struct.pack("!B", self.type)
            return

        # Validate if there is enough data to decode rest of message
        if len(data) < self.length:
            self.data_length_error = True
            self.data_length_expected = self.length
            return

        if self.type == OPEN:

            # Validate Length field
            if self.length < 19 + 10:
                self.message_error_code = 1
                self.message_error_subcode = 2
                self.message_error_data = struct.pack("!H", self.length)
                return

            self.version, self.asn, self.hold_time, self.bgp_id, self.opt_len = struct.unpack("!BHHIB", data[19:29])
            opt_param = data[29:self.length]

        if self.type == UPDATE:
            pass

        if self.type == NOTIFICATION:

            # Validate Length field
            if self.length < 19 + 2:
                self.message_error_code = 1
                self.message_error_subcode = 2
                self.message_error_data = struct.pack("!H", self.length)
                return

            self.error_code, self.error_subcode = struct.unpack("!BB", data[:2])

        if self.type == KEEPALIVE:
            pass


class Open:
    def __init__(self, asn, bgp_id, hold_time=180, opt=b"", version=4):
        self.len = 19 + 10 + len(opt)
        self.type = OPEN
        self.version = version
        self.asn = asn
        self.hold_time = hold_time
        self.bgp_id = struct.unpack("!L", socket.inet_aton(bgp_id))[0]
        self.opt_len = len(opt)
        self.opt = opt

    def write(self):
        return b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff" + struct.pack("!HB",
                self.len, self.type) + struct.pack("!BHHIB", self.version, self.asn, self.hold_time, self.bgp_id, self.opt_len) + self.opt


class Notification:
    def __init__(self, error_code, error_subcode=0, data=b""):
        self.len = 19 + 2 + len(data)
        self.type = NOTIFICATION
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.data = data

    def write(self):
        return b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff" + struct.pack("!HB",
                self.len, self.type) + struct.pack("!BB",
                self.error_code, self.error_subcode) + self.data


class Update:
    def __init__(self):
        pass
    

class Keepalive:
    def __init__(self):
        pass

    def write(self):
        self.len = 19
        self.type = KEEPALIVE
        return b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff" + struct.pack("!HB", self.len, self.type)

