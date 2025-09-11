import os

import httpx
from dotenv import find_dotenv, load_dotenv
from mcp.server import FastMCP

mcp = FastMCP(name="weather-mcp")

load_dotenv(find_dotenv())

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def format_weather_data(response: dict) -> str:
    """Formats raw weather data from OpenWeatherMap API into a string intended for a LLM"""

    description = response.get("weather", [{}])[0].get(
        "description", "No description available"
    )
    temp = response.get("main", {}).get("temp", 0)
    feels_like = response.get("main", {}).get("feels_like", 0)
    city = response.get("name", "Unknown")
    country = response.get("sys", {}).get("country", "Unknown")

    return (
        f"City: {city}, {country}\n"
        f"Condition: {description}\n"
        f"Temperature: {temp}°C\n"
        f"Feels Like: {feels_like}°C"
    )


@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Fetches current weather data for a specified city.
    Args:
        city (str): The name of the city to fetch weather for, along with optional country code (e.g., "London,GB", "Hyderabad,IN", "Hyderabad,PK").
    Returns:
        str: A string describing the current weather conditions, or an error message.
    """
    if not OPENWEATHER_API_KEY:
        print("OPENWEATHER_API_KEY not set. Returning mock data.")
        return "Sunny, 30°C"

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            weather_data = response.json()
            return format_weather_data(weather_data)

    except httpx.HTTPStatusError as e:
        return f"Error fetching weather for {city}: {e.response.status_code} - {e.response.text}"

    except httpx.RequestError as e:
        return f"Network error fetching weather for {city}: {e}"

    except KeyError:
        return f"Could not parse weather data for {city}. Please check the city name."


if __name__ == "__main__":
    mcp.run()
