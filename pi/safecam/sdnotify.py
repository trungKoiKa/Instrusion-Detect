"""Báo trạng thái cho systemd (READY=1, WATCHDOG=1) qua socket trong NOTIFY_SOCKET.

Không có biến NOTIFY_SOCKET (chạy tay, laptop, pytest) thì không làm gì.
"""
import os
import socket


def socket_address(addr):
    """Đổi địa chỉ '@...' (socket ẩn của Linux) thành '\\0...'; địa chỉ thường giữ nguyên."""
    if addr.startswith("@"):
        return "\0" + addr[1:]
    return addr


def notify(msg):
    """Gửi chuỗi msg cho systemd. Trả True nếu gửi được; lỗi không làm dừng chương trình."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(socket_address(addr))
            sock.sendall(msg.encode())
        return True
    except OSError:
        return False
