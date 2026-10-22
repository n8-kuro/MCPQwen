""" Печатает схему каждого инструмента сервера - ровно то, что видит модель.

Запуск: python show_schema.py            (сервер столовой)
        python show_schema.py weak_tools (сервер с испорченным контрактом)
"""

import asyncio
import importlib
import json
import sys

from mcp.client import Client


module_name = sys.argv[1] if len(sys.argv) > 1 else "canteen_tools"
server = importlib.import_module(module_name).mcp

def describe_property(name: str, spec: dict, required: list[str]) -> str:
    """Собрать человекочитаемую строку про один аргумент."""
    kind  = spec.get("type", "?")
    if "enum" in spec:
        kind = "одно из: " + ", ".join(str(value) for value in spec["enum"])
    if "anyOf" in spec:
        kind = " или ".join(part.get("type", "?") for part in spec["anyOf"])
    if kind == "array":
        kind = "array из " + spec.get("items", {}).get("type", "?")
    mark = "обязательный" if name in required else f"по умолчанию {spec.get('default')!r}"
    return f"    {name}: {kind} ({mark})"

    
async def main() -> None:
    async with Client(server) as client:
     listing = await client.list_tools()
     print(f"Инструментов на сервере: {len(listing.tools)}")
     for tool in listing.tools:
        print()
        print("=" * 72)
        print("Имя:     ", tool.name)
        print("заголовок:", tool.title)
        first_line = (tool.description or "").strip().splitlines()[0:1]
        print("описание:  ", first_line[0] if first_line else "(empty!)")
        print("Длина описания, символов:", len(tool.description or ""))

        schema = tool.input_schema
        required = schema.get("required", [])
        print("аргументы")
        if not schema.get("properties"):
            print("    (нет)")
        for name, spec in schema.get("properties", {}).items():
            print(describe_property(name, spec, required))

        if tool.output_schema is None:
            print("схема результатов: ОТСУСТВУЕТ (structured_content будет пустым)")
        else:
            print("Схема результата:", 
                  json.dumps(tool.output_schema, ensure_ascii=False))

        if tool.annotations is not None:
            print("подсказки", json.dumps(tool.annotations.model_dump(exclude_none=True, by_alias=True), ensure_ascii=False))

    print()
    print("=" * 72)
    print("Схема menu_for_day целиком, как она уходит по протоколу:")
    for tool in listing.tools:
        if tool.name == "menu_for_day":
            print(json.dumps(tool.model_dump(exclude_none=True, by_alias=True), ensure_ascii=False, indent=2))

asyncio.run(main())