"""Test sdnotify: chạy trên laptop, không cần systemd."""
import socket
import sys

import pytest

from safecam.sdnotify import notify, socket_address


def test_no_socket_does_nothing(monkeypatch):
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    assert notify("READY=1") is False


def test_socket_address():
    assert socket_address("@abc") == "\0abc"
    assert socket_address("/run/systemd/notify") == "/run/systemd/notify"


@pytest.mark.skipif(sys.platform == "win32", reason="Windows không có socket Unix kiểu datagram")
def test_send_real(monkeypatch, tmp_path):
    path = str(tmp_path / "notify.sock")
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:  # systemd giả
        server.bind(path)
        monkeypatch.setenv("NOTIFY_SOCKET", path)
        assert notify("WATCHDOG=1") is True
        assert server.recv(100) == b"WATCHDOG=1"
