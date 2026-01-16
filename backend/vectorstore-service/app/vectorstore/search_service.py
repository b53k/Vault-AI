from typing import List, Dict, Optional
from app.config.database import db_connection
from app.vectorstore.embeddings import embeddings_service

class VectorSearchService:
    def __init__(self, similarity_threshold: float = 0.7, max_results: int = 5):
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results

    def search(
        self,
        query: str,
        similarity_threshold: Optional[float] = None,
        max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search policy documents using vector similarity search

        Args:
            query: The search query
            similarity_threshold: The similarity threshold for the search (default: 0.7)
            max_results: The maximum number of results to return (default: 5)

        Returns:
            List of dictionaries with relevent information from the policy documents
        """
        # Generate embedding for query
        query_embedding = embeddings_service.generate_embedding(query)
        embedding_str = embeddings_service.embedding_to_pgvector_string(query_embedding)

        threshold = similarity_threshold or self.similarity_threshold
        limit = int(max_results) if max_results is not None else self.max_results

        #print(f"DEBUG search: query='{query}', threshold={threshold}, limit={limit}, similarity_threshold param={similarity_threshold}")

        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, content, metadata, (embedding <=> %s::vector) AS similarity_distance
                    FROM policy_document
                    WHERE embedding <=> %s::vector < %s
                    ORDER BY similarity_distance ASC
                """, (embedding_str, embedding_str, threshold))

                results = cur.fetchall()

                print(f"DEBUG search: DB returned {len(results)} rows")

                # Format results into list of dictionaries
                formatted_results = []
                for row in results[:limit]:
                    formatted_results.append({
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'metadata': row[3],
                        'similarity_distance': row[4]
                    })

                return formatted_results
    

    def get_context_for_rag(self, query: str, max_chunks: int = 3, similarity_threshold: Optional[float] = None) -> str:
        """
        Get context for RAG pipeline

        Args:
            query: The search query
            max_chunks: The maximum number of chunks to return (default: 3)

        Returns:
            String with context for RAG pipeline
        """
      
        results = self.search(query, max_results=max_chunks, similarity_threshold=similarity_threshold)
        
        #print(f"DEBUG get_context_for_rag: found {len(results)} results")

        if not results:
            return "No relevant policy information found."

        context_parts = []
        for result in results:
            context_parts.append(
                f"**{result['title']}**\n{result['content']}\n"
            )

        return "\n---\n".join(context_parts)


vector_search_service = VectorSearchService()