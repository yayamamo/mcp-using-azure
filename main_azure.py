#!/usr/bin/env python3
"""
Azure OpenAI + Azure AI Search を使用した MCP Server

Azure OpenAI API の text-embedding-3-small と Azure AI Search を使用して
ベクトル検索機能を提供します。
"""

import logging
import os
from typing import Dict, List, Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
)
AZURE_OPENAI_API_VERSION = "2024-02-01"

# Azure AI Search configuration
SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "documents-index")

# Initialize clients
openai_client = None
search_client = None

try:
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )
    
    search_credential = AzureKeyCredential(SEARCH_API_KEY)
    search_client = SearchClient(
        endpoint=SEARCH_SERVICE_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=search_credential
    )
    logger.info("Azure clients initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Azure clients: {e}")

server_instructions = """
This MCP server provides search and document retrieval capabilities 
for deep research using Azure OpenAI and Azure AI Search. 
Use the search tool to find relevant documents based on semantic 
similarity, then use the fetch tool to retrieve complete document 
content with citations.
"""


def get_embedding(text: str) -> List[float]:
    """テキストをベクトル化"""
    response = openai_client.embeddings.create(
        input=text,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    return response.data[0].embedding


def create_server():
    """Create and configure the MCP server with search and fetch tools."""

    # Initialize the FastMCP server
    mcp = FastMCP(
        name="Azure Deep Research MCP Server",
        instructions=server_instructions
    )

    @mcp.tool()
    async def search(query: str, top: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for documents using Azure AI Search with semantic vector search.
        
        This tool searches through the Azure AI Search index to find semantically 
        relevant matches using Azure OpenAI embeddings. Returns a list of search 
        results with basic information. Use the fetch tool to get complete document content.
        
        Args:
            query: Search query string. Natural language queries work best for semantic search.
            top: Maximum number of results to return (default: 5, max: 20)
        
        Returns:
            Dictionary with 'results' key containing list of matching documents.
            Each result includes id, title, text snippet, score, and optional URL.
        """
        if not query or not query.strip():
            return {"results": []}

        if not openai_client or not search_client:
            logger.error("Azure clients not initialized")
            raise ValueError("Azure OpenAI and Search clients are required")

        # Limit top parameter
        top = min(max(1, top), 20)

        logger.info(f"Searching Azure AI Search for query: '{query}' (top={top})")

        try:
            # クエリをベクトル化
            query_vector = get_embedding(query)
            
            # ベクトル検索クエリの作成
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top,
                fields="content_vector"
            )
            
            # Azure AI Search で検索実行
            results_list = search_client.search(
                search_text=None,  # 純粋なベクトル検索
                vector_queries=[vector_query],
                select=["id", "title", "text", "url", "category", "author", "date"],
                top=top
            )
            
            results = []
            for item in results_list:
                # テキストスニペットの作成
                text_content = item.get("text", "")
                text_snippet = text_content[:200] + "..." if len(
                    text_content) > 200 else text_content
                
                result = {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "text": text_snippet,
                    "url": item.get("url"),
                    "score": item.get("@search.score", 0),
                    "category": item.get("category"),
                    "author": item.get("author"),
                    "date": item.get("date")
                }
                results.append(result)
            
            logger.info(f"Azure AI Search returned {len(results)} results")
            return {"results": results}
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    @mcp.tool()
    async def fetch(id: str) -> Dict[str, Any]:
        """
        Retrieve complete document content by ID for detailed analysis and citation.
        
        This tool fetches the full document content from Azure AI Search. 
        Use this after finding relevant documents with the search tool to get 
        complete information for analysis and proper citation.
        
        Args:
            id: Document ID from the search results
            
        Returns:
            Complete document with id, title, full text content, URL, and metadata
            
        Raises:
            ValueError: If the specified ID is not found
        """
        if not id:
            raise ValueError("Document ID is required")

        if not search_client:
            logger.error("Azure Search client not initialized")
            raise ValueError("Azure Search client is required")

        logger.info(f"Fetching document from Azure AI Search: {id}")

        try:
            # ドキュメントを取得
            document = search_client.get_document(key=id)
            
            if not document:
                raise ValueError(f"Document not found: {id}")
            
            result = {
                "id": document.get("id"),
                "title": document.get("title"),
                "text": document.get("content"),  # 完全なコンテンツ
                "url": document.get("url"),
                "metadata": {
                    "category": document.get("category"),
                    "author": document.get("author"),
                    "date": document.get("date"),
                    "tags": document.get("tags")
                }
            }
            
            logger.info(f"Fetched document: {id}")
            return result
            
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            raise ValueError(f"Failed to fetch document {id}: {str(e)}")

    @mcp.tool()
    async def hybrid_search(
        query: str, 
        top: int = 5,
        use_semantic: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Hybrid search combining vector search and full-text search.
        
        This tool combines semantic vector search with traditional keyword search
        for more comprehensive results.
        
        Args:
            query: Search query string
            top: Maximum number of results to return (default: 5, max: 20)
            use_semantic: Whether to use semantic ranking (default: True)
        
        Returns:
            Dictionary with 'results' key containing list of matching documents
        """
        if not query or not query.strip():
            return {"results": []}

        if not openai_client or not search_client:
            logger.error("Azure clients not initialized")
            raise ValueError("Azure OpenAI and Search clients are required")

        top = min(max(1, top), 20)

        logger.info(f"Hybrid search for query: '{query}' (top={top})")

        try:
            # クエリをベクトル化
            query_vector = get_embedding(query)
            
            # ベクトル検索クエリの作成
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top,
                fields="content_vector"
            )
            
            # ハイブリッド検索（ベクトル + フルテキスト）
            results_list = search_client.search(
                search_text=query,  # キーワード検索も併用
                vector_queries=[vector_query],
                select=["id", "title", "text", "content", "url", "category", "author", "date"],
                top=top
            )
            
            results = []
            for item in results_list:
                text_content = item.get("text", "")
                text_snippet = text_content[:200] + "..." if len(
                    text_content) > 200 else text_content
                
                result = {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "text": text_snippet,
                    "url": item.get("url"),
                    "score": item.get("@search.score", 0),
                    "category": item.get("category"),
                    "author": item.get("author"),
                    "date": item.get("date")
                }
                results.append(result)
            
            logger.info(f"Hybrid search returned {len(results)} results")
            return {"results": results}
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            raise

    return mcp


def main():
    """Main function to start the MCP server."""
    # Verify clients are initialized
    if not openai_client or not search_client:
        logger.error("Azure clients not initialized. Please check environment variables.")
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_SEARCH_ENDPOINT",
            "AZURE_SEARCH_API_KEY"
        ]
        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        raise ValueError("Failed to initialize Azure clients")

    logger.info(f"Using Azure AI Search index: {SEARCH_INDEX_NAME}")

    # Create the MCP server
    server = create_server()

    # Configure and start the server
    logger.info("Starting MCP server on 0.0.0.0:8800")
    logger.info("Server will be accessible via SSE transport")

    try:
        # Use FastMCP's built-in run method with SSE transport
        server.run(transport="sse", host="0.0.0.0", port=8800)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()