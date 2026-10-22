import asyncio 
import importlib
import json 
import sys

from mcp.client import Client

server = importlib.import_module(sys.argv[1]).mcp

async def main():
    async with Client(server) as client:
        listing =  await client.list_tools()
        for tool in listing.tools:
            print("=" * 60)
            print("name:", tool.name)
            first_line = (tool.description or "").strip().splitlines()[0:1]
            print("description", first_line[0] if first_line else "no have description")
            print("arguments", json.dumps(tool.input_schema, ensure_ascii=False, indent=2))
            print("result", json.dumps(tool.output_schema, ensure_ascii=False))
asyncio.run(main())
