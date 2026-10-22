"""Мост между локальной моделью Ollama и MCP-сервером пункта выдачи заказов.

Запуск:  python bridge.py "Сколько стоит доставить 3 кг в Казань?"
Без аргумента отрабатывает сценарий из трёх вопросов подряд.
"""

import asyncio
import json
import sys
import urllib.error
import urllib.request

from mcp.client import Client

from pickup_point import mcp as server

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"

SYSTEM_PORT = (
     "Ты — оператор пункта выдачи заказов. Отвечай ТОЛЬКО на русском языке, "
    "коротко и по делу. Для расчётов и справок обязательно вызывай доступные "
    "инструменты, не придумывай цифры сам. Ответ строй по данным инструмента."
)

def ask_ollama(message: list[dict], tools: list[dict]) -> dict:
    """ Отправить один запрос в Ollama и вернуть разобранный ответ целиком."""
    payload = {
        "model": MODEL,
        "messages": message, 
        "tools": tools, 
        "stream": False, 
    }
    request = urllib.request.Request(
        OLLAMA_URL, 
        data=json.dumps(payload).encode("utf-8"), 
        headers={"Content-Type": "application/json"}, 
    )
    try: 
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.load(response)
    except urllib.error.URLError as error: 
        raise SystemExit(
            f"Ollama не отвечает по адресу {OLLAMA_URL}: {error}. "
            "Запустите ollama serve и проверьте, что модель скачана."
        ) from error

def to_ollama_tools(mcp_tools) -> list[dict]:
    """Перевести описание инструментов MCP в формат, понятный Ollama"""
    return [
        {
            "type": "function", 
            "function": {
                "name": tool.name, 
                "description": tool.description, 
                "parameters": tool.input_schema,
            },
        }
        for tool in mcp_tools
    ] 

async def answer(client: Client, tools: list[dict], messages: list[dict]) -> str:
    """Провести полный цикл: запрос - вызовы инструментов - финальный ответ."""
    for step in range(1, 6):
        reply = ask_ollama(messages, tools)
        message = reply["message"]
        message.pop("thinking", None)
        calls = message.get("tool_calls") or []
        messages.append(message)

        if not calls:
            return message.get("content", "").strip()

        for call in calls:
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            print(f" [шаг {step}] модель просит вызвать {name} с {arguments}")

            result = await client.call_tool(name, arguments)
            text = result.content[0].text if result.content else ""
            mark = "ОШИБКА" if result.is_error else "ок"
            print(f" [шаг {step} сервер ответил ({mark}): {text}]")

            messages.append({"role": "tool", "tool_name": name, "content": text})

    return "Модель зациклилалсь на вызовах инструментов, прерываю."

async def main() -> None:
    questions = sys.argv[1:] or [
        "Сколько стоит доставить посылку 3 кг в Казань?", 
        "А если посылка будет весить 7 килограммов?", 
        "Когда мне нужно забрать заказ PVZ-1042?",
    ]

    async with Client(server) as client:
        listing = await client.list_tools()
        tools = to_ollama_tools(listing.tools)
        print("Инструменты сервера:", [tool.name for tool in listing.tools])
        print(f"Модель: {MODEL}\n")

        messages = [{"role": "system", "content": SYSTEM_PROMT}]
        for question in questions:
            print(f"Вопрос: {question}")
            messages.append({"role": "user", "content": question})
            final = await answer(client, tools, messages)
            print(f"Ответ модели: {final}\n")

if __name__ == "__main__":
    asyncio.run(main())
    
