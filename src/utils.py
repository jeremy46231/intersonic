from typing import Tuple, Optional
import requests
import os

LyricLine = Tuple[Optional[int], str]  # (ms, text)


def to_ms(min_str: str, sec_str: str, ms_str: str) -> int:
    # Ensure ms is 3 digits (pad with zeros if needed)
    ms_str = ms_str.ljust(3, "0")
    return int(min_str) * 60000 + int(sec_str) * 1000 + int(ms_str)


def extend_env(
    variables: dict[str, str] = {}, no_proxy: bool = False
) -> dict[str, str]:
    """Extend the environment dictionary with additional variables."""
    env = os.environ.copy()
    env.update(variables)
    if no_proxy:
        for key in list(env):
            if key.upper() in {"ALL_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"}:
                del env[key]
    return env


def get_public_ipv4():
    """
    Fetches the public IPv4 address using a new, isolated request session.
    This prevents connection pooling issues when network settings (like a
    Tailscale exit node) change during the script's lifetime.
    """
    # Using a new Session for each call ensures no old connections are reused.
    with requests.Session() as session:
        # The session will automatically detect and use the proxy environment variables.
        try:
            response = session.get("https://api.ipify.org", timeout=60)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise RuntimeError(f"Failed to get public IPv4 address: {e}") from e
