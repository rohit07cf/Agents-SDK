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

@mcp.tool(name="filter_s3_user_violations", description="Fetch S3 user violations based on model_config and user_id tags")
async def filter_s3_user_violations(model_config: str, user_id: str) -> list:
    """
    Scans S3 user violations under a given prefix and returns contents of files
    matching the specified model_config and user_id.
    """
    bucket_name = 'romitestbucket07'
    prefix = 'llm-dev/security_data/'
    
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    
    matched_files = []

    for page in page_iterator:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('/'):
                continue

            tagging = s3.get_object_tagging(Bucket=bucket_name, Key=key)
            tags = {tag['Key']: tag['Value'] for tag in tagging['TagSet']}
            
            if tags.get("model_config") == model_config and tags.get("user_id") == user_id:
                response = s3.get_object(Bucket=bucket_name, Key=key)
                content = response['Body'].read().decode('utf-8')
                matched_files.append({
                    "content": content
                })

    return matched_files

if __name__ == "__main__":
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
