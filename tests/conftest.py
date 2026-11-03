import socket

import pytest

_real_connect = socket.socket.connect


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests must never reach the internet (WhatsApp, Claude, Google...). Local loopback and unix sockets stay allowed."""
    def guard(self, address, *args, **kwargs):
        if self.family == socket.AF_UNIX or (isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1", "localhost")):
            return _real_connect(self, address, *args, **kwargs)
        raise RuntimeError(f"network access attempted in a test: {address}")

    def no_dns(*args, **kwargs):
        raise RuntimeError(f"DNS lookup attempted in a test: {args[:1]}")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "getaddrinfo", no_dns)
