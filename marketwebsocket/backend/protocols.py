# encoding:utf-8
import os
import array
import struct
import select
import socket
import hashlib
import base64
import six
from errno import EINTR

try:
    import selectors
except ImportError:
    import selectors34 as selectors


class WebSocketProtocol13(object):

    OPCODE_TEXT = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CLOSE = 0x8
    OPCODE_PING = 0x9
    OPCODE_PONG = 0xa
    STATUS_NORMAL = 1000
    STATUS_GOING_AWAY = 1001
    STATUS_PROTOCOL_ERROR = 1002
    STATUS_UNSUPPORTED_DATA_TYPE = 1003
    STATUS_STATUS_NOT_AVAILABLE = 1005
    STATUS_ABNORMAL_CLOSED = 1006
    STATUS_INVALID_PAYLOAD = 1007
    STATUS_POLICY_VIOLATION = 1008
    STATUS_MESSAGE_TOO_BIG = 1009
    STATUS_INVALID_EXTENSION = 1010
    STATUS_UNEXPECTED_CONDITION = 1011
    STATUS_TLS_HANDSHAKE_ERROR = 1015

    def __init__(self, sock, headers, mask_outgoing=False):
        self.sock = sock
        self.headers = headers
        self.mask_outgoing = mask_outgoing
        self.close_code = None
        self.close_reason = None
        self.server_terminated = False
        self.client_terminated = False
        self.selector = selectors.DefaultSelector()

    def accept_connection(self):
        fields = ("HTTP_SEC_WEBSOCKET_KEY", "HTTP_SEC_WEBSOCKET_VERSION")
        if not all(map(self.headers.get, fields)):
            raise ValueError("Missing/Invalid WebSocket headers")

        subprotocol_header = ''
        subprotocols = self.headers.get(
            "HTTP_SEC_WEBSOCKET_PROTOCOL", '')
        subprotocols = [s.strip() for s in subprotocols.split(',')]
        if subprotocols:
            selected = self.select_subprotocol(subprotocols)
            if selected:
                assert selected in subprotocols
                subprotocol_header = (
                    "Sec-WebSocket-Protocol: %s\r\n" % selected
                )
        accept_header = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Accept: %s\r\n"
            "%s"
            "\r\n" % (
                self.compute_accept_value(
                    self.headers.get("HTTP_SEC_WEBSOCKET_KEY").encode("utf8")
                ).decode("utf8"),
                subprotocol_header
            )
        )
        try:
            self.sock.sendall(accept_header.encode("utf8"))
        except socket.error:
            self._abort()

    def read(self):
        try:
            opcode, data = self.read_data()
            return data
        except socket.error:
            self._abort()

    def write(self, message, binary=False):
        if binary:
            opcode = self.OPCODE_BINARY
        else:
            opcode = self.OPCODE_TEXT
        self._write_frame(True, opcode, message)

    def close(self, code=None, reason=None):
        self.close_code = code
        self.close_reason = reason
        if not self.server_terminated:
            if not reason:
                reason = b''
            if not code:
                code = self.STATUS_NORMAL
            self.write_close(code, reason)
            self.server_terminated = True
            self._abort()
        if self.client_terminated:
            self._abort()

    def read_data(self):
        """
        Recieve data with operation code.

        return  value: tuple of operation code and string(byte array) value.
        """
        while not self.server_terminated and not self.client_terminated:
            fin, opcode, data = self.read_frame()
            if opcode in (self.OPCODE_TEXT, self.OPCODE_BINARY):
                return (opcode, data)
            elif opcode == self.OPCODE_CLOSE:
                self.client_terminated = True
                close_code, close_reason = None, None
                if len(data) >= 2:
                    close_code = struct.unpack('>H', data[:2])[0]
                if len(data) > 2:
                    close_reason = data[2:]
                self.close(close_code, close_reason)
                return (opcode, None)
            elif opcode == self.OPCODE_PING:
                self.write_pong(data)
            else:
                raise ValueError(
                    "Unknown opcode %s(fin:%s, data:%s)" % (opcode, fin, data)
                )
        raise EOFError("EOF when reading a line, websocket has been closed")


    def read_frame(self):
        """
        resolving control frame and data frame from bytes
        """
        header_bytes = self._read_bytes(2)
        b1 = header_bytes[0] if six.PY3 else ord(header_bytes[0])
        fin = b1 >> 7 & 1
        opcode = b1 & 0xf
        b2 = header_bytes[1] if six.PY3 else ord(header_bytes[1])
        mask = b2 >> 7 & 1
        length = b2 & 0x7f

        if length == 0x7e:
            length_data = self._read_bytes(2)
            length = struct.unpack("!H", length_data)[0]
        elif length == 0x7f:
            length_data = self._read_bytes(8)
            length = struct.unpack("!Q", length_data)[0]
        mask_key = ""
        if mask:
            mask_key = self._read_bytes(4)
        data = self._read_bytes(length)
        if mask:
            data = self.mask_or_unmask(mask_key, data)
        return fin, opcode, data

    def _read_bytes(self, bufsize):
        remaining = bufsize
        _bytes = b""
        while remaining:
            _buffer = self.sock.recv(bufsize)
            if not _buffer:
                raise socket.error(socket.EBADF, 'Bad file descriptor')
            _bytes += _buffer
            remaining = bufsize - len(_bytes)
        return _bytes
    def connected1(self):
        a = 1
        # self.sock.setblocking(False)

    def can_read(self, timeout=0.0):
        '''
        Return ``True`` if new data can be read from the socket.
        '''
        try:
            self.selector.register(self.sock, selectors.EVENT_READ, self.connected1())
            events = self.selector.select()
            self.selector.unregister(self.sock)
        except select.error as err:
            # self.selector.unregister(self.sock.fileno())
            self.selector.close()
            if err.args[0] == EINTR:
                return False
            self._abort()
        if events:
            return True
        return None

    def _write_frame(self, fin, opcode, data):
        if fin:
            finbit = 0x80
        else:
            finbit = 0
        frame = struct.pack("B", finbit | opcode)
        l = len(data)
        if self.mask_outgoing:
            mask_bit = 0x80
        else:
            mask_bit = 0
        if l < 126:
            frame += struct.pack("B", l | mask_bit)
        elif l <= 0xFFFF:
            frame += struct.pack("!BH", 126 | mask_bit, l)
        else:
            frame += struct.pack("!BQ", 127 | mask_bit, l)
        if self.mask_outgoing:
            mask = os.urandom(4)
            data = mask + self.mask_or_unmask(mask, data)
        frame += data
        try:
            self.sock.sendall(frame)
        except socket.error:
            self._abort()

    def write_ping(self, payload=""):
        """
        write ping data.

        payload: data payload to write server.
        """
        self._write_frame(True, self.OPCODE_PING, payload)

    def write_pong(self, data):
        """
        write pong data.

        payload: data payload to write server.
        """
        self._write_frame(True, self.OPCODE_PONG, data)

    def write_close(self, code=None, reason=None):
        """
        write close data to the server.
        reason: the reason to close. This must be string.
        """
        if code is None and reason is not None:
            code = self.STATUS_NORMAL
        if code is None:
            close_data = b''
        else:
            close_data = struct.pack('>H', code)
        if reason is not None:
            close_data += reason
        self._write_frame(True, self.OPCODE_CLOSE, close_data)

    def _abort(self):
        self.server_terminated = True
        self.client_terminated = True
        self.sock.close()  # forcibly tear down the connection

    @classmethod
    def mask_or_unmask(cls, mask, data):
        mask = array.array("B", mask)
        unmasked = array.array("B", data)
        for i in range(len(data)):
            unmasked[i] = unmasked[i] ^ mask[i % 4]
        if hasattr(unmasked, 'tobytes'):
            # In python 3.2: tostring() is renamed to tobytes() for clarity.
            return unmasked.tobytes()
        else:
            return unmasked.tostring()

    @classmethod
    def select_subprotocol(cls, subprotocols):
        pass

    @classmethod
    def compute_accept_value(cls, key):
        """
        Computes the value for the Sec-WebSocket-Accept header,
        given the value for Sec-WebSocket-Key.
        """
        sha1 = hashlib.sha1()
        sha1.update(key)
        sha1.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")  # Magic value
        return base64.b64encode(sha1.digest())


protocols = {
    '13': WebSocketProtocol13
}

get_websocket_protocol = protocols.get
