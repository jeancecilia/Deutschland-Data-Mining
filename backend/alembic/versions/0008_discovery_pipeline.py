"""add initial discovery pipeline tables

Creates:
  discovery_sources, raw_discovery_items, discovery_entities,
  discovery_entity_aliases, discovery_entity_relations,
  niche_candidates, niche_candidate_keywords

Extends:
  keywords table with source_niche_candidate_id + discovery_origin_type
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0008_discovery_pipeline"
down_revision = "0007_ai_semantic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── discovery_sources ──────────────────────────────────────────────
    op.create_table(
        "discovery_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("country", sa.String(length=10), nullable=False, server_default="DE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rate_limit_config", JSONB(), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discovery_sources_source_type", "discovery_sources", ["source_type"])

    # ── raw_discovery_items ────────────────────────────────────────────
    op.create_table(
        "raw_discovery_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("discovery_source_id", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("raw_url", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("country", sa.String(length=10), nullable=False, server_default="DE"),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_discovery_items_source_id", "raw_discovery_items", ["discovery_source_id"])
    op.create_index("ix_raw_discovery_items_status", "raw_discovery_items", ["status"])
    op.create_foreign_key("fk_raw_items_source", "raw_discovery_items", "discovery_sources", ["discovery_source_id"], ["id"])

    # ── discovery_entities ─────────────────────────────────────────────
    op.create_table(
        "discovery_entities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("country", sa.String(length=10), nullable=False, server_default="DE"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name", "entity_type", "language", name="uq_de_normalized"),
    )
    op.create_index("ix_de_normalized_name", "discovery_entities", ["normalized_name"])
    op.create_index("ix_de_entity_type", "discovery_entities", ["entity_type"])

    # ── discovery_entity_aliases ───────────────────────────────────────
    op.create_table(
        "discovery_entity_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_id", "alias", name="uq_de_alias"),
    )
    op.create_index("ix_de_alias_entity_id", "discovery_entity_aliases", ["entity_id"])
    op.create_foreign_key("fk_de_alias_entity", "discovery_entity_aliases", "discovery_entities", ["entity_id"], ["id"])

    # ── discovery_entity_relations ─────────────────────────────────────
    op.create_table(
        "discovery_entity_relations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("evidence_source", sa.Text(), nullable=True),
        sa.Column("metadata_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_entity_id", "target_entity_id", "relation_type", name="uq_de_relation"),
    )
    op.create_index("ix_de_rel_source", "discovery_entity_relations", ["source_entity_id"])
    op.create_index("ix_de_rel_target", "discovery_entity_relations", ["target_entity_id"])
    op.create_index("ix_de_rel_type", "discovery_entity_relations", ["relation_type"])
    op.create_foreign_key("fk_de_rel_source", "discovery_entity_relations", "discovery_entities", ["source_entity_id"], ["id"])
    op.create_foreign_key("fk_de_rel_target", "discovery_entity_relations", "discovery_entities", ["target_entity_id"], ["id"])

    # ── niche_candidates ───────────────────────────────────────────────
    op.create_table(
        "niche_candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("main_topic_entity_id", sa.Integer(), nullable=True),
        sa.Column("audience_entity_id", sa.Integer(), nullable=True),
        sa.Column("problem_entity_id", sa.Integer(), nullable=True),
        sa.Column("format_entity_id", sa.Integer(), nullable=True),
        sa.Column("book_class_guess", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("marketplace", sa.String(length=16), nullable=False, server_default="amazon.de"),
        sa.Column("generation_template", sa.Text(), nullable=True),
        sa.Column("source_entities", JSONB(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("risk_level", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("fast_validation_score", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("promotion_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_index("ix_niche_candidates_normalized", "niche_candidates", ["normalized_name"])
    op.create_index("ix_niche_candidates_status", "niche_candidates", ["status"])
    op.create_index("ix_nc_main_topic", "niche_candidates", ["main_topic_entity_id"])
    op.create_index("ix_nc_audience", "niche_candidates", ["audience_entity_id"])
    op.create_index("ix_nc_problem", "niche_candidates", ["problem_entity_id"])
    op.create_index("ix_nc_format", "niche_candidates", ["format_entity_id"])
    op.create_foreign_key("fk_nc_main_topic", "niche_candidates", "discovery_entities", ["main_topic_entity_id"], ["id"])
    op.create_foreign_key("fk_nc_audience", "niche_candidates", "discovery_entities", ["audience_entity_id"], ["id"])
    op.create_foreign_key("fk_nc_problem", "niche_candidates", "discovery_entities", ["problem_entity_id"], ["id"])
    op.create_foreign_key("fk_nc_format", "niche_candidates", "discovery_entities", ["format_entity_id"], ["id"])

    # ── niche_candidate_keywords ───────────────────────────────────────
    op.create_table(
        "niche_candidate_keywords",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("niche_candidate_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("keyword_type", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nck_candidate_id", "niche_candidate_keywords", ["niche_candidate_id"])
    op.create_foreign_key("fk_nck_candidate", "niche_candidate_keywords", "niche_candidates", ["niche_candidate_id"], ["id"])

    # ── extend keywords table ──────────────────────────────────────────
    op.add_column("keywords", sa.Column("source_niche_candidate_id", sa.Integer(), nullable=True))
    op.add_column("keywords", sa.Column("discovery_origin_type", sa.String(length=50), nullable=True))
    op.create_index("ix_keywords_source_niche_candidate_id", "keywords", ["source_niche_candidate_id"])
    op.create_foreign_key("fk_keywords_niche_candidate", "keywords", "niche_candidates", ["source_niche_candidate_id"], ["id"])


def downgrade() -> None:
    # keywords extension
    op.drop_constraint("fk_keywords_niche_candidate", "keywords", type_="foreignkey")
    op.drop_index("ix_keywords_source_niche_candidate_id", table_name="keywords")
    op.drop_column("keywords", "discovery_origin_type")
    op.drop_column("keywords", "source_niche_candidate_id")

    # niche_candidate_keywords
    op.drop_index("ix_nck_candidate_id", table_name="niche_candidate_keywords")
    op.drop_table("niche_candidate_keywords")

    # niche_candidates
    op.drop_index("ix_nc_format", table_name="niche_candidates")
    op.drop_index("ix_nc_problem", table_name="niche_candidates")
    op.drop_index("ix_nc_audience", table_name="niche_candidates")
    op.drop_index("ix_nc_main_topic", table_name="niche_candidates")
    op.drop_index("ix_niche_candidates_status", table_name="niche_candidates")
    op.drop_index("ix_niche_candidates_normalized", table_name="niche_candidates")
    op.drop_table("niche_candidates")

    # discovery_entity_relations
    op.drop_index("ix_de_rel_type", table_name="discovery_entity_relations")
    op.drop_index("ix_de_rel_target", table_name="discovery_entity_relations")
    op.drop_index("ix_de_rel_source", table_name="discovery_entity_relations")
    op.drop_table("discovery_entity_relations")

    # discovery_entity_aliases
    op.drop_index("ix_de_alias_entity_id", table_name="discovery_entity_aliases")
    op.drop_table("discovery_entity_aliases")

    # discovery_entities
    op.drop_index("ix_de_entity_type", table_name="discovery_entities")
    op.drop_index("ix_de_normalized_name", table_name="discovery_entities")
    op.drop_table("discovery_entities")

    # raw_discovery_items
    op.drop_index("ix_raw_discovery_items_status", table_name="raw_discovery_items")
    op.drop_index("ix_raw_discovery_items_source_id", table_name="raw_discovery_items")
    op.drop_table("raw_discovery_items")

    # discovery_sources
    op.drop_index("ix_discovery_sources_source_type", table_name="discovery_sources")
    op.drop_table("discovery_sources")
