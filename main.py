#!/usr/bin/env python3
"""
Sample MCP Server for ChatGPT Deep Research Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's deep research feature.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global data storage
RECORDS: List[Dict[str, Any]] = []
LOOKUP: Dict[str, Dict[str, Any]] = {}

def load_sample_data():
    """Load sample data from JSON file."""
    global RECORDS, LOOKUP
    
    try:
        data_file = Path("sample_data.json")
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                RECORDS = data.get("records", [])
                
            # Create lookup dictionary for fast retrieval
            LOOKUP = {record["id"]: record for record in RECORDS}
            logger.info(f"Loaded {len(RECORDS)} records from sample_data.json")
        else:
            logger.warning("sample_data.json not found, using empty dataset")
            RECORDS = []
            LOOKUP = {}
            
    except Exception as e:
        logger.error(f"Failed to load sample data: {e}")
        RECORDS = []
        LOOKUP = {}

def create_server():
    """Create and configure the MCP server with search and fetch tools."""
    
    # Initialize the FastMCP server
    mcp = FastMCP(
        name="Sample Deep Research MCP Server",
        instructions="""
        This MCP server provides search and document retrieval capabilities for deep research.
        Use the search tool to find relevant documents based on keywords, then use the fetch 
        tool to retrieve complete document content with citations.
        """
    )

    @mcp.tool()
    async def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using keyword matching.
        
        This tool searches across document titles, content, and metadata to find relevant matches.
        Returns a list of search results with basic information. Use the fetch tool to get 
        complete document content.
        
        Args:
            query: Search query string. Can include multiple keywords separated by spaces.
                  All keywords will be matched against document content.
        
        Returns:
            Dictionary with 'results' key containing list of matching documents.
            Each result includes id, title, text snippet, and optional URL.
        """
        if not query or not query.strip():
            return {"results": []}
        
        # Tokenize query for keyword matching
        query_tokens = query.lower().strip().split()
        if not query_tokens:
            return {"results": []}
        
        results = []
        
        for record in RECORDS:
            # Create searchable text from all relevant fields
            searchable_fields = [
                record.get("title", ""),
                record.get("text", ""),
                record.get("content", ""),  # Additional content field
            ]
            
            # Add metadata values to searchable content
            metadata = record.get("metadata", {})
            if isinstance(metadata, dict):
                searchable_fields.extend(str(v) for v in metadata.values())
            
            # Combine all searchable text
            searchable_text = " ".join(searchable_fields).lower()
            
            # Check if any query token matches
            if any(token in searchable_text for token in query_tokens):
                # Create result with required fields
                result = {
                    "id": record["id"],
                    "title": record.get("title", f"Document {record['id']}"),
                    "text": record.get("text", record.get("content", ""))[:200] + "...",  # Snippet
                }
                
                # Add optional URL if available
                if "url" in record and record["url"]:
                    result["url"] = record["url"]
                
                results.append(result)
        
        logger.info(f"Search query '{query}' returned {len(results)} results")
        return {"results": results}

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID for detailed analysis and citation.
        
        This tool fetches the full document content including all metadata. Use this after
        finding relevant documents with the search tool to get complete information for
        analysis and proper citation.
        
        Args:
            id: Unique identifier of the document to retrieve
            
        Returns:
            Complete document with id, title, full text content, optional URL, and metadata
            
        Raises:
            ValueError: If the specified ID is not found
        """
        if not id or id not in LOOKUP:
            available_ids = list(LOOKUP.keys())[:5]  # Show first 5 IDs as examples
            raise ValueError(
                f"Document with ID '{id}' not found. "
                f"Available IDs include: {available_ids}..."
            )
        
        document = LOOKUP[id].copy()
        
        # Ensure required fields are present
        result = {
            "id": document["id"],
            "title": document.get("title", f"Document {document['id']}"),
            "text": document.get("text", document.get("content", "")),
        }
        
        # Add optional fields if available
        if "url" in document and document["url"]:
            result["url"] = document["url"]
        
        if "metadata" in document and document["metadata"]:
            result["metadata"] = document["metadata"]
        
        logger.info(f"Fetched document with ID: {id}")
        return result

    return mcp

def main():
    """Main function to start the MCP server."""
    # Load sample data
    load_sample_data()
    
    if not RECORDS:
        logger.warning("No sample data loaded. Server will run with empty dataset.")
    
    # Create the MCP server
    server = create_server()
    
    # Configure and start the server
    logger.info("Starting MCP server on 0.0.0.0:8000")
    logger.info("Server will be accessible via SSE transport")
    logger.info("Connect this server to ChatGPT Deep Research for testing")
    
    try:
        # Use FastMCP's built-in run method with SSE transport
        server.run(transport="sse", host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()
