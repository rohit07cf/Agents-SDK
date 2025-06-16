from fastmcp import FastMCP
import os
import requests
import uvicorn
import boto3
import logging
import json
from collections import defaultdict

# Initialize the FastMCP server
mcp = FastMCP()

# Global multi-index & metadata
TAG_INDEX_LOOKUP = defaultdict(lambda: defaultdict(set))  # e.g., TAG_INDEX_LOOKUP["model_config"]["test1"] = {s3_keys}
S3_KEY_META = {}  # s3_key → full tag metadata

# -----------------------------------------------
# Step 1: Update Tag Index to JSON (flat format)
# -----------------------------------------------
def update_tag_index():
    logging.info("Refreshing S3 tag index...")

    s3 = boto3.client('s3')
    bucket = 'romitestbucket07'
    prefix = 'llm-dev/security_data/'
    tag_index = []

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('/'):
                continue
            try:
                tags = s3.get_object_tagging(Bucket=bucket, Key=key)['TagSet']
                tag_dict = {t['Key']: t['Value'] for t in tags}
                tag_dict['s3_key'] = key
                tag_index.append(tag_dict)
            except Exception as e:
                logging.error(f"Failed to get tags for {key}: {e}")

    with open('tag_index.json', 'w') as f:
        json.dump(tag_index, f, indent=2)

    logging.info(f"Tag index updated with {len(tag_index)} entries.")

# -----------------------------------------------
# Step 2: Load multi-index from flat tag_index.json
# -----------------------------------------------
def load_index():
    global TAG_INDEX_LOOKUP, S3_KEY_META
    TAG_INDEX_LOOKUP.clear()
    S3_KEY_META.clear()

    try:
        with open('tag_index.json', 'r') as f:
            flat_list = json.load(f)

        for entry in flat_list:
            key = entry.get("s3_key")
            S3_KEY_META[key] = entry  # Full metadata

            for tag_key in ["model_config", "user_id", "year", "month", "day"]:
                tag_value = entry.get(tag_key)
                if tag_value:
                    TAG_INDEX_LOOKUP[tag_key][tag_value].add(key)
        
        # Save TAG_INDEX_LOOKUP as JSON (convert sets to lists)
        lookup_json = {
            tag: {val: list(keys) for val, keys in val_dict.items()}
            for tag, val_dict in TAG_INDEX_LOOKUP.items()
        }
        with open('tag_index_lookup.json', 'w') as f:
            json.dump(lookup_json, f, indent=2)

        # Save S3_KEY_META
        with open('s3_key_meta.json', 'w') as f:
            json.dump(S3_KEY_META, f, indent=2)

        logging.info("Saved TAG_INDEX_LOOKUP and S3_KEY_META to disk.")


        logging.info(f"Loaded tag index with {len(S3_KEY_META)} entries into multi-index.")

    except FileNotFoundError:
        logging.warning("tag_index.json not found. Run update_tag_index() first.")

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

# -----------------------------------------------
# Step 3: Fast query using multi-index
# -----------------------------------------------
@mcp.tool(name="filter_s3_user_violations", description="Fetch S3 user violations based on tag filters")
async def filter_s3_user_violations(
    model_config: str = None,
    user_id: str = None,
    year: str = None,
    month: str = None,
    day: str = None
) -> list:
    """
    Scans S3 user violations under a given prefix and returns contents of files
    matching the specified filters like year, month, day, model_config and user_id. All filters are optional in nature but the more filters provided the better
    """
    bucket_name = 'romitestbucket07'
    s3 = boto3.client('s3')

    filters = {
        "model_config": model_config,
        "user_id": user_id,
        "year": year,
        "month": month,
        "day": day
    }

    sets = []
    for tag, val in filters.items():
        if val:
            match_set = TAG_INDEX_LOOKUP.get(tag, {}).get(val, set())
            sets.append(match_set)

    if not sets:
        return []  # No filters provided

    # Intersect to get matching keys
    matching_keys = set.intersection(*sets)

    matched_files = []
    for key in matching_keys:
        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            matched_files.append({
                "s3_key": key,
                "tags": S3_KEY_META.get(key, {}),
                "content": content
            })
        except Exception as e:
            logging.error(f"Failed to fetch {key}: {e}")
    
    return matched_files


if __name__ == "__main__":
    update_tag_index()       # optional: refresh at startup
    load_index()             # load index into memory
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
