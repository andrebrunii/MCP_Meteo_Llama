"""Server MCP locale: un solo strumento meteo, trasporto stdio."""
import http.client
import json
import math
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlencode

from mcp.server.fastmcp import FastMCP

CITIES = {
    "Roma": (41.9028, 12.4964),
    "Milano": (45.4642, 9.1900),
    "Torino": (45.0703, 7.6869),
    "Chieri": (45.0105, 7.8213),
    "Napoli": (40.8518, 14.2681),
}
City = Literal["Roma", "Milano", "Torino", "Chieri", "Napoli"]
mcp = FastMCP("Meteo didattico", log_level="WARNING")


def condition(code):
    descriptions = {
        0: "Sereno", 1: "Prevalentemente sereno", 2: "Parzialmente nuvoloso",
        3: "Coperto", 45: "Nebbia", 48: "Nebbia con brina",
        51: "Pioviggine debole", 53: "Pioviggine moderata", 55: "Pioviggine intensa",
        56: "Pioviggine gelata debole", 57: "Pioviggine gelata intensa",
        61: "Pioggia debole", 63: "Pioggia moderata", 65: "Pioggia intensa",
        66: "Pioggia gelata debole", 67: "Pioggia gelata intensa",
        71: "Neve debole", 73: "Neve moderata", 75: "Neve intensa", 77: "Granuli di neve",
        80: "Rovesci deboli", 81: "Rovesci moderati", 82: "Rovesci violenti",
        85: "Rovesci di neve deboli", 86: "Rovesci di neve intensi",
        95: "Temporale", 96: "Temporale con grandine debole",
        99: "Temporale con grandine intensa",
    }
    return descriptions.get(code, "Codice meteo non riconosciuto")


def fetch_weather(city):
    # Lista chiusa: il modello non puo scegliere URL, percorsi o comandi.
    if city not in CITIES:
        raise ValueError("Citta non supportata")
    latitude, longitude = CITIES[city]
    query = urlencode({
        "latitude": latitude, "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "temperature_unit": "celsius", "wind_speed_unit": "kmh",
        "timezone": "Europe/Rome", "forecast_days": 1,
    })
    connection = http.client.HTTPSConnection("api.open-meteo.com", timeout=20)
    try:
        connection.request("GET", "/v1/forecast?" + query,
                           headers={"User-Agent": "student-weather-mcp/1.0"})
        response = connection.getresponse()
        raw = response.read(100_001)
        if response.status != 200:
            raise RuntimeError(f"Open-Meteo HTTP {response.status}")
        if len(raw) > 100_000:
            raise RuntimeError("Risposta meteo troppo grande")
        data = json.loads(raw)
    finally:
        connection.close()
    current = data["current"]
    for key in ("temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m"):
        value = current.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise RuntimeError(f"Dato meteo assente o non valido: {key}")
    units = data["current_units"]
    if units.get("temperature_2m") != "°C" or units.get("wind_speed_10m") != "km/h" or units.get("relative_humidity_2m") != "%":
        raise RuntimeError("Unita meteo inattese")
    return {
        "city": city,
        "latitude_requested": latitude, "longitude_requested": longitude,
        "temperature_c": current["temperature_2m"],
        "humidity_percent": current["relative_humidity_2m"],
        "wind_kmh": current["wind_speed_10m"],
        "condition": condition(current["weather_code"]),
        "weather_code": current["weather_code"],
        "valid_at": current["time"],
        "timezone": data["timezone"],
        "utc_offset_seconds": data["utc_offset_seconds"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Open-Meteo",
        "source_url": "https://open-meteo.com/",
        "data_note": "Condizioni attuali stimate da modelli meteorologici, non misura di una stazione sul posto.",
    }


@mcp.tool()
def get_current_weather(city: City) -> dict:
    """Get current weather for one supported Italian city: Roma, Milano, Torino, Chieri or Napoli. Returns Celsius, humidity %, wind km/h, condition, timestamp and source."""
    return fetch_weather(city)


if __name__ == "__main__":
    mcp.run(transport="stdio")
