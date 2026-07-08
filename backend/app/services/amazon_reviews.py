from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
import re

from bs4 import BeautifulSoup

from app.services.amazon_book import build_book_detail_url
from app.services.amazon_book import GERMAN_MONTHS
from app.services.amazon_search import AMAZON_DE_BASE_URL, fetch_amazon_html
from app.services.text_utils import normalize_text


@dataclass(frozen=True)
class AmazonReviewItem:
    rating: int | None
    title: str | None
    body: str | None
    review_date: date | None
    verified_purchase: bool | None
    helpful_count: int | None
    language: str
    captured_at: datetime


def build_reviews_url(asin: str, page: int = 1) -> str:
    return (
        f"{AMAZON_DE_BASE_URL}/portal/customer-reviews/{asin}/ref=cm_cr_dp_d_show_all_top"
        f"?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
    )


def fetch_reviews(asin: str, *, page: int = 1, timeout: float = 20.0) -> list[AmazonReviewItem]:
    html = fetch_amazon_html(
        build_reviews_url(asin, page=page),
        timeout=timeout,
        referer=build_book_detail_url(asin),
    )
    reviews = parse_reviews_page(html)
    if reviews:
        return reviews
    if "/ap/signin" in html.casefold():
        fallback_html = fetch_amazon_html(build_book_detail_url(asin), timeout=timeout)
        return parse_reviews_page(fallback_html)
    return reviews


def parse_reviews_page(html: str) -> list[AmazonReviewItem]:
    soup = BeautifulSoup(html, "html.parser")
    reviews: list[AmazonReviewItem] = []

    for node in soup.select('[data-hook="review"]'):
        rating = _extract_rating(node)
        title = _extract_title(node)
        body = _extract_body(node)
        review_date = _extract_review_date(node)
        verified_purchase = _extract_verified_purchase(node)
        helpful_count = _extract_helpful_count(node)

        reviews.append(
            AmazonReviewItem(
                rating=rating,
                title=title,
                body=body,
                review_date=review_date,
                verified_purchase=verified_purchase,
                helpful_count=helpful_count,
                language="de",
                captured_at=datetime.now(UTC),
            )
        )

    return reviews


def _extract_rating(node) -> int | None:
    candidate = node.select_one('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]')
    if not candidate:
        return None
    text = candidate.get_text(" ", strip=True)
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def _extract_title(node) -> str | None:
    selectors = [
        '[data-hook="review-title"]',
        '[data-hook="reviewTitle"]',
        'h5[data-hook="reviewTitle"]',
    ]
    for selector in selectors:
        candidate = node.select_one(selector)
        if candidate:
            text = normalize_text(candidate.get_text(" ", strip=True))
            if text:
                return text
    return None


def _extract_body(node) -> str | None:
    selectors = [
        '[data-hook="reviewRichContentContainer"]',
        '[data-hook="review-body"]',
        '[data-hook="reviewText"]',
    ]
    for selector in selectors:
        candidate = node.select_one(selector)
        if candidate:
            text = normalize_text(candidate.get_text(" ", strip=True))
            if text:
                return text
    return None


def _extract_review_date(node) -> date | None:
    candidate = node.select_one('[data-hook="review-date"]')
    if not candidate:
        return None
    text = (normalize_text(candidate.get_text(" ", strip=True)) or "").casefold()
    match = re.search(r"(?:am|vom)\s+(\d{1,2})\.\s*([a-zäöü]+)\s+(\d{4})", text)
    if not match:
        return None

    day = int(match.group(1))
    month = GERMAN_MONTHS.get(match.group(2))
    year = int(match.group(3))
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_verified_purchase(node) -> bool | None:
    text = (normalize_text(node.get_text(" ", strip=True)) or "").casefold()
    if "verifizierter kauf" in text:
        return True
    return None


def _extract_helpful_count(node) -> int | None:
    candidate = node.select_one('[data-hook="helpful-vote-statement"]')
    if not candidate:
        return None
    text = (normalize_text(candidate.get_text(" ", strip=True)) or "").casefold()
    if "eine person" in text:
        return 1
    match = re.search(r"(\d+)", text.replace(".", ""))
    return int(match.group(1)) if match else None
