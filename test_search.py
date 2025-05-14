import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
import asyncio

async def test_search(query):
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("INDEX_NAME")
    key = os.getenv("AZURE_SEARCH_KEY")
    
    client = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))

    async with client:
        search_results = await client.search(
            search_text=query,
            query_type="simple",
            top=5,
            select="chunk_id, chunk, title"  # Usamos los campos disponibles
        )

        async for result in search_results:
            print(f"{result['chunk_id']} - {result['title']}: {result['chunk']}")

asyncio.run(test_search("ITAM"))
