from fastapi import APIRouter

from app.api.routes import books, clusters, discovery, health, keywords, operations, reports


api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
