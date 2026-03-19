"""Firebase Cloud Function entrypoints for RE-Storage web APIs."""

from __future__ import annotations

import functions_framework
from flask import Request, Response
from flask_cors import cross_origin
from handlers.run_excel import handle_run_excel
from handlers.run_json import handle_run_json


@functions_framework.http
@cross_origin()
def runExcel(request: Request) -> Response:  # noqa: N802
    return handle_run_excel(request)


@functions_framework.http
@cross_origin()
def runJson(request: Request) -> Response:  # noqa: N802
    return handle_run_json(request)
