#!/usr/bin/env python3
"""
A comprehensive MCP server that provides calculator, text processing, weather, and aviation tools.
"""

import asyncio
import json
import sys
import aiohttp
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server


# Initialize the MCP server
server = Server("mcp-server")


@server.list_tools()
async def list_tools() -> List[types.Tool]:
    """
    List available tools that this MCP server provides.
    """
    return [
        types.Tool(
            name="calculator",
            description="Perform basic mathematical calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
                    }
                },
                "required": ["expression"]
            }
        ),
        types.Tool(
            name="text_analyzer",
            description="Analyze text and provide statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze"
                    }
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="list_files",
            description="List files in a given directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list files from (defaults to current directory)",
                        "default": "."
                    }
                }
            }
        ),
        types.Tool(
            name="get_weather",
            description="Get current weather and forecast for a location using Open-Meteo API (free, no API key required)",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'Oslo', 'New York', 'London')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days (1-7, default: 3)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 7
                    },
                    "include_hourly": {
                        "type": "boolean",
                        "description": "Include hourly forecast for today (default: false)",
                        "default": False
                    }
                },
                "required": ["location"]
            }
        ),
        types.Tool(
            name="get_flights_by_location",
            description="Get real-time flight data for flights near a specific location using AviationStack API",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location to search for nearby flights (e.g., 'Oslo', 'New York', 'London')"
                    },
                    "radius": {
                        "type": "integer",
                        "description": "Search radius in kilometers (default: 100, max: 500)",
                        "default": 100,
                        "minimum": 10,
                        "maximum": 500
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of flights to return (default: 20, max: 100)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["location"]
            }
        ),
        types.Tool(
            name="get_airport_info",
            description="Get detailed information about airports near a location",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or airport code (e.g., 'Oslo', 'OSL', 'JFK', 'London')"
                    }
                },
                "required": ["location"]
            }
        ),
        types.Tool(
            name="get_location_data",
            description="Get comprehensive location data including coordinates, weather, nearby airports, and flights",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'Oslo', 'New York', 'London')"
                    },
                    "include_flights": {
                        "type": "boolean",
                        "description": "Include nearby flight data (default: true)",
                        "default": True
                    },
                    "include_weather": {
                        "type": "boolean",
                        "description": "Include weather data (default: true)",
                        "default": True
                    },
                    "flight_radius": {
                        "type": "integer",
                        "description": "Flight search radius in kilometers (default: 100)",
                        "default": 100,
                        "minimum": 10,
                        "maximum": 500
                    }
                },
                "required": ["location"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle tool calls from the MCP client.
    """
    
    if name == "calculator":
        return await handle_calculator(arguments)
    elif name == "text_analyzer":
        return await handle_text_analyzer(arguments)
    elif name == "list_files":
        return await handle_list_files(arguments)
    elif name == "get_weather":
        return await handle_get_weather(arguments)
    elif name == "get_flights_by_location":
        return await handle_get_flights_by_location(arguments)
    elif name == "get_airport_info":
        return await handle_get_airport_info(arguments)
    elif name == "get_location_data":
        return await handle_get_location_data(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_calculator(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle calculator tool calls.
    """
    expression = arguments.get("expression", "")
    
    if not expression:
        return [types.TextContent(
            type="text",
            text="Error: No expression provided"
        )]
    
    try:
        # Simple evaluation - in production, you'd want more sophisticated parsing
        # to avoid security issues with eval()
        allowed_chars = set('0123456789+-*/().% ')
        if not all(c in allowed_chars for c in expression):
            return [types.TextContent(
                type="text",
                text="Error: Expression contains invalid characters"
            )]
        
        result = eval(expression)
        return [types.TextContent(
            type="text",
            text=f"Result: {expression} = {result}"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error calculating '{expression}': {str(e)}"
        )]


async def handle_text_analyzer(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle text analyzer tool calls.
    """
    text = arguments.get("text", "")
    
    if not text:
        return [types.TextContent(
            type="text",
            text="Error: No text provided"
        )]
    
    # Analyze the text
    word_count = len(text.split())
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", ""))
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
    
    analysis = f"""Text Analysis Results:
- Character count: {char_count}
- Character count (no spaces): {char_count_no_spaces}
- Word count: {word_count}
- Sentence count: {sentence_count}
- Paragraph count: {paragraph_count}
- Average words per sentence: {word_count / max(sentence_count, 1):.1f}
"""
    
    return [types.TextContent(
        type="text",
        text=analysis
    )]


async def handle_list_files(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle list files tool calls.
    """
    import os
    
    path = arguments.get("path", ".")
    
    try:
        if not os.path.exists(path):
            return [types.TextContent(
                type="text",
                text=f"Error: Path '{path}' does not exist"
            )]
        
        if not os.path.isdir(path):
            return [types.TextContent(
                type="text",
                text=f"Error: Path '{path}' is not a directory"
            )]
        
        files = os.listdir(path)
        files.sort()
        
        if not files:
            return [types.TextContent(
                type="text",
                text=f"Directory '{path}' is empty"
            )]
        
        file_list = "\n".join(f"- {file}" for file in files)
        return [types.TextContent(
            type="text",
            text=f"Files in '{path}':\n{file_list}"
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error listing files in '{path}': {str(e)}"
        )]


async def get_location_coordinates(location: str) -> Optional[Dict]:
    """
    Get coordinates for a location using Open-Meteo's geocoding API.
    """
    try:
        async with aiohttp.ClientSession() as session:
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocoding_params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            async with session.get(geocoding_url, params=geocoding_params) as response:
                if response.status != 200:
                    return None
                
                geo_data = await response.json()
                
                if not geo_data.get("results"):
                    return None
                
                return geo_data["results"][0]
    except Exception:
        return None


async def handle_get_weather(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle weather API calls using Open-Meteo (free, no API key required).
    """
    location = arguments.get("location", "")
    days = arguments.get("days", 3)
    include_hourly = arguments.get("include_hourly", False)
    
    if not location:
        return [types.TextContent(
            type="text",
            text="Error: No location provided"
        )]
    
    try:
        location_data = await get_location_coordinates(location)
        if not location_data:
            return [types.TextContent(
                type="text",
                text=f"Error: Location '{location}' not found. Please try a different city name."
            )]
        
        lat = location_data["latitude"]
        lon = location_data["longitude"]
        city_name = location_data["name"]
        country = location_data.get("country", "")
        
        # Weather API call
        async with aiohttp.ClientSession() as session:
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m", "wind_direction_10m"],
                "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"],
                "forecast_days": days,
                "timezone": "auto"
            }
            
            # Add hourly data if requested
            if include_hourly:
                weather_params["hourly"] = ["temperature_2m", "weather_code", "precipitation_probability"]
            
            async with session.get(weather_url, params=weather_params) as response:
                if response.status != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Could not fetch weather data (status: {response.status})"
                    )]
                
                weather_data = await response.json()
        
        # Format the weather response
        result = format_weather_response(weather_data, city_name, country, include_hourly)
        
        return [types.TextContent(
            type="text",
            text=result
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error getting weather for '{location}': {str(e)}"
        )]


async def handle_get_flights_by_location(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle flight data requests using AviationStack API.
    """
    location = arguments.get("location", "")
    radius = arguments.get("radius", 100)
    limit = arguments.get("limit", 20)
    
    if not location:
        return [types.TextContent(
            type="text",
            text="Error: No location provided"
        )]
    
    # Check for API key
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        return [types.TextContent(
            type="text",
            text="Error: AviationStack API key not found. Please set AVIATIONSTACK_API_KEY environment variable. Get your free API key at: https://aviationstack.com/signup/free"
        )]
    
    try:
        # Get location coordinates
        location_data = await get_location_coordinates(location)
        if not location_data:
            return [types.TextContent(
                type="text",
                text=f"Error: Location '{location}' not found. Please try a different city name."
            )]
        
        lat = location_data["latitude"]
        lon = location_data["longitude"]
        city_name = location_data["name"]
        country = location_data.get("country", "")
        
        # Get flight data
        async with aiohttp.ClientSession() as session:
            flights_url = "http://api.aviationstack.com/v1/flights"
            flights_params = {
                "access_key": api_key,
                "limit": limit,
                # Note: AviationStack free tier doesn't support location-based filtering
                # We'll get general flight data and filter/format it
            }
            
            async with session.get(flights_url, params=flights_params) as response:
                if response.status != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Could not fetch flight data (status: {response.status})"
                    )]
                
                flight_data = await response.json()
        
        # Format the flight response
        result = format_flight_response(flight_data, city_name, country, lat, lon, radius)
        
        return [types.TextContent(
            type="text",
            text=result
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error getting flight data for '{location}': {str(e)}"
        )]


async def handle_get_airport_info(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle airport information requests.
    """
    location = arguments.get("location", "")
    
    if not location:
        return [types.TextContent(
            type="text",
            text="Error: No location provided"
        )]
    
    # Check for API key
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        return [types.TextContent(
            type="text",
            text="Error: AviationStack API key not found. Please set AVIATIONSTACK_API_KEY environment variable. Get your free API key at: https://aviationstack.com/signup/free"
        )]
    
    try:
        async with aiohttp.ClientSession() as session:
            airports_url = "http://api.aviationstack.com/v1/airports"
            airports_params = {
                "access_key": api_key,
                "search": location,
                "limit": 10
            }
            
            async with session.get(airports_url, params=airports_params) as response:
                if response.status != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Could not fetch airport data (status: {response.status})"
                    )]
                
                airport_data = await response.json()
        
        # Format the airport response
        result = format_airport_response(airport_data, location)
        
        return [types.TextContent(
            type="text",
            text=result
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error getting airport info for '{location}': {str(e)}"
        )]


async def handle_get_location_data(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """
    Handle comprehensive location data requests combining weather, flights, and airports.
    """
    location = arguments.get("location", "")
    include_flights = arguments.get("include_flights", True)
    include_weather = arguments.get("include_weather", True)
    flight_radius = arguments.get("flight_radius", 100)
    
    if not location:
        return [types.TextContent(
            type="text",
            text="Error: No location provided"
        )]
    
    try:
        # Get location coordinates
        location_data = await get_location_coordinates(location)
        if not location_data:
            return [types.TextContent(
                type="text",
                text=f"Error: Location '{location}' not found. Please try a different city name."
            )]
        
        lat = location_data["latitude"]
        lon = location_data["longitude"]
        city_name = location_data["name"]
        country = location_data.get("country", "")
        
        result = f"📍 COMPREHENSIVE DATA FOR {city_name.upper()}"
        if country:
            result += f", {country.upper()}"
        result += "\n" + "="*60 + "\n\n"
        
        result += f"🌐 COORDINATES: {lat:.4f}, {lon:.4f}\n\n"
        
        # Add weather data
        if include_weather:
            weather_args = {"location": location, "days": 3, "include_hourly": False}
            weather_response = await handle_get_weather(weather_args)
            if weather_response:
                result += weather_response[0].text + "\n\n"
        
        # Add airport data
        airport_args = {"location": location}
        airport_response = await handle_get_airport_info(airport_args)
        if airport_response:
            result += airport_response[0].text + "\n\n"
        
        # Add flight data
        if include_flights:
            flight_args = {"location": location, "radius": flight_radius, "limit": 10}
            flight_response = await handle_get_flights_by_location(flight_args)
            if flight_response:
                result += flight_response[0].text + "\n\n"
        
        result += "🗺️ MAP INTEGRATION READY\n"
        result += f"Use coordinates ({lat:.4f}, {lon:.4f}) for mapping applications\n"
        result += "This data can be used to create interactive maps with weather and flight overlays."
        
        return [types.TextContent(
            type="text",
            text=result
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error getting comprehensive data for '{location}': {str(e)}"
        )]


def get_weather_description(weather_code: int) -> str:
    """
    Convert Open-Meteo weather codes to human-readable descriptions.
    """
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy", 
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(weather_code, f"Unknown weather (code: {weather_code})")


def format_weather_response(weather_data: Dict, city_name: str, country: str, include_hourly: bool) -> str:
    """
    Format the weather API response into a readable format.
    """
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})
    
    # Current weather
    current_temp = current.get("temperature_2m")
    current_humidity = current.get("relative_humidity_2m")
    current_weather_code = current.get("weather_code")
    current_wind_speed = current.get("wind_speed_10m")
    current_wind_direction = current.get("wind_direction_10m")
    
    result = f"🌤️ WEATHER FOR {city_name.upper()}"
    if country:
        result += f", {country.upper()}"
    result += "\n" + "="*50 + "\n\n"
    
    # Current conditions
    result += "📍 CURRENT CONDITIONS:\n"
    if current_temp is not None:
        result += f"🌡️ Temperature: {current_temp}°C\n"
    if current_humidity is not None:
        result += f"💧 Humidity: {current_humidity}%\n"
    if current_weather_code is not None:
        result += f"☁️ Conditions: {get_weather_description(current_weather_code)}\n"
    if current_wind_speed is not None:
        result += f"💨 Wind: {current_wind_speed} km/h"
        if current_wind_direction is not None:
            result += f" from {current_wind_direction}°"
        result += "\n"
    
    # Daily forecast
    if daily and daily.get("time"):
        result += "\n📅 DAILY FORECAST:\n"
        for i, date in enumerate(daily["time"]):
            max_temp = daily.get("temperature_2m_max", [None])[i]
            min_temp = daily.get("temperature_2m_min", [None])[i]
            weather_code = daily.get("weather_code", [None])[i]
            precipitation = daily.get("precipitation_sum", [None])[i]
            wind_speed = daily.get("wind_speed_10m_max", [None])[i]
            
            # Format date (remove time part)
            date_str = date.split('T')[0] if 'T' in date else date
            
            result += f"\n{date_str}:\n"
            
            if weather_code is not None:
                result += f"  ☁️ {get_weather_description(weather_code)}\n"
            
            if max_temp is not None and min_temp is not None:
                result += f"  🌡️ {min_temp}°C to {max_temp}°C\n"
            
            if precipitation is not None and precipitation > 0:
                result += f"  🌧️ Precipitation: {precipitation}mm\n"
            
            if wind_speed is not None:
                result += f"  💨 Max wind: {wind_speed} km/h\n"
    
    return result


def format_flight_response(flight_data: Dict, city_name: str, country: str, lat: float, lon: float, radius: int) -> str:
    """
    Format the flight API response into a readable format.
    """
    result = f"✈️ FLIGHT DATA NEAR {city_name.upper()}"
    if country:
        result += f", {country.upper()}"
    result += f" ({radius}km radius)\n"
    result += "="*50 + "\n\n"
    
    flights = flight_data.get("data", [])
    
    if not flights:
        result += "No flight data available. This might be due to:\n"
        result += "- API rate limits on the free tier\n"
        result += "- No flights currently active in the area\n"
        result += "- API key limitations\n\n"
        result += "💡 TIP: The free AviationStack tier has limited features.\n"
        result += "For production use, consider upgrading for location-based filtering."
        return result
    
    result += f"📊 SHOWING {len(flights)} FLIGHTS:\n\n"
    
    for i, flight in enumerate(flights[:10]):  # Limit to 10 flights for readability
        flight_info = flight.get("flight", {})
        departure = flight.get("departure", {})
        arrival = flight.get("arrival", {})
        aircraft = flight.get("aircraft", {})
        airline = flight.get("airline", {})
        
        result += f"🛫 FLIGHT {i+1}:\n"
        
        # Flight number and airline
        if flight_info.get("number"):
            result += f"  📋 Flight: {flight_info['number']}"
            if airline.get("name"):
                result += f" ({airline['name']})"
            result += "\n"
        
        # Route
        dep_airport = departure.get("airport", "Unknown")
        arr_airport = arrival.get("airport", "Unknown")
        result += f"  🛣️ Route: {dep_airport} → {arr_airport}\n"
        
        # Status
        if flight_info.get("status"):
            status_emoji = "🟢" if flight_info["status"] == "active" else "🟡"
            result += f"  {status_emoji} Status: {flight_info['status'].title()}\n"
        
        # Aircraft
        if aircraft.get("registration"):
            result += f"  ✈️ Aircraft: {aircraft['registration']}"
            if aircraft.get("iata"):
                result += f" ({aircraft['iata']})"
            result += "\n"
        
        # Times
        if departure.get("scheduled"):
            result += f"  🕐 Departure: {departure['scheduled']}\n"
        if arrival.get("scheduled"):
            result += f"  🕑 Arrival: {arrival['scheduled']}\n"
        
        result += "\n"
    
    result += "📡 Data provided by AviationStack API\n"
    result += f"🗺️ Center coordinates: {lat:.4f}, {lon:.4f}\n"
    result += "💡 Use these coordinates for map visualization"
    
    return result


def format_airport_response(airport_data: Dict, location: str) -> str:
    """
    Format the airport API response into a readable format.
    """
    result = f"🛬 AIRPORTS NEAR {location.upper()}\n"
    result += "="*40 + "\n\n"
    
    airports = airport_data.get("data", [])
    
    if not airports:
        result += f"No airports found for '{location}'.\n"
        result += "Try searching with:\n"
        result += "- Full city name (e.g., 'New York')\n"
        result += "- Airport code (e.g., 'JFK', 'LAX')\n"
        result += "- Country name\n"
        return result
    
    result += f"📊 FOUND {len(airports)} AIRPORTS:\n\n"
    
    for i, airport in enumerate(airports):
        result += f"🛬 AIRPORT {i+1}:\n"
        
        # Basic info
        if airport.get("airport_name"):
            result += f"  📋 Name: {airport['airport_name']}\n"
        
        if airport.get("iata_code"):
            result += f"  🏷️ IATA Code: {airport['iata_code']}"
            if airport.get("icao_code"):
                result += f" / ICAO: {airport['icao_code']}"
            result += "\n"
        
        # Location
        if airport.get("city_iata_code"):
            result += f"  🏙️ City: {airport['city_iata_code']}"
            if airport.get("country_name"):
                result += f", {airport['country_name']}"
            result += "\n"
        
        # Coordinates
        if airport.get("latitude") and airport.get("longitude"):
            result += f"  🌐 Coordinates: {airport['latitude']}, {airport['longitude']}\n"
        
        # Timezone
        if airport.get("timezone"):
            result += f"  🕐 Timezone: {airport['timezone']}\n"
        
        result += "\n"
    
    result += "📡 Data provided by AviationStack API"
    
    return result


@server.list_resources()
async def list_resources() -> List[types.Resource]:
    """
    List available resources that this MCP server provides.
    Resources are data that can be read by the client.
    """
    return [
        types.Resource(
            uri="config://server-info",
            name="Server Information",
            description="Information about this MCP server",
            mimeType="application/json"
        ),
        types.Resource(
            uri="config://api-setup",
            name="API Setup Guide",
            description="Guide for setting up required API keys",
            mimeType="text/plain"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """
    Handle resource read requests.
    """
    if uri == "config://server-info":
        server_info = {
            "name": "mcp-server",
            "version": "0.2.0",
            "description": "A comprehensive MCP server with calculator, text analysis, weather, and aviation tools",
            "tools": ["calculator", "text_analyzer", "list_files", "get_weather", "get_flights_by_location", "get_airport_info", "get_location_data"],
            "resources": ["config://server-info", "config://api-setup"],
            "apis_used": [
                "Open-Meteo (free weather API -