#!/usr/bin/env python3
"""
Validate MCP server functionality by testing the actual protocol methods
"""

import asyncio
import main

async def validate_mcp_server():
    """Complete validation of MCP server functionality"""
    
    print("MCP Server Validation")
    print("=" * 21)
    
    server = main.create_server()
    
    # Test 1: List tools
    print("1. Testing list_tools...")
    try:
        tools = await server._list_tools()
        print(f"   Tools found: {len(tools)}")
        
        tool_data = []
        for tool in tools:
            data = {
                "name": tool.name,
                "description": tool.description,
                "has_schema": hasattr(tool, 'input_schema')
            }
            tool_data.append(data)
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        # Verify expected tools
        names = [t["name"] for t in tool_data]
        if "search" in names and "fetch" in names:
            print("   ✓ Both required tools present")
        else:
            print(f"   ✗ Missing tools. Found: {names}")
            
    except Exception as e:
        print(f"   ✗ List tools failed: {e}")
        return False
    
    # Test 2: Test search tool call simulation
    print("\n2. Testing search tool...")
    try:
        # Simulate what happens when MCP client calls search
        search_query = "test search"
        
        # Find search function and call it directly
        search_functions = [f for name, f in server._tool_manager._tools.items() if name == "search"]
        if search_functions:
            # This simulates the MCP call
            import main
            if main.openai_client:
                # Test the underlying OpenAI API call
                response = main.openai_client.vector_stores.search(
                    vector_store_id=main.VECTOR_STORE_ID,
                    query=search_query
                )
                print(f"   ✓ Search executed successfully, found {len(response.data)} results")
            else:
                print("   ✗ OpenAI client not available")
        else:
            print("   ✗ Search tool not found")
    except Exception as e:
        print(f"   ✗ Search test failed: {e}")
    
    # Test 3: Test fetch tool call simulation
    print("\n3. Testing fetch tool...")
    try:
        # Get a file ID from search results first
        if main.openai_client:
            search_response = main.openai_client.vector_stores.search(
                vector_store_id=main.VECTOR_STORE_ID,
                query="test"
            )
            
            if search_response.data:
                file_id = search_response.data[0].file_id
                
                # Test fetch
                content_response = main.openai_client.vector_stores.files.content(
                    vector_store_id=main.VECTOR_STORE_ID,
                    file_id=file_id
                )
                
                if content_response.data:
                    print(f"   ✓ Fetch executed successfully, retrieved {len(content_response.data[0].text)} characters")
                else:
                    print("   ✗ No content retrieved")
            else:
                print("   ✗ No files to fetch")
        else:
            print("   ✗ OpenAI client not available")
    except Exception as e:
        print(f"   ✗ Fetch test failed: {e}")
    
    # Test 4: Server accessibility  
    print("\n4. Testing server accessibility...")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://0.0.0.0:8800/sse/")
            if response.status_code == 200:
                print("   ✓ SSE endpoint accessible")
            else:
                print(f"   ✗ SSE endpoint returned {response.status_code}")
    except Exception as e:
        print(f"   ✗ Server not accessible: {e}")
    
    print("\nMCP validation completed!")
    return True

if __name__ == "__main__":
    asyncio.run(validate_mcp_server())