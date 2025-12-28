"""Utility module for sending backend events to an external logging endpoint."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib import request
from urllib.error import URLError, HTTPError


@dataclass(frozen=True)
class ExternalLoggerConfig:
    endpoint_url: str
    token: str


def _load_dotenv() -> None:
    """Load environment variables from a local .env file if present.

    This keeps the dependency footprint minimal by avoiding external dotenv libs.
    """
    dotenv_path = Path.cwd() / ".env"
    if not dotenv_path.exists():
        return

    try:
        contents = dotenv_path.read_text(encoding="utf-8")
    except OSError:
        return

    for line in contents.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_config() -> Optional[ExternalLoggerConfig]:
    _load_dotenv()
    endpoint_url = os.getenv("LOG_ENDPOINT_URL")
    token = os.getenv("LOG_ENDPOINT_TOKEN")
    if not endpoint_url or not token:
        return None
    return ExternalLoggerConfig(endpoint_url=endpoint_url, token=token)


def _send_event(event_type: str, payload: Mapping[str, Any]) -> None:
    config = _get_config()
    if not config:
        return

    body = json.dumps({"event": event_type, "payload": payload}).encode("utf-8")
    req = request.Request(
        config.endpoint_url,
        data=body,
        headers={
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=5):
            return
    except (URLError, HTTPError, ValueError):
        return


def log_login(user_id: str, email: Optional[str] = None, ip_address: Optional[str] = None) -> None:
    _send_event(
        "login",
        {
            "user_id": user_id,
            "email": email,
            "ip_address": ip_address,
        },
    )


def log_product_created(
    product_id: str,
    name: str,
    created_by: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> None:
    _send_event(
        "product.created",
        {
            "product_id": product_id,
            "name": name,
            "created_by": created_by,
            "metadata": dict(metadata or {}),
        },
    )


def log_product_updated(
    product_id: str,
    updated_by: Optional[str] = None,
    changes: Optional[Mapping[str, Any]] = None,
) -> None:
    _send_event(
        "product.updated",
        {
            "product_id": product_id,
            "updated_by": updated_by,
            "changes": dict(changes or {}),
        },
    )


def log_stock_movement(
    product_id: str,
    quantity: float,
    from_location: Optional[str] = None,
    to_location: Optional[str] = None,
    movement_type: Optional[str] = None,
    reference: Optional[str] = None,
) -> None:
    _send_event(
        "stock.movement",
        {
            "product_id": product_id,
            "quantity": quantity,
            "from_location": from_location,
            "to_location": to_location,
            "movement_type": movement_type,
            "reference": reference,
        },
    )
