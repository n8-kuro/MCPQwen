from datetime import datetime

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer ("Pracrice server")

@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    if height_m <= 0:
        raise ToolError("Рост должен быть больше нуля")
    bmi = weight_kg / (height_m ** 2)
    return f"ИМТ = {bmi:.1f}"
@mcp.tool()
def get_system_time() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

@mcp.tool()
def text_length(text: str) -> int:
    return len(text)

if __name__ == "__main__":
    print("\n--- ЗАПУСК ЛОКАЛЬНОГО ТЕСТА ИНСТРУМЕНТОВ ---")
    
    print(calculate_bmi(weight_kg=75.0, height_m=1.75))
    
    print(f"Текущее время: {get_system_time()}")
    
    print(f"Длина текста: {text_length('Привет, MCP!')}")
    print("-------------------------------------------\n")

    mcp.run()

