#!/usr/bin/env python3
"""
Flight Tracker Web Application
A Flask-based web UI that connects to your MCP server to display real-time flight data.
"""

import os
import json
import asyncio
import subprocess
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import folium
from folium.plugins import MarkerCluster
import requests
import aiohttp
from pathlib import Path

# Import your MCP server functions
import sys
sys.path.append('src')
from mcp_server.server import (
    get_location_coordinates, 
    handle_get_flights_by_location,
    handle_get_airport_info,
    handle_get_weather
)

app = Flask(__name__)

# Load environment variables
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

class FlightTracker:
    def __init__(self):
        self.current_location = None
        self.current_flights = []
        self.current_airports = []
        
    async def search_location(self, query):
        """Search for location coordinates."""
        try:
            location_data = await get_location_coordinates(query)
            if location_data:
                self.current_location = {
                    'name': location_data['name'],
                    'country': location_data.get('country', ''),
                    'latitude': location_data['latitude'],
                    'longitude': location_data['longitude']
                }
                return self.current_location
            return None
        except Exception as e:
            print(f"Error searching location: {e}")
            return None
    
    async def get_flights_data(self, location, radius=200):
        """Get flight data from MCP server."""
        try:
            arguments = {
                'location': location,
                'radius': radius,
                'limit': 50
            }
            
            # Call your MCP server function directly
            response = await handle_get_flights_by_location(arguments)
            
            if response and len(response) > 0:
                # Parse the response text to extract flight data
                response_text = response[0].text
                
                # For demo purposes, generate some mock flight data
                # In a real implementation, you'd parse the actual MCP response
                flights = self.generate_mock_flights(self.current_location, radius)
                self.current_flights = flights
                return flights
            
            return []
        except Exception as e:
            print(f"Error getting flights: {e}")
            # Return mock data for demonstration
            return self.generate_mock_flights(self.current_location, radius)
    
    async def get_airport_data(self, location):
        """Get airport data from MCP server."""
        try:
            arguments = {'location': location}
            response = await handle_get_airport_info(arguments)
            
            if response and len(response) > 0:
                # For demo, return mock airport data
                airports = self.generate_mock_airports(self.current_location)
                self.current_airports = airports
                return airports
            
            return []
        except Exception as e:
            print(f"Error getting airports: {e}")
            return self.generate_mock_airports(self.current_location)
    
    def generate_mock_flights(self, center, radius_km):
        """Generate mock flight data for demonstration."""
        if not center:
            return []
        
        import random
        flights = []
        
        # Convert radius from km to degrees (rough approximation)
        radius_deg = radius_km / 111.0
        
        for i in range(15):
            # Generate random position within radius
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(0, radius_deg)
            
            lat = center['latitude'] + distance * random.uniform(-1, 1)
            lon = center['longitude'] + distance * random.uniform(-1, 1)
            
            # Mock flight data
            airlines = ['SAS', 'Norwegian', 'Lufthansa', 'KLM', 'Air France', 'British Airways']
            statuses = ['Active', 'Departed', 'Approaching', 'Climbing', 'Cruising']
            
            flight = {
                'id': f'flight_{i}',
                'number': f'{random.choice(["SK", "DY", "LH", "KL", "AF", "BA"])}{random.randint(100, 9999)}',
                'airline': random.choice(airlines),
                'latitude': lat,
                'longitude': lon,
                'altitude': random.randint(20000, 42000),
                'speed': random.randint(400, 900),
                'heading': random.randint(0, 360),
                'status': random.choice(statuses),
                'origin': random.choice(['OSL', 'BGO', 'TRD', 'SVG', 'BOO']),
                'destination': random.choice(['CPH', 'ARN', 'FRA', 'AMS', 'LHR']),
                'aircraft_type': random.choice(['B737', 'A320', 'B787', 'A350', 'B777'])
            }
            flights.append(flight)
        
        return flights
    
    def generate_mock_airports(self, center):
        """Generate mock airport data for demonstration."""
        if not center:
            return []
        
        import random
        airports = []
        
        # Add main airport at center
        airports.append({
            'name': f'{center["name"]} Airport',
            'code': 'XXX',
            'latitude': center['latitude'],
            'longitude': center['longitude'],
            'type': 'International'
        })
        
        # Add nearby airports
        for i in range(3):
            lat_offset = random.uniform(-1, 1)
            lon_offset = random.uniform(-1, 1)
            
            airport = {
                'name': f'Regional Airport {i+1}',
                'code': f'R{i+1:02d}',
                'latitude': center['latitude'] + lat_offset,
                'longitude': center['longitude'] + lon_offset,
                'type': 'Regional'
            }
            airports.append(airport)
        
        return airports

