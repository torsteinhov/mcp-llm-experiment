#!/usr/bin/env python3
"""
A simple MCP server that provides basic calculator, text processing, and weather tools.
"""

import asyncio
import json
import sys
import aiohttp
from typing import Any, Dict, List, Optional

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
        # First, get coordinates for the location using Open-Meteo's geocoding
        async with aiohttp.ClientSession() as session:
            # Geocoding API call
            geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
            geocoding_params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            async with session.get(geocoding_url, params=geocoding_params) as response:
                if response.status != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Could not fetch location data (status: {response.status})"
                    )]
                
                geo_data = await response.json()
                
                if not geo_data.get("results"):
                    return [types.TextContent(
                        type="text",
                        text=f"Error: Location '{location}' not found. Please try a different city name."
                    )]
                
                # Get the first result
                location_data = geo_data["results"][0]
                lat = location_data["latitude"]
                lon = location_data["longitude"]
                city_name = location_data["name"]
                country = location_data.get("country", "")
                
            # Weather API call
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
        
    except aiohttp.ClientError as e:
        return [types.TextContent(
            type="text",
            text=f"Error: Network error while fetching weather data: {str(e)}"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error getting weather for '{location}': {str(e)}"
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
    
    result = f"🌤️ Weather for {city_name}"
    if country:
        result += f", {country}"
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
    
    # Hourly forecast (if requested)
    if include_hourly and weather_data.get("hourly"):
        hourly = weather_data["hourly"]
        result += "\n🕐 TODAY'S HOURLY FORECAST:\n"
        
        # Show next 12 hours
        for i in range(min(12, len(hourly.get("time", [])))):
            time = hourly["time"][i]
            temp = hourly.get("temperature_2m", [None])[i]
            weather_code = hourly.get("weather_code", [None])[i]
            precipitation_prob = hourly.get("precipitation_probability", [None])[i]
            
            # Format time (show only hour)
            hour = time.split('T')[1][:5] if 'T' in time else time
            
            result += f"\n{hour}: "
            if temp is not None:
                result += f"{temp}°C, "
            if weather_code is not None:
                result += f"{get_weather_description(weather_code)}"
            if precipitation_prob is not None and precipitation_prob > 0:
                result += f", {precipitation_prob}% rain chance"
            result = result.rstrip(", ") + "\n"
    
    result += "\n📡 Data provided by Open-Meteo (open-meteo.com)"
    
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
            "version": "0.1.0",
            "description": "A sample MCP server with calculator, text analysis, and weather tools",
            "tools": ["calculator", "text_analyzer", "list_files", "get_weather"],
            "resources": ["config://server-info"],
            "apis_used": ["Open-Meteo (free weather API)"]
        }
        return json.dumps(server_info, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def main():
    """
    Main entry point for the MCP server.
    """
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())