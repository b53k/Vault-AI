import httpx
from typing import Dict, Any
import os

class RAGTool:
    def __init__(self):
        self.vectorstore_url = os.getenv(
            "VECTORSTORE_SERVICE_URL",
            "http://localhost:8001"    # Default port for vectorstore-service
        )

    async def search_policy(self, query: str) -> Dict[str, Any]:
        """
        Search policy documents using RAG

        Args:
            query: User query about bank policies/fees etc.

        Returns:
            Dictionary with search results
        """

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.vectorstore_url}/search/",
                json = {
                    "query": query,
                    "similarity_threshold": 0.7,
                    "max_results": 3
                }
            )

            response.raise_for_status()
            return response.json()

    
    async def get_policy_context(self, query: str) -> str:
        """
        Get formatted context for RAG prompt

        Args:
            query: User query

        Returns:
            Formateed context string
        """

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.vectorstore_url}/search/rag-context",
                json = {
                    "query": query,
                    "similarity_threshold": 0.7,
                    "max_results": 3
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("context", "No relevant information found.")


# Tool instance for agent use
rag_tool = RAGTool()