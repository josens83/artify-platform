"""
ChromaDB Vector Database Client for Content Backend
Handles semantic search and similar content recommendations
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class VectorDBClient:
    """ChromaDB client for semantic content search"""

    COLLECTION_TEXTS = "generated_texts"
    COLLECTION_IMAGES = "generated_images"
    COLLECTION_BRAND_GUIDELINES = "brand_guidelines"
    COLLECTION_PROMPT_CACHE = "prompt_cache"

    def __init__(self, persist_dir: str = "./chroma_data"):
        """Initialize ChromaDB client"""
        try:
            # ChromaDB 클라이언트 초기화
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # OpenAI 클라이언트 초기화
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OpenAI API key not found. Embeddings will fail.")
                self.openai_client = None
            else:
                self.openai_client = OpenAI(api_key=openai_api_key)

            # 컬렉션 초기화
            self.text_collection = self.client.get_or_create_collection(
                name=self.COLLECTION_TEXTS,
                metadata={"description": "AI generated text content"}
            )

            self.image_collection = self.client.get_or_create_collection(
                name=self.COLLECTION_IMAGES,
                metadata={"description": "AI generated image metadata"}
            )

            self.brand_guidelines_collection = self.client.get_or_create_collection(
                name=self.COLLECTION_BRAND_GUIDELINES,
                metadata={"description": "Brand voice and guidelines for RAG"}
            )

            self.prompt_cache_collection = self.client.get_or_create_collection(
                name=self.COLLECTION_PROMPT_CACHE,
                metadata={"description": "Semantic prompt cache for cost savings"}
            )

            logger.info("✅ ChromaDB client initialized successfully (4 collections)")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            raise

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-ada-002"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def add_text_content(
        self,
        content_id: int,
        text: str,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add generated text content to vector database

        Args:
            content_id: Unique content ID
            text: Generated text content
            prompt: Original prompt
            model: Model used for generation
            metadata: Additional metadata (user_id, segment_id, etc.)

        Returns:
            True if successful
        """
        try:
            # 임베딩 생성
            embedding = self._get_embedding(text)

            # 메타데이터 구성
            doc_metadata = {
                "content_id": content_id,
                "prompt": prompt[:500],  # 프롬프트 길이 제한
                "model": model,
                "created_at": datetime.utcnow().isoformat(),
                "content_length": len(text),
                **(metadata or {})
            }

            # ChromaDB에 추가
            self.text_collection.add(
                ids=[f"text_{content_id}"],
                embeddings=[embedding],
                documents=[text],
                metadatas=[doc_metadata]
            )

            logger.info(f"✅ Added text content {content_id} to vector DB")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add text content {content_id}: {e}")
            return False

    def add_image_metadata(
        self,
        content_id: int,
        prompt: str,
        image_url: str,
        model: str = "dall-e-3",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add generated image metadata to vector database

        Args:
            content_id: Unique content ID
            prompt: Image generation prompt
            image_url: Generated image URL
            model: Model used for generation
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # 프롬프트 임베딩 생성
            embedding = self._get_embedding(prompt)

            # 메타데이터 구성
            doc_metadata = {
                "content_id": content_id,
                "image_url": image_url,
                "model": model,
                "created_at": datetime.utcnow().isoformat(),
                "prompt_length": len(prompt),
                **(metadata or {})
            }

            # ChromaDB에 추가
            self.image_collection.add(
                ids=[f"image_{content_id}"],
                embeddings=[embedding],
                documents=[prompt],  # 이미지는 프롬프트를 문서로 저장
                metadatas=[doc_metadata]
            )

            logger.info(f"✅ Added image metadata {content_id} to vector DB")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add image metadata {content_id}: {e}")
            return False

    def search_similar_texts(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar text content

        Args:
            query: Search query
            n_results: Number of results to return
            where: Metadata filters (e.g., {"model": "gpt-3.5-turbo"})

        Returns:
            List of similar content with metadata
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._get_embedding(query)

            # 유사도 검색
            results = self.text_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # 결과 포맷팅
            similar_contents = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    similar_contents.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - results['distances'][0][i],  # 코사인 유사도
                        "distance": results['distances'][0][i]
                    })

            logger.info(f"✅ Found {len(similar_contents)} similar texts")
            return similar_contents

        except Exception as e:
            logger.error(f"❌ Failed to search similar texts: {e}")
            return []

    def search_similar_images(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar image prompts

        Args:
            query: Search query
            n_results: Number of results to return
            where: Metadata filters

        Returns:
            List of similar images with metadata
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._get_embedding(query)

            # 유사도 검색
            results = self.image_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            # 결과 포맷팅
            similar_images = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    similar_images.append({
                        "id": results['ids'][0][i],
                        "prompt": results['documents'][0][i],
                        "image_url": results['metadatas'][0][i].get('image_url'),
                        "metadata": results['metadatas'][0][i],
                        "similarity": 1 - results['distances'][0][i],
                        "distance": results['distances'][0][i]
                    })

            logger.info(f"✅ Found {len(similar_images)} similar images")
            return similar_images

        except Exception as e:
            logger.error(f"❌ Failed to search similar images: {e}")
            return []

    def update_content_performance(
        self,
        content_id: int,
        content_type: str,
        performance_score: float,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Update content performance metrics in Vector DB

        Args:
            content_id: Content ID
            content_type: 'text' or 'image'
            performance_score: Calculated performance score (0-1)
            metrics: Performance metrics dict (impressions, clicks, conversions, etc.)

        Returns:
            True if successful
        """
        try:
            collection = self.text_collection if content_type == "text" else self.image_collection
            doc_id = f"{content_type}_{content_id}"

            # 기존 메타데이터 가져오기
            existing = collection.get(ids=[doc_id])

            if not existing['ids']:
                logger.warning(f"Content {doc_id} not found in Vector DB")
                return False

            # 메타데이터 업데이트
            updated_metadata = existing['metadatas'][0]
            updated_metadata.update({
                "performance_score": performance_score,
                "impressions": metrics.get("impressions", 0),
                "clicks": metrics.get("clicks", 0),
                "conversions": metrics.get("conversions", 0),
                "ctr": metrics.get("ctr", 0.0),
                "cvr": metrics.get("cvr", 0.0),
                "last_updated": datetime.utcnow().isoformat()
            })

            # Vector DB 업데이트
            collection.update(
                ids=[doc_id],
                metadatas=[updated_metadata]
            )

            logger.info(f"✅ Updated performance for {doc_id}: score={performance_score:.4f}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update performance for {content_type}_{content_id}: {e}")
            return False

    def search_high_performing_texts(
        self,
        query: str,
        min_score: float = 0.05,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for high-performing similar text content

        Args:
            query: Search query
            min_score: Minimum performance score threshold
            n_results: Number of results

        Returns:
            List of high-performing similar content
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._get_embedding(query)

            # 고성과 필터 적용하여 검색
            results = self.text_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 3,  # 필터링 위해 더 많이 가져옴
                include=["documents", "metadatas", "distances"]
            )

            # 성과 점수로 필터링
            filtered_results = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    metadata = results['metadatas'][0][i]
                    performance_score = metadata.get('performance_score', 0)

                    if performance_score >= min_score:
                        filtered_results.append({
                            "id": results['ids'][0][i],
                            "content": results['documents'][0][i],
                            "metadata": metadata,
                            "similarity": 1 - results['distances'][0][i],
                            "performance_score": performance_score,
                            "ctr": metadata.get('ctr', 0),
                            "cvr": metadata.get('cvr', 0)
                        })

            # 성과 점수로 정렬 및 제한
            filtered_results.sort(key=lambda x: x['performance_score'], reverse=True)
            filtered_results = filtered_results[:n_results]

            logger.info(f"✅ Found {len(filtered_results)} high-performing texts (min_score={min_score})")
            return filtered_results

        except Exception as e:
            logger.error(f"❌ Failed to search high-performing texts: {e}")
            return []

    def add_brand_guideline(
        self,
        brand_id: int,
        guideline_text: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add brand guideline to Vector DB

        Args:
            brand_id: Brand identifier
            guideline_text: Guideline content
            category: Category (tone, style, values, etc.)
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            # 임베딩 생성
            embedding = self._get_embedding(guideline_text)

            # 메타데이터 구성
            doc_metadata = {
                "brand_id": brand_id,
                "category": category,
                "created_at": datetime.utcnow().isoformat(),
                "text_length": len(guideline_text),
                **(metadata or {})
            }

            # ChromaDB에 추가
            doc_id = f"brand_{brand_id}_{category}_{datetime.utcnow().timestamp()}"
            self.brand_guidelines_collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[guideline_text],
                metadatas=[doc_metadata]
            )

            logger.info(f"✅ Added brand guideline for brand {brand_id}, category: {category}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add brand guideline: {e}")
            return False

    def get_brand_context(
        self,
        brand_id: int,
        query: str,
        n_results: int = 3
    ) -> str:
        """
        Retrieve brand guidelines as context for RAG

        Args:
            brand_id: Brand identifier
            query: User query to match relevant guidelines
            n_results: Number of guidelines to retrieve

        Returns:
            Formatted context string
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._get_embedding(query)

            # 브랜드 가이드라인 검색
            results = self.brand_guidelines_collection.query(
                query_embeddings=[query_embedding],
                where={"brand_id": brand_id},
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )

            if not results['ids'][0]:
                logger.warning(f"No brand guidelines found for brand {brand_id}")
                return ""

            # 컨텍스트 포맷팅
            context_parts = []
            for i in range(len(results['ids'][0])):
                category = results['metadatas'][0][i].get('category', 'general')
                document = results['documents'][0][i]
                similarity = 1 - results['distances'][0][i]

                context_parts.append(f"[{category.upper()}] (관련도: {similarity:.2f})\n{document}")

            context = "\n\n".join(context_parts)
            logger.info(f"✅ Retrieved {len(results['ids'][0])} guidelines for brand {brand_id}")

            return context

        except Exception as e:
            logger.error(f"❌ Failed to get brand context: {e}")
            return ""

    def search_brand_guidelines(
        self,
        brand_id: int,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search brand guidelines by brand_id and optional category

        Args:
            brand_id: Brand identifier
            category: Optional category filter
            limit: Maximum results

        Returns:
            List of guidelines
        """
        try:
            where = {"brand_id": brand_id}
            if category:
                where["category"] = category

            results = self.brand_guidelines_collection.get(
                where=where,
                limit=limit,
                include=["documents", "metadatas"]
            )

            guidelines = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    guidelines.append({
                        "id": results['ids'][i],
                        "text": results['documents'][i],
                        "metadata": results['metadatas'][i]
                    })

            logger.info(f"✅ Found {len(guidelines)} guidelines for brand {brand_id}")
            return guidelines

        except Exception as e:
            logger.error(f"❌ Failed to search brand guidelines: {e}")
            return []

    def add_prompt_cache(
        self,
        prompt: str,
        result: str,
        model: str,
        job_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a prompt and its result to cache

        Args:
            prompt: The original prompt
            result: The generated result
            model: Model used (e.g., 'gpt-3.5-turbo', 'dall-e-3')
            job_type: 'text' or 'image'
            metadata: Additional metadata

        Returns:
            Document ID
        """
        try:
            timestamp = datetime.now().isoformat()
            doc_id = f"cache_{job_type}_{hash(prompt)}_{timestamp}"

            # Generate embedding from prompt
            embedding = self._get_embedding(prompt)

            # Prepare metadata (store result in metadata for quick retrieval)
            cache_metadata = {
                "job_type": job_type,
                "model": model,
                "prompt_length": len(prompt),
                "result_length": len(result),
                "result": result,  # Store the actual result for cache hits
                "cached_at": timestamp,
                "hit_count": 0  # Track how many times this cache is used
            }

            if metadata:
                cache_metadata.update(metadata)

            # Add to cache collection
            self.prompt_cache_collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[prompt],
                metadatas=[cache_metadata]
            )

            logger.info(f"✅ Added prompt to cache: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"❌ Failed to add prompt cache: {e}")
            raise

    def search_prompt_cache(
        self,
        query: str,
        job_type: str = "text",
        model: Optional[str] = None,
        similarity_threshold: float = 0.95
    ) -> Optional[Dict[str, Any]]:
        """
        Search for similar cached prompts

        Args:
            query: The prompt to search for
            job_type: 'text' or 'image'
            model: Filter by model (optional)
            similarity_threshold: Minimum similarity (0-1, default: 0.95 = 95%)

        Returns:
            Cached result if found with similarity >= threshold, None otherwise
        """
        try:
            # Generate embedding from query
            query_embedding = self._get_embedding(query)

            # Build where clause
            where = {"job_type": job_type}
            if model:
                where["model"] = model

            # Search cache
            results = self.prompt_cache_collection.query(
                query_embeddings=[query_embedding],
                n_results=1,
                where=where
            )

            if not results["ids"] or len(results["ids"][0]) == 0:
                logger.info(f"❌ Cache miss: No similar prompts found")
                return None

            # Check similarity (ChromaDB returns distance, need to convert to similarity)
            # Distance 0 = perfect match, distance 1 = orthogonal
            # Similarity = 1 - (distance / 2)  # Cosine similarity conversion
            distance = results["distances"][0][0]
            similarity = 1 - (distance / 2)

            logger.info(f"🔍 Cache search: similarity={similarity:.4f}, threshold={similarity_threshold}")

            if similarity < similarity_threshold:
                logger.info(f"❌ Cache miss: Similarity {similarity:.4f} below threshold {similarity_threshold}")
                return None

            # Cache hit!
            doc_id = results["ids"][0][0]
            metadata = results["metadatas"][0][0]
            cached_prompt = results["documents"][0][0]

            # Increment hit count
            try:
                hit_count = metadata.get("hit_count", 0) + 1
                metadata["hit_count"] = hit_count
                metadata["last_hit_at"] = datetime.now().isoformat()

                self.prompt_cache_collection.update(
                    ids=[doc_id],
                    metadatas=[metadata]
                )
            except Exception as e:
                logger.warning(f"⚠️  Failed to update hit count: {e}")

            logger.info(f"✅ Cache HIT: {doc_id} (similarity: {similarity:.4f})")

            return {
                "cache_id": doc_id,
                "cached_prompt": cached_prompt,
                "cached_result": metadata.get("result"),  # Retrieve cached result
                "similarity": round(similarity, 4),
                "model": metadata.get("model"),
                "cached_at": metadata.get("cached_at"),
                "hit_count": hit_count,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"❌ Failed to search prompt cache: {e}")
            return None

    def get_cached_result(self, cache_id: str) -> Optional[str]:
        """
        Get the cached result from a cache_id

        Note: This requires storing the result somewhere. Options:
        1. Store in metadata (limited size)
        2. Store in a separate document field
        3. Link to PostgreSQL via cache_id

        For now, we'll return None and let the caller handle it via DB lookup.
        """
        # TODO: Implement result retrieval if storing results directly in Vector DB
        logger.warning(f"⚠️  get_cached_result not implemented. Use DB lookup with cache_id: {cache_id}")
        return None

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about collections"""
        try:
            text_count = self.text_collection.count()
            image_count = self.image_collection.count()
            brand_count = self.brand_guidelines_collection.count()
            cache_count = self.prompt_cache_collection.count()

            return {
                "texts": {
                    "count": text_count,
                    "collection": self.COLLECTION_TEXTS
                },
                "images": {
                    "count": image_count,
                    "collection": self.COLLECTION_IMAGES
                },
                "brand_guidelines": {
                    "count": brand_count,
                    "collection": self.COLLECTION_BRAND_GUIDELINES
                },
                "prompt_cache": {
                    "count": cache_count,
                    "collection": self.COLLECTION_PROMPT_CACHE
                },
                "total": text_count + image_count + brand_count + cache_count
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}


# 전역 클라이언트 인스턴스 (싱글톤 패턴)
_vector_client: Optional[VectorDBClient] = None


def get_vector_client() -> VectorDBClient:
    """Get or create VectorDB client instance"""
    global _vector_client
    if _vector_client is None:
        _vector_client = VectorDBClient()
    return _vector_client
