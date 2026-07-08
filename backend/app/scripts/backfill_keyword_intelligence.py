from app.db import base  # noqa: F401
from app.db.session import SessionLocal
from app.models.keyword import Keyword
from app.services.keyword_intelligence import infer_keyword_intelligence


def main() -> None:
    db = SessionLocal()
    try:
        keywords = list(db.query(Keyword).order_by(Keyword.id.asc()))
        updated = 0
        for keyword in keywords:
            intelligence = infer_keyword_intelligence(keyword.keyword, book_type=keyword.book_type)
            keyword.target_audience = keyword.target_audience or intelligence.target_audience
            keyword.category_hint = keyword.category_hint or intelligence.category_hint
            keyword.search_intent_family = keyword.search_intent_family or intelligence.search_intent_family
            keyword.specificity_score = intelligence.specificity_score
            keyword.intent_score = intelligence.intent_score
            keyword.audience_clarity_score = intelligence.audience_clarity_score
            keyword.format_suitability_score = intelligence.format_suitability_score
            keyword.competition_probability_score = intelligence.competition_probability_score
            keyword.production_effort_score = intelligence.production_effort_score
            keyword.risk_level = keyword.risk_level or intelligence.risk_level
            updated += 1

        db.commit()
        print(f"Updated {updated} keywords.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
