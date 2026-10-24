"""Find a free localhost port."""

from __future__ import annotations

import socket

from grill_me_better.paths import DEFAULT_HOST, DEFAULT_PORT_START


def pick_port(host: str = DEFAULT_HOST, start: int = DEFAULT_PORT_START) -> int:
    port = start
    while port < start + 500:
        if _is_free(host, port):
            return port
        port += 1
    raise RuntimeError(f"No free port found from {start}")


def _is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True
