from __future__ import annotations

from app.db import base  # noqa: F401
from app.db.session import SessionLocal
from app.models.book import Book
from app.models.keyword import Keyword
from app.models.niche import NicheCluster
from app.models.report import Report
from app.models.review import Review, ReviewCluster
from app.services.text_utils import normalize_text


def main() -> None:
    db = SessionLocal()
    try:
        updated = 0
        for row in db.query(Keyword).all():
            updated += _repair_fields(row, ["keyword", "notes"])
        for row in db.query(Book).all():
            updated += _repair_fields(
                row,
                ["title", "subtitle", "author", "publisher", "formats", "description"],
            )
        for row in db.query(NicheCluster).all():
            updated += _repair_fields(row, ["name", "description", "main_keyword"])
        for row in db.query(Review).all():
            updated += _repair_fields(row, ["title", "body"])
        for row in db.query(ReviewCluster).all():
            updated += _repair_fields(
                row,
                ["cluster_name", "summary", "example_snippets", "suggested_improvements"],
            )
        for row in db.query(Report).all():
            updated += _repair_fields(row, ["title", "markdown_content"])

        db.commit()
        print(f"Updated {updated} text field(s).")
    finally:
        db.close()


def _repair_fields(row: object, field_names: list[str]) -> int:
    updated = 0
    for field_name in field_names:
        current_value = getattr(row, field_name, None)
        if not isinstance(current_value, str):
            continue
        repaired_value = normalize_text(current_value)
        if repaired_value != current_value:
            setattr(row, field_name, repaired_value)
            updated += 1
    return updated


if __name__ == "__main__":
    main()
