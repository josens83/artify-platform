"""
Redis Cache Layer for Content Backend
Provides caching utilities for static data
"""
import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
import redis
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# TTL 설정 (초 단위)
TTL_TEMPLATES = 86400  # 24시간 (거의 변하지 않음)
TTL_SEGMENTS = 3600    # 1시간 (가끔 업데이트)
TTL_BRAND_GUIDELINES = 3600  # 1시간
TTL_CAMPAIGN_SETTINGS = 600  # 10분 (자주 변경 가능)
TTL_VECTOR_STATS = 300  # 5분


class RedisCache:
    """Redis 캐시 클라이언트"""

    def __init__(self):
        """Redis 클라이언트 초기화"""
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # 연결 테스트
            self.client.ping()
            logger.info(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
            self.enabled = True
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"⚠️  Redis connection failed: {e}. Cache disabled.")
            self.enabled = False
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache GET error for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 값 저장"""
        if not self.enabled:
            return False

        try:
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        if not self.enabled:
            return False

        try:
            deleted = self.client.delete(key)
            if deleted:
                logger.debug(f"Cache DELETE: {key}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Cache DELETE error for {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """패턴에 매칭되는 모든 키 삭제"""
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cache DELETE pattern: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache DELETE pattern error for {pattern}: {e}")
            return 0

    def flush_all(self) -> bool:
        """모든 캐시 삭제 (주의: 전체 DB 삭제)"""
        if not self.enabled:
            return False

        try:
            self.client.flushdb()
            logger.warning("⚠️  Cache FLUSHED: All keys deleted")
            return True
        except Exception as e:
            logger.error(f"Cache FLUSH error: {e}")
            return False

    def get_stats(self) -> dict:
        """캐시 통계"""
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.client.info("stats")
            return {
                "enabled": True,
                "host": f"{REDIS_HOST}:{REDIS_PORT}",
                "total_keys": self.client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100,
                    2
                )
            }
        except Exception as e:
            logger.error(f"Cache STATS error: {e}")
            return {"enabled": True, "error": str(e)}


# 전역 캐시 인스턴스 (싱글톤 패턴)
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get or create cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


# 데코레이터: 함수 결과 캐싱
def cached(key_prefix: str, ttl: int = 3600):
    """
    함수 결과를 캐싱하는 데코레이터

    Usage:
        @cached(key_prefix="segments", ttl=3600)
        async def get_all_segments(db: Session):
            return db.query(Segment).all()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}"

            # 캐시 조회
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 함수 실행
            result = await func(*args, **kwargs)

            # 캐시 저장
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


# 캐시 키 생성 헬퍼
def make_cache_key(*parts) -> str:
    """캐시 키 생성 헬퍼"""
    return ":".join(str(p) for p in parts)
