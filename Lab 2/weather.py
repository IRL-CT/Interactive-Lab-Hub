import requests
import os
# pip install requests

API_KEY = os.environ.get("WEATHERAPI_KEY")
LOCATION = "New York"

def get_current_weather():
    url = "https://api.weatherapi.com/v1/current.json"

    params = {
        "key": API_KEY,
        "q": LOCATION,
        "aqi": "no"
    }

    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()

    temperature = round(data["current"]["temp_f"])
    condition_code = data["current"]["condition"]["code"]

    return temperature, condition_code