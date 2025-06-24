# Replit.md

## Overview

This is a sample Model Context Protocol (MCP) server designed to integrate with ChatGPT's Deep Research feature. The application provides search and document retrieval capabilities for a knowledge base through a FastMCP server implementation. It serves as a reference implementation for building custom MCP servers that can extend ChatGPT with company-specific knowledge and tools.

## System Architecture

The application follows a simple server-based architecture:

- **Backend Framework**: FastMCP (Model Context Protocol implementation)
- **Runtime**: Python 3.11 with uvicorn ASGI server
- **Transport**: Server-Sent Events (SSE) for real-time communication
- **Data Storage**: In-memory storage with JSON file loading
- **Deployment**: Single-process server running on port 8000

## Key Components

### 1. MCP Server (`main.py`)
- **Purpose**: Main application entry point implementing MCP protocol
- **Key Functions**:
  - `load_sample_data()`: Loads documents from JSON file into memory
  - `create_server()`: Configures FastMCP server with tools
- **Architecture Decision**: Uses FastMCP library for simplified MCP implementation
- **Rationale**: FastMCP abstracts away protocol complexity while maintaining full MCP compatibility

### 2. Sample Data (`sample_data.json`)
- **Purpose**: Static knowledge base with sample documents
- **Structure**: Array of document records with metadata
- **Fields**: id, title, text, content, url, metadata (category, author, date, tags)
- **Architecture Decision**: JSON file for simple data storage
- **Rationale**: Demonstrates data structure without database complexity

### 3. Configuration Files
- **`.replit`**: Defines Python 3.11 environment and workflow automation
- **`pyproject.toml`**: Python project dependencies (fastmcp, uvicorn)
- **`uv.lock`**: Dependency lock file for reproducible builds

## Data Flow

1. **Server Startup**: 
   - Load sample data from JSON file into memory
   - Create lookup dictionary for fast document retrieval
   - Initialize FastMCP server with search and fetch tools

2. **Search Operations**:
   - Accept keyword-based search queries
   - Search across document titles, content, and metadata
   - Return matching document summaries

3. **Fetch Operations**:
   - Accept document ID requests
   - Return complete document with full content and metadata
   - Provide fast retrieval through in-memory lookup

4. **MCP Communication**:
   - Use Server-Sent Events for real-time communication
   - Follow MCP protocol for tool invocation and responses

## External Dependencies

### Core Dependencies
- **fastmcp (>=2.9.0)**: MCP protocol implementation
- **uvicorn (>=0.34.3)**: ASGI server for hosting
- **pydantic**: Data validation (indirect dependency)

### Development Environment
- **Python 3.11**: Runtime environment
- **Nix**: Package management and environment reproducibility

## Deployment Strategy

### Development Deployment
- **Platform**: Replit environment with Nix package management
- **Process**: Single uvicorn server process
- **Port**: 8000 (configured in workflow)
- **Auto-restart**: Enabled through Replit workflow configuration

### Production Considerations
- **Scaling**: Currently single-process, would need load balancing for production
- **Data Persistence**: JSON file storage suitable for read-only scenarios
- **Security**: No authentication implemented (would need to add for production)

### Architecture Decision: In-Memory Storage
- **Problem**: Need fast document retrieval for MCP operations
- **Solution**: Load all documents into memory at startup
- **Pros**: Fast lookup times, simple implementation
- **Cons**: Limited by available memory, data lost on restart
- **Alternative Considered**: Database storage (would add complexity for sample)

## Recent Changes

- **June 24, 2025**: Created complete MCP server implementation
  - Built FastMCP server with search and fetch tools
  - Added 5 sample documents for testing
  - Implemented SSE transport for ChatGPT integration
  - Server successfully running on port 8000
  - All tools working and ready for ChatGPT Deep Research connection

## Changelog

```
Changelog:
- June 24, 2025: Initial MCP server setup complete
  - FastMCP server with search/fetch tools
  - Sample knowledge base with 5 documents  
  - SSE transport enabled for ChatGPT integration
  - Comprehensive documentation and setup guide
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```