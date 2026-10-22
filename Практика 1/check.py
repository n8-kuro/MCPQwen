import asyncio 

from mcp.client import Client

from group_tools import mcp as server

async def main():
    async with Client(server) as client:
        tools = await client.list_tools()
        print("Инструменты:", [t.name for t in tools.tools])

        result = await client.call_tool("average_grade", {"grades": [5, 4, 5, 3]})
        print("Среднее:",  result.content[0].text)

        bad = await client.call_tool("average_grade", {"grades": []})
        print("Признак ошибки:", bad.is_error)
        print("Текст:", bad.content[0].text)

asyncio.run(main())
