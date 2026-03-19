"""Request validation helpers for model run endpoints."""

from __future__ import annotations

from flask import Request


def ensure_post_method(request: Request) -> str | None:
    if request.method != "POST":
        return "Method not allowed. Use POST."
    return None


def ensure_uploaded_file(request: Request, field_name: str) -> str | None:
    if field_name not in request.files:
        return f"Missing required upload: {field_name}"

    uploaded = request.files[field_name]
    if uploaded.filename is None or uploaded.filename.strip() == "":
        return f"Uploaded file for '{field_name}' has no filename"

    return None
