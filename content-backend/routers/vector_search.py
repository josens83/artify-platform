from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from utils.vector import get_vector_db, VectorDB

router = APIRouter()

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    collection: str = "copy_texts"
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    id: str
    distance: float
    metadata: Dict[str, Any]
    document: str

@router.post("/search", response_model=dict)
async def search_vectors(request: SearchRequest):
    """Search for similar content in vector database"""
    try:
        vector_db = get_vector_db()

        # Validate collection name
        valid_collections = [
            VectorDB.COLLECTION_COPY_TEXTS,
            VectorDB.COLLECTION_IMAGES,
            VectorDB.COLLECTION_TEMPLATES
        ]

        if request.collection not in valid_collections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid collection. Must be one of: {', '.join(valid_collections)}"
            )

        # Perform search
        results = vector_db.search_similar(
            query=request.query,
            collection_name=request.collection,
            top_k=request.top_k,
            filters=request.filters
        )

        return {
            "success": True,
            "query": request.query,
            "collection": request.collection,
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections", response_model=dict)
async def get_collections_info():
    """Get information about all vector collections"""
    try:
        vector_db = get_vector_db()

        collections_info = {}
        for name in [VectorDB.COLLECTION_COPY_TEXTS, VectorDB.COLLECTION_IMAGES, VectorDB.COLLECTION_TEMPLATES]:
            collection = vector_db.collections[name]
            collections_info[name] = {
                "name": name,
                "count": collection.count(),
                "metadata": collection.metadata
            }

        return {
            "success": True,
            "collections": collections_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections/{collection_name}/info", response_model=dict)
async def get_collection_info(collection_name: str):
    """Get detailed information about a specific collection"""
    try:
        vector_db = get_vector_db()

        if collection_name not in vector_db.collections:
            raise HTTPException(status_code=404, detail="Collection not found")

        collection = vector_db.collections[collection_name]

        return {
            "success": True,
            "collection": {
                "name": collection_name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
