#!/usr/bin/env python3
"""
Sample MCP Server for ChatGPT Deep Research Integration

This server implements the Model Context Protocol (MCP) with search and fetch
capabilities designed to work with ChatGPT's deep research feature.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastmcp import FastMCP
import uvicorn
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VECTOR_STORE_ID = "vs_682552f3ab90819185d4b99adcae7a07"

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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
        Search for documents using OpenAI Vector Store search.
        
        This tool searches through the vector store to find semantically relevant matches.
        Returns a list of search results with basic information. Use the fetch tool to get 
        complete document content.
        
        Args:
            query: Search query string. Natural language queries work best for semantic search.
        
        Returns:
            Dictionary with 'results' key containing list of matching documents.
            Each result includes id, title, text snippet, and optional URL.
        """
        if not query or not query.strip():
            return {"results": []}
        
        if not openai_client:
            logger.error("OpenAI client not initialized - API key missing")
            # Fallback to local search if OpenAI unavailable
            return await _fallback_local_search(query)
        
        try:
            # Search the vector store using OpenAI API
            logger.info(f"Searching vector store {VECTOR_STORE_ID} for query: '{query}'")
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = openai_client.vector_stores.search(
                vector_store_id=VECTOR_STORE_ID,
                query=query
            )
            
            results = []
            
            # Process the vector store search results
            if hasattr(response, 'data') and response.data:
                for i, item in enumerate(response.data):
                    # Extract file_id, filename, and content from the VectorStoreSearchResponse
                    item_id = getattr(item, 'file_id', f"vs_{i}")
                    item_filename = getattr(item, 'filename', f"Document {i+1}")
                    
                    # Extract text content from the content array
                    content_list = getattr(item, 'content', [])
                    text_content = ""
                    if content_list and len(content_list) > 0:
                        # Get text from the first content item
                        first_content = content_list[0]
                        if hasattr(first_content, 'text'):
                            text_content = first_content.text
                        elif isinstance(first_content, dict):
                            text_content = first_content.get('text', '')
                    
                    if not text_content:
                        text_content = "No content available"
                    
                    # Create a snippet from content
                    text_snippet = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    
                    result = {
                        "id": item_id,
                        "title": item_filename,
                        "text": text_snippet,
                    }
                    
                    results.append(result)
            
            logger.info(f"Vector store search returned {len(results)} results")
            return {"results": results}
            
        except Exception as e:
            logger.error(f"Vector store search failed: {e}")
            # Fallback to local search if vector store search fails
            logger.info("Falling back to local keyword search")
            return await _fallback_local_search(query)

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID for detailed analysis and citation.
        
        This tool fetches the full document content from OpenAI Vector Store or local storage.
        Use this after finding relevant documents with the search tool to get complete 
        information for analysis and proper citation.
        
        Args:
            id: File ID from vector store (file-xxx) or local document ID
            
        Returns:
            Complete document with id, title, full text content, optional URL, and metadata
            
        Raises:
            ValueError: If the specified ID is not found
        """
        if not id:
            raise ValueError("Document ID is required")
        
        # Check if this is a vector store file ID
        if id.startswith("file-") and openai_client:
            try:
                logger.info(f"Fetching content from vector store for file ID: {id}")
                
                # Fetch file content from vector store
                content_response = openai_client.vector_stores.files.content(
                    vector_store_id=VECTOR_STORE_ID,
                    file_id=id
                )
                
                # Get file metadata
                file_info = openai_client.vector_stores.files.retrieve(
                    vector_store_id=VECTOR_STORE_ID,
                    file_id=id
                )
                
                # Extract content from paginated response
                file_content = ""
                if hasattr(content_response, 'data') and content_response.data:
                    # Combine all content chunks from FileContentResponse objects
                    content_parts = []
                    for content_item in content_response.data:
                        if hasattr(content_item, 'text'):
                            content_parts.append(content_item.text)
                    file_content = "\n".join(content_parts)
                else:
                    file_content = "No content available"
                
                result = {
                    "id": id,
                    "title": f"Document {id}",
                    "text": file_content,
                }
                
                # Add metadata if available from file info
                if hasattr(file_info, 'attributes') and file_info.attributes:
                    result["metadata"] = file_info.attributes
                
                logger.info(f"Successfully fetched vector store file: {id}")
                return result
                
            except Exception as e:
                logger.error(f"Failed to fetch from vector store: {e}")
                # Fall through to local lookup
        
        # Fallback to local document lookup
        if id not in LOOKUP:
            available_ids = list(LOOKUP.keys())[:5]
            raise ValueError(
                f"Document with ID '{id}' not found in vector store or local storage. "
                f"Available local IDs include: {available_ids}..."
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
        
        logger.info(f"Fetched local document with ID: {id}")
        return result

    return mcp

async def _fallback_local_search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fallback local search function when OpenAI vector store is unavailable.
    """
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
            record.get("content", ""),
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
                "text": record.get("text", record.get("content", ""))[:200] + "...",
            }
            
            # Add optional URL if available
            if "url" in record and record["url"]:
                result["url"] = record["url"]
            
            results.append(result)
    
    logger.info(f"Fallback search for '{query}' returned {len(results)} results")
    return {"results": results}

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
