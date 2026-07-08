from __future__ import annotations

from contextlib import suppress
import json
from threading import Lock
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import parse_qs, quote_plus, urlparse

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


AMAZON_BASE_URL = "https://www.amazon.de"
CHROME_CDP_URL = "http://127.0.0.1:9222"
AMAZON_BLOCK_MARKERS = (
    "enter the characters you see below",
    "automated access to amazon data",
    "sorry, we just need to make sure you're not a robot",
    "api-services-support@amazon.com",
    "validatecaptcha",
    "robot check",
    "tut uns leid!",
    "wahrend wir ihre eingabe ausfuhren wollten",
)
AMAZON_CONSENT_MARKERS = (
    "cookie- und werbeeinstellungen",
    "cookie-und werbeeinstellungen",
    "wenn du zustimmst",
)
AMAZON_CONSENT_ACCEPT_SELECTORS = (
    "#sp-cc-accept",
    'input[name="accept"]',
    'button:has-text("Alle akzeptieren")',
    'button:has-text("Akzeptieren")',
    'button:has-text("Accept")',
)
AMAZON_SEARCH_BOX_SELECTORS = (
    "#twotabsearchtextbox",
    'input[name="field-keywords"]',
    'input[type="search"]',
)
AMAZON_SEARCH_SUBMIT_SELECTORS = (
    "#nav-search-submit-button",
    'input[type="submit"][aria-label*="Amazon durchsuchen"]',
    'input[type="submit"][value*="Go"]',
)
AMAZON_REVIEW_LINK_SELECTORS = (
    'a[href*="/portal/customer-reviews/"][href*="show_all_top"]',
    'a[href*="/portal/customer-reviews/"][href*="reviewerType=all_reviews"]',
    'a[data-hook="see-all-reviews-link-foot"]',
    "#acrCustomerReviewLink",
)
AMAZON_CONTENT_READY_SELECTORS = (
    '[data-component-type="s-search-result"]',
    "#search",
    "#centerCol",
    '[data-hook="review"]',
    "#cm_cr-review_list",
    '[data-hook="cr-filter-info-review-rating-count"]',
    "#productTitle",
)

app = FastAPI(title="Chrome Amazon Bridge", version="0.1.0")
_bridge_lock = Lock()


class FetchHtmlRequest(BaseModel):
    url: str
    referer: str | None = AMAZON_BASE_URL
    timeout_seconds: float = Field(default=45.0, ge=5.0, le=180.0)


class FetchHtmlResponse(BaseModel):
    final_url: str
    title: str
    html: str


@app.get("/health")
def health() -> dict[str, object]:
    chrome_debug_url = f"{CHROME_CDP_URL}/json/version"

    try:
        with urlopen(chrome_debug_url, timeout=2.5) as response:
            chrome_payload = json.load(response)
    except (OSError, URLError, ValueError) as exc:
        return {
            "status": "degraded",
            "chrome_debugging_ready": False,
            "chrome_cdp_url": CHROME_CDP_URL,
            "detail": str(exc),
        }

    return {
        "status": "ok",
        "chrome_debugging_ready": True,
        "chrome_cdp_url": CHROME_CDP_URL,
        "browser": chrome_payload.get("Browser"),
        "protocol_version": chrome_payload.get("Protocol-Version"),
        "user_agent": chrome_payload.get("User-Agent"),
    }


@app.post("/fetch-html", response_model=FetchHtmlResponse)
def fetch_html(payload: FetchHtmlRequest) -> FetchHtmlResponse:
    timeout_ms = int(payload.timeout_seconds * 1000)

    with _bridge_lock:
        page = None
        playwright = None
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp(CHROME_CDP_URL)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()

            if _is_search_url(payload.url):
                html = _open_search_url(page, payload.url, timeout_ms=timeout_ms, referer=payload.referer)
            elif _is_reviews_url(payload.url):
                asin = _extract_asin_from_url(payload.url)
                if not asin:
                    raise HTTPException(status_code=400, detail=f"Missing ASIN in reviews URL: {payload.url}")
                html = _open_reviews_from_detail(page, asin, timeout_ms=timeout_ms)
            else:
                html = _open_target(page, payload.url, timeout_ms=timeout_ms, referer=payload.referer)

            title = page.title()
            final_url = page.url

            if _looks_like_blocked_html(html) or "validatecaptcha" in final_url.casefold():
                raise HTTPException(status_code=409, detail=f"Amazon gated the request for {final_url}")
            if _looks_like_consent_html(html):
                raise HTTPException(status_code=503, detail=f"Amazon returned a consent page for {final_url}")

            return FetchHtmlResponse(
                final_url=final_url,
                title=title,
                html=html,
            )
        except PlaywrightTimeoutError as exc:
            raise HTTPException(status_code=503, detail=f"Chrome bridge timed out for {payload.url}: {exc}") from exc
        except PlaywrightError as exc:
            raise HTTPException(status_code=503, detail=f"Chrome bridge failed for {payload.url}: {exc}") from exc
        finally:
            if page is not None:
                with suppress(Exception):
                    page.close()
            if playwright is not None:
                with suppress(Exception):
                    playwright.stop()


