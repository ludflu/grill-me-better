"""Port selection for serve."""

from __future__ import annotations

from grill_me_better.port import is_port_free, resolve_serve_port


def test_resolve_serve_port_returns_bindable_port() -> None:
    preferred = 8765
    port = resolve_serve_port("127.0.0.1", preferred)
    assert is_port_free("127.0.0.1", port)
    if is_port_free("127.0.0.1", preferred):
        assert port == preferred
    else:
        assert port > preferred
