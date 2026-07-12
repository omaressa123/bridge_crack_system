import json
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from models import AuditLog


def _serialize(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def log_admin_action(
    db: Session,
    *,
    user_id: Optional[int],
    action: str,
    request: Optional[Request] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    before: Any = None,
    after: Any = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=get_client_ip(request) if request else None,
        before_value=_serialize(before),
        after_value=_serialize(after),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
