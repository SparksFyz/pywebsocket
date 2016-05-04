#encoding:utf-8
import collections

class WebSocket(object):

    def __init__(self, protocol):
        self.protocol = protocol
        self.closed = False
        self._message_queue = collections.deque()

    def __iter__(self):
        while True:
            message = self.wait()
            yield message
            if message is None:
                break

    def accept_connection(self):
        self.protocol.accept_connection()

    def send(self, message):
        if not self.closed:
            self.protocol.write(message)

    def _get_new_messages(self):
        if self.protocol.can_read():
            self._message_queue.append(self.protocol.read())
            if self._message_queue:
                return

    def read(self):

        if self._message_queue:
            return self._message_queue.popleft()
        self._get_new_messages()
        if self._message_queue:
            return self._message_queue.popleft()
        return

    def wait(self):
        if not self._message_queue:
            if self.closed:
                return None
            new_data = self.read()
            if not new_data:
                return None
            self._message_queue.append(new_data)
        return self._message_queue.popleft()

    def close(self, code=None, reason=None):
        if not self.closed:
            self.protocol.close(code, reason)
            self.closed = True