def _open_search_url(page, url: str, *, timeout_ms: int, referer: str | None) -> str:
    html = _open_target(page, url, timeout_ms=timeout_ms, referer=referer)
    if _search_page_looks_valid(page, html):
        return html

    keyword = _extract_search_keyword(url)
    if not keyword:
        return html

    fallback_url = f"{AMAZON_BASE_URL}/s?k={quote_plus(keyword)}&i=stripbooks"
    html = _open_target(page, fallback_url, timeout_ms=timeout_ms, referer=referer)
    return html


def _open_target(page, url: str, *, timeout_ms: int, referer: str | None) -> str:
    goto_kwargs = {
        "wait_until": "domcontentloaded",
        "timeout": timeout_ms,
    }
    if referer:
        goto_kwargs["referer"] = referer
    page.goto(url, **goto_kwargs)
    page.wait_for_timeout(1000)
    _accept_consent_if_present(page, timeout_ms=timeout_ms)
    _wait_for_amazon_content(page, timeout_ms=timeout_ms)
    page.wait_for_timeout(1200)
    return page.content()


def _open_reviews_from_detail(page, asin: str, *, timeout_ms: int) -> str:
    page.goto(f"{AMAZON_BASE_URL}/dp/{asin}", wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(1500)
    _accept_consent_if_present(page, timeout_ms=timeout_ms)

    review_link = _first_visible_locator(page, AMAZON_REVIEW_LINK_SELECTORS, timeout_ms=5000)
    if review_link is not None:
        review_link.click(timeout=min(timeout_ms, 5000))
        page.wait_for_url(
            lambda current: "/portal/customer-reviews/" in current or "/product-reviews/" in current,
            timeout=timeout_ms,
        )
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    else:
        page.goto(_build_portal_reviews_url(asin), wait_until="domcontentloaded", timeout=timeout_ms)

    _wait_for_amazon_content(page, timeout_ms=timeout_ms)
    page.wait_for_timeout(2500)
    return page.content()


def _accept_consent_if_present(page, *, timeout_ms: int) -> None:
    html = page.content()
    if not _looks_like_consent_html(html):
        return
    for selector in AMAZON_CONSENT_ACCEPT_SELECTORS:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=1500):
                locator.click(timeout=min(timeout_ms, 5000))
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1200)
                return
        except Exception:
            continue


def _wait_for_amazon_content(page, *, timeout_ms: int) -> None:
    selector_timeout_ms = max(1200, min(5000, timeout_ms // max(1, len(AMAZON_CONTENT_READY_SELECTORS))))
    for selector in AMAZON_CONTENT_READY_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=selector_timeout_ms)
            return
        except PlaywrightTimeoutError:
            continue
    page.wait_for_timeout(800)


def _first_visible_locator(page, selectors: tuple[str, ...], *, timeout_ms: int):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=timeout_ms):
                return locator
        except Exception:
            continue
    return None


def _looks_like_blocked_html(html: str) -> bool:
    lowered = _normalize_html_text(html)
    return any(marker in lowered for marker in AMAZON_BLOCK_MARKERS)


def _looks_like_consent_html(html: str) -> bool:
    lowered = _normalize_html_text(html)
    return any(marker in lowered for marker in AMAZON_CONSENT_MARKERS)


def _search_page_looks_valid(page, html: str) -> bool:
    if '[data-component-type="s-search-result"]' in html:
        return True
    parsed = urlparse(page.url)
    query = parse_qs(parsed.query)
    return parsed.path == "/s" and query.get("i", [None])[0] == "stripbooks"


def _normalize_html_text(value: str) -> str:
    return (
        value.casefold()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
    )


def _is_search_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path == "/s" and bool(parse_qs(parsed.query).get("k"))


def _is_reviews_url(url: str) -> bool:
    parsed = urlparse(url)
    return "/product-reviews/" in parsed.path or "/portal/customer-reviews/" in parsed.path


def _extract_search_keyword(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    keyword = query.get("k", [None])[0] or query.get("field-keywords", [None])[0]
    return keyword.strip() if keyword else None


def _extract_asin_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    for marker in ("dp", "product-reviews", "customer-reviews"):
        if marker in parts:
            index = parts.index(marker)
            if index + 1 < len(parts):
                return parts[index + 1]
    return None


def _build_portal_reviews_url(asin: str, page: int = 1) -> str:
    return (
        f"{AMAZON_BASE_URL}/portal/customer-reviews/{asin}/ref=cm_cr_dp_d_show_all_top"
        f"?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"
    )
