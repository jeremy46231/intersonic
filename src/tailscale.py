import subprocess
import asyncio
import json

from tailscale_types import TailscaleStatus


async def run_tailscale(*args):
    command = "tailscale"
    process = await asyncio.create_subprocess_exec(
        command, *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()


async def wait_for_tailscale():
    while True:
        try:
            status, stdout, stderr = await run_tailscale("status")
            if status == 0:
                print("Tailscale is running.")
                return
        except Exception as e:
            print(f"Error checking Tailscale status: {e}")
        await asyncio.sleep(0.5)  # Wait before retrying


async def tailscale_status():
    status, stdout, stderr = await run_tailscale("status", "--json")
    if status != 0:
        raise RuntimeError(f"Tailscale status command failed: {stderr}")
    try:
        status_data: TailscaleStatus = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Tailscale status JSON: {e}")
    return status_data


async def tailscale_exit_nodes():
    status = await tailscale_status()
    nodes = status.get("Peer", {}).values()
    exit_nodes = [
        node
        for node in nodes
        if node.get("ExitNodeOption", False) and node.get("Online", False)
    ]
    return exit_nodes
