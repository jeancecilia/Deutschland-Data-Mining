from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.services.amazon_search import AMAZON_DE_BASE_URL, fetch_amazon_html
from app.services.text_utils import normalize_text


GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


@dataclass(frozen=True)
class AmazonBookDetails:
    asin: str
    title: str | None
    subtitle: str | None
    author: str | None
    publisher: str | None
    formats: str | None
    publication_date: date | None
    page_count: int | None
    description: str | None
    cover_url: str | None
    edition_info: str | None
    primary_category: str | None
    secondary_category: str | None
    tertiary_category: str | None
    table_of_contents: str | None
    bsr_main: int | None
    category_bsr_1: int | None
    category_bsr_2: int | None
    category_bsr_3: int | None


def build_book_detail_url(asin: str) -> str:
    return f"{AMAZON_DE_BASE_URL}/dp/{asin}"


def fetch_book_details(asin: str, *, timeout: float = 20.0) -> AmazonBookDetails:
    html = fetch_amazon_html(build_book_detail_url(asin), timeout=timeout)
    return parse_book_detail_page(asin, html)


def parse_book_detail_page(asin: str, html: str) -> AmazonBookDetails:
    soup = BeautifulSoup(html, "html.parser")

    title = _first_text(
        soup,
        [
            "#productTitle",
            "span#ebooksProductTitle",
            "span.a-size-extra-large",
        ],
    )
    subtitle = _first_text(
        soup,
        [
            "#productSubtitle",
            "#subtitle",
            ".a-section.a-spacing-none.a-text-center span.a-size-medium",
        ],
    )
    author = _extract_author(soup)
    cover_url = _extract_cover_url(soup)
    description = _extract_description(soup)
    formats = _extract_formats(soup)
    categories = _extract_categories(soup)
    table_of_contents = _extract_table_of_contents(soup)

    details_map = _extract_detail_map(soup)
    publication_date = _parse_german_date(
        details_map.get("erscheinungstermin")
        or details_map.get("verlag")
        or details_map.get("publication date")
    )
    publisher = _extract_publisher(details_map)
    edition_info = _extract_edition_info(details_map)
    page_count = _parse_first_int(
        details_map.get("seitenzahl der print-ausgabe")
        or details_map.get("seitenzahl")
        or details_map.get("print length")
    )

    ranking_values = _extract_bsr_values(soup, details_map)

    return AmazonBookDetails(
        asin=asin,
        title=title,
        subtitle=subtitle,
        author=author,
        publisher=publisher,
        formats=formats,
        publication_date=publication_date,
        page_count=page_count,
        description=description,
        cover_url=cover_url,
        edition_info=edition_info,
        primary_category=categories[0],
        secondary_category=categories[1],
        tertiary_category=categories[2],
        table_of_contents=table_of_contents,
        bsr_main=ranking_values[0],
        category_bsr_1=ranking_values[1],
        category_bsr_2=ranking_values[2],
        category_bsr_3=ranking_values[3],
    )


def _first_text(soup: BeautifulSoup, selectors: list[str]) -> str | None:
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = normalize_text(node.get_text(" ", strip=True))
            if text:
                return text
    return None


def _extract_cover_url(soup: BeautifulSoup) -> str | None:
    for selector in ["#landingImage", "#imgBlkFront", ".a-dynamic-image"]:
        node = soup.select_one(selector)
        if node and node.get("src"):
            return node.get("src")
    return None


def _extract_description(soup: BeautifulSoup) -> str | None:
    candidates = [
        "#bookDescription_feature_div .a-expander-content",
        "#productDescription p",
        "#productDescription .a-unordered-list",
    ]
    for selector in candidates:
        node = soup.select_one(selector)
        if node:
            text = normalize_text(node.get_text(" ", strip=True))
            if text:
                return text
    return None


def _extract_table_of_contents(soup: BeautifulSoup) -> str | None:
    selectors = [
        "#feature-bullets ul li",
        "#bookDescription_feature_div li",
        "#editorialReviews_feature_div li",
        "#fromPublisher_feature_div li",
    ]
    items: list[str] = []
    for selector in selectors:
        for node in soup.select(selector):
            text = normalize_text(node.get_text(" ", strip=True))
            if not text or len(text) < 8:
                continue
            if text not in items:
                items.append(text)
        if len(items) >= 4:
            break
    if items:
        return " | ".join(items[:8])
    return None


def _extract_formats(soup: BeautifulSoup) -> str | None:
    values: list[str] = []
    allowed_tokens = [
        "kindle",
        "taschenbuch",
        "gebundenes buch",
        "gebundene ausgabe",
        "hörbuch",
        "audio-cd",
        "spiralbindung",
    ]
    for node in soup.select("#tmmSwatches li, #formats li, #mediaTab_heading_0"):
        text = node.get_text(" ", strip=True)
        if not text:
            continue
        text = normalize_text(text) or ""
        normalized = text.casefold()
        if any(token in normalized for token in allowed_tokens):
            compact = re.sub(r"\s+", " ", text)
            if compact not in values:
                values.append(compact)
    return ", ".join(values) if values else None


