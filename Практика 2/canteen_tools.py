from typing import Literal
from typing_extensions import TypedDict

from mcp.server import MCPServer 
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations 

mcp = MCPServer("Столовая колледжа")

Day = Literal["понедельник","вторник","среда","четверг","пятница"]

class DishOnMenu(TypedDict):
    блюдо: str
    цена: float
    калории: float
    вегетарианское: bool

class DishCard(TypedDict):
    цена: float
    калории: float
    белки: float
    жиры: float
    углеводы: float

class OrderTotal(TypedDict):
    сумма: float
    скидка: float
    к_оплате: float
    калории: float

class Reservation(TypedDict):
    студент: str
    день: str
    блюдо: str
    к_оплате: str

DISHES: dict[str, dict] = {
    "борщ": {"price": 95.0, "kcal": 210.0, "protein": 7.5, "fat": 8.0, "carbs": 24.0, "veg": False},
    "суп гороховый": {"price": 85.0, "kcal": 190.0, "protein": 9.0, "fat": 4.5, "carbs": 28.0, "veg": True},
    "котлета куриная": {"price": 130.0, "kcal": 280.0, "protein": 22.0, "fat": 17.0, "carbs": 9.0, "veg": False},
    "рыба запечённая": {"price": 160.0, "kcal": 240.0, "protein": 26.0, "fat": 12.0, "carbs": 3.0, "veg": False},
    "пюре картофельное": {"price": 60.0, "kcal": 180.0, "protein": 3.0, "fat": 6.0, "carbs": 27.0, "veg": True}, 
    "гречка отварная": {"price": 55.0, "kcal": 160.0, "protein": 6.0, "fat": 2.5, "carbs": 30.0, "veg": True},
    "сырники": {"price": 70.0, "kcal": 90.0, "protein": 2.0, "fat": 5.0, "carbs": 8.0, "veg": True},
    "салат овощной": {"price": 70.0, "kcal": 90.0, "protein": 2.0, "fat": 5.0, "carbs": 8.0, "veg": True},
    "каша овсяная": {"price": 110.0, "kcal": 320.0, "protein": 15.0, "fat": 14.0, "carbs": 33.0, "veg": True},
    "компот": {"price": 35.0, "kcal": 80.0, "protein": 0.2, "fat": 0.0, "carbs": 20.0, "veg": True},
    "чай с лимоном": {"price": 25.0, "kcal": 30.0, "protein": 0.0, "fat": 0.0, "carbs": 7.0, "veg": True},
}

MENU: dict[str, dict[str, list[str]]] = {
    "понедельник": {"завтрак": ["каша овсяная", "чай с лимоном"],
                    "обед": ["борщ", "котлета куриная", "пюре картофельное", "компот"]},
    "вторник": {"завтрак": ["сырники", "чай с лимоном"],
                "обед": ["суп гороховый", "рыба запечённая", "гречка отварная", "компот"]},
    "среда": {"завтрак": ["каша овсяная", "компот"],
              "обед": ["борщ", "рыба запечённая", "пюре картофельное", "салат овощной"]},
    "четверг": {"завтрак": ["сырники", "компот"],
                "обед": ["суп гороховый", "котлета куриная", "гречка отварная", "чай с лимоном"]},
    "пятница": {"завтрак": ["каша овсяная", "чай с лимоном"],
                "обед": ["борщ", "котлета куриная", "салат овощной", "компот"]},
}

RESERVATIONS: dict[tuple[str,str], list[str]] = {}

STUDENT_DISCOUNT = 0.15

def dish_key(name: str) -> str:
    key = name.strip().lower().replace("ё", "е")
    if not key:
        raise ToolError("Название блюда не может быть пустым")
    normalized = {k.replace("ё", "е"): k for k in DISHES}
    if key not in normalized:
        known = ", ".join(sorted(DISHES))
        raise ToolError(f"Блюдо «{name}» в меню не значится. Есть такие блюда: {known}")
    return normalized[key] 


@mcp.tool(
    annotations=ToolAnnotations(title="Меню дня", read_only_hint=True, open_world_hint=False)
)

