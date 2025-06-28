import subprocess
import json
import os
import time

from tailscale_types import TailscaleStatus
from utils import extend_env, get_public_ipv4


def run_tailscale(*args):
    result = subprocess.run(
        ["tailscale"] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=extend_env(no_proxy=True),
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def tailscale_up(*, authkey: str | None = None, exit_node: str | None = None):
    status, stdout, stderr = run_tailscale(
        "up",
        "--reset",
        *(["--auth-key", authkey] if authkey else []),
        "--hostname",
        os.environ.get("TS_NAME", "music-downloader"),
        *(
            ["--exit-node", exit_node, "--exit-node-allow-lan-access"]
            if exit_node
            else []
        ),
        "--json",
    )
    if status != 0:
        raise RuntimeError(f"Tailscale up command failed: {stdout}{stderr}")


def wait_for_tailscale():
    while True:
        try:
            status, stdout, stderr = run_tailscale("status")
            if status == 0:
                return
        except Exception as e:
            print(f"Error checking Tailscale status: {e}")
        time.sleep(0.5)  # Wait before retrying


def tailscale_status():
    status, stdout, stderr = run_tailscale("status", "--json")
    if status != 0:
        raise RuntimeError(f"Tailscale status command failed: {stdout}{stderr}")
    try:
        status_data: TailscaleStatus = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Tailscale status JSON: {e}") from e
    return status_data


def tailscale_exit_nodes():
    status = tailscale_status()
    nodes = status.get("Peer", {}).values()
    exit_nodes = [
        node
        for node in nodes
        if node.get("ExitNodeOption", False) and node.get("Online", False)
    ]
    return exit_nodes


def tailscale_setup():
    authkey = os.environ.get("TS_AUTHKEY")
    if not authkey:
        raise ValueError("TS_AUTHKEY environment variable is not set")
    exit_node_name = os.environ.get("TS_EXIT_NODE")
    if not exit_node_name:
        raise ValueError("TS_EXIT_NODE environment variable is not set")

    tailscale_up(authkey=authkey)
    print(f"Public IPv4: {get_public_ipv4()}")

    exit_nodes = tailscale_exit_nodes()
    print("Exit Nodes:")
    for node in exit_nodes:
        print(f"- {node['DNSName'][:-1]} ({node['Relay']})")

    matching_nodes = [
        node for node in exit_nodes if node["DNSName"].startswith(exit_node_name)
    ]
    if len(matching_nodes) != 1:
        raise RuntimeError(
            f"Expected exactly one exit node matching '{exit_node_name}', found {len(matching_nodes)}"
        )
    exit_node = matching_nodes[0]
    print(f"Setting exit node to: {exit_node['DNSName'][:-1]} ({exit_node['Relay']})")
    tailscale_up(exit_node=exit_node["DNSName"])
    time.sleep(1)
    print("Tailscale is up and running with the specified exit node")

    print(f"Public IPv4: {get_public_ipv4()}")
