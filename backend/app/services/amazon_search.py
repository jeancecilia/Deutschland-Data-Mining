from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from threading import Lock
import time
from urllib.parse import parse_qs, quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup
from app.core.config import get_settings
from app.services.book_filters import is_probable_book_listing

try:
    from curl_cffi import requests as curl_requests
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    curl_requests = None

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:  # pragma: no cover - optional runtime dependency
    PlaywrightTimeoutError = None
    sync_playwright = None

from app.services.text_utils import normalize_text


AMAZON_DE_BASE_URL = "https://www.amazon.de"
DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "de-DE,de;q=0.9,en;q=0.8",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="126", "Google Chrome";v="126", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
}
AMAZON_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
AMAZON_BLOCK_MARKERS = (
    "enter the characters you see below",
    "automated access to amazon data",
    "sorry, we just need to make sure you're not a robot",
    "api-services-support@amazon.com",
    "validatecaptcha",
    "robot check",
)
AMAZON_CONSENT_MARKERS = (
    "cookie- und werbeeinstellungen",
    "cookie-und werbeeinstellungen",
    "wenn du zustimmst",
    "cookies speichern oder greifen auf standardgerateinformationen",
    "cookies speichern oder greifen auf standardgeräteinformationen",
)
AMAZON_CONSENT_ACCEPT_SELECTORS = (
    "#sp-cc-accept",
    'input[name="accept"]',
    'button:has-text("Alle akzeptieren")',
    'button:has-text("Akzeptieren")',
    'input[type="submit"][value*="Akzeptieren"]',
    'button:has-text("Accept")',
    'input[type="submit"][value*="Accept"]',
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
MAX_AMAZON_FETCH_ATTEMPTS = 3
AMAZON_CONTENT_READY_SELECTORS = (
    '[data-component-type="s-search-result"]',
    "#search",
    "#centerCol",
    '[data-hook="review"]',
    "#cm_cr-review_list",
    '[data-hook="cr-filter-info-review-rating-count"]',
    "#productTitle",
)
_AMAZON_FETCH_PACING_LOCK = Lock()
_last_amazon_fetch_started_at = 0.0


@dataclass(frozen=True)
class AmazonSearchListing:
    asin: str
    title: str | None
    detail_url: str | None
    is_sponsored: bool
    price: Decimal | None
    rating: float | None
    review_count: int | None
    captured_at: datetime


class AmazonFetchError(RuntimeError):
    pass


class AmazonTransientError(AmazonFetchError):
    pass


class AmazonBlockedError(AmazonFetchError):
    pass


def build_search_url(keyword: str) -> str:
    return f"{AMAZON_DE_BASE_URL}/s?k={quote_plus(keyword)}&i=stripbooks"


def collect_search_results(keyword: str, *, timeout: float = 20.0) -> list[AmazonSearchListing]:
    html = fetch_amazon_html(build_search_url(keyword), timeout=timeout)
    listings = parse_search_results(html)
    if listings:
        return listings
    if _looks_like_consent_html(html):
        raise AmazonTransientError("Amazon returned a consent page without parsable search results.")
    if _looks_like_blocked_html(html):
        raise AmazonBlockedError("Amazon returned a gated search page without parsable listings.")
    return listings


def fetch_amazon_html(
    url: str,
    *,
    timeout: float = 20.0,
    referer: str | None = AMAZON_DE_BASE_URL,
) -> str:
    settings = get_settings()
    fetch_mode = settings.amazon_fetch_mode.casefold().strip()

    if settings.amazon_chrome_bridge_enabled:
        try:
            return _fetch_amazon_html_with_chrome_bridge(url, timeout=timeout, referer=referer)
        except AmazonBlockedError:
            raise
        except AmazonFetchError:
            if fetch_mode == "chrome_bridge":
                raise

    if settings.amazon_browser_enabled and fetch_mode == "playwright":
        return _fetch_amazon_html_with_playwright(url, timeout=timeout, referer=referer)

    if settings.amazon_browser_enabled and fetch_mode == "hybrid":
        try:
            return _fetch_amazon_html_with_playwright(url, timeout=timeout, referer=referer)
        except AmazonBlockedError:
            raise
        except AmazonFetchError:
            pass

    if fetch_mode == "curl":
        if curl_requests is None:
            raise AmazonFetchError("curl_cffi is not available for Amazon fetch mode 'curl'.")
        return _fetch_amazon_html_with_curl(url, timeout=timeout, referer=referer)

    if fetch_mode == "httpx":
        return _fetch_amazon_html_with_httpx(url, timeout=timeout, referer=referer)

    if curl_requests is not None:
        try:
            return _fetch_amazon_html_with_curl(url, timeout=timeout, referer=referer)
        except AmazonFetchError:
            pass

    return _fetch_amazon_html_with_httpx(url, timeout=timeout, referer=referer)


def _fetch_amazon_html_with_chrome_bridge(
    url: str,
    *,
    timeout: float = 20.0,
    referer: str | None = AMAZON_DE_BASE_URL,
) -> str:
    settings = get_settings()
    bridge_url = settings.amazon_chrome_bridge_url.rstrip("/")
    request_timeout = max(timeout, settings.amazon_chrome_bridge_timeout_seconds)

    try:
        response = httpx.post(
            f"{bridge_url}/fetch-html",
            json={
                "url": url,
                "referer": referer,
                "timeout_seconds": request_timeout,
            },
            timeout=request_timeout + 5.0,
        )
    except httpx.TimeoutException as exc:
        raise AmazonTransientError(f"Chrome bridge timed out for {url}: {exc}") from exc
    except httpx.HTTPError as exc:
        raise AmazonTransientError(f"Chrome bridge request failed for {url}: {exc}") from exc

    if response.status_code == 409:
        detail = _extract_bridge_error_detail(response)
        raise AmazonBlockedError(detail or f"Chrome bridge reported a gated Amazon page for {url}")
    if response.status_code >= 500:
        detail = _extract_bridge_error_detail(response)
        raise AmazonTransientError(detail or f"Chrome bridge failed for {url}")
    if response.status_code >= 400:
        detail = _extract_bridge_error_detail(response)
        raise AmazonFetchError(detail or f"Chrome bridge returned {response.status_code} for {url}")

    payload = response.json()
    html = payload.get("html", "")
    final_url = payload.get("final_url") or url
    classified_error = _classify_status_text(200, final_url, html)
    if classified_error is not None:
        raise classified_error
    if _is_search_url(url) and not _html_contains_search_results(html):
        raise AmazonTransientError(f"Chrome bridge returned no parsable Amazon listings for {final_url}")
    return html


def _fetch_amazon_html_with_playwright(
    url: str,
    *,
    timeout: float = 20.0,
    referer: str | None = AMAZON_DE_BASE_URL,
) -> str:
    if sync_playwright is None or PlaywrightTimeoutError is None:
        raise AmazonFetchError("Playwright runtime is not available.")

    settings = get_settings()
    timeout_ms = int(max(timeout, settings.amazon_browser_timeout_seconds) * 1000)
    is_search_request = _is_search_url(url)
    search_keyword = _extract_search_keyword(url) if is_search_request else None
    last_error: AmazonFetchError | None = None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=settings.amazon_browser_headless,
            args=[
                "--disable-dev-shm-usage",
                f"--lang={settings.amazon_browser_locale}",
            ],
        )
        context_kwargs = {
            "locale": settings.amazon_browser_locale,
            "timezone_id": settings.amazon_browser_timezone_id,
            "user_agent": DEFAULT_HEADERS["user-agent"],
            "viewport": {"width": 1440, "height": 1600},
        }
        storage_state_path = _playwright_storage_state_path()
        if storage_state_path is not None and storage_state_path.exists():
            context_kwargs["storage_state"] = str(storage_state_path)
        context = browser.new_context(**context_kwargs)
        context.set_extra_http_headers(_playwright_request_headers(referer=referer))
        try:
            _prime_amazon_session_with_playwright(context, timeout_ms=timeout_ms)
            for attempt in range(1, MAX_AMAZON_FETCH_ATTEMPTS + 1):
                _respect_amazon_fetch_pacing()
                page = context.new_page()
                try:
                    if is_search_request and search_keyword:
                        html = _perform_amazon_search_with_playwright(
                            page,
                            search_keyword,
                            timeout_ms=timeout_ms,
                        )
                    else:
                        html = _open_amazon_target_with_playwright(page, url, timeout_ms=timeout_ms)

                    if _looks_like_consent_html(html):
                        if _accept_amazon_consent(page, timeout_ms=timeout_ms):
                            _save_playwright_storage_state(context)
                            if is_search_request and search_keyword:
                                html = _perform_amazon_search_with_playwright(
                                    page,
                                    search_keyword,
                                    timeout_ms=timeout_ms,
                                )
                            else:
                                html = _open_amazon_target_with_playwright(
                                    page,
                                    url,
                                    timeout_ms=timeout_ms,
                                )

                    _wait_for_amazon_content(page, timeout_ms=timeout_ms)
                    page.wait_for_timeout(settings.amazon_browser_wait_after_load_ms)
                    html = page.content()
                    if _looks_like_blocked_html(html) or "validatecaptcha" in page.url.casefold():
                        last_error = AmazonBlockedError(f"Amazon gated the request for {page.url}")
                    elif _looks_like_consent_html(html):
                        last_error = AmazonTransientError(
                            f"Amazon showed a consent page instead of content for {page.url}"
                        )
                    elif is_search_request and not _html_contains_search_results(html):
                        last_error = AmazonTransientError(
                            f"Amazon search did not expose parsable listings for {page.url}"
                        )
                    else:
                        _save_playwright_storage_state(context)
                        return html
                except PlaywrightTimeoutError:
                    last_error = AmazonTransientError(f"Amazon page timed out for {url}")
                except Exception as exc:
                    last_error = AmazonFetchError(f"Amazon browser fetch failed for {url}: {exc}")
                finally:
                    page.close()

                if attempt < MAX_AMAZON_FETCH_ATTEMPTS:
                    time.sleep(1.5 * attempt)
        finally:
            context.close()
            browser.close()

    raise last_error or AmazonFetchError(f"Amazon browser fetch failed for {url}")


