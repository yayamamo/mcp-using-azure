#!/usr/bin/env python3
"""
Azure MCP Server のテストクライアント
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_search(session: ClientSession, query: str):
    """search ツールのテスト"""
    print(f"\n{'='*60}")
    print(f"Testing search with query: '{query}'")
    print('='*60)
    
    try:
        result = await session.call_tool("search", arguments={"query": query})
        print("\nSearch Results:")
        print(result)
        return result
    except Exception as e:
        print(f"Error during search: {e}")
        return None


async def test_fetch(session: ClientSession, doc_id: str):
    """fetch ツールのテスト"""
    print(f"\n{'='*60}")
    print(f"Testing fetch with ID: '{doc_id}'")
    print('='*60)
    
    try:
        result = await session.call_tool("fetch", arguments={"id": doc_id})
        print("\nFetch Result:")
        print(result)
        return result
    except Exception as e:
        print(f"Error during fetch: {e}")
        return None


async def test_hybrid_search(session: ClientSession, query: str):
    """hybrid_search ツールのテスト"""
    print(f"\n{'='*60}")
    print(f"Testing hybrid search with query: '{query}'")
    print('='*60)
    
    try:
        result = await session.call_tool("hybrid_search", arguments={"query": query})
        print("\nHybrid Search Results:")
        print(result)
        return result
    except Exception as e:
        print(f"Error during hybrid search: {e}")
        return None


async def main():
    """メインテスト関数"""
    
    # MCPサーバーへの接続パラメータ
    # Note: stdio方式ではなくSSEを使用している場合は別の接続方法が必要
    server_params = StdioServerParameters(
        command="python",
        args=["main_azure.py"],
        env=None
    )
    
    print("Connecting to MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # サーバーの初期化
            await session.initialize()
            
            print("\n✓ Connected to MCP server")
            print("\nAvailable tools:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:100]}...")
            
            # テスト1: search ツール
            await test_search(session, "machine learning")
            
            # テスト2: fetch ツール
            await test_fetch(session, "doc_001")
            
            # テスト3: hybrid_search ツール
            await test_hybrid_search(session, "Python development")
            
            print("\n" + "="*60)
            print("All tests completed!")
            print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
