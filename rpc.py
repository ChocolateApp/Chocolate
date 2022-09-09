# References:
# * https://github.com/devsnek/discord-rpc/tree/master/src/transports/IPC.js
# * https://github.com/devsnek/discord-rpc/tree/master/example/main.js
# * https://github.com/discordapp/discord-rpc/tree/master/documentation/hard-mode.md
# * https://github.com/discordapp/discord-rpc/tree/master/src
# * https://discordapp.com/developers/docs/rich-presence/how-to#updating-presence-update-presence-payload-fields

from abc import ABCMeta, abstractmethod
import json
import logging
import os
import socket
import sys
import struct
import uuid

OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2
OP_PING = 3
OP_PONG = 4

logger = logging.getLogger(__name__)


class DiscordIpcError(Exception):
    pass


class DiscordIpcClient(metaclass=ABCMeta):

    """Work with an open Discord instance via its JSON IPC for its rich presence API.

    In a blocking way.
    Classmethod `for_platform`
    will resolve to one of WinDiscordIpcClient or UnixDiscordIpcClient,
    depending on the current platform.
    Supports context handler protocol.
    """

    def __init__(self, client_id):
        self.client_id = client_id
        self._connect()
        self._do_handshake()
        logger.info("connected via ID %s", client_id)

    @classmethod
    def for_platform(cls, client_id, platform=sys.platform):
        if platform == 'win32':
            return WinDiscordIpcClient(client_id)
        else:
            return UnixDiscordIpcClient(client_id)

    @abstractmethod
    def _connect(self):
        pass

    def _do_handshake(self):
        ret_op, ret_data = self.send_recv({'v': 1, 'client_id': self.client_id}, op=OP_HANDSHAKE)
        # {'cmd': 'DISPATCH', 'data': {'v': 1, 'config': {...}}, 'evt': 'READY', 'nonce': None}
        if ret_op == OP_FRAME and ret_data['cmd'] == 'DISPATCH' and ret_data['evt'] == 'READY':
            return
        else:
            if ret_op == OP_CLOSE:
                self.close()
            raise RuntimeError(ret_data)

    @abstractmethod
    def _write(self, date: bytes):
        pass

    @abstractmethod
    def _recv(self, size: int) -> bytes:
        pass

    def _recv_header(self) -> (int, int):
        header = self._recv_exactly(8)
        return struct.unpack("<II", header)

    def _recv_exactly(self, size) -> bytes:
        buf = b""
        size_remaining = size
        while size_remaining:
            chunk = self._recv(size_remaining)
            buf += chunk
            size_remaining -= len(chunk)
        return buf

    def close(self):
        logger.warning("closing connection")
        try:
            self.send({}, op=OP_CLOSE)
        finally:
            self._close()

    @abstractmethod
    def _close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def send_recv(self, data, op=OP_FRAME):
        self.send(data, op)
        return self.recv()

    def send(self, data, op=OP_FRAME):
        logger.debug("sending %s", data)
        data_str = json.dumps(data, separators=(',', ':'))
        data_bytes = data_str.encode('utf-8')
        header = struct.pack("<II", op, len(data_bytes))
        self._write(header)
        self._write(data_bytes)

    def recv(self) -> (int, "JSON"):
        """Receives a packet from discord.

        Returns op code and payload.
        """
        op, length = self._recv_header()
        payload = self._recv_exactly(length)
        data = json.loads(payload.decode('utf-8'))
        logger.debug("received %s", data)
        return op, data

    def set_activity(self, act):
        # act
        data = {
            'cmd': 'SET_ACTIVITY',
            'args': {'pid': os.getpid(),
                     'activity': act},
            'nonce': str(uuid.uuid4())
        }
        self.send(data)


class WinDiscordIpcClient(DiscordIpcClient):

    _pipe_pattern = R'\\?\pipe\discord-ipc-{}'

    def _connect(self):
        for i in range(10):
            path = self._pipe_pattern.format(i)
            try:
                self._f = open(path, "w+b")
            except OSError as e:
                logger.error("failed to open {!r}: {}".format(path, e))
            else:
                break
        else:
            return DiscordIpcError("Failed to connect to Discord pipe")

        self.path = path

    def _write(self, data: bytes):
        self._f.write(data)
        self._f.flush()

    def _recv(self, size: int) -> bytes:
        return self._f.read(size)

    def _close(self):
        self._f.close()


class UnixDiscordIpcClient(DiscordIpcClient):

    def _connect(self):
        self._sock = socket.socket(socket.AF_UNIX)
        pipe_pattern = self._get_pipe_pattern()

        for i in range(10):
            path = pipe_pattern.format(i)
            if not os.path.exists(path):
                continue
            try:
                self._sock.connect(path)
            except OSError as e:
                logger.error("failed to open {!r}: {}".format(path, e))
            else:
                break
        else:
            return DiscordIpcError("Failed to connect to Discord pipe")

    @staticmethod
    def _get_pipe_pattern():
        env_keys = ('XDG_RUNTIME_DIR', 'TMPDIR', 'TMP', 'TEMP')
        for env_key in env_keys:
            dir_path = os.environ.get(env_key)
            if dir_path:
                break
        else:
            dir_path = '/tmp'
        return os.path.join(dir_path, 'discord-ipc-{}')

    def _write(self, data: bytes):
        self._sock.sendall(data)

    def _recv(self, size: int) -> bytes:
        return self._sock.recv(size)

    def _close(self):
        self._sock.close()
