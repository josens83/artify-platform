from supabase import create_client, Client
from utils.config import settings
import logging

logger = logging.getLogger(__name__)

# Supabase 클라이언트
supabase: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global supabase
    if supabase is None:
        supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client initialized")
    return supabase

def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )

# Dependency for FastAPI routes
async def get_db() -> Client:
    """FastAPI dependency to get Supabase client"""
    return get_supabase_client()
