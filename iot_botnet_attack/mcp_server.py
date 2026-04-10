#!/usr/bin/env python3
# mcp_server.py
import asyncio
import json
import httpx
from mcp.server.fastmcp import FastMCP

# Initialisation du serveur MCP
mcp = FastMCP("IoT-Botnet-Controller")
API_BASE = "http://localhost:8000"

@mcp.tool()
async def list_bots() -> str:
    """Récupère l'état actuel du botnet et l'IP du broker."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{API_BASE}/status")
            return json.dumps(r.json(), indent=2)
        except Exception as e:
            return f"Error: {e}"

@mcp.tool()
async def trigger_attack(mode: str, bias: float = 0.0) -> str:
    """
    Déclenche une attaque sur le botnet.
    Modes disponibles: 'NORMAL', 'ATTACK', 'FREEZE', 'REPLAY', 'FLOOD', 'KILL'
    """
    payload = {
        "target": "all",
        "mode": mode,
        "params": {"bias": bias}
    }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{API_BASE}/command", json=payload)
            return f"Command {mode} sent successfully: {r.text}"
        except Exception as e:
            return f"Error connecting to api_server: {e}"

@mcp.tool()
async def deploy_clones(count: int = 5) -> str:
    """Déploie plusieurs nouveaux bots simulés sur le réseau."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{API_BASE}/spawn", json={"count": count})
            return f"Spawned {count} bots: {r.text}"
        except Exception as e:
            return f"Error: {e}"

if __name__ == "__main__":
    mcp.run()
