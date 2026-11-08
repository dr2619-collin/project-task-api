"""Deprecation behavior for the original unversioned resource paths."""

from fastapi import Request


async def add_legacy_api_headers(request: Request, call_next):
    """Mark the original unversioned Project and Task paths as deprecated."""
    response = await call_next(request)
    path = request.url.path
    is_legacy_resource_path = any(
        path == prefix or path.startswith(f"{prefix}/")
        for prefix in ("/projects", "/tasks")
    )
    if is_legacy_resource_path:
        successor = f"/api/v1{path}"
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "Wed, 09 Dec 2026 06:00:00 GMT"
        response.headers["Link"] = f'<{successor}>; rel="successor-version"'
    return response
