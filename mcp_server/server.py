#!/usr/bin/env python3
"""
A simple MCP server that provides basic calculator and text processing tools.
"""

import asyncio
import json
import sys
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
            "description": "A sample MCP server with calculator and text analysis tools",
            "tools": ["calculator", "text_analyzer", "list_files"],
            "resources": ["config://server-info"]
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