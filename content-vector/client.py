import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
import openai
from config import settings

logger = logging.getLogger(__name__)

class ChromaDBClient:
    """ChromaDB Vector Database Client for Content Management"""

    # 컬렉션 이름 상수
    COLLECTION_COPY_TEXTS = "copy_texts"
    COLLECTION_IMAGES = "images"
    COLLECTION_TEMPLATES = "templates"

    def __init__(self):
        """Initialize ChromaDB client and collections"""
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=settings.CHROMA_PERSIST_DIR
        ))

        # OpenAI API 키 설정
        openai.api_key = settings.OPENAI_API_KEY

        # 컬렉션 초기화
        self.collections = {}
        self._ensure_collections()

        logger.info("ChromaDB client initialized successfully")

    def _ensure_collections(self):
        """Ensure all required collections exist"""
        collection_names = [
            self.COLLECTION_COPY_TEXTS,
            self.COLLECTION_IMAGES,
            self.COLLECTION_TEMPLATES
        ]

        for name in collection_names:
            try:
                # 컬렉션이 있으면 가져오고, 없으면 생성
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={
                        "description": f"Collection for {name}",
                        "embedding_model": settings.EMBEDDING_MODEL
                    }
                )
                logger.info(f"Collection '{name}' ready")
            except Exception as e:
                logger.error(f"Error ensuring collection {name}: {e}")
                raise

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = openai.Embedding.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            embedding = response['data'][0]['embedding']
            return embedding
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
        """
        Add creative to specified collection

        Args:
            creative_id: Unique creative identifier
            text: Text content to embed
            metadata: Additional metadata
            collection_name: Target collection (copy_texts, images, templates)

        Returns:
            True if successful, False otherwise
        """
        try:
            # 컬렉션 확인
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return False

            collection = self.collections[collection_name]

            # 임베딩 생성
            embedding = self._get_embedding(text)

            # 메타데이터에 텍스트 추가
            metadata_with_text = {**metadata, "text": text}

            # ChromaDB에 추가
            collection.add(
                ids=[str(creative_id)],
                embeddings=[embedding],
                metadatas=[metadata_with_text],
                documents=[text]
            )

            logger.info(f"Added creative {creative_id} to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error adding creative {creative_id}: {e}")
            return False

    def search_similar(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar creatives

        Args:
            query: Search query text
            collection_name: Collection to search in
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of similar creatives with distances and metadata
        """
        try:
            # 컬렉션 확인
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return []

            collection = self.collections[collection_name]

            # 쿼리 임베딩 생성
            query_embedding = self._get_embedding(query)

            # 검색 실행
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )

            # 결과 포맷팅
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "distance": results['distances'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "document": results['documents'][0][i]
                    })

            logger.info(f"Found {len(formatted_results)} similar creatives")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching similar creatives: {e}")
            return []

    def delete_creative(
        self,
        creative_id: int,
        collection_name: str = COLLECTION_COPY_TEXTS
    ) -> bool:
        """
        Delete creative from collection

        Args:
            creative_id: Creative identifier to delete
            collection_name: Collection to delete from

        Returns:
            True if successful, False otherwise
        """
        try:
            # 컬렉션 확인
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return False

            collection = self.collections[collection_name]

            # 삭제 실행
            collection.delete(ids=[str(creative_id)])

            logger.info(f"Deleted creative {creative_id} from {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting creative {creative_id}: {e}")
            return False

    def get_creative(
        self,
        creative_id: int,
        collection_name: str = COLLECTION_COPY_TEXTS
    ) -> Optional[Dict[str, Any]]:
        """
        Get creative by ID

        Args:
            creative_id: Creative identifier
            collection_name: Collection to search in

        Returns:
            Creative data or None if not found
        """
        try:
            # 컬렉션 확인
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return None

            collection = self.collections[collection_name]

            # 조회
            result = collection.get(ids=[str(creative_id)])

            if result['ids']:
                return {
                    "id": result['ids'][0],
                    "metadata": result['metadatas'][0],
                    "document": result['documents'][0]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting creative {creative_id}: {e}")
            return None

    def batch_add_creatives(
        self,
        creatives: List[Dict[str, Any]],
        collection_name: str = COLLECTION_COPY_TEXTS
    ) -> bool:
        """
        Batch add multiple creatives

        Args:
            creatives: List of creative dicts with id, text, and metadata
            collection_name: Target collection

        Returns:
            True if successful, False otherwise
        """
        try:
            # 컬렉션 확인
            if collection_name not in self.collections:
                logger.error(f"Collection {collection_name} not found")
                return False

            collection = self.collections[collection_name]

            ids = []
            embeddings = []
            metadatas = []
            documents = []

            for creative in creatives:
                creative_id = str(creative['id'])
                text = creative['text']
                metadata = creative.get('metadata', {})

                # 임베딩 생성
                embedding = self._get_embedding(text)

                ids.append(creative_id)
                embeddings.append(embedding)
                metadatas.append({**metadata, "text": text})
                documents.append(text)

            # 배치 추가
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )

            logger.info(f"Batch added {len(creatives)} creatives to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error batch adding creatives: {e}")
            return False

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get collection information

        Args:
            collection_name: Collection name

        Returns:
            Collection info dict
        """
        try:
            if collection_name not in self.collections:
                return {"error": f"Collection {collection_name} not found"}

            collection = self.collections[collection_name]

            return {
                "name": collection_name,
                "count": collection.count(),
                "metadata": collection.metadata
            }

        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}

    def get_all_collections_info(self) -> Dict[str, Any]:
        """Get information for all collections"""
        return {
            name: self.get_collection_info(name)
            for name in self.collections.keys()
        }

# Singleton instance
_chroma_client = None

def get_chroma_client() -> ChromaDBClient:
    """Get or create ChromaDB client instance"""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaDBClient()
    return _chroma_client
