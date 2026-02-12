"""
Utility functions for OneMap MCP Server.
Provides HTTP client management, response formatting, and error handling.
"""
import json
from typing import Any, Dict, Optional

import httpx


# Global HTTP client cache
_http_clients: Dict[str, httpx.AsyncClient] = {}


async def get_async_client(base_url: str, timeout: float = 30.0) -> httpx.AsyncClient:
    """
    Get or create an async HTTP client for the given base URL.
    
    Args:
        base_url: The base URL for the client
        timeout: Request timeout in seconds
        
    Returns:
        An async HTTP client instance
    """
    if base_url not in _http_clients:
        _http_clients[base_url] = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout
        )
    return _http_clients[base_url]


async def cleanup_clients():
    """Close all cached HTTP clients."""
    for client in _http_clients.values():
        await client.aclose()
    _http_clients.clear()


def success_response(data: Any) -> Dict[str, Any]:
    """
    Create a success response wrapper.
    
    Args:
        data: The response data
        
    Returns:
        Success response dictionary
    """
    return {
        "success": True,
        "data": data
    }


def error_response(message: str, details: Any = None) -> Dict[str, Any]:
    """
    Create an error response wrapper.
    
    Args:
        message: Error message
        details: Optional error details
        
    Returns:
        Error response dictionary
    """
    response = {
        "success": False,
        "error": message
    }
    if details is not None:
        response["details"] = details
    return response


def format_response(response: Dict[str, Any]) -> str:
    """
    Format a response dictionary as a JSON string.
    
    Args:
        response: Response dictionary
        
    Returns:
        JSON formatted string
    """
    return json.dumps(response, indent=2, ensure_ascii=False)


def handle_http_error(exc: httpx.HTTPError) -> Dict[str, Any]:
    """
    Handle HTTP errors and return a formatted error response.
    
    Args:
        exc: The HTTP exception
        
    Returns:
        Error response dictionary
    """
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        try:
            error_detail = exc.response.json()
        except (json.JSONDecodeError, ValueError):
            error_detail = exc.response.text
        
        return error_response(
            f"HTTP {status_code} error",
            details=error_detail
        )
    elif isinstance(exc, httpx.TimeoutException):
        return error_response("Request timed out")
    elif isinstance(exc, httpx.ConnectError):
        return error_response("Failed to connect to OneMap API")
    else:
        return error_response(f"HTTP error: {str(exc)}")


def format_mcp_response(result: Any, tool_name: str) -> Dict[str, Any]:
    """
    Format a response according to MCP specification.
    
    Args:
        result: The result data to format
        tool_name: Name of the tool that produced the result
        
    Returns:
        Properly formatted MCP response
    """
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
            }
        ],
        "isError": False
    }


def format_mcp_error(error_message: str, tool_name: str) -> Dict[str, Any]:
    """
    Format an error response according to MCP specification.
    
    Args:
        error_message: The error message
        tool_name: Name of the tool that produced the error
        
    Returns:
        Properly formatted MCP error response
    """
    return {
        "content": [
            {
                "type": "text",
                "text": f"Error: {error_message}"
            }
        ],
        "isError": True
    }


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate latitude and longitude values.
    
    Args:
        lat: Latitude value
        lng: Longitude value
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    if not (-90 <= lat <= 90):
        return False
    if not (-180 <= lng <= 180):
        return False
    return True


def parse_route_type(route_type: str) -> str:
    """
    Parse and validate route type for OneMap routing API.
    
    Args:
        route_type: Route type string (drive, walk, cycle, pt, bfa)
        
    Returns:
        Validated route type
    """
    valid_types = ["drive", "walk", "cycle", "pt", "bfa"]
    route_type_lower = route_type.lower()
    if route_type_lower not in valid_types:
        raise ValueError(f"Invalid route type. Must be one of: {', '.join(valid_types)}")
    return route_type_lower


def format_address_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a single address search result for cleaner output.
    
    Args:
        result: Raw result from OneMap search API
        
    Returns:
        Formatted address result
    """
    return {
        "address": result.get("ADDRESS", ""),
        "building_name": result.get("BUILDING", ""),
        "postal_code": result.get("POSTAL", ""),
        "latitude": result.get("LATITUDE", ""),
        "longitude": result.get("LONGITUDE", ""),
        "x": result.get("X", ""),
        "y": result.get("Y", "")
    }


def generate_json_rpc_response(id: Any, result: Any) -> Dict[str, Any]:
    """
    Generate a JSON-RPC 2.0 response.
    
    Args:
        id: Request ID
        result: Result data
        
    Returns:
        JSON-RPC 2.0 formatted response
    """
    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    }


def generate_json_rpc_error(id: Any, code: int, message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    """
    Generate a JSON-RPC 2.0 error response.
    
    Args:
        id: Request ID
        code: Error code
        message: Error message
        data: Optional additional error data
        
    Returns:
        JSON-RPC 2.0 formatted error response
    """
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
        
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": error
    }
