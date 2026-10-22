from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("Помощник Старосты")

@mcp.tool()
def average_grade(grades: list[int]) -> str:
    if not grades: 
        raise ToolError("Список оценок пуст. Передайте хотя бы одну оценку")
    for grade in grades:
        if grade < 2 or grade > 5:
            raise ToolError(f"Оценка {grade} вне допустимого диапазона. Оценки бывают от 2 до 5")
    return f"Средний балл: {sum(grades) / len(grades):.1f}"
@mcp.tool()
def lessons_left(current_lesson: int, total_lessons: int) -> str:
    if current_lesson < 1:
        raise ToolError("Номер текущей пары не должен быть меньше 1")
    if total_lessons < 1:
        raise ToolError("Всего пар за день должно быть не меньше 1")
    if current_lesson > total_lessons:
        raise ToolError(f"Текущая пара {current_lesson} больше общего числа пар {total_lessons}" "Проверьте расписание")
    left = total_lessons - current_lesson
    return f"осталось пар: {left}" if left else "это последняя пара сегодня"

@mcp.tool()
def format_fio(surname: str, name: str, patronymic: str) -> str:
    if not surname.strip():
        raise ToolError("Фамилия не может быть пустой")
    if not name.strip():
        raise ToolError("Имя не можеть быть пустым")
    short = f"{surname.strip()} {name.strip()[0].upper()}"
    return short

if __name__ == "__main__":
    print("\n ---Запуск локального теста---")

    print(average_grade([2, 4]))

    print(f"осталось пар {lessons_left(1, 3)}")

    print(f"ФИО {format_fio('Баймагамбетов', 'Руслан')}")

    print("\n ------------------------------")

mcp.run()