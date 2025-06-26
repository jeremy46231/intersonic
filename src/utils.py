import requests
import os


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
        response = session.get("https://api.ipify.org", timeout=60)
        response.raise_for_status()
        return response.text
