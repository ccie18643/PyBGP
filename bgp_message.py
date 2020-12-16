#!/usr/bin/env python3

############################################################################
#                                                                          #
#  PyBGP - Python BGP implementation                                       #
#  Copyright (C) 2020  Sebastian Majewski                                  #
#                                                                          #
#  This program is free software: you can redistribute it and/or modify    #
#  it under the terms of the GNU General Public License as published by    #
#  the Free Software Foundation, either version 3 of the License, or       #
#  (at your option) any later version.                                     #
#                                                                          #
#  This program is distributed in the hope that it will be useful,         #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#  GNU General Public License for more details.                            #
#                                                                          #
#  You should have received a copy of the GNU General Public License       #
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                          #
#  Author's email: ccie18643@gmail.com                                     #
#  Github repository: https://github.com/ccie18643/PyBGP                   #
#                                                                          #
############################################################################


import socket
import struct

OPEN = 1
UPDATE = 2
NOTIFICATION = 3
KEEPALIVE = 4

HEADER_SIZE = 19

# Error codes
MESSAGE_HEADER_ERROR = 1
OPEN_MESSAGE_ERROR = 2
UPDATE_MESSAGE_ERROR = 3
HOLD_TIMER_EXPIRED = 4
FINITE_STATE_MACHINE_ERROR = 5
CEASE = 6

# Meassage header error subcodes
CONNECTION_NOT_SYNCHRONISED = 1
BAD_MESSAGE_LENGTH = 2
BAD_MESSAGE_TYPE = 3

# OPEN message error subcodes
UNSUPPORTED_VERSION_NUMBER = 1
BAD_PEER_AS = 2
BAD_BGP_IDENTIFIER = 3
UNSUPPORTED_OPTIONAL_PARAMETER = 4
UNACCEPTABLE_HOLD_TIME = 6

# UPDATE message error subcodes
MALFORMED_ATTRIBUTE_LIST = 1
UNRECOGNIZED_WELL_KNOWN_ATTRIBUTE = 2
MISSING_WELL_KNOWN_ATTRIBUTE = 3
ATTRIBUTE_FLAGS_ERROR = 4
ATTRIBUTE_LENGTH_WRROR = 5
INVALID_ORIGIN_ATTRIBUTE = 6
INVALID_NEXT_HOP_ATTRIBUTE = 8
OPTIONAL_ATTRIBUTE_ERROR = 9
INVALID_NETWORK_FIELD = 10
MALFORMED_AS_PATH = 11


class DecodeMessage:
    def __init__(self, data, local_id="0.0.0.0", peer_asn=0):

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
            if m[0] != 0xFF:
                self.message_error_code = MESSAGE_HEADER_ERROR
                self.message_error_subcode = CONNECTION_NOT_SYNCHRONISED
                return

        self.length, self.type = struct.unpack("!HB", data[16:19])

        # Validate Length field
        if self.length < 19 or self.length > 4096:
            self.message_error_code = MESSAGE_HEADER_ERROR
            self.message_error_subcode = BAD_MESSAGE_LENGTH
            self.message_error_data = struct.pack("!H", self.length)
            return

        # Validate Type field
        if self.type not in {OPEN, UPDATE, NOTIFICATION, KEEPALIVE}:
            self.message_error_code = MESSAGE_HEADER_ERROR
            self.message_error_subcode = BAD_MESSAGE_TYPE
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
                self.message_error_code = MESSAGE_HEADER_ERROR
                self.message_error_subcode = BAD_MESSAGE_LENGTH
                self.message_error_data = struct.pack("!H", self.length)
                return

            self.version, self.asn, self.hold_time, self.id, self.opt_len = struct.unpack("!BHHIB", data[19:29])
            self.id = socket.inet_ntoa(struct.pack("!L", self.id))
            self.opt_param = data[29 : self.length]

            if self.version != 4:
                self.message_error_code = OPEN_MESSAGE_ERROR
                self.message_error_subcode = UNSUPPORTED_VERSION_NUMBER

            if self.asn != peer_asn:
                self.message_error_code = OPEN_MESSAGE_ERROR
                self.message_error_subcode = BAD_PEER_AS

            # <!!!> Need to check for valid unicast IP
            if self.id == local_id:
                self.message_error_code = OPEN_MESSAGE_ERROR
                self.message_error_subcode = BAD_BGP_IDENTIFIER

            # <!!!> Need to add check for supported optional parameters

            if self.hold_time in {1, 2}:
                self.message_error_code = OPEN_MESSAGE_ERROR
                self.message_error_subcode = UNACCEPTABLE_HOLD_TIME

        if self.type == UPDATE:
            pass

        if self.type == NOTIFICATION:

            # Validate Length field
            if self.length < 19 + 2:
                self.message_error_code = 1
                self.message_error_subcode = 2
                self.message_error_data = struct.pack("!H", self.length)
                return

            self.error_code, self.error_subcode = struct.unpack("!BB", data[19:21])
            self.error_data = data[21 : self.length]

        if self.type == KEEPALIVE:
            pass


class Open:
    def __init__(self, local_id, local_asn, local_hold_time=180, opt=b"", version=4):
        self.len = 19 + 10 + len(opt)
        self.type = OPEN
        self.version = version
        self.asn = local_asn
        self.hold_time = local_hold_time
        self.bgp_id = struct.unpack("!L", socket.inet_aton(local_id))[0]
        self.opt_len = len(opt)
        self.opt = opt

    def write(self):
        return (
            b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
            + struct.pack("!HB", self.len, self.type)
            + struct.pack("!BHHIB", self.version, self.asn, self.hold_time, self.bgp_id, self.opt_len)
            + self.opt
        )


class Notification:
    def __init__(self, error_code, error_subcode=0, data=b""):
        self.len = 19 + 2 + len(data)
        self.type = NOTIFICATION
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.data = data

    def write(self):
        return (
            b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
            + struct.pack("!HB", self.len, self.type)
            + struct.pack("!BB", self.error_code, self.error_subcode)
            + self.data
        )


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
