# OneMap MCP Server v2

A Python-based MCP (Model Context Protocol) server that provides comprehensive access to Singapore's OneMap APIs. Built with FastMCP for easy integration with AI assistants and Microsoft AI Foundry.

## Features

This server exposes **35+ tools** across 10 API categories:

- **Search** - Address and location search
- **Reverse Geocode** - Convert coordinates to addresses (WGS84 and SVY21)
- **Routing** - Public transport, driving, walking, cycling, barrier-free routes
- **Coordinate Converters** - EPSG 4326 (WGS84), EPSG 3414 (SVY21), EPSG 3857
- **Themes** - Access 100+ thematic layers for locations, amenities, boundaries
- **Planning Area** - Singapore's 55 planning area information
- **Population Query** - Demographics and statistics by planning area
- **Nearby Transport** - Find nearby MRT/LRT stations and bus stops
- **Static Map** - Generate static map images with optional overlays

## Prerequisites

- Python 3.11+
- OneMap Account (register at [OneMap API](https://www.onemap.gov.sg/apidocs/))

## Installation

### Local Development

1. Clone the repository:
```bash
cd onemap-mcp
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your credentials:
```bash
cp .env.example .env
# Edit .env with your OneMap credentials
```

5. Run the server:
```bash
python server.py
```

### Environment Variables

Create a `.env` file with:

```env
ONEMAP_EMAIL=your_email@example.com
ONEMAP_EMAIL_PASSWORD=your_password
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t onemap-mcp .
```

2. Run the container:
```bash
docker run -d \
  -e ONEMAP_EMAIL="your_email@example.com" \
  -e ONEMAP_EMAIL_PASSWORD="your_password" \
  --name onemap-mcp \
  onemap-mcp
```

## Available Tools

### Search & Geocoding
| Tool | Description |
|------|-------------|
| `search` | Search for addresses, buildings, postal codes |
| `reverse_geocode_wgs84` | Get address from WGS84 coordinates |
| `reverse_geocode_svy21` | Get address from SVY21 coordinates |

### Routing
| Tool | Description |
|------|-------------|
| `route_walk_drive_cycle` | Walking, driving, cycling, barrier-free routes |
| `route_public_transport` | Bus and MRT routes with fare info |

### Coordinate Conversion
| Tool | Description |
|------|-------------|
| `convert_4326_to_3857` | WGS84 → Web Mercator |
| `convert_4326_to_3414` | WGS84 → SVY21 |
| `convert_3414_to_4326` | SVY21 → WGS84 |
| `convert_3414_to_3857` | SVY21 → Web Mercator |
| `convert_3857_to_4326` | Web Mercator → WGS84 |
| `convert_3857_to_3414` | Web Mercator → SVY21 |

### Themes
| Tool | Description |
|------|-------------|
| `get_all_themes_info` | List all 100+ thematic layers |
| `get_theme_info` | Get info about a specific theme |
| `check_theme_status` | Check if theme was updated |
| `retrieve_theme` | Retrieve theme data |

### Planning Areas
| Tool | Description |
|------|-------------|
| `get_all_planning_areas` | Get all 55 planning area polygons |
| `get_planning_area_names` | List planning area names |
| `get_planning_area_by_location` | Get planning area for a location |

### Population Data
| Tool | Description |
|------|-------------|
| `get_population_age_group` | Population by age |
| `get_ethnic_distribution` | Ethnic group distribution |
| `get_economic_status` | Employment statistics |
| `get_household_monthly_income` | Income distribution |
| `get_education_status` | Education levels |
| ... and more |

### Transport
| Tool | Description |
|------|-------------|
| `get_nearby_mrt_stations` | Find nearby MRT/LRT stations |
| `get_nearby_bus_stops` | Find nearby bus stops |

### Static Maps
| Tool | Description |
|------|-------------|
| `get_static_map` | Generate map images with overlays |

## Usage Examples

### Search for a location
```python
# Search for Marina Bay Sands
result = await search(search_value="Marina Bay Sands")
```

### Get route directions
```python
# Driving route from Changi to Orchard
result = await route_walk_drive_cycle(
    start_lat=1.3644,
    start_lon=103.9915,
    end_lat=1.3048,
    end_lon=103.8318,
    route_type="drive"
)
```

### Find nearby MRT stations
```python
result = await get_nearby_mrt_stations(
    latitude=1.3521,
    longitude=103.8198,
    radius_in_meters=1000
)
```

## Project Structure

```
onemap-mcp/
├── server.py          # FastMCP server with all tools
├── mcp.json           # MCP manifest
├── tools.json         # Tool definitions for AI Foundry
├── onemap/
│   ├── __init__.py
│   └── utils.py       # HTTP client and utility functions
├── .env               # Your credentials (not in git)
├── .env.example       # Template for credentials
├── Dockerfile
├── requirements.txt
└── README.md
```

## Deployment to Azure

### Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry <registry-name> --image onemap-mcp:latest .

# Deploy to Container Apps
az containerapp create \
  --name onemap-mcp \
  --resource-group <resource-group> \
  --image <registry-name>.azurecr.io/onemap-mcp:latest \
  --env-vars ONEMAP_EMAIL=<email> ONEMAP_EMAIL_PASSWORD=<password>
```

## Microsoft AI Foundry Integration

1. Deploy the server to a publicly accessible endpoint
2. Use the `tools.json` file to configure tool definitions
3. Configure `ONEMAP_EMAIL` and `ONEMAP_EMAIL_PASSWORD` environment variables

## License

MIT

## Resources

- [OneMap API Documentation](https://www.onemap.gov.sg/apidocs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Microsoft AI Foundry](https://ai.azure.com/)