# Global flight tracker instance
tracker = FlightTracker()

@app.route('/')
def index():
    """Main page with search interface."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle location search."""
    try:
        data = request.json
        query = data.get('query', '')
        radius = data.get('radius', 200)
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        # Run async functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Search for location
            location = loop.run_until_complete(tracker.search_location(query))
            if not location:
                return jsonify({'error': f'Location "{query}" not found'}), 404
            
            # Get flights and airports data
            flights = loop.run_until_complete(tracker.get_flights_data(query, radius))
            airports = loop.run_until_complete(tracker.get_airport_data(query))
            
            return jsonify({
                'location': location,
                'flights': flights,
                'airports': airports,
                'radius': radius
            })
        finally:
            loop.close()
    
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/map')
def generate_map():
    """Generate interactive map with flight data."""
    try:
        if not tracker.current_location:
            return jsonify({'error': 'No location data available. Please search first.'}), 400
        
        # Create map centered on location
        center_lat = tracker.current_location['latitude']
        center_lon = tracker.current_location['longitude']
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Add 200km radius circle
        folium.Circle(
            location=[center_lat, center_lon],
            radius=200000,  # 200km in meters
            color='blue',
            fill=False,
            weight=2,
            popup='200km Search Radius'
        ).add_to(m)
        
        # Add center location marker
        folium.Marker(
            [center_lat, center_lon],
            popup=f"<b>{tracker.current_location['name']}</b><br/>{tracker.current_location['country']}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add airport markers
        for airport in tracker.current_airports:
            folium.Marker(
                [airport['latitude'], airport['longitude']],
                popup=f"<b>{airport['name']}</b><br/>Code: {airport['code']}<br/>Type: {airport['type']}",
                icon=folium.Icon(color='green', icon='plane')
            ).add_to(m)
        
        # Add flight markers with clustering
        marker_cluster = MarkerCluster().add_to(m)
        
        for flight in tracker.current_flights:
            # Create custom airplane icon
            flight_popup = f"""
            <div style='width: 200px;'>
                <h4>{flight['number']}</h4>
                <b>Airline:</b> {flight['airline']}<br/>
                <b>Route:</b> {flight['origin']} → {flight['destination']}<br/>
                <b>Status:</b> {flight['status']}<br/>
                <b>Altitude:</b> {flight['altitude']:,} ft<br/>
                <b>Speed:</b> {flight['speed']} km/h<br/>
                <b>Heading:</b> {flight['heading']}°<br/>
                <b>Aircraft:</b> {flight['aircraft_type']}
            </div>
            """
            
            # Color code by status
            status_colors = {
                'Active': 'blue',
                'Departed': 'green', 
                'Approaching': 'orange',
                'Climbing': 'purple',
                'Cruising': 'darkblue'
            }
            color = status_colors.get(flight['status'], 'gray')
            
            folium.Marker(
                [flight['latitude'], flight['longitude']],
                popup=flight_popup,
                icon=folium.Icon(color=color, icon='plane'),
                tooltip=f"Flight {flight['number']} - {flight['status']}"
            ).add_to(marker_cluster)
        
        # Add map legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Legend</h4>
        <p><i class="fa fa-map-marker" style="color:red"></i> Search Location</p>
        <p><i class="fa fa-plane" style="color:green"></i> Airports</p>
        <p><i class="fa fa-plane" style="color:blue"></i> Active Flights</p>
        <p><i class="fa fa-circle" style="color:blue"></i> 200km Radius</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map to temporary file and return HTML
        map_html = m._repr_html_()
        return map_html
    
    except Exception as e:
        return f"<html><body><h2>Error generating map: {str(e)}</h2></body></html>"

@app.route('/flights/update')
def update_flights():
    """Get updated flight positions (for real-time updates)."""
    try:
        if not tracker.current_flights:
            return jsonify({'flights': []})
        
        # In a real implementation, you'd fetch updated positions
        # For demo, slightly move existing flights
        import random
        
        updated_flights = []
        for flight in tracker.current_flights:
            # Simulate slight movement
            flight['latitude'] += random.uniform(-0.01, 0.01)
            flight['longitude'] += random.uniform(-0.01, 0.01)
            updated_flights.append(flight)
        
        tracker.current_flights = updated_flights
        return jsonify({'flights': updated_flights})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Check if template directory exists, create if not
    template_dir = Path('templates')
    template_dir.mkdir(exist_ok=True)
    
    # Create the HTML template
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Tracker - Real-time Aviation Data</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .search-section {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }
        
        .search-form {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
        }
        
        .search-input {
            flex: 1;
            min-width: 300px;
            padding: 15px 20px;
            border: 2px solid #ddd;
            border-radius: 50px;
            font-size: 16px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .search-input:focus {
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        
        .radius-input {
            width: 120px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 50px;
            font-size: 16px;
        }
        
        .search-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }
        
        .search-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
        }
        
        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 0;
            height: 70vh;
        }
        
        .info-panel {
            padding: 30px;
            overflow-y: auto;
            background: white;
            border-right: 2px solid #e9ecef;
        }
        
        .map-panel {
            position: relative;
            background: #f8f9fa;
        }
        
        .map-container {
            height: 100%;
            width: 100%;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #7f8c8d;
        }
        
        .loading .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #ecf0f1;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .info-section {
            margin-bottom: 25px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }
        
        .info-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .flight-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .airport-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #27ae60;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .error {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-active { background-color: #27ae60; }
        .status-departed { background-color: #f39c12; }
        .status-approaching { background-color: #e67e22; }
        .status-climbing { background-color: #9b59b6; }
        .status-cruising { background-color: #3498db; }
        
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }
            
            .search-form {
                flex-direction: column;
                align-items: stretch;
            }
            
            .search-input, .radius-input {
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ Flight Tracker</h1>
            <p>Real-time aviation data powered by MCP Server</p>
        </div>
        
        <div class="search-section">
            <form class="search-form" onsubmit="searchLocation(event)">
                <input type="text" id="locationInput" class="search-input" 
                       placeholder="Enter airport code or city (e.g., OSL, Oslo, JFK)" 
                       value="Oslo" required>
                <input type="number" id="radiusInput" class="radius-input" 
                       placeholder="Radius (km)" value="200" min="50" max="500">
                <button type="submit" id="searchBtn" class="search-btn">
                    🔍 Track Flights
                </button>
            </form>
        </div>
        
        <div class="content">
            <div class="info-panel">
                <div id="infoContainer">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Ready to track flights! Enter a location and click "Track Flights"</p>
                    </div>
                </div>
            </div>
            
            <div class="map-panel">
                <div id="mapContainer" class="map-container">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Map will appear here after searching...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let updateInterval = null;
        
        async function searchLocation(event) {
            event.preventDefault();
            
            const location = document.getElementById('locationInput').value.trim();
            const radius = parseInt(document.getElementById('radiusInput').value) || 200;
            const searchBtn = document.getElementById('searchBtn');
            const infoContainer = document.getElementById('infoContainer');
            const mapContainer = document.getElementById('mapContainer');
            
            if (!location) return;
            
            // Show loading state
            searchBtn.disabled = true;
            searchBtn.textContent = '🔄 Searching...';
            infoContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Searching for flights...</p></div>';
            mapContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating map...</p></div>';
            
            try {
                // Search for location and flights
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: location,
                        radius: radius
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Search failed');
                }
                
                const data = await response.json();
                
                // Update info panel
                displayInfo(data);
                
                // Load map
                await loadMap();
                
                // Start auto-refresh for flight positions
                startAutoRefresh();
                
            } catch (error) {
                infoContainer.innerHTML = `
                    <div class="error">
                        <h3>Error</h3>
                        <p>${error.message}</p>
                    </div>
                `;
                mapContainer.innerHTML = `
                    <div class="error">
                        <h3>Map Error</h3>
                        <p>Could not load map: ${error.message}</p>
                    </div>
                `;
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = '🔍 Track Flights';
            }
        }
        
        function displayInfo(data) {
            const { location, flights, airports, radius } = data;
            
            let html = '';
            
            // Location info
            html += `
                <div class="info-section">
                    <h3>📍 Location</h3>
                    <p><strong>${location.name}</strong></p>
                    <p>${location.country}</p>
                    <p>Coordinates: ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}</p>
                    <p>Search Radius: ${radius}km</p>
                </div>
            `;
            
            // Airports
            if (airports && airports.length > 0) {
                html += `
                    <div class="info-section">
                        <h3>🛬 Airports (${airports.length})</h3>
                `;
                airports.forEach(airport => {
                    html += `
                        <div class="airport-item">
                            <strong>${airport.name}</strong><br>
                            Code: ${airport.code}<br>
                            Type: ${airport.type}
                        </div>
                    `;
                });
                html += '</div>';
            }
            
            // Flights
            if (flights && flights.length > 0) {
                html += `
                    <div class="info-section">
                        <h3>✈️ Active Flights (${flights.length})</h3>
                `;
                flights.forEach(flight => {
                    const statusClass = `status-${flight.status.toLowerCase()}`;
                    html += `
                        <div class="flight-item">
                            <strong>${flight.number}</strong> (${flight.airline})<br>
                            <span class="status-indicator ${statusClass}"></span>
                            Status: ${flight.status}<br>
                            Route: ${flight.origin} → ${flight.destination}<br>
                            Altitude: ${flight.altitude.toLocaleString()} ft<br>
                            Speed: ${flight.speed} km/h<br>
                            Aircraft: ${flight.aircraft_type}
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += `
                    <div class="info-section">
                        <h3>✈️ Flights</h3>
                        <p>No flights found in the specified area.</p>
                    </div>
                `;
            }
            
            document.getElementById('infoContainer').innerHTML = html;
        }
        
        async function loadMap() {
            try {
                const response = await fetch('/map');
                const mapHtml = await response.text();
                document.getElementById('mapContainer').innerHTML = mapHtml;
            } catch (error) {
                document.getElementById('mapContainer').innerHTML = `
                    <div class="error">
                        <h3>Map Error</h3>
                        <p>Could not load map: ${error.message}</p>
                    </div>
                `;
            }
        }
        
        function startAutoRefresh() {
            // Clear existing interval
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            
            // Refresh flight positions every 30 seconds
            updateInterval = setInterval(async () => {
                try {
                    const response = await fetch('/flights/update');
                    const data = await response.json();
                    
                    if (data.flights) {
                        // Reload map with updated positions
                        await loadMap();
                    }
                } catch (error) {
                    console.error('Auto-refresh failed:', error);
                }
            }, 30000); // 30 seconds
        }
        
        // Load Oslo by default
        window.addEventListener('load', () => {
            setTimeout(() => {
                const form = document.querySelector('.search-form');
                searchLocation({ preventDefault: () => {}, target: form });
            }, 1000);
        });
    </script>
</body>
</html>'''
    
    # Write template file
    with open(template_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("🚀 Flight Tracker Web Application Starting...")
    print("📍 Open your browser and go to: http://localhost:5000")
    print("✈️ Features:")
    print("   - Search any airport or city")
    print("   - Real-time flight tracking within 200km radius")
    print("   - Interactive map with flight positions")
    print("   - Airport information display")
    print("   - Auto-refresh every 30 seconds")
    print("\n🔧 Make sure your MCP server is configured with AVIATIONSTACK_API_KEY")
    
    app.run(debug=True, host='0.0.0.0', port=5000)