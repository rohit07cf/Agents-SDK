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

@mcp.tool(name="get_weather", description="Get weather details using latitude and longitude")
async def get_weather(lat: float, lon: float) -> dict:
    """
    Fetches current weather for the specified coordinates using OpenWeatherMap API.
    """
    api_key = ""
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY is missing")
    print(f"Coordinates: lat={lat}, lon={lon}")

    # Call OpenWeatherMap API
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
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
