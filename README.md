# Sample MCP Server for ChatGPT Deep Research

This is a sample Model Context Protocol (MCP) server designed to work with ChatGPT's Deep Research feature. It provides search and document retrieval capabilities for a sample knowledge base, demonstrating how to build custom MCP servers that can extend ChatGPT with company-specific knowledge and tools.

## Features

- **Search Tool**: Keyword-based search across document titles, content, and metadata
- **Fetch Tool**: Complete document retrieval by ID with full content and metadata
- **SSE Transport**: Server-Sent Events transport for real-time communication with ChatGPT
- **Sample Data**: Includes 5 sample documents covering various technical topics
- **MCP Compliance**: Follows OpenAI's MCP specification for deep research integration

## Requirements

- Python 3.8+
- fastmcp (>=2.9.0)
- uvicorn (>=0.34.3)
- pydantic (dependency of fastmcp)

## Installation

1. Install the required dependencies:
```bash
pip install fastmcp uvicorn
```

2. Run the MCP server:
```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` with SSE transport enabled.

## Usage

### Connecting to ChatGPT Deep Research

1. **Access ChatGPT Settings**: Go to [ChatGPT settings](https://chatgpt.com/#settings)
2. **Navigate to Connectors**: Click on the "Connectors" tab
3. **Add MCP Server**: Add your server URL: `http://your-domain:8000/sse/`
4. **Test Connection**: The server should appear as available for deep research

### Server Endpoints

- **SSE Endpoint**: `http://0.0.0.0:8000/sse/` - Main MCP communication endpoint
- **Health Check**: Server logs will show successful startup and tool registration

### Available Tools

#### Search Tool
- **Purpose**: Find relevant documents using keyword matching
- **Input**: Search query string with keywords
- **Output**: List of matching documents with ID, title, and text snippet
- **Usage**: ChatGPT will use this to find relevant documents based on your research queries

#### Fetch Tool  
- **Purpose**: Retrieve complete document content for detailed analysis
- **Input**: Document ID from search results
- **Output**: Full document with complete text, metadata, and optional URL for citations
- **Usage**: ChatGPT will use this to get full content after finding relevant documents

## Sample Data

The server includes 5 sample documents covering:
- Machine Learning fundamentals
- Python development best practices  
- REST API design principles
- Database optimization techniques
- Cloud security fundamentals

## Customization

### Adding Your Own Data

1. **Edit `sample_data.json`**: Replace the sample documents with your own content
2. **Document Structure**: Each document should include:
   ```json
   {
     "id": "unique_identifier",
     "title": "Document Title",
     "text": "Short description or excerpt",
     "content": "Full document content",
     "url": "https://optional-source-url.com",
     "metadata": {
       "category": "document_category",
       "author": "Author Name",
       "date": "2024-01-01",
       "tags": "comma,separated,tags"
     }
   }
   ```

3. **Restart Server**: The server loads data at startup, so restart after making changes

### Modifying Search Logic

The search function in `main.py` can be customized for:
- Advanced query parsing (e.g., boolean operators)
- Relevance scoring and ranking
- Fuzzy matching or semantic search
- Custom filtering by metadata fields

## Deployment

### Local Development
The server runs locally on port 8000 and is accessible for testing with ChatGPT.

### Production Deployment
For production use:
1. **Use HTTPS**: Ensure your server has SSL/TLS certificates
2. **Authentication**: Consider adding OAuth or API key authentication
3. **Rate Limiting**: Implement rate limiting for production traffic
4. **Monitoring**: Add logging and monitoring for server health
5. **Scaling**: Consider load balancing for high-traffic scenarios

### Tunneling for Local Testing
If running locally and need external access, use tunneling tools like:
```bash
# Using ngrok
ngrok http 8000

# Using cloudflare tunnel
cloudflared tunnel --url http://localhost:8000
```

## Architecture

This MCP server uses:
- **FastMCP**: Simplified MCP protocol implementation
- **Uvicorn**: ASGI server for HTTP/SSE transport
- **In-Memory Storage**: Fast document lookup from JSON data
- **Keyword Search**: Simple but effective text matching algorithm

## Troubleshooting

### Common Issues

1. **Server won't start**: Check if port 8000 is already in use
2. **ChatGPT can't connect**: Ensure the server URL is correct and accessible
3. **No search results**: Check that your data is properly formatted in `sample_data.json`
4. **Tools not appearing**: Verify the server is running and MCP protocol is working

### Debugging

- Check server logs for detailed error messages
- Use curl to test the SSE endpoint: `curl http://localhost:8000/sse/`
- Verify JSON data format with a JSON validator

## Contributing

This is a sample implementation. To extend it:
1. Add more sophisticated search algorithms
2. Implement database storage for larger datasets  
3. Add authentication and security features
4. Create additional MCP tools beyond search and fetch

## License

This sample code is provided for educational and demonstration purposes.
