"""Проверка контракта: что происходит при верных и заведомо неверных аргументах.

Каждая строка отчёта — один вызов инструмента: признак ошибки, текстовый
результат и структурированный результат.

Запуск: python type_probe.py
"""

import asyncio

from mcp.client import Client

from canteen_tools import mcp as server 

PROBES = [
     ("menu_for_day", {"day": "среда"}, "по умолчанию обед"),
    ("menu_for_day", {"day": "среда", "meal": "завтрак"}, "явно указан завтрак"),
    ("menu_for_day", {"day": "суббота"}, "дня нет в наборе Literal"),
    ("menu_for_day", {}, "не передан обязательный аргумент"),
    ("dish_info", {"dish": "Борщ"}, "регистр не важен"),
    ("dish_info", {"dish": "шаурма"}, "блюда нет в справочнике"),
    ("order_total", {"dishes": ["борщ", "компот"]}, "обычный заказ"),
    ("order_total", {"dishes": ["борщ", "компот"], "student_card": True}, "со скидкой"),
    ("order_total", {"dishes": ["борщ"], "student_card": "true"}, "строка вместо булева"),
    ("order_total", {"dishes": ["борщ"], "student_card": "да"}, "непонятная строка"),
    ("order_total", {"dishes": '["борщ", "компот"]'}, "список прислан строкой JSON"),
    ("order_total", {"dishes": "борщ, компот"}, "список прислан обычной строкой"),
    ("order_total", {"dishes": []}, "пустой список"),
    ("order_total", {"dishes": ["борщ"], "student_card": True, "table": 7},
     "лишний аргумент, которого нет в схеме"),
    ("find_dishes", {}, "все аргументы по умолчанию"),
    ("find_dishes", {"max_price": "70", "vegetarian": True}, "число прислано строкой"),
    ("find_dishes", {"limit": 3}, "ограничение длины ответа"),
    ("find_dishes", {"limit": 3.5}, "дробное значение для аргумента int"),
    ("find_dishes", {"limit": 3.0}, "дробное с нулевой дробной частью для int"),
    ("find_dishes", {"limit": "два"}, "буквы вместо числа"),
    ("find_dishes", {"max_price": 0}, "нарушено правило внутри инструмента"),
    ("find_dishes", {"keyword": "шаверма"}, "ничего не найдено, но это не ошибка"),
    ("reserve_lunch", {"student": "Петров Илья", "day": "вторник",
                       "dishes": ["суп гороховый", "гречка отварная"]}, "запись заказа"),
    ("reserve_lunch", {"student": "  ", "day": "вторник", "dishes": ["борщ"]},
     "пустое имя студента"),
]

async def main() -> None:
    async with Client(server) as client:
        for name, arguments, comment in PROBES:
            result = await client.call_tool(name, arguments)
            print("-" * 72 )
            print(f"{name}{arguments})  # (comment")
            print(f"  is_error = {result.is_error}")
            print(f"  блоков в content: {len(result.content)}")
            texts = [getattr(block, "text", repr(block)) for block in result.content]
            preview = texts[0].replace("\n", " ") if texts else ""
            print(f"  content[0] = {preview[:150]}")
            print(f"  structured_content = {str(result.structured_content)[:150]}")


asyncio.run(main())