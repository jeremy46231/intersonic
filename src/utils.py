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
    print(os.environ.get("ALL_PROXY", ""))
    return requests.get("https://api.ipify.org").text