def _fetch_amazon_html_with_httpx(
    url: str,
    *,
    timeout: float = 20.0,
    referer: str | None = AMAZON_DE_BASE_URL,
) -> str:
    last_error: AmazonFetchError | None = None
    with httpx.Client(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=timeout,
        http2=_http2_supported(),
    ) as client:
        _prime_amazon_session(client)
        for attempt in range(1, MAX_AMAZON_FETCH_ATTEMPTS + 1):
            _respect_amazon_fetch_pacing()
            try:
                response = client.get(url, headers=_request_headers(referer=referer))
            except httpx.TimeoutException:
                last_error = AmazonTransientError(f"Amazon request timed out for {url}")
            except httpx.HTTPError as exc:
                last_error = AmazonTransientError(f"Amazon request failed for {url}: {exc}")
            else:
                classified_error = _classify_amazon_response(response)
                if classified_error is None:
                    return response.text
                last_error = classified_error

            if attempt < MAX_AMAZON_FETCH_ATTEMPTS:
                time.sleep(1.25 * attempt)

    raise last_error or AmazonFetchError(f"Amazon fetch failed for {url}")


def _fetch_amazon_html_with_curl(
    url: str,
    *,
    timeout: float = 20.0,
    referer: str | None = AMAZON_DE_BASE_URL,
) -> str:
    assert curl_requests is not None

    session = curl_requests.Session(headers=DEFAULT_HEADERS)
    last_error: AmazonFetchError | None = None
    try:
        _prime_amazon_session_with_curl(session)
        for attempt in range(1, MAX_AMAZON_FETCH_ATTEMPTS + 1):
            _respect_amazon_fetch_pacing()
            try:
                response = session.get(
                    url,
                    headers=_request_headers(referer=referer),
                    allow_redirects=True,
                    timeout=timeout,
                    impersonate="chrome124",
                )
            except Exception as exc:
                last_error = AmazonTransientError(f"Amazon request failed for {url}: {exc}")
            else:
                classified_error = _classify_status_text(
                    response.status_code,
                    str(getattr(response, "url", url)),
                    response.text,
                )
                if classified_error is None:
                    return response.text
                last_error = classified_error

            if attempt < MAX_AMAZON_FETCH_ATTEMPTS:
                time.sleep(1.25 * attempt)
    finally:
        session.close()

    raise last_error or AmazonFetchError(f"Amazon fetch failed for {url}")