def _extract_categories(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    categories: list[str] = []
    for node in soup.select("#wayfinding-breadcrumbs_feature_div a, #bylineInfo_feature_div a"):
        text = normalize_text(node.get_text(" ", strip=True))
        if not text or len(text) < 3:
            continue
        if text not in categories:
            categories.append(text)
    padded = (categories + [None, None, None])[:3]
    return padded[0], padded[1], padded[2]


def _extract_author(soup: BeautifulSoup) -> str | None:
    text = _first_text(
        soup,
        [
            "#bylineInfo",
            ".author a.a-link-normal",
            ".author .a-link-normal",
        ],
    )
    if not text:
        return None
    cleaned = normalize_text(text) or ""
    if cleaned.casefold().startswith("von "):
        cleaned = cleaned[4:]
    cleaned = re.split(r"\bFormat:\b", cleaned, maxsplit=1)[0].strip()
    return cleaned or None


def _extract_detail_map(soup: BeautifulSoup) -> dict[str, str]:
    details: dict[str, str] = {}

    for row in soup.select("#detailBullets_feature_div li"):
        label = row.select_one(".a-text-bold")
        if not label:
            continue
        key = _normalize_label(label.get_text(" ", strip=True))
        text = normalize_text(
            row.get_text(" ", strip=True).replace(label.get_text(" ", strip=True), "", 1).strip(" :")
        )
        if key and text:
            details[key] = text

    for row in soup.select("#productDetailsTable .content li, #detailBulletsWrapper_feature_div li"):
        label = row.select_one("b")
        if not label:
            continue
        key = _normalize_label(label.get_text(" ", strip=True))
        text = normalize_text(
            row.get_text(" ", strip=True).replace(label.get_text(" ", strip=True), "", 1).strip(" :")
        )
        if key and text and key not in details:
            details[key] = text

    for row in soup.select("#productDetails_detailBullets_sections1 tr"):
        heading = row.select_one("th")
        value = row.select_one("td")
        if not heading or not value:
            continue
        key = _normalize_label(heading.get_text(" ", strip=True))
        text = normalize_text(value.get_text(" ", strip=True))
        if key and text:
            details[key] = text

    return details


def _normalize_label(text: str) -> str:
    return (normalize_text(text) or "").strip().strip(":").casefold()


def _extract_publisher(details_map: dict[str, str]) -> str | None:
    publisher_field = details_map.get("verlag") or details_map.get("publisher")
    if not publisher_field:
        return None
    return normalize_text(publisher_field.split(";", 1)[0].strip())


def _extract_edition_info(details_map: dict[str, str]) -> str | None:
    edition = details_map.get("auflage") or details_map.get("edition")
    if edition:
        return normalize_text(edition)

    publisher_field = details_map.get("verlag") or details_map.get("publisher")
    if not publisher_field or ";" not in publisher_field:
        return None
    suffix = normalize_text(publisher_field.split(";", 1)[1].strip())
    return suffix or None


def _extract_bsr_values(soup: BeautifulSoup, details_map: dict[str, str]) -> tuple[int | None, int | None, int | None, int | None]:
    ranking_text = (
        details_map.get("amazon bestseller-rang")
        or details_map.get("best sellers rank")
        or _first_text(
            soup,
            [
                "#detailBulletsWrapper_feature_div",
                "#detailBullets_feature_div",
                "#productDetails_detailBullets_sections1",
            ],
        )
        or ""
    )
    numbers = _extract_rank_numbers(ranking_text)
    padded = (numbers + [None, None, None, None])[:4]
    return padded[0], padded[1], padded[2], padded[3]


def _extract_rank_numbers(text: str) -> list[int | None]:
    matches = re.findall(r"#?([\d\.\,]+)", text)
    values: list[int | None] = []
    for match in matches:
        cleaned = match.replace(".", "").replace(",", "").strip()
        if not cleaned.isdigit():
            continue
        values.append(int(cleaned))
    return values


def _parse_first_int(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    return int(match.group(1))


def _parse_german_date(text: str | None) -> date | None:
    if not text:
        return None

    normalized = (normalize_text(text) or "").casefold().replace("(", " ").replace(")", " ")
    match = re.search(r"(\d{1,2})\.\s*([a-zäöü]+)\s+(\d{4})", normalized)
    if not match:
        return None

    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))
    month = GERMAN_MONTHS.get(month_name)
    if not month:
        return None

    try:
        return date(year, month, day)
    except ValueError:
        return None
