import asyncio

from tailscale import tailscale_suggested_exit_node, wait_for_tailscale, tailscale_exit_nodes

print("Hello from main.py!")

async def main():
    await wait_for_tailscale()
    
    exit_nodes = await tailscale_exit_nodes()
    print("Exit Nodes:")
    for node in exit_nodes:
        print(f"- {node['DNSName'][:-1]} ({node['Relay']})")
    suggested_exit_node = await tailscale_suggested_exit_node()
    print(f"Suggested Exit Node: {suggested_exit_node}")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
