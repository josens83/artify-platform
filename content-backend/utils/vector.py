import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
import openai
from .config import settings

logger = logging.getLogger(__name__)

class VectorDB:
    """ChromaDB embedded client for vector storage"""

    # Collection names
    COLLECTION_COPY_TEXTS = "copy_texts"
    COLLECTION_IMAGES = "images"
    COLLECTION_TEMPLATES = "templates"

    def __init__(self):
        """Initialize ChromaDB in embedded mode"""
        self.client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=settings.CHROMA_PERSIST_DIR
        ))

        openai.api_key = settings.OPENAI_API_KEY

        # Initialize collections
        self.collections = {}
        self._ensure_collections()

        logger.info("ChromaDB embedded client initialized")

    def _ensure_collections(self):
        """Ensure all required collections exist"""
        for name in [self.COLLECTION_COPY_TEXTS, self.COLLECTION_IMAGES, self.COLLECTION_TEMPLATES]:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"embedding_model": settings.EMBEDDING_MODEL}
            )
            logger.info(f"Collection '{name}' ready")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            response = openai.Embedding.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def add_creative(
        self,
        creative_id: int,
        text: str,
        metadata: Dict[str, Any],
        collection_name: str = COLLECTION_COPY_TEXTS
    ) -> bool:
        """Add creative with auto-embedding"""
        try:
            collection = self.collections[collection_name]
            embedding = self._get_embedding(text)

            collection.add(
                ids=[str(creative_id)],
                embeddings=[embedding],
                metadatas=[{**metadata, "text": text}],
                documents=[text]
            )

            logger.info(f"Added creative {creative_id} to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding creative: {e}")
            return False

    def search_similar(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar creatives"""
        try:
            collection = self.collections[collection_name]
            query_embedding = self._get_embedding(query)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )

            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "distance": results['distances'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "document": results['documents'][0][i]
                    })

            return formatted_results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def delete_creative(self, creative_id: int, collection_name: str = COLLECTION_COPY_TEXTS) -> bool:
        """Delete creative from collection"""
        try:
            collection = self.collections[collection_name]
            collection.delete(ids=[str(creative_id)])
            logger.info(f"Deleted creative {creative_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting: {e}")
            return False

# Singleton instance
_vector_db = None

def get_vector_db() -> VectorDB:
    """Get or create VectorDB instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db
