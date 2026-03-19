"""Handler for Excel-based model runs."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from flask import Request, Response, jsonify
from utils.serialise import serialise_results
from utils.validate import ensure_post_method, ensure_uploaded_file

from re_storage.core.exceptions import REStorageError
from re_storage.pipeline import run_full_model


def handle_run_excel(request: Request) -> Response:
    method_error = ensure_post_method(request)
    if method_error is not None:
        return jsonify({"error": method_error}), 405

    file_error = ensure_uploaded_file(request, "file")
    if file_error is not None:
        return jsonify({"error": file_error}), 400

    uploaded = request.files["file"]
    filename = uploaded.filename or ""
    if not filename.lower().endswith(".xlsx"):
        return jsonify({"error": "Uploaded file must have .xlsx extension"}), 400

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        model_results = run_full_model(Path(tmp_path))
        return jsonify(serialise_results(model_results))
    except REStorageError as exc:
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 422
    except ValueError as exc:
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 400
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": str(exc), "type": type(exc).__name__}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