def parse_search_results(html: str) -> list[AmazonSearchListing]:
    soup = BeautifulSoup(html, "html.parser")
    listings: list[AmazonSearchListing] = []
    seen_asins: set[str] = set()

    for node in soup.select('[data-component-type="s-search-result"]'):
        asin = (node.get("data-asin") or "").strip()
        if not asin or asin in seen_asins:
            continue

        seen_asins.add(asin)
        captured_at = datetime.now(UTC)
        title = _extract_title(node)
        if not is_probable_book_listing(title):
            continue
        detail_url = _extract_detail_url(node)
        is_sponsored = _extract_is_sponsored(node)
        price = _extract_price(node)
        rating = _extract_rating(node)
        review_count = _extract_review_count(node)

        listings.append(
            AmazonSearchListing(
                asin=asin,
                title=title,
                detail_url=detail_url,
                is_sponsored=is_sponsored,
                price=price,
                rating=rating,
                review_count=review_count,
                captured_at=captured_at,
            )
        )

    return listings


def _wait_for_amazon_content(page, *, timeout_ms: int) -> None:
    selector_timeout_ms = max(1200, min(5000, timeout_ms // max(1, len(AMAZON_CONTENT_READY_SELECTORS))))
    for selector in AMAZON_CONTENT_READY_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=selector_timeout_ms)
            return
        except PlaywrightTimeoutError:
            continue
    page.wait_for_timeout(800)


def _prime_amazon_session(client: httpx.Client) -> None:
    try:
        client.get(
            AMAZON_DE_BASE_URL,
            headers=_request_headers(referer=None, sec_fetch_site="none"),
            timeout=10.0,
        )
    except httpx.HTTPError:
        return


def _prime_amazon_session_with_curl(session) -> None:
    try:
        session.get(
            AMAZON_DE_BASE_URL,
            headers=_request_headers(referer=None, sec_fetch_site="none"),
            allow_redirects=True,
            timeout=10.0,
            impersonate="chrome124",
        )
    except Exception:
        return


def _prime_amazon_session_with_playwright(context, *, timeout_ms: int) -> None:
    page = context.new_page()
    try:
        page.goto(AMAZON_DE_BASE_URL, wait_until="domcontentloaded", timeout=min(timeout_ms, 15000))
        page.wait_for_timeout(600)
        if _looks_like_consent_html(page.content()) and _accept_amazon_consent(page, timeout_ms=timeout_ms):
            _save_playwright_storage_state(context)
    except Exception:
        return
    finally:
        page.close()


def _open_amazon_target_with_playwright(page, url: str, *, timeout_ms: int) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(600)
    html = page.content()
    if _looks_like_consent_html(html) and _accept_amazon_consent(page, timeout_ms=timeout_ms):
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(600)
        html = page.content()
    return html


def _perform_amazon_search_with_playwright(page, keyword: str, *, timeout_ms: int) -> str:
    page.goto(AMAZON_DE_BASE_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(600)

    html = page.content()
    if _looks_like_consent_html(html) and _accept_amazon_consent(page, timeout_ms=timeout_ms):
        page.goto(AMAZON_DE_BASE_URL, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(600)

    search_box = _first_visible_locator(page, AMAZON_SEARCH_BOX_SELECTORS, timeout_ms=3000)
    if search_box is None:
        direct_url = build_search_url(keyword)
        page.goto(direct_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(600)
        return page.content()

    search_box.click()
    search_box.fill("")
    search_box.type(keyword, delay=80)

    submit = _first_visible_locator(page, AMAZON_SEARCH_SUBMIT_SELECTORS, timeout_ms=3000)
    if submit is not None:
        submit.click()
    else:
        search_box.press("Enter")

    page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(600)
    return page.content()


def _first_visible_locator(page, selectors: tuple[str, ...], *, timeout_ms: int):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=timeout_ms):
                return locator
        except Exception:
            continue
    return None


def _accept_amazon_consent(page, *, timeout_ms: int) -> bool:
    if not _looks_like_consent_html(page.content()):
        return False

    click_timeout_ms = min(timeout_ms, 5000)
    for selector in AMAZON_CONSENT_ACCEPT_SELECTORS:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=1500):
                locator.click(timeout=click_timeout_ms)
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1000)
                return True
        except Exception:
            continue
    return False


def _request_headers(*, referer: str | None, sec_fetch_site: str = "same-origin") -> dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    headers["sec-fetch-site"] = sec_fetch_site
    if referer:
        headers["referer"] = referer
    return headers


def _playwright_request_headers(*, referer: str | None) -> dict[str, str]:
    headers = {
        "accept-language": DEFAULT_HEADERS["accept-language"],
        "cache-control": DEFAULT_HEADERS["cache-control"],
    }
    if referer:
        headers["referer"] = referer
    return headers


def _classify_amazon_response(response: httpx.Response) -> AmazonFetchError | None:
    return _classify_status_text(
        response.status_code,
        str(response.request.url),
        response.text,
    )


def _extract_bridge_error_detail(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or None
    return str(payload.get("detail") or payload.get("message") or "").strip() or None


def _classify_status_text(status_code: int, url: str, html: str) -> AmazonFetchError | None:
    if status_code in AMAZON_RETRY_STATUS_CODES:
        return AmazonTransientError(f"Amazon returned {status_code} for {url}")
    if status_code >= 400:
        return AmazonFetchError(f"Amazon returned {status_code} for {url}")
    if _looks_like_consent_html(html):
        return AmazonTransientError(f"Amazon returned a consent page for {url}")
    if _looks_like_blocked_html(html) or "validatecaptcha" in url.casefold():
        return AmazonBlockedError(f"Amazon gated the request for {url}")
    return None


def _looks_like_blocked_html(html: str) -> bool:
    lowered = html.casefold()
    return any(marker in lowered for marker in AMAZON_BLOCK_MARKERS)


def _looks_like_consent_html(html: str) -> bool:
    lowered = html.casefold()
    return any(marker in lowered for marker in AMAZON_CONSENT_MARKERS)


def _html_contains_search_results(html: str) -> bool:
    lowered = html.casefold()
    return (
        'data-component-type="s-search-result"' in html
        or '"componenttype":"s-search-result"' in lowered
        or "s-main-slot" in lowered
    )


def _is_search_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path == "/s" and bool(parse_qs(parsed.query).get("k"))


def _extract_search_keyword(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    value = query.get("k", [None])[0]
    if value is None:
        value = query.get("field-keywords", [None])[0]
    normalized = normalize_text(value) if value else None
    return normalized or None


def _respect_amazon_fetch_pacing() -> None:
    settings = get_settings()
    min_interval_seconds = max(0.0, settings.amazon_fetch_min_interval_seconds)
    if min_interval_seconds == 0:
        return

    global _last_amazon_fetch_started_at
    with _AMAZON_FETCH_PACING_LOCK:
        now = time.monotonic()
        remaining_sleep = min_interval_seconds - (now - _last_amazon_fetch_started_at)
        if remaining_sleep > 0:
            time.sleep(remaining_sleep)
        _last_amazon_fetch_started_at = time.monotonic()


def _playwright_storage_state_path() -> Path | None:
    raw_path = get_settings().amazon_browser_storage_state_path.strip()
    if not raw_path:
        return None
    return Path(raw_path)


def _save_playwright_storage_state(context) -> None:
    storage_state_path = _playwright_storage_state_path()
    if storage_state_path is None:
        return
    storage_state_path.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(storage_state_path))


@lru_cache
def _http2_supported() -> bool:
    try:
        import h2  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _extract_title(node) -> str | None:
    title_selectors = [
        "h2 span",
        "a h2 span",
        '[data-cy="title-recipe-title"]',
    ]
    for selector in title_selectors:
        match = node.select_one(selector)
        if match:
            text = normalize_text(match.get_text(" ", strip=True))
            if text:
                return text
    return None


def _extract_detail_url(node) -> str | None:
    for anchor in node.select("a[href]"):
        href = anchor.get("href")
        if not href:
            continue
        if "/dp/" in href or "/gp/" in href:
            if href.startswith("http"):
                return href
            return f"{AMAZON_DE_BASE_URL}{href}"
    return None


def _extract_is_sponsored(node) -> bool:
    text = node.get_text(" ", strip=True).casefold()
    return "gesponsert" in text or "sponsored" in text


def _extract_price(node) -> Decimal | None:
    offscreen = node.select_one(".a-price .a-offscreen")
    if offscreen:
        parsed = _parse_decimal(offscreen.get_text(strip=True))
        if parsed is not None:
            return parsed

    whole = node.select_one(".a-price-whole")
    fraction = node.select_one(".a-price-fraction")
    if whole and fraction:
        return _parse_decimal(f"{whole.get_text(strip=True)},{fraction.get_text(strip=True)}")

    return None


def _extract_rating(node) -> float | None:
    for candidate in node.select('[aria-label*="von 5 Sternen"], [aria-label*="out of 5 stars"]'):
        label = candidate.get("aria-label", "")
        value = _extract_leading_number(label)
        if value is not None:
            return value
    return None


def _extract_review_count(node) -> int | None:
    selectors = [
        ".a-size-base.s-underline-text",
        '[aria-label$="Bewertungen"]',
        '[aria-label$="ratings"]',
    ]
    for selector in selectors:
        for candidate in node.select(selector):
            text = candidate.get_text(" ", strip=True) or candidate.get("aria-label", "")
            value = _parse_int(text)
            if value is not None:
                return value
    return None


def _extract_leading_number(text: str) -> float | None:
    chars: list[str] = []
    for char in text:
        if char.isdigit() or char in {".", ","}:
            chars.append(char)
        elif chars:
            break
    if not chars:
        return None
    try:
        return float("".join(chars).replace(",", "."))
    except ValueError:
        return None


def _parse_decimal(text: str) -> Decimal | None:
    normalized = (
        text.replace("EUR", "")
        .replace("€", "")
        .replace("\xa0", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    if not normalized:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _parse_int(text: str) -> int | None:
    digits = "".join(char for char in text if char.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None