def menu_for_day(day: Day, meal: Literal["завтрак", "обед"] = "обед") -> list[DishOnMenu]:
     """Вернуть меню столовой на указанный день недели.

    Один вызов возвращает список блюд одного приёма пищи: для каждого блюда
    известны название, цена в рублях, калорийность порции и признак
    вегетарианского. Аргумент meal выбирает приём пищи, по умолчанию обед.
    Столовая работает с понедельника по пятницу, выходные не обслуживаются.
    """
     return [
        {
            "блюдо": name,
            "цена": DISHES[name]["price"],
            "калории": DISHES[name]["kcal"],
            "вегетарианское": DISHES[name]["veg"],
        }
        for name in MENU[day][meal]
    ]

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def dish_info(dish: str) -> DishCard:
     """Вернуть цену и пищевую ценность одной порции блюда.

    Название блюда пишется так же, как в меню, регистр не важен: подойдёт и
    «борщ», и «Котлета куриная». Возвращаются цена в рублях, калорийность
    порции и содержание белков, жиров и углеводов в граммах.
    """
     card = DISHES[dish_key(dish)]
     return {
        "цена": card["price"],
        "калории": card["kcal"],
        "белки": card["protein"], 
        "жиры": card["fat"],
        "углеводы": card["carbs"],
    }

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def order_total(dishes: list[str], student_card: bool = False) -> OrderTotal:
    """Посчитать стоимость и калорийность заказа из нескольких блюд.

    Аргумент dishes — список названий блюд; одно и то же блюдо можно указать
    несколько раз, тогда оно посчитается несколько раз. Если student_card равен
    true, на сумму начисляется скидка по студенческому билету 15 процентов.
    Возвращаются сумма без скидки, размер скидки, сумма к оплате в рублях и
    суммарная калорийность заказа.
    """
    if not dishes:
        raise ToolError("список блюд пуст: укажите хотя бы одно блюдо из меню")
    total = 0.0
    kcal = 0.0
    for name in dishes:
        card = DISHES[dish_key(name)]
        total += card["price"]
        kcal += card["kcal"]
    discount = round(total * STUDENT_DISCOUNT, 2) if student_card else 0.0
    return {
        "сумма": round(total, 2), 
        "скидка": discount,
        "к_оплате": round(total - discount, 2),
        "калории": round(kcal, 1),
    }

@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
def find_dishes(keyword: str = "", max_price: float | None = None, vegetarian: bool = False, limit: int = 10) -> list[DishOnMenu]:
    """Найти блюда столовой по подстроке названия, цене и признаку вегетарианского.

    Все аргументы необязательны: без аргументов возвращается весь ассортимент.
    Аргумент keyword ищет подстроку в названии без учёта регистра, max_price
    ограничивает цену сверху в рублях, vegetarian равный true оставляет только
    вегетарианские блюда, limit ограничивает длину ответа (по умолчанию десять
    блюд). Возвращается список блюд с ценой и калорийностью, отсортированный по
    возрастанию цены; пустой список означает, что под условия не подошло ни одно
    блюдо.
    """
    if max_price is not None and max_price <= 0:
        raise ToolError("Максимальная цена должна быть больше нуля")
    if limit < 1: 
        raise ToolError("Ограничение на длину ответа должно быть не меньше единицы")
    needle = keyword.strip().lower()
    found = []
    for name, card in DISHES.items():
        if needle and needle not in name:
            continue
        if max_price is not None and card["price"] > max_price:
            continue
        if vegetarian and not card["veg"]:
            continue
        found.append({
            "блюдо": name,
            "цена": card["price"],
            "калории": card["kcal"],
            "вегетарианское": card["veg"],
        })
    return sorted(found, key=lambda item: item["цена"])[:limit]

@mcp.tool(
    annotations=ToolAnnotations(title="Записать заказ", read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)

)
def reserve_lunch(student: str, day: Day, dishes: list[str]) -> Reservation:
    """Записать предварительный заказ студента на обед указанного дня.

    Заказ хранится в памяти сервера до его остановки. Повторная запись на тот
    же день заменяет прежний заказ, а не добавляет второй, поэтому вызов можно
    безопасно повторить. Возвращается подтверждение с суммой к оплате.
    """
    name = student.strip()
    if not name:
        raise ToolError("Укажите фамилию и имя студента")
    if not dishes:
        raise ToolError("Список блюд пуст: укажите хотя бы одно блюдо из меню")
    total = 0.0
    keys = []
    for item in dishes:
        key = dish_key(item)
        total += DISHES[key]["price"]
        keys.append(key)
    RESERVATIONS[(name, day)] = keys
    return {
        "студент": name, 
        "день": day, 
        "блюдо": ", ".join(keys), 
        "к_оплате": f"{total:.2f} руб",   
    }
if __name__ == "__main__":
    mcp.run()

