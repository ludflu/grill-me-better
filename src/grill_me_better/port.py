"""Find a free localhost port."""

from __future__ import annotations

import socket

from grill_me_better.paths import DEFAULT_HOST, DEFAULT_PORT_START


def pick_port(host: str = DEFAULT_HOST, start: int = DEFAULT_PORT_START) -> int:
    port = start
    while port < start + 500:
        if is_port_free(host, port):
            return port
        port += 1
    raise RuntimeError(f"No free port found from {start}")


def resolve_serve_port(host: str, preferred: int | None) -> int:
    """Use preferred port when free; otherwise scan from DEFAULT_PORT_START."""
    if preferred is not None and is_port_free(host, preferred):
        return preferred
    return pick_port(host, DEFAULT_PORT_START)


def is_port_free(host: str, port: int) -> bool:
    return _is_free(host, port)


def _is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True
