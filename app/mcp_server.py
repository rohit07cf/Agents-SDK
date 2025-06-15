from fastmcp import FastMCP
import os
import requests
import uvicorn

# Initialize the FastMCP server
mcp = FastMCP()

@mcp.tool(name="add_numbers", description="Add two numbers")
async def add_numbers(a: float, b: float) -> float:
    """
    Returns the sum of two numbers.
    """
    return a + b

@mcp.tool(name="get_weather", description="Get weather details for a given location")
async def get_weather(location: str) -> dict:
    """
    Fetches current weather for the specified location using OpenWeatherMap API.

    Environment variable:
      OPENWEATHER_API_KEY: Your API key from OpenWeatherMap
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY environment variable not set")

    # Call OpenWeatherMap API
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Return a simplified weather summary
    return {
        "location": data.get("name"),
        "temperature_celsius": data.get("main", {}).get("temp"),
        "weather_description": data.get("weather", [{}])[0].get("description")
    }

if __name__ == "__main__":
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
