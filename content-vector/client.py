from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import logging
from config import settings

logger = logging.getLogger(__name__)

class VectorDBClient:
    """Qdrant Vector Database Client for Content Management"""

    def __init__(self):
        """Initialize Qdrant client"""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=settings.QDRANT_TIMEOUT
        )
        self.collection_name = settings.COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure collection exists, create if not"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

    def upsert_content(
        self,
        content_id: int,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Insert or update content embedding

        Args:
            content_id: Unique content identifier
            embedding: Content embedding vector
            metadata: Additional metadata (title, type, keywords, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            point = PointStruct(
                id=content_id,
                vector=embedding,
                payload=metadata
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Upserted content: {content_id}")
            return True
        except Exception as e:
            logger.error(f"Error upserting content {content_id}: {e}")
            return False

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional metadata filters

        Returns:
            List of similar content with scores
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=filters
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "metadata": result.payload
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching similar content: {e}")
            return []

    def delete_content(self, content_id: int) -> bool:
        """
        Delete content from vector database

        Args:
            content_id: Content identifier to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[content_id]
            )
            logger.info(f"Deleted content: {content_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting content {content_id}: {e}")
            return False

    def get_content(self, content_id: int) -> Optional[Dict[str, Any]]:
        """
        Get content by ID

        Args:
            content_id: Content identifier

        Returns:
            Content data or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[content_id]
            )

            if result:
                point = result[0]
                return {
                    "id": point.id,
                    "vector": point.vector,
                    "metadata": point.payload
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving content {content_id}: {e}")
            return None

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def batch_upsert(
        self,
        contents: List[Dict[str, Any]]
    ) -> bool:
        """
        Batch insert/update contents

        Args:
            contents: List of content dicts with id, embedding, and metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            points = [
                PointStruct(
                    id=content["id"],
                    vector=content["embedding"],
                    payload=content["metadata"]
                )
                for content in contents
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Batch upserted {len(contents)} contents")
            return True
        except Exception as e:
            logger.error(f"Error batch upserting: {e}")
            return False

# Singleton instance
_vector_client = None

def get_vector_client() -> VectorDBClient:
    """Get or create vector database client instance"""
    global _vector_client
    if _vector_client is None:
        _vector_client = VectorDBClient()
    return _vector_client
