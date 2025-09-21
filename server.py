from fastmcp import FastMCP
import requests
import os

mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"

@mcp.tool
def get_weather(city: str) -> str:
    """
    This tool provides the weather of a chosen city using the OpenWeatherMap API.
    Args:
        city: str
    Output:
        City: temperature, condition
    """
    api = os.environ("WEATHER_API_KEY")  # <-- keep private in real projects
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api}&units=metric"

    response = requests.get(url)
    data = response.json()

    if data.get("cod") != 200:
        return f"Error: {data.get('message')}"
    
    temp = data["main"]["temp"]
    cond = data["weather"][0]["description"]
    return f"{city}: {temp}°C, {cond}"

if __name__ == "__main__":
    mcp.run()
