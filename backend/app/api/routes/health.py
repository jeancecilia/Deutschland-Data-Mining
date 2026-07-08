from fastapi import APIRouter
import httpx
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal


router = APIRouter()


@router.get("")
def health_check() -> dict[str, str]:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))

    return {"status": "ok"}


@router.get("/runtime")
def runtime_health() -> dict[str, object]:
    settings = get_settings()
    bridge_url = settings.amazon_chrome_bridge_url.rstrip("/")
    bridge_status: dict[str, object] = {
        "enabled": settings.amazon_chrome_bridge_enabled,
        "url": bridge_url,
        "status": "disabled",
        "reachable": False,
        "chrome_debugging_ready": False,
        "detail": None,
    }

    if settings.amazon_chrome_bridge_enabled:
        try:
            response = httpx.get(
                f"{bridge_url}/health",
                timeout=min(settings.amazon_chrome_bridge_timeout_seconds, 5.0),
            )
            response.raise_for_status()
            payload = response.json()
            bridge_status.update(
                {
                    "status": str(payload.get("status", "ok")),
                    "reachable": True,
                    "chrome_debugging_ready": bool(payload.get("chrome_debugging_ready", False)),
                    "detail": payload.get("detail"),
                    "browser": payload.get("browser"),
                    "protocol_version": payload.get("protocol_version"),
                    "user_agent": payload.get("user_agent"),
                }
            )
        except (httpx.HTTPError, ValueError) as exc:
            bridge_status.update(
                {
                    "status": "offline",
                    "detail": str(exc),
                }
            )

    runtime_status = "ready"
    if not bridge_status["enabled"]:
        runtime_status = "degraded"
    elif not bridge_status["reachable"] or not bridge_status["chrome_debugging_ready"]:
        runtime_status = "degraded"

    return {
        "status": runtime_status,
        "mode": "desktop_local",
        "requires_authenticated_browser": True,
        "fetch_mode": settings.amazon_fetch_mode,
        "chrome_bridge": bridge_status,
        "browser_automation": {
            "enabled": settings.amazon_browser_enabled,
            "headless": settings.amazon_browser_headless,
            "timeout_seconds": settings.amazon_browser_timeout_seconds,
            "storage_state_path": settings.amazon_browser_storage_state_path,
        },
        "recommended_commands": {
            "desktop_stack": ".\\scripts\\start_desktop_stack.ps1 -Build",
            "bridge_only": ".\\scripts\\start_chrome_bridge.ps1",
        },
    }
