import asyncio
import os

from tailscale import (
    tailscale_up,
    wait_for_tailscale,
    tailscale_exit_nodes,
)
from utils import get_public_ipv4
from download import temp_download


async def main():
    print("Hello from main.py!")
    
    await tailscale_up(authkey=os.environ.get("TS_AUTHKEY"))
    print(f"Public IPv4: {get_public_ipv4()}")

    exit_nodes = await tailscale_exit_nodes()
    print("Exit Nodes:")
    for node in exit_nodes:
        print(f"- {node['DNSName'][:-1]} ({node['Relay']})")

    exit_node_name = os.environ.get("TS_EXIT_NODE")
    matching_nodes = [
        node for node in exit_nodes if node["DNSName"].startswith(exit_node_name)
    ]
    if len(matching_nodes) != 1:
        raise RuntimeError(
            f"Expected exactly one exit node matching '{exit_node_name}', found {len(matching_nodes)}"
        )
    exit_node = matching_nodes[0]
    print(f"Setting exit node to: {exit_node['DNSName'][:-1]} ({exit_node['Relay']})")
    await tailscale_up(exit_node=exit_node["DNSName"])
    await asyncio.sleep(1)
    print("Tailscale is up and running with the specified exit node.")

    print(f"Public IPv4: {get_public_ipv4()}")
    
    temp_download()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
