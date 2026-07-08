from fastapi import FastAPI
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import get_settings


def configure_monitoring(app: FastAPI | None = None) -> None:
    settings = get_settings()
    if not settings.sentry_dsn:
        return

    integrations = [CeleryIntegration(), SqlalchemyIntegration()]
    if app is not None:
        integrations.append(FastApiIntegration())

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=integrations,
    )
