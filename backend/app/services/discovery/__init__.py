"""Discovery Pipeline services — Initial Discovery Layer (Teil B–D).

Source → Raw Items → Entities → Relations → Candidates → Keywords → Validation
"""

from app.services.discovery.source_registry import (
    ensure_default_discovery_sources,
    get_active_discovery_sources,
    get_discovery_source_by_type,
    import_seed_csv_to_raw_items,
    list_discovery_sources,
    SEED_UNIVERSE_DIR,
    SEED_UNIVERSE_MANIFEST,
)
from app.services.discovery.entity_normalizer import (
    normalize_german_text,
    normalize_entity_name,
)
from app.services.discovery.entity_extractor import (
    EntityExtractionResult,
    extract_entities_from_raw_items,
)
from app.services.discovery.relation_builder import (
    RelationBuilderResult,
    build_entity_relations,
)
from app.services.discovery.topic_graph import (
    TopicGraphQuery,
    get_entity_graph_overview,
    get_graph_neighbors,
    get_entities_by_type,
)
from app.services.discovery.constraint_engine import (
    ConstraintCheckResult,
    constraint_engine,
    CONSTRAINT_BLOCK,
    CONSTRAINT_FLAG_RISK,
    CONSTRAINT_DOWNGRADE,
    CONSTRAINT_ALLOW,
)
from app.services.discovery.template_engine import (
    DEFAULT_TEMPLATES,
    TemplateEngine,
    template_engine,
)
from app.services.discovery.niche_candidate_composer import (
    ComposeBatch,
    compose_niche_candidates,
)
from app.services.discovery.fast_validator import (
    FastValidationResult,
    validate_candidates_fast,
)
from app.services.discovery.candidate_promoter import (
    PromoteBatch,
    promote_candidates_to_seeds,
)

__all__ = [
    "build_entity_relations",
    "compose_niche_candidates",
    "ComposeBatch",
    "CONSTRAINT_ALLOW",
    "CONSTRAINT_BLOCK",
    "CONSTRAINT_DOWNGRADE",
    "CONSTRAINT_FLAG_RISK",
    "ConstraintCheckResult",
    "constraint_engine",
    "DEFAULT_TEMPLATES",
    "ensure_default_discovery_sources",
    "EntityExtractionResult",
    "extract_entities_from_raw_items",
    "FastValidationResult",
    "get_active_discovery_sources",
    "get_discovery_source_by_type",
    "get_entities_by_type",
    "get_entity_graph_overview",
    "get_graph_neighbors",
    "import_seed_csv_to_raw_items",
    "list_discovery_sources",
    "normalize_entity_name",
    "normalize_german_text",
    "promote_candidates_to_seeds",
    "PromoteBatch",
    "RelationBuilderResult",
    "SEED_UNIVERSE_DIR",
    "SEED_UNIVERSE_MANIFEST",
    "TemplateEngine",
    "template_engine",
    "TopicGraphQuery",
    "validate_candidates_fast",
]
