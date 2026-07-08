from pydantic import BaseModel

from app.schemas.analysis import NicheClusterAnalysisRead
from app.schemas.book import BookDetailCollectionRead
from app.schemas.review_cluster import ReviewClusterRead
from app.schemas.search import SearchRunDetailRead


class PipelineRunRead(BaseModel):
    seed_keyword_id: int
    seed_keyword: str
    expanded_keyword_count: int
    collected_search_runs: list[SearchRunDetailRead]
    enriched_books: list[BookDetailCollectionRead]
    analyzed_review_books: dict[int, list[ReviewClusterRead]]
    cluster_analysis: NicheClusterAnalysisRead

