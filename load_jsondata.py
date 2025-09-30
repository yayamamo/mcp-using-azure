#!/usr/bin/env python3
"""
Azure OpenAI + Azure AI Search を使用したベクトルデータベース構築スクリプト
"""

import json
import os
from typing import List, Dict, Any
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

# Azure OpenAI 設定
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small"
)
AZURE_OPENAI_API_VERSION = "2024-02-01"

# Azure AI Search 設定
SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
SEARCH_INDEX_NAME = "documents-index"

# ベクトル次元数（text-embedding-3-small は 1536次元）
VECTOR_DIMENSIONS = 1536


def create_azure_openai_client() -> AzureOpenAI:
    """Azure OpenAI クライアントを初期化"""
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )


def create_search_index(index_client: SearchIndexClient) -> None:
    """Azure AI Search のインデックスを作成"""
    
    # ベクトル検索の設定
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ]
    )
    
    # インデックスフィールドの定義
    fields = [
        SearchField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True
        ),
        SearchField(
            name="title",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True
        ),
        SearchField(
            name="text",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchField(
            name="url",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        SearchField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="author",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="date",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True
        ),
        SearchField(
            name="tags",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="vector-profile"
        )
    ]
    
    # インデックスの作成
    index = SearchIndex(
        name=SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search
    )
    
    print(f"Creating index: {SEARCH_INDEX_NAME}")
    index_client.create_or_update_index(index)
    print("Index created successfully")


def get_embedding(client: AzureOpenAI, text: str) -> List[float]:
    """テキストをベクトル化"""
    response = client.embeddings.create(
        input=text,
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    return response.data[0].embedding


def load_and_index_documents(
    openai_client: AzureOpenAI,
    search_client: SearchClient,
    json_file_path: str
) -> None:
    """JSON ファイルからデータを読み込み、ベクトル化してインデックスに登録"""
    
    # JSON データの読み込み
    print(f"Loading data from {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data.get("records", [])
    print(f"Found {len(records)} records")
    
    # 各ドキュメントを処理
    documents = []
    for i, record in enumerate(records):
        print(f"Processing record {i+1}/{len(records)}: {record['id']}")
        
        # コンテンツをベクトル化
        content_text = record.get("content", "")
        embedding = get_embedding(openai_client, content_text)
        
        # Azure AI Search 用のドキュメント形式に変換
        document = {
            "id": record["id"],
            "title": record["title"],
            "text": record["text"],
            "content": content_text,
            "url": record["url"],
            "category": record["metadata"]["category"],
            "author": record["metadata"]["author"],
            "date": record["metadata"]["date"],
            "tags": record["metadata"]["tags"],
            "content_vector": embedding
        }
        documents.append(document)
    
    # バッチでアップロード
    print(f"Uploading {len(documents)} documents to search index")
    result = search_client.upload_documents(documents=documents)
    
    succeeded = sum([1 for r in result if r.succeeded])
    print(f"Successfully uploaded {succeeded}/{len(documents)} documents")


def main():
    """メイン処理"""
    
    # 環境変数のチェック
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    # クライアントの初期化
    print("Initializing Azure clients...")
    openai_client = create_azure_openai_client()
    
    search_credential = AzureKeyCredential(SEARCH_API_KEY)
    index_client = SearchIndexClient(
        endpoint=SEARCH_SERVICE_ENDPOINT,
        credential=search_credential
    )
    search_client = SearchClient(
        endpoint=SEARCH_SERVICE_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=search_credential
    )
    
    # インデックスの作成
    create_search_index(index_client)
    
    # データのロードとインデックス化
    json_file = "sample_data.json"
    load_and_index_documents(openai_client, search_client, json_file)
    
    print("\nData loading completed successfully!")
    print(f"Index name: {SEARCH_INDEX_NAME}")
    print(f"Search endpoint: {SEARCH_SERVICE_ENDPOINT}")


if __name__ == "__main__":
    main()