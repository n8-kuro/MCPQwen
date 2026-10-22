import logging
import sys
from datetime import date, timedelta

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr, 
    format="[ПВЗ] %(levelname)s %(message)s", 
)
log = logging.getLogger("pickup_point")

mcp = MCPServer("Пункт выдачи заказов")

TARIFFS = {
    "Казань": (250, 60),
    "Омск": (320, 80),
    "Новосибирск": (300, 75),
    "Екатеринбург": (280, 70),
}

ORDERS = { 
    "PVZ-1042": {
        "статус": "готов к выдаче", 
        "прибыл": date.today() - timedelta(days=5), 
        "получатель": "Смирнов А. П.", 
        "ячейка": "B-14", 
    },
       "PVZ-2075": {
        "статус": "в пути",
        "прибыл": None,
        "получатель": "Ковалёв Д. С.",
        "ячейка": None,
    },
    "PVZ-3311": {
        "статус": "готов к выдаче",
        "прибыл": date.today() - timedelta(days=1),
        "получатель": "Мухаметшин Р. Р.",
        "ячейка": "A-03",
    },
}

STORAGE_DAYS = 7

@mcp.tool()
def delivery_cost(weight_kg: float, city: str) -> str:
    """ Рассчитать стоимость доставки посылки до пункта выдачи заказов.

    Принимает вес посылки в килограммах и город назначения. Стоимость складывается 
    из базовой цены за первый килограмм и доплаты за каждый следующий полный килограмм;
    цены зависят от  города. Возвращает готовую фазу со стоимостью в рублях.
    """
    if weight_kg <= 0:
        raise ToolError("Вес посылки должен быть больше нуля")
    if city not in TARIFFS:
        raise ToolError(
            f"Город «{city}» нет в списке доставки."
            f"Доступны: {', '.join(TARIFFS)}"
        )
    base, extra = TARIFFS[city]
    extra_kg = max(0, int(weight_kg - 1 + 0.999))
    total = base + extra * extra_kg
    log.info("Расчет доставки: %s кг в %s -> %s руб", weight_kg, city, total)
    return f"Доставка {weight_kg} кг в город {city} стоит {total} руб"


@mcp.tool()
def order_status(track_code: str) -> str: 
    """ Узнать текущий статус заказов по трек-номер.

    Трек-номер имеет вид PVZ-9999. Возвращает стату («в пути» или «готов
    к выдаче»), фамилию получателя и номер ячейки, если заказ уже на пункте.
    """
    order = ORDERS.get(track_code.strip().upper)
    if order is None:
        raise ToolError(
            f"Заказ с трек-номером {track_code} на пункте нет."
            f"Известные номера: {', '.join(ORDERS)}"
        )
    if order["статус"] == "в пути":
        return(
            f"Заказ {track_code}: {order['статус']}, получатель {order['получатель']}, "
            f"ячейка {order['ячейка']}"           
        )

@mcp.tool()
def storage_left(track_code: str) -> str: 
    """Узнать, сколько дней осталось до возврата заказа отправителю.

    Пункт выдачи хранит посылку семь дней с момента поступления, после чего
    отправляет её обратно. Принимает трек-номер вида PVZ-9999, возвращает
    число оставшихся дней и дату, после которой заказ забрать уже нельзя.
    """
    order = ORDERS.get(track_code.strip().upper())
    if order is None:
        raise ToolError(
            f"Заказа с трек-номером {track_code} на пункте нет. "
            f"Известные номера: {', '.join(ORDERS)}"
        )
    if order["прибыл"] is None:
        return f"Заказ {track_code} еще в пути, срок хранения не начался"
    deadline = order["прибыл"] + timedelta(days=STORAGE_DAYS)
    left = (deadline - date.today().days)
    if left < 0: 
        return f"Заказ {track_code} уже отправлен обратно {deadline:%d.%m.%Y}"
    log.info("Хранение в %s: осталось %s дн.", track_code, left)
    return (
        f"Заказ {track_code} хранится еще {left} дн., "
        f"забрать нужно до {deadline:%d.%m.%Y} включительно"
    )

@mcp.tool()
def points_in_city(city: str) -> str:
    """Показать адреса пунктов выдачи заказов в указанном городе.

    Принимает название города, возвращает перечень адресов с часами работы.
    Применяйте, когда спрашивают, куда именно приехать за посылкой.
    """
    points = {
        "Казань": ["ул. Баумана, 12 (9:00-21:00)", "пр. Победы, 45 (10:00-20:00)"],
        "Омск": ["ул. Ленина, 3 (9:00-20:00)"],
        "Новосибирск": ["Красный проспект, 77 (10:00-21:00)"],
        "Екатеринбург": ["ул. Малышева, 5 (9:00-20:00)"],
    }
    if city not in points:
        raise ToolError(
            f"пунктов выдачи в городе «{city}» нет." 
            f"Города с пунктами: {', '.join(points[city])}"
        )

if __name__ == "__main__":
    mcp.run()

    