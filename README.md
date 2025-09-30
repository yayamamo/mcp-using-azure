# Sample MCP Server for ChatGPT Deep Research

This is derived from https://replit.com/@kwhinnery-oai/DeepResearchServer?v=1#README.md, and modified to support Azure OpenAI APIs.
You need:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_KEY
- AZURE_SEARCH_ENDPOINT
- AZURE_SEARCH_API_KEY
The modified version is `main_azure.py`, and `load_jsondata.py` is used to load `sample_data.json` to the Azure AI Search DB.
In addition, `validate_mcp.py` can be used to test if the MCP server runs properly.
Below is a copy from the original repository.
---
This is a sample Model Context Protocol (MCP) server designed to work with ChatGPT's Deep Research feature. It provides semantic search through OpenAI's Vector Store API and document retrieval capabilities, demonstrating how to build custom MCP servers that can extend ChatGPT with company-specific knowledge and tools.

## Features

- **Search Tool**: Semantic search using OpenAI Vector Store API
- **Fetch Tool**: Complete document retrieval by ID with full content and metadata
- **SSE Transport**: Server-Sent Events transport for real-time communication with ChatGPT
- **Sample Data**: Includes 5 sample documents covering various technical topics
- **MCP Compliance**: Follows OpenAI's MCP specification for deep research integration

## Requirements

- Python 3.8+
- fastmcp (>=2.9.0)
- uvicorn (>=0.34.3)
- openai (Python SDK for vector store search)
- pydantic (dependency of fastmcp)

## Installation

1. Install the required dependencies:
```bash
pip install fastmcp uvicorn openai
```

2. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Run the MCP server:
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
- **Purpose**: Find relevant documents using OpenAI Vector Store semantic search
- **Input**: Search query string (natural language works best)
- **Output**: List of matching documents from vector store with ID, title, and text snippet
- **Usage**: ChatGPT will use this to find semantically relevant documents from your vector store
- **Requirements**: Requires valid OpenAI API key and vector store access

#### Fetch Tool  
- **Purpose**: Retrieve complete document content from OpenAI Vector Store or local storage
- **Input**: File ID from vector store (file-xxx) or local document ID
- **Output**: Full document content with complete text and metadata
- **Usage**: ChatGPT will use this to get complete document content for detailed analysis and citations
- **Requirements**: Requires valid file IDs from vector store search results

## Vector Store Integration

The server is configured to search vector store `vs_682552f3ab90819185d4b99adcae7a07` which contains documents like:
- Palantir 10-Q financial reports
- Other documents uploaded to your OpenAI vector store

The server uses only OpenAI Vector Store APIs for both search and content retrieval - no local fallback data.

## Customization

### Using Your Own Vector Store

1. **Update Vector Store ID**: Change `VECTOR_STORE_ID` in `main.py` to your vector store ID
2. **Upload Documents**: Use OpenAI's API to upload documents to your vector store
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
- Different vector store IDs or multiple vector stores
- Custom result filtering and ranking
- Additional metadata processing from vector store results
- Custom content snippet length and formatting

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
- **OpenAI Vector Store**: Semantic search and content retrieval through OpenAI's API

## Troubleshooting

### Common Issues

1. **Server won't start**: Check if port 8000 is already in use
2. **ChatGPT can't connect**: Ensure the server URL is correct and accessible
3. **No search results**: Verify your OpenAI API key and vector store ID are correct
4. **Vector store errors**: Check that the vector store exists and contains documents
5. **Tools not appearing**: Verify the server is running and MCP protocol is working

### Debugging

- Check server logs for detailed error messages
- Use curl to test the SSE endpoint: `curl http://localhost:8000/sse/`
- Test OpenAI API key: `python -c "from openai import OpenAI; OpenAI().models.list()"`
- Verify vector store exists: Check OpenAI dashboard or API
- Verify vector store contains documents and files

## Contributing

This is a sample implementation. To extend it:
1. Add more sophisticated search algorithms
2. Implement database storage for larger datasets  
3. Add authentication and security features
4. Create additional MCP tools beyond search and fetch

## License

This sample code is provided for educational and demonstration purposes.
