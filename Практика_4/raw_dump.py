"""Показать сырые JSON запроса и ответа Ollama при вызове инструмента.

Ничего не скрывает: печатает список инструментов ров в том виде, в каком он уходит модели,
и ответ модели целиком, вместе с полем thinking и tool_calls.

Запуск: python raw_dump.py
"""

import asyncio 
import json

from mcp.client import Client

from bridge import MODEL, OLLAMA_URL, SYSTEM_PORT, ask_ollama, to_ollama_tools
from pickup_point import mcp as server

QUESTION = "Сколько стоит доставить посылку в 3 кг в Казань?"

def show(title: str, data) -> None: 
    print(f"\n===== {title} =====")
    print(json.dumps(data, ensure_ascii=False, indent=2))

async def main() -> None:
    async with Client(server) as client:
        listing = await client.list_tools()
        tools = to_ollama_tools(listing.tools)

        messages = [
            {"role": "system", "content": SYSTEM_PROMT}, 
            {"role": "user", "content": QUESTION}, 
        ]

        show("ЧТО УХОДИТ В OLLAMA (адрес " + OLLAMA_URL +")",
        {"model": MODEL, "messages": messages, "tools": tools[:1] + ["...еще"], 
         "stream": False
        })

        reply = ask_ollama(messages, tools)
        show("ОТВЕТ МОДЕЛИ ЦЕЛИКОМ", reply)

        calls = reply["message"].get("tool_calls") or []
        if not calls: 
            print("\nМодель не стала вызвать инструмент - попробуйте еще раз.")
            return 

        call = calls[0]["function"]
        result = await client.call_tool(call["name"], call["arguments"])
        show("ЧТО ВЕРНУЛИ MCP-СЕРВЕР", {
            "is_error": result.is_error, 
            "content": [block.text for block in result.content], 
            "structured_content": result.structured_content
        })

        messages.append(reply["message"])
        messages.append({
            "role": "tool", 
            "tool_name": call["name"], 
            "content": result.content[0].text, 
        })
        final = ask_ollama(messages, tools)
        show("ВТОРОЙ ЗАПРОС: ОТВЕТ ПОСЛЕ РЕЗУЛЬТАТА", final["message"])

asyncio.run(main())
